@echo off
rem SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
rem SPDX-License-Identifier: LicenseRef-NvidiaProprietary
rem
rem First-time setup script.
rem Run this once after cloning the repository to populate the webrtc-react webapp
rem submodule (webapp\webrtc-react\).
rem
rem Usage:  setup.bat

SETLOCAL

set SCRIPT_DIR=%~dp0

echo ==================================================
echo   Kit-CAE -- First-time setup
echo ==================================================
echo.
echo Initialising Git submodules...
echo   -^> webapp/webrtc-react  (https://github.com/RGoharimehr/webrtc-react)
echo.

git -C "%SCRIPT_DIR%" submodule update --init --recursive
if %errorlevel% neq 0 (
    echo.
    echo ERROR: git submodule update failed.
    echo        Check your internet connection and that Git is in your PATH.
    exit /b 1
)

if not exist "%SCRIPT_DIR%webapp\webrtc-react\package.json" (
    echo.
    echo ERROR: webapp\webrtc-react\package.json not found after submodule init.
    echo        Check your internet connection and that you have access to
    echo        https://github.com/RGoharimehr/webrtc-react
    exit /b 1
)

echo.
echo Done!  webapp\webrtc-react is now populated.
echo.
echo Next steps:
echo   * To start the full streaming stack (Kit + webapp):
echo       launch_streaming.bat
echo.
echo   * To start the desktop editor only:
echo       repo.bat build -r          (build first, if not already built)
echo       repo.bat launch -n omni.cae.kit
echo.

ENDLOCAL
