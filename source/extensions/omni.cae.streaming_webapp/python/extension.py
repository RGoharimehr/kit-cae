# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""
omni.cae.streaming_webapp
=========================
Kit extension loaded by omni.cae_streaming.kit.

On startup it:
  1. Locates the webapp/webrtc-react directory (relative to the repo root).
  2. Checks whether the dev server is already listening on port 3001.
  3. If not, runs `npm install` then `npm start` in a background process.
  4. Waits (async, non-blocking) until port 3001 accepts connections.
  5. Opens the default browser to http://localhost:3001.

On shutdown it terminates the subprocess it started (if any).
"""
from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import webbrowser

import carb
import omni.ext

_WEBAPP_PORT = 3001
_WEBAPP_SUBPATH = os.path.join("webapp", "webrtc-react")


def _find_repo_root() -> str | None:
    """Walk up from this file until we find repo.bat / repo.sh (the repo root).

    12 levels is enough for any reasonable install depth
    (e.g. _build/platform/release/exts/omni.cae.streaming_webapp/python/).
    """
    path = os.path.dirname(os.path.abspath(__file__))
    for _ in range(12):
        if os.path.isfile(os.path.join(path, "repo.bat")) or os.path.isfile(
            os.path.join(path, "repo.sh")
        ):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    return None


def _port_open(port: int) -> bool:
    """Return True if something is already listening on localhost:port."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0):
            return True
    except OSError:
        return False


def _npm() -> str:
    """Return the npm executable name for the current platform."""
    return "npm.cmd" if sys.platform == "win32" else "npm"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:
        self._proc: subprocess.Popen | None = None

        repo_root = _find_repo_root()
        if repo_root is None:
            carb.log_warn(
                "[omni.cae.streaming_webapp] Cannot locate repo root — skipping webapp auto-launch. "
                "Start the webapp manually: cd webapp/webrtc-react && npm start"
            )
            return

        webapp_dir = os.path.join(repo_root, _WEBAPP_SUBPATH)
        if not os.path.isfile(os.path.join(webapp_dir, "package.json")):
            carb.log_warn(
                "[omni.cae.streaming_webapp] webapp/webrtc-react/package.json not found. "
                "Run setup.bat / setup.sh first to initialise the Git submodule."
            )
            return

        if _port_open(_WEBAPP_PORT):
            carb.log_info(
                f"[omni.cae.streaming_webapp] Port {_WEBAPP_PORT} already open — "
                "webapp is already running; opening browser."
            )
            webbrowser.open(f"http://localhost:{_WEBAPP_PORT}")
            return

        carb.log_info(
            f"[omni.cae.streaming_webapp] Starting webrtc-react webapp from {webapp_dir}"
        )

        # npm install (synchronous; fast if node_modules already present)
        try:
            subprocess.run(
                [_npm(), "--prefix", webapp_dir, "install"],
                check=True,
                timeout=180,
            )
        except Exception as exc:
            carb.log_warn(f"[omni.cae.streaming_webapp] npm install failed: {exc}")
            return

        # Start dev server in a new process group so we can kill the whole tree
        try:
            kwargs: dict = {"cwd": webapp_dir}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["start_new_session"] = True

            self._proc = subprocess.Popen(
                [_npm(), "--prefix", webapp_dir, "start"], **kwargs
            )
            carb.log_info(
                f"[omni.cae.streaming_webapp] Webapp process started (PID {self._proc.pid})"
            )
        except Exception as exc:
            carb.log_warn(f"[omni.cae.streaming_webapp] Failed to start webapp: {exc}")
            return

        # Poll for readiness asynchronously so Kit's main thread is not blocked
        asyncio.ensure_future(self._wait_and_open())

    async def _wait_and_open(self) -> None:
        for _ in range(60):  # wait up to 60 seconds
            await asyncio.sleep(1.0)
            if _port_open(_WEBAPP_PORT):
                webbrowser.open(f"http://localhost:{_WEBAPP_PORT}")
                carb.log_info(
                    f"[omni.cae.streaming_webapp] Browser opened → http://localhost:{_WEBAPP_PORT}"
                )
                return
        carb.log_warn(
            f"[omni.cae.streaming_webapp] Webapp did not become ready on port "
            f"{_WEBAPP_PORT} within 60 s."
        )

    def on_shutdown(self) -> None:
        if self._proc is None:
            return

        carb.log_info(
            f"[omni.cae.streaming_webapp] Stopping webapp process (PID {self._proc.pid})…"
        )
        try:
            import signal

            if sys.platform == "win32":
                self._proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(self._proc.pid), signal.SIGTERM)
        except Exception as exc:
            carb.log_warn(f"[omni.cae.streaming_webapp] Error stopping webapp: {exc}")
        finally:
            self._proc = None
