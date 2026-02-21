# WebRTC React Webapp

This directory hosts the [webrtc-react](https://github.com/RGoharimehr/webrtc-react) web frontend
as a Git submodule. It provides the browser-based interface for connecting to the Kit-CAE
streaming session via WebRTC.

## First-time setup

Initialize and clone the submodule after cloning this repository:

```sh
git submodule update --init --recursive
```

This will populate the `webrtc-react/` subdirectory with the webapp source code.

## Manual setup (if submodule is unavailable)

If you need to set up the webapp manually, clone the repository directly:

```sh
git clone https://github.com/RGoharimehr/webrtc-react webrtc-react
```

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
