# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# Kit startup script — starts the webrtc-react webapp when omni.cae_streaming.kit launches.
#
# This is a plain Python script referenced by omni.cae_streaming.kit via:
#   [settings.app.python]
#   scripts.'++' = ["${app}/start_webapp.py"]
#
# Kit runs it at startup inside its Python interpreter.
# No extension, no build step, no registry lookup needed.

import os
import socket
import subprocess
import sys
import threading
import webbrowser

_WEBAPP_PORT = 3001
_WEBAPP_SUBPATH = os.path.join("webapp", "webrtc-react")
_MAX_WAIT_SECS = 60


def _find_repo_root():
    """Walk up from this script's location until we find repo.bat / repo.sh."""
    # __file__ may be a symlink (Linux prebuild_link) — resolve both the real
    # path and the link so either works.
    candidates = [os.path.abspath(__file__)]
    try:
        candidates.append(os.path.realpath(__file__))
    except Exception:
        pass

    for start in candidates:
        path = os.path.dirname(start)
        for _ in range(12):
            if os.path.isfile(os.path.join(path, "repo.bat")) or \
               os.path.isfile(os.path.join(path, "repo.sh")):
                return path
            parent = os.path.dirname(path)
            if parent == path:
                break
            path = parent
    return None


def _port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0):
            return True
    except OSError:
        return False


def _npm():
    return "npm.cmd" if sys.platform == "win32" else "npm"


def _run():
    """Main function — runs on a daemon thread so Kit is never blocked."""
    try:
        import carb
        log = lambda msg: carb.log_info(f"[start_webapp] {msg}")
        warn = lambda msg: carb.log_warn(f"[start_webapp] {msg}")
    except Exception:
        log = warn = print

    repo_root = _find_repo_root()
    if repo_root is None:
        warn("Cannot find repo root — skipping webapp auto-launch. "
             "Run: cd webapp/webrtc-react && npm start")
        return

    webapp_dir = os.path.join(repo_root, _WEBAPP_SUBPATH)
    if not os.path.isfile(os.path.join(webapp_dir, "package.json")):
        warn(f"webapp/webrtc-react/package.json not found at {webapp_dir}. "
             "Run setup.bat / setup.sh first.")
        return

    if _port_open(_WEBAPP_PORT):
        log(f"Port {_WEBAPP_PORT} already open — webapp is already running.")
        webbrowser.open(f"http://localhost:{_WEBAPP_PORT}")
        return

    log(f"Starting webrtc-react webapp from {webapp_dir}")

    # npm install (fast no-op if node_modules/ already present)
    try:
        subprocess.run([_npm(), "--prefix", webapp_dir, "install"],
                       check=True, timeout=180)
    except Exception as exc:
        warn(f"npm install failed: {exc}")
        return

    # Start the dev server in its own process group
    try:
        kwargs = {"cwd": webapp_dir}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True

        proc = subprocess.Popen([_npm(), "--prefix", webapp_dir, "start"], **kwargs)
        log(f"Webapp process started (PID {proc.pid})")
    except Exception as exc:
        warn(f"Failed to start webapp: {exc}")
        return

    # Wait for the dev server to become ready, then open the browser
    import time
    for _ in range(_MAX_WAIT_SECS):
        time.sleep(1.0)
        if _port_open(_WEBAPP_PORT):
            webbrowser.open(f"http://localhost:{_WEBAPP_PORT}")
            log(f"Browser opened → http://localhost:{_WEBAPP_PORT}")
            return

    warn(f"Webapp did not become ready on port {_WEBAPP_PORT} within {_MAX_WAIT_SECS}s.")


# Run on a background daemon thread so Kit's main thread is never blocked
threading.Thread(target=_run, daemon=True, name="start_webapp").start()
