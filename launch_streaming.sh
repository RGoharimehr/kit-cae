#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
#
# Launch the Kit-CAE streaming application alongside the WebRTC React webapp.
#
# Usage:
#   ./launch_streaming.sh [-- <extra kit args>]
#
# The script will:
#   1. Initialize the webrtc-react Git submodule if not already present.
#   2. Install Node.js dependencies (npm install).
#   3. Start the React dev server in the background.
#   4. Launch the Kit streaming application (omni.cae_streaming.kit).
#   5. Shut down the React dev server when Kit exits.

set -e

SCRIPT_DIR="$( cd "$(dirname "$0")" ; pwd -P )"
WEBAPP_DIR="${SCRIPT_DIR}/webapp/webrtc-react"
WEBAPP_PORT=3000

# ---------------------------------------------------------------------------
# 1. Ensure the webrtc-react submodule is initialised
# ---------------------------------------------------------------------------
if [ ! -f "${WEBAPP_DIR}/package.json" ]; then
    echo "[launch_streaming] Initialising webrtc-react submodule..."
    if ! git -C "${SCRIPT_DIR}" submodule update --init --recursive webapp/webrtc-react 2>/dev/null; then
        # Fallback: clone directly if the gitlink entry hasn't been committed yet
        echo "[launch_streaming] Submodule not committed; cloning webrtc-react directly..."
        git clone https://github.com/RGoharimehr/webrtc-react "${WEBAPP_DIR}"
    fi
fi

# Verify the submodule was populated
if [ ! -f "${WEBAPP_DIR}/package.json" ]; then
    echo "[launch_streaming] ERROR: webapp/webrtc-react/package.json not found." >&2
    echo "  Make sure you have access to https://github.com/RGoharimehr/webrtc-react" >&2
    echo "  and that git submodule update --init --recursive has been run." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Install Node.js dependencies
# ---------------------------------------------------------------------------
if ! command -v npm &> /dev/null; then
    echo "[launch_streaming] ERROR: 'npm' was not found. Please install Node.js." >&2
    exit 1
fi

echo "[launch_streaming] Installing webapp dependencies..."
npm --prefix "${WEBAPP_DIR}" install

# ---------------------------------------------------------------------------
# 3. Start the React dev server in the background
# ---------------------------------------------------------------------------
echo "[launch_streaming] Starting WebRTC React webapp..."
# Run the dev server in its own process group so we can kill the whole tree later
setsid npm --prefix "${WEBAPP_DIR}" start &
WEBAPP_PID=$!

# Wait up to 30 seconds for the dev server to start accepting connections
echo "[launch_streaming] Waiting for webapp to become ready on port ${WEBAPP_PORT}..."
WAIT_SECS=0
while [ "${WAIT_SECS}" -lt 30 ]; do
    if bash -c "echo > /dev/tcp/127.0.0.1/${WEBAPP_PORT}" 2>/dev/null; then
        break
    fi
    sleep 1
    WAIT_SECS=$((WAIT_SECS + 1))
done

# Open the browser (best-effort; not all environments support xdg-open)
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:${WEBAPP_PORT}" &
elif command -v open &> /dev/null; then
    open "http://localhost:${WEBAPP_PORT}" &
fi

# ---------------------------------------------------------------------------
# 4. Launch the Kit streaming application
# ---------------------------------------------------------------------------
echo "[launch_streaming] Starting Kit-CAE streaming application..."

# Any arguments after '--' are passed through to the Kit app
KIT_EXTRA_ARGS=()
PASS_THROUGH=false
for arg in "$@"; do
    if [ "$arg" = "--" ]; then
        PASS_THROUGH=true
        continue
    fi
    if $PASS_THROUGH; then
        KIT_EXTRA_ARGS+=("$arg")
    fi
done

"${SCRIPT_DIR}/repo.sh" launch -n omni.cae_streaming.kit -- "${KIT_EXTRA_ARGS[@]}" || true

# ---------------------------------------------------------------------------
# 5. Shut down the React dev server once Kit exits
# ---------------------------------------------------------------------------
echo "[launch_streaming] Kit exited. Stopping WebRTC React webapp (PID ${WEBAPP_PID})..."
# Kill the entire process group to ensure webpack child processes are also terminated
kill -- -"${WEBAPP_PID}" 2>/dev/null || kill "${WEBAPP_PID}" 2>/dev/null || true
wait "${WEBAPP_PID}" 2>/dev/null || true
echo "[launch_streaming] Done."
