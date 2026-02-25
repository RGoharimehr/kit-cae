# WebRTC React Webapp

> **This directory is a Git submodule.**
> If `webrtc-react/` is **empty**, run the setup script from the repository root:
>
> ```
> # Windows — open a terminal at the repo root and run:
> setup.bat
>
> # Linux
> ./setup.sh
> ```
>
> Or manually: `git submodule update --init --recursive`

This directory hosts the [webrtc-react](https://github.com/RGoharimehr/webrtc-react) web frontend
as a Git submodule. It provides the browser-based interface for connecting to the Kit-CAE
streaming session via WebRTC.

## Submodule verification

After running setup, verify the submodule is populated:

```sh
git submodule status
# Expected (no leading '-'): b0c8410... webapp/webrtc-react (heads/Omnicool-WebApp)
ls webapp/webrtc-react/package.json   # must exist
```

A leading `-` before the commit hash means the submodule is still not initialized — re-run `setup.bat` / `./setup.sh`.

## What's included

| Component | Port | Description |
|---|---|---|
| React app (`src/`) | **3001** | Browser UI that connects to the Kit WebRTC stream |
| `flownex-bridge/` | **8001** | Python FastAPI server bridging Kit USD data to the web UI |
| `stream.config.json` | — | WebRTC signaling configuration (Kit server address) |

The Kit WebRTC signalling server listens on **port 49100**.

## Configuring the Kit server address

The webapp connects to Kit using settings in `webapp/webrtc-react/stream.config.json`:

```json
"local": {
    "server": "127.0.0.1",
    "signalingPort": 49100,
    "mediaPort": null
}
```

| Setting | Default | Change when… |
|---|---|---|
| `server` | `127.0.0.1` | Kit is running on a **different machine** — set to that machine's IP |
| `signalingPort` | `49100` | Kit's WebRTC signaling port was changed |

> **Note:** The `.env` file contains `REACT_APP_OV_SIGNAL_HOST` — this variable is **not read by the app**.
> The only place that controls the Kit server address is `stream.config.json`.

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
