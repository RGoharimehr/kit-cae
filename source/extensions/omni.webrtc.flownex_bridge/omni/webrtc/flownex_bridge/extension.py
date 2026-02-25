# omni/webrtc/flownex_bridge/extension.py
#
# Omniverse Kit extension — Flownex WebRTC Bridge
# ────────────────────────────────────────────────
# Bridges the web dashboard and the USD stage.
#
# Supported message protocol (JSON over the Omniverse streaming channel):
#
# Browser → Kit
# ─────────────
#   {
#     "type":      "get_prim_property",
#     "prim_path": "/World/MyPrim",   ← optional: empty/absent → Kit picks at (pick.x, pick.y)
#     "property":  "flownex:componentName",
#     "pick":      { "x": 0.42, "y": 0.61 }   ← normalised 0-1 coords (used when prim_path is empty)
#   }
#
# Kit → Browser
# ─────────────
#   {
#     "type":      "prim_property_result",
#     "prim_path": "/World/MyPrim",
#     "property":  "flownex:componentName",
#     "value":     "Pump_01"          ← null when prim / attribute not found
#   }
from __future__ import annotations

import json
import logging
from typing import Optional, Union

import carb
import omni.ext
import omni.kit.app
import omni.usd

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Messaging API shim
# ---------------------------------------------------------------------------
# The actual API to send messages back to the browser differs between Kit
# versions.  We try the most common paths and fall back gracefully.

def _get_streaming_manager():
    """Return the streaming-manager singleton or None."""
    try:
        import omni.services.streaming.manager as sm
        return sm.get_instance()
    except Exception:
        pass
    try:
        from omni.kit.livestream.messaging import send_message_to_clients
        return None  # handled separately
    except Exception:
        pass
    return None


def _send_message_to_web(payload: dict) -> None:
    """Serialise *payload* and send it to all connected web clients."""
    raw = json.dumps(payload)
    log.info("FlownexBridge: _send_message_to_web — trying to send: %s", raw)

    # Try omni.services.streaming.manager (Kit 105+)
    try:
        import omni.services.streaming.manager as sm
        sm.get_instance().send_message(raw)
        log.info("FlownexBridge: _send_message_to_web — sent via omni.services.streaming.manager")
        return
    except Exception as exc:
        log.info("FlownexBridge: _send_message_to_web — streaming.manager failed: %s", exc)

    # Try omni.kit.livestream.messaging (older Kit)
    try:
        from omni.kit.livestream.messaging import send_message_to_clients
        send_message_to_clients(raw)
        log.info("FlownexBridge: _send_message_to_web — sent via omni.kit.livestream.messaging")
        return
    except Exception as exc:
        log.info("FlownexBridge: _send_message_to_web — livestream.messaging failed: %s", exc)

    # Try direct AppStreamer message bus
    try:
        import omni.kit.app as kit_app
        msg_bus = kit_app.get_app().get_message_bus_event_stream()
        event = carb.events.type_from_string("omni.kit.app.messaging.OUT")
        msg_bus.push(event, payload={"data": raw})
        log.info("FlownexBridge: _send_message_to_web — sent via message bus event stream")
        return
    except Exception as exc:
        log.info("FlownexBridge: _send_message_to_web — message bus failed: %s", exc)

    log.warning("FlownexBridge: _send_message_to_web — ALL send methods exhausted, response not delivered: %s", raw)


# ---------------------------------------------------------------------------
# USD helpers
# ---------------------------------------------------------------------------

def _read_attribute(prim_path: str, attr_name: str) -> object:
    """
    Return the value of *attr_name* on the prim at *prim_path*, or None.
    Handles string, int, float, bool, and Gf/Vt types by converting to
    plain Python objects that are JSON-serialisable.
    """
    ctx = omni.usd.get_context()
    stage = ctx.get_stage() if ctx else None
    if stage is None:
        log.warning("FlownexBridge: no USD stage open")
        return None

    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        log.debug("FlownexBridge: prim not found: %s", prim_path)
        return None

    attr = prim.GetAttribute(attr_name)
    if not attr or not attr.IsValid():
        log.debug("FlownexBridge: attribute '%s' not found on %s", attr_name, prim_path)
        return None

    raw = attr.Get()
    if raw is None:
        return None

    # Convert common USD types to plain Python so json.dumps doesn't fail
    type_name = type(raw).__name__

    # Strings
    if isinstance(raw, str):
        return raw

    # Numeric primitives
    if isinstance(raw, (int, float, bool)):
        return raw

    # GfVec / GfMatrix — convert to list
    if hasattr(raw, "__iter__") and not isinstance(raw, (str, bytes)):
        try:
            return list(raw)
        except Exception:
            pass

    return str(raw)


