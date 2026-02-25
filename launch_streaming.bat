@echo off

rem SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
rem SPDX-License-Identifier: LicenseRef-NvidiaProprietary
rem
rem NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
rem property and proprietary rights in and to this material, related
rem documentation and any modifications thereto. Any use, reproduction,
rem disclosure or distribution of this material and related documentation
rem without an express license agreement from NVIDIA CORPORATION or
rem  its affiliates is strictly prohibited.
rem
rem Launch the Kit-CAE streaming application alongside the WebRTC React webapp.
rem
rem Usage:
rem   launch_streaming.bat [-- <extra kit args>]
rem
rem The script will:
rem   1. Initialise the webrtc-react Git submodule if not already present.
rem   2. Install Node.js dependencies (npm install).
rem   3. Start the React dev server in a new window.
rem   4. Launch the Kit streaming application (omni.cae_streaming.kit).
rem   5. Prompt to close the React dev server window when Kit exits.

SETLOCAL ENABLEDELAYEDEXPANSION

set SCRIPT_DIR=%~dp0
set WEBAPP_DIR=%SCRIPT_DIR%webapp\webrtc-react
rem Port is set in webapp\webrtc-react\.env (PORT=3001)
set WEBAPP_PORT=3001

rem ---------------------------------------------------------------------------
rem 1. Ensure the webrtc-react submodule is initialised
rem ---------------------------------------------------------------------------
if not exist "%WEBAPP_DIR%\package.json" (
    echo [launch_streaming] Initialising webrtc-react submodule...
    git -C "%SCRIPT_DIR%" submodule update --init --recursive webapp/webrtc-react
    if %errorlevel% neq 0 (
        rem Fallback: clone directly if the gitlink entry hasn't been committed yet
        echo [launch_streaming] Submodule not committed; cloning webrtc-react directly...
        git clone https://github.com/RGoharimehr/webrtc-react "%WEBAPP_DIR%"
    )
)

if not exist "%WEBAPP_DIR%\package.json" (
    echo [launch_streaming] ERROR: webapp\webrtc-react\package.json not found.
    echo   Make sure you have access to https://github.com/RGoharimehr/webrtc-react
    echo   and that "git submodule update --init --recursive" has been run.
    exit /b 1
)

rem ---------------------------------------------------------------------------
rem 2. Install Node.js dependencies
rem ---------------------------------------------------------------------------
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [launch_streaming] ERROR: 'npm' was not found. Please install Node.js.
    exit /b 1
)

rem The webapp's 'npm start' also launches the flownex-bridge Python server via
rem concurrently (see flownex-bridge/requirements.txt: fastapi, uvicorn).
rem Warn the user early if Python is missing.
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [launch_streaming] WARNING: Python was not found. The flownex-bridge server
    echo   ^(started by 'npm start'^) requires Python with fastapi and uvicorn installed.
    echo   Install: pip install fastapi "uvicorn[standard]"
)

echo [launch_streaming] Installing webapp dependencies...
npm --prefix "%WEBAPP_DIR%" install
if %errorlevel% neq 0 ( exit /b %errorlevel% )

rem ---------------------------------------------------------------------------
rem 3. Start the React dev server in a new console window
rem ---------------------------------------------------------------------------
echo [launch_streaming] Starting WebRTC React webapp...
start "WebRTC React Webapp" cmd /k "npm --prefix "%WEBAPP_DIR%" start"

rem Wait up to 30 seconds for the dev server to start accepting connections on WEBAPP_PORT
echo [launch_streaming] Waiting for webapp to become ready on port %WEBAPP_PORT%...
set WAIT_SECS=0
:WaitLoop
if %WAIT_SECS% GEQ 30 goto WaitDone
powershell -NoProfile -Command "try { (New-Object Net.Sockets.TcpClient('127.0.0.1', %WEBAPP_PORT%)).Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% EQU 0 goto WaitDone
timeout /t 1 /nobreak >nul
set /a WAIT_SECS=%WAIT_SECS%+1
goto WaitLoop
:WaitDone

rem Open the browser
start "" "http://localhost:%WEBAPP_PORT%"

rem ---------------------------------------------------------------------------
rem 4. Launch the Kit streaming application
rem ---------------------------------------------------------------------------
echo [launch_streaming] Starting Kit-CAE streaming application...

rem Collect any extra Kit arguments passed after '--'
set PASS_THROUGH=0
set KIT_EXTRA_ARGS=
for %%A in (%*) do (
    if "%%A"=="--" (
        set PASS_THROUGH=1
    ) else if !PASS_THROUGH!==1 (
        set KIT_EXTRA_ARGS=!KIT_EXTRA_ARGS! %%A
    )
)

call "%SCRIPT_DIR%repo.bat" launch -n omni.cae_streaming.kit -- %KIT_EXTRA_ARGS%

rem ---------------------------------------------------------------------------
rem 5. Notify about the webapp window
rem ---------------------------------------------------------------------------
echo [launch_streaming] Kit exited. Close the "WebRTC React Webapp" console window to stop the dev server.

ENDLOCAL
