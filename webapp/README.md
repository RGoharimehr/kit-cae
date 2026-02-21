# WebRTC React Webapp

This directory hosts the [webrtc-react](https://github.com/RGoharimehr/webrtc-react) web frontend
as a Git submodule. It provides the browser-based interface for connecting to the Kit-CAE
streaming session via WebRTC.

## What's included

| Component | Description |
|---|---|
| React app (`src/`) | Browser UI that connects to the Kit WebRTC stream |
| `flownex-bridge/` | Python FastAPI server (port 8001) that bridges Kit USD data to the web UI |
| `omniverse-kit-extension/` | Omniverse Kit extension code (already integrated into kit-cae as `omni.webrtc.flownex_bridge`) |

The React dev server listens on **port 3001**.  
The Kit WebRTC signalling server listens on **port 49100**.

## First-time setup

Initialize and clone the submodule after cloning this repository:

```sh
git submodule update --init --recursive
```

This will populate the `webrtc-react/` subdirectory with the webapp source code.

## Prerequisites

* [Node.js](https://nodejs.org/) 18+ (includes `npm`)
* Python 3.9+ with the bridge dependencies:

  ```sh
  pip install fastapi "uvicorn[standard]"
  ```

  The `flownex-bridge/` Python server is started automatically by `npm start` via `concurrently`.

## Running the full streaming stack

Use the provided launch scripts at the repository root to start both the Kit streaming server and
this webapp together:

```sh
# Linux
./launch_streaming.sh

# Windows
launch_streaming.bat
```

These scripts handle submodule initialization, `npm install`, starting the webpack dev server, and
launching the Kit streaming application automatically.

## Manual setup

```sh
# Install Node.js deps
cd webapp/webrtc-react
npm install

# Start the React dev server + flownex-bridge Python server (both via concurrently)
npm start
# → React app:      http://localhost:3001
# → flownex-bridge: http://localhost:8001
```

Then in a separate terminal start the Kit streaming application:

```sh
./repo.sh launch -n omni.cae_streaming.kit   # Linux
repo.bat  launch -n omni.cae_streaming.kit   # Windows
```