def _pick_prim_at_ndc(norm_x: float, norm_y: float) -> Optional[str]:
    """
    Perform a viewport pick at normalised device coordinates (0-1) and return
    the USD prim path string, or None when nothing is hit.

    This uses the omni.usd picking API when available.  On older Kit versions
    the async variant is preferred; here we fall back to a synchronous query.
    """
    try:
        from omni.usd.utils import get_world_transform_matrix  # noqa -- side effect import OK
        import omni.kit.viewport.utility as vp_util
        viewport_api = vp_util.get_active_viewport()
        if viewport_api is None:
            log.info("FlownexBridge: _pick_prim_at_ndc — no active viewport found")
            return None

        # Convert normalised coords to pixel coords
        w, h = viewport_api.resolution
        px = int(norm_x * w)
        py = int(norm_y * h)
        log.info("FlownexBridge: _pick_prim_at_ndc — viewport %dx%d, pixel (%d, %d)", w, h, px, py)

        # Kit 105 API
        result = viewport_api.pick(px, py)
        log.info("FlownexBridge: _pick_prim_at_ndc — viewport.pick result: %r", result)
        if result:
            prim_path = str(result.path) if hasattr(result, "path") else str(result)
            resolved = prim_path if prim_path not in ("", "/") else None
            log.info("FlownexBridge: _pick_prim_at_ndc — resolved prim_path=%r", resolved)
            return resolved
    except Exception as exc:
        log.info("FlownexBridge: _pick_prim_at_ndc — viewport utility failed (%s) — trying fallback", exc)

    # Fallback: omni.usd selection (older Kit / no viewport utility)
    try:
        import omni.usd as ousd
        ctx = ousd.get_context()
        if ctx:
            selected = ctx.get_selection().get_selected_prim_paths()
            log.info("FlownexBridge: _pick_prim_at_ndc — selection fallback, selected=%r", selected)
            if selected:
                return selected[0]
    except Exception as exc:
        log.info("FlownexBridge: _pick_prim_at_ndc — selection fallback failed: %s", exc)

    log.info("FlownexBridge: _pick_prim_at_ndc — no prim resolved, returning None")
    return None


# ---------------------------------------------------------------------------
# Extension class
# ---------------------------------------------------------------------------

