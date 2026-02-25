#!/bin/bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# First-time setup script.
# Run this once after cloning the repository to populate the webrtc-react webapp
# submodule (webapp/webrtc-react/).
#
# Usage:  ./setup.sh

set -e

SCRIPT_DIR="$( cd "$(dirname "$0")" ; pwd -P )"

echo "=================================================="
echo "  Kit-CAE — First-time setup"
echo "=================================================="
echo ""
echo "Initialising Git submodules..."
echo "  -> webapp/webrtc-react  (https://github.com/RGoharimehr/webrtc-react)"
echo ""

git -C "${SCRIPT_DIR}" submodule update --init --recursive

if [ ! -f "${SCRIPT_DIR}/webapp/webrtc-react/package.json" ]; then
    echo ""
    echo "ERROR: webapp/webrtc-react/package.json not found after submodule init." >&2
    echo "       Check your internet connection and that you have access to" >&2
    echo "       https://github.com/RGoharimehr/webrtc-react" >&2
    exit 1
fi

echo ""
echo "Done!  webapp/webrtc-react is now populated."
echo ""
echo "Next steps:"
echo "  • To start the full streaming stack (Kit + webapp):"
echo "      ./launch_streaming.sh"
echo ""
echo "  • To start the desktop editor only:"
echo "      ./repo.sh build -r          # build first (if not already built)"
echo "      ./repo.sh launch -n omni.cae.kit"
echo ""