class FlownexBridgeExtension(omni.ext.IExt):
    """
    Registers a message handler on the Omniverse streaming channel and
    processes *get_prim_property* requests from the web dashboard.
    """

    def on_startup(self, ext_id: str) -> None:
        log.info("FlownexBridge: startup (ext_id=%s)", ext_id)
        self._subscription = None
        self._register_message_handler()

    def on_shutdown(self) -> None:
        log.info("FlownexBridge: shutdown")
        if self._subscription is not None:
            try:
                self._subscription.unsubscribe()
            except Exception:
                pass
            self._subscription = None

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def _register_message_handler(self) -> None:
        """
        Subscribe to incoming messages from the web client.

        Kit 105+ exposes omni.services.streaming.manager; older versions
        use omni.kit.livestream.messaging.  We try both.
        """

        # ── Kit 105+ ──────────────────────────────────────────────────
        try:
            import omni.services.streaming.manager as sm
            mgr = sm.get_instance()
            mgr.register_message_handler(self._on_web_message)
            self._subscription = _UnsubscribeProxy(mgr, self._on_web_message)
            log.info("FlownexBridge: registered via omni.services.streaming.manager")
            return
        except Exception as exc:
            log.debug("FlownexBridge: streaming.manager not available (%s)", exc)

        # ── Older Kit ────────────────────────────────────────────────
        try:
            from omni.kit.livestream.messaging import (
                register_message_handler,
                unregister_message_handler,
            )
            register_message_handler("get_prim_property", self._on_web_message)
            self._subscription = _CallbackUnsubscribe(
                unregister_message_handler,
                "get_prim_property",
                self._on_web_message,
            )
            log.info("FlownexBridge: registered via omni.kit.livestream.messaging")
            return
        except Exception as exc:
            log.debug("FlownexBridge: livestream.messaging not available (%s)", exc)

        log.warning(
            "FlownexBridge: no messaging API found — "
            "get_prim_property queries will not be processed"
        )

    # ------------------------------------------------------------------
    # Message handler
    # ------------------------------------------------------------------

    def _on_web_message(self, raw: Union[str, dict]) -> None:
        """
        Called by the Kit messaging layer whenever the web client sends a
        message over the streaming channel.

        *raw* may be a JSON string or an already-decoded dict depending on
        which API version is installed.
        """
        log.info("FlownexBridge: _on_web_message called, raw type=%s", type(raw).__name__)

        if isinstance(raw, (str, bytes)):
            try:
                msg = json.loads(raw)
                log.info("FlownexBridge: message parsed OK, type=%s", msg.get("type"))
            except json.JSONDecodeError as exc:
                log.warning("FlownexBridge: JSON decode error — %s — raw was: %r", exc, raw)
                return
        elif isinstance(raw, dict):
            msg = raw
            log.info("FlownexBridge: message already a dict, type=%s", msg.get("type"))
        else:
            log.warning("FlownexBridge: unexpected raw type %s — ignoring", type(raw).__name__)
            return

        if msg.get("type") != "get_prim_property":
            log.info("FlownexBridge: ignoring message type=%r", msg.get("type"))
            return

        prim_path: str = msg.get("prim_path") or ""
        attr_name: str = msg.get("property") or ""
        pick_coords: dict = msg.get("pick") or {}

        log.info(
            "FlownexBridge: get_prim_property — prim_path=%r, property=%r, pick=%r",
            prim_path, attr_name, pick_coords,
        )

        # Validate required field
        if not attr_name:
            log.warning("FlownexBridge: 'property' field missing — cannot query")
            return

        # Resolve prim_path via viewport pick when it was not supplied
        if not prim_path:
            norm_x = float(pick_coords.get("x", 0.5))
            norm_y = float(pick_coords.get("y", 0.5))
            log.info("FlownexBridge: no prim_path supplied — picking at NDC (%.3f, %.3f)", norm_x, norm_y)
            prim_path = _pick_prim_at_ndc(norm_x, norm_y) or ""
            log.info("FlownexBridge: viewport pick resolved prim_path=%r", prim_path)

        if not prim_path:
            log.info("FlownexBridge: prim_path still empty after pick — sending null result")
            _send_message_to_web({
                "type":      "prim_property_result",
                "prim_path": "",
                "property":  attr_name,
                "value":     None,
            })
            return

        log.info("FlownexBridge: reading attribute '%s' on prim '%s'", attr_name, prim_path)
        value = _read_attribute(prim_path, attr_name)
        log.info("FlownexBridge: attribute value = %r", value)

        response = {
            "type":      "prim_property_result",
            "prim_path": prim_path,
            "property":  attr_name,
            "value":     value,
        }
        log.info("FlownexBridge: sending response: %r", response)
        _send_message_to_web(response)


# ---------------------------------------------------------------------------
# Helpers for clean subscription teardown
# ---------------------------------------------------------------------------

class _UnsubscribeProxy:
    """Wraps a streaming-manager handler so on_shutdown can deregister it."""

    def __init__(self, mgr, handler):
        self._mgr = mgr
        self._handler = handler

    def unsubscribe(self):
        try:
            self._mgr.unregister_message_handler(self._handler)
        except Exception:
            pass


class _CallbackUnsubscribe:
    """Wraps a (unregister_fn, *args) call for clean teardown."""

    def __init__(self, fn, *args):
        self._fn = fn
        self._args = args

    def unsubscribe(self):
        try:
            self._fn(*self._args)
        except Exception:
            pass
