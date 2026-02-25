# Kit-CAE — Omniverse CAE Sample Application

[![Version](https://img.shields.io/badge/version-1.5.0-blue.svg)](CHANGELOG.md)
[![Kit SDK](https://img.shields.io/badge/Kit%20SDK-109.0.1-green.svg)](tools/deps/kit-sdk.packman.xml)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey.svg)](#system-requirements)

Kit-CAE is an NVIDIA Omniverse sample application that demonstrates **Computer-Aided Engineering (CAE) data processing and rendering** workflows. It showcases how to build domain-specific Omniverse extensions on top of the Kit SDK for scientific datasets — including CGNS, HDF5, NumPy, EnSight, and VTK file formats — and how to stream the 3D viewport to a React-based web browser interface via WebRTC.

![Kit-CAE Based Editor](./docs/kit-cae-based-editor.png)

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Getting Started — First Clone](#getting-started--first-clone)
3. [Building](#building)
   - [Linux](#linux)
   - [Windows](#windows)
4. [Running the Application](#running-the-application)
   - [Desktop Editor](#desktop-editor)
   - [VTK-powered Variant](#vtk-powered-variant)
   - [Streaming with WebRTC React Webapp](#streaming-with-webrtc-react-webapp)
5. [Installing Optional PIP Dependencies](#installing-optional-pip-dependencies)
6. [Sample Scripts](#sample-scripts)
7. [Project Structure](#project-structure)
8. [Extension Overview](#extension-overview)
9. [USD Schema](#usd-schema)
10. [Architecture — Data Delegate & Operator Commands](#architecture--data-delegate--operator-commands)
11. [Combining with Kit Application Template (KAT) Apps](#combining-with-kit-application-template-kat-apps)
12. [User Guide](#user-guide)
13. [License & Third-Party Credits](#license--third-party-credits)
14. [Contributing](#contributing)
15. [Security](#security)

---

## System Requirements

| Requirement | Details |
|---|---|
| **OS** | Linux x86-64 or Windows 10/11 x86-64 |
| **GPU** | NVIDIA RTX GPU (Turing or later recommended) |
| **Driver** | Latest NVIDIA driver supporting the Kit SDK |
| **Kit SDK** | 109.0.1 (downloaded automatically by the build) |
| **C++ toolchain** (Windows) | Visual Studio 2019 or 2022 with C++ build tools and Windows SDK |
| **Python** | 3.9+ (bundled with Kit; system Python needed only for the `flownex-bridge` server) |
| **Node.js** (streaming mode only) | 18+ (includes `npm`) |
| **Git** | Any recent version; `git lfs` is **not** required |

---

## Getting Started — First Clone

> **`webapp/webrtc-react` is empty?**
> This is normal if you cloned without `--recurse-submodules`.
> Run the one-step setup script to populate it:
> ```
> # Windows
> setup.bat
>
> # Linux
> ./setup.sh
> ```

This repository uses a **Git submodule** for the WebRTC React webapp under `webapp/webrtc-react/`.
The simplest way to get everything in one go:

```sh
# Linux / macOS
git clone --recurse-submodules https://github.com/RGoharimehr/kit-cae
cd kit-cae

# Windows
git clone --recurse-submodules https://github.com/RGoharimehr/kit-cae
cd kit-cae
```

**Already cloned without `--recurse-submodules`?** Run the setup script once:

```sh
# Windows — double-click or run in any terminal
setup.bat

# Linux
./setup.sh
```

Both scripts run `git submodule update --init --recursive` and print next-step instructions.

---

## Building

The build system is driven by `repo.sh` (Linux) / `repo.bat` (Windows). These scripts bootstrap a Packman-managed Python environment and download all required dependencies (Kit SDK, native libraries, headers) automatically.

### Linux

```sh
# Step 1 — Build USD schemas (C++)
./repo.sh schema

# Step 2 — Build all extensions (-r = release config)
./repo.sh build -r
```

### Windows

#### Visual Studio 2019

```bat
:: Step 1 — Build USD schemas
repo.bat schema

:: Step 2 — Build extensions
repo.bat --set-token vs_version:vs2019 build -r
```

#### Visual Studio 2022

```bat
:: Step 1 — Build USD schemas
repo.bat schema --vs2022

:: Step 2 — Build extensions
repo.bat --set-token vs_version:vs2022 build -r
```

> **Tip:** You can also edit `repo.toml` and set `vs_version = "vs2019"` or `vs_version = "vs2022"` permanently instead of passing the token on the command line.

Use `./repo.sh --help` or `./repo.sh [tool] --help` to see all available options.

---

## Running the Application

### Desktop Editor

Launches the full Kit-CAE editor with the Omniverse viewport:

```sh
# Linux
./repo.sh launch -n omni.cae.kit

# Windows
repo.bat launch -n omni.cae.kit
```

### VTK-powered Variant

Includes VTK-based algorithms (streamlines, VTK file import, etc.). Requires the VTK pip package — see [Installing Optional PIP Dependencies](#installing-optional-pip-dependencies) first.

```sh
# Linux
./repo.sh launch -n omni.cae_vtk.kit

# Windows
repo.bat launch -n omni.cae_vtk.kit
```

### Streaming with WebRTC React Webapp

Kit-CAE ships a streaming configuration (`omni.cae_streaming.kit`) that streams the 3D viewport over WebRTC to the **[webrtc-react](https://github.com/RGoharimehr/webrtc-react)** web dashboard. This is the only Kit app that starts the WebRTC server — the other two apps (`omni.cae.kit`, `omni.cae_vtk.kit`) are desktop-only.

#### How to Launch (standard command)

```sh
# Linux
./repo.sh launch -n omni.cae_streaming.kit

# Windows
repo.bat launch -n omni.cae_streaming.kit
```

**This single command starts everything automatically:**
- Kit opens and begins streaming on port **49100**
- The `omni.cae.streaming_webapp` extension starts the React dev server (`npm start`) on port **3001**
- Your default browser opens to `http://localhost:3001`

#### Prerequisites

1. First-time only: run `setup.bat` / `./setup.sh` to populate `webapp/webrtc-react/` (see [Getting Started](#getting-started--first-clone))
2. [Node.js 18+](https://nodejs.org/) must be installed

#### How It Works

```
  repo.bat launch -n omni.cae_streaming.kit
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│  omni.cae_streaming.kit                                 │
│  ├─ omni.kit.livestream.webrtc  →  WebRTC  port 49100   │
│  └─ omni.cae.streaming_webapp   →  starts npm start     │
│                                     opens browser        │
└───────────────────┬─────────────────────────────────────┘
                    │ WebRTC video + signaling
┌───────────────────▼─────────────────────────────────────┐
│  Browser  http://localhost:3001  (React webapp)          │
└─────────────────────────────────────────────────────────┘
```

| Service | Port | Who starts it |
|---|---|---|
| Kit WebRTC signaling | **49100** | `omni.kit.livestream.webrtc` |
| React dev server | **3001** | `omni.cae.streaming_webapp` extension |
| flownex-bridge | **8001** | `npm start` (via `concurrently` inside the webapp) |

#### Alternative: launch_streaming scripts

The `launch_streaming.bat` / `launch_streaming.sh` scripts at the repo root do the same job but also handle submodule init and `npm install` before launching Kit:

```sh
# Linux
./launch_streaming.sh

# Windows
launch_streaming.bat
```

Use these scripts if you need the extra safety net (e.g. first run on a fresh clone before the submodule is initialised).

Pass extra Kit arguments after `--`:

```sh
# Linux example
./launch_streaming.sh -- --/app/renderer/resolution/width=1280

# Windows example
launch_streaming.bat -- --/app/renderer/resolution/width=1280
```

#### Manual Launch (Two-Terminal)

```sh
# Terminal 1 — webapp + flownex-bridge
cd webapp/webrtc-react
npm install
npm start          # React → :3001, flownex-bridge → :8001

# Terminal 2 — Kit streaming app
./repo.sh launch -n omni.cae_streaming.kit   # Linux
repo.bat  launch -n omni.cae_streaming.kit   # Windows
```

---

## Installing Optional PIP Dependencies

Certain extensions use external Python packages (VTK, h5py). Because the Kit sandbox does not use an online pip index, you must download the packages first and then point Kit to the archive directory.

**Download:**

```sh
# Linux
./repo.sh pip_download --dest /tmp/pip_archives -r ./tools/deps/requirements.txt

# Windows
repo.bat pip_download --dest C:/temp/pip_archives -r ./tools/deps/requirements.txt
```

**Launch with archives (note the required `[` and `]`):**

```sh
# Linux
./repo.sh launch -n omni.cae_vtk.kit -- --/exts/omni.kit.pipapi/archiveDirs=[/tmp/pip_archives]

# Windows
repo.bat launch -n omni.cae_vtk.kit -- --/exts/omni.kit.pipapi/archiveDirs=[C:/temp/pip_archives]
```

This is only needed on the **first launch** (or after a cache cleanup). Packages are cached locally afterward.

Current required packages (see `tools/deps/requirements.txt`):

| Package | Version | Used by |
|---|---|---|
| `vtk` | 9.4 | `omni.cae.vtk`, `omni.cae.algorithms.vtk` |
| `h5py` | 3.13 | `omni.cae.hdf5` |

---

## Sample Scripts

The `scripts/` directory contains ready-to-run Python scripts that exercise Kit-CAE algorithms. Run them by passing `--exec` to the launcher:

```sh
# Linux
./repo.sh launch -n omni.cae.kit -- --exec scripts/example-bounding-box.py

# Windows
repo.bat launch -n omni.cae.kit -- --exec scripts/example-bounding-box.py
```

Scripts that depend on VTK must use `omni.cae_vtk.kit`:

```sh
# Linux
./repo.sh launch -n omni.cae_vtk.kit -- --exec scripts/example-streamlines.py
```

| Script | Description |
|---|---|
| `example-bounding-box.py` | Computes and visualises dataset bounding boxes |
| `example-faces.py` | Renders external surface faces |
| `example-glyphs.py` | Renders arrow/cone/sphere glyphs at point locations |
| `example-headsq-vti.py` | Loads a VTI medical volume (`headsq.vti`) |
| `example-npz.py` | Imports a NumPy `.npz` dataset |
| `example-npz-point-cloud.py` | Point cloud from an NPZ file |
| `example-npz-volume-streamlines.py` | Streamlines over an NPZ volume (VTK required) |
| `example-points.py` | Scalar-coloured point cloud |
| `example-slice.py` | 2D cross-section slice through a dataset |
| `example-slice-on-volume.py` | Slice displayed on a volume render |
| `example-streamlines.py` | Particle-advection streamlines (VTK required) |
| `example-volume.py` | IndeX volume rendering |
| `example-nvdb-slice.py` | NanoVDB slice rendering |
| `example-nvdb-slice-on-volume.py` | NanoVDB slice on a volume render |

---

## Project Structure

```
kit-cae/
├── data/                        # Sample CAE data files (CGNS, NPZ, VTK, …)
├── docs/                        # Architecture diagrams, Data Delegate & Operator Commands docs
│   ├── DataDelegate.md
│   ├── Extensions.svg
│   └── OperatorCommands.md
├── scripts/                     # Runnable Python example scripts
├── source/
│   ├── apps/
│   │   ├── omni.cae.kit         # Desktop editor app config (.kit)
│   │   ├── omni.cae_vtk.kit     # VTK-enabled variant
│   │   └── omni.cae_streaming.kit   # WebRTC streaming variant
│   └── extensions/              # All Omniverse extensions (see table below)
│       ├── omni.cae.*           # CAE-specific extensions
│       └── omni.webrtc.flownex_bridge  # WebRTC↔USD bridge extension
├── stages/                      # Sample USD stages
├── tools/
│   └── deps/                    # Packman dependency XMLs, pip requirements
├── usdSchema/                   # USD schema source (C++) + documentation
├── webapp/
│   └── webrtc-react/            # Git submodule → webrtc-react webapp
├── launch_streaming.sh          # One-command streaming launcher (Linux)
├── launch_streaming.bat         # One-command streaming launcher (Windows)
├── repo.sh / repo.bat           # Main build/launch entry points
└── repo.toml                    # Repository configuration
```

---

## Extension Overview

All extensions live under `source/extensions/`. The diagram below shows the high-level dependency relationships:

![Extension Diagram](./docs/Extensions.svg)

### USD Schema Extensions

| Extension | Description |
|---|---|
| `omni.cae.schema` | Loads the CAE USD schemas into Omniverse at startup |
| `omni.cae.algorithms.schema` | Loads codeless USD schemas for algorithm prims |

### Data Importer Extensions

These extensions add items to the **File › Import** menu.

| Extension | Formats | Notes |
|---|---|---|
| `omni.cae.asset_importer.cgns` | `.cgns` | Relies on `omni.cae.file_format.cgns` |
| `omni.cae.asset_importer.npz` | `.npz`, `.npy` | NumPy array files |
| `omni.cae.asset_importer.vtk` | `.vtk`, `.vti`, `.vtu` | Limited VTK support |
| `omni.cae.asset_importer.ensight` | `.case` | EnSight Gold CASE; surface meshes only |

### Data Delegate Implementations

These extensions implement the `IDataDelegate` interface so that algorithms can read raw data out of `CaeFieldArray` prims.

| Extension | Format / Data model | Language |
|---|---|---|
| `omni.cae.file_format.cgns` | CGNS file format (USD plugin) | C++ |
| `omni.cae.cgns` | CGNS / SIDS data delegate | C++ |
| `omni.cae.hdf5` | HDF5 data delegate | C++ |
| `omni.cae.npz` | NumPy (`.npy` / `.npz`) | Python |
| `omni.cae.ensight` | EnSight Gold CASE | Python |
| `omni.cae.vtk` | VTK file formats | Python |
| `omni.cae.sids` | CGNS SIDS unstructured operator commands | Python |

### Algorithm Extensions

| Extension | Technology | Capabilities |
|---|---|---|
| `omni.cae.algorithms.core` | Pure USD/USDRT | Points, Glyphs, External Faces, Bounding Box, Slice, Streamlines, Volume |
| `omni.cae.algorithms.warp` | NVIDIA Warp | GPU-accelerated voxelisation, NanoVDB streamlines |
| `omni.cae.algorithms.vtk` | VTK | Streamlines, surface extraction, unstructured grid processing |
| `omni.cae.index` | NVIDIA IndeX | Irregular-grid & NanoVDB volume rendering |
| `omni.cae.flow` | NVIDIA Flow | Fluid simulation rendering |

### UI Extensions

| Extension | Description |
|---|---|
| `omni.cae.context_menu` | Right-click context menus in the Stage widget for CAE operations |
| `omni.cae.property.bundle` | Custom property panel widgets for CAE prim types |
| `omni.cae.widget.stage_icons` | Custom icons for CAE prim types in the Stage widget |

### WebRTC Bridge Extension

| Extension | Description |
|---|---|
| `omni.webrtc.flownex_bridge` | Handles `get_prim_property` / `prim_property_result` JSON messages between the React web dashboard and the USD stage over the Omniverse streaming channel |

---

## USD Schema

Kit-CAE extends USD with domain-specific prim types for scientific datasets. Full details are in [`usdSchema/README.md`](./usdSchema/README.md).

![USD Schema](./usdSchema/docs/OmniCae.schema.svg)

### Core Prim Types

| Prim Type | Description |
|---|---|
| `CaeDataSet` | Top-level container for a scientific dataset. Similar to `UsdVolVolume`. Holds field relationships and carries data-model API schemas. |
| `CaeFieldArray` | Represents one named data array in a dataset. Subtypes carry file-specific attributes. |
| `CaeCgnsFieldArray` | `CaeFieldArray` subtype for CGNS/HDF5 data |
| `CaeNumPyFieldArray` | `CaeFieldArray` subtype for NumPy data |
| `CaeHdf5FieldArray` | `CaeFieldArray` subtype for raw HDF5 data |

### Data Model API Schemas

API schemas applied to `CaeDataSet` prims tell algorithms how to interpret the field arrays:

| API Schema | Describes |
|---|---|
| `CaePointCloudAPI` | Unordered set of 3D points |
| `CaeSidsUnstructuredAPI` | CGNS SIDS unstructured mesh (elements, connectivity) |

### Minimal USD Example

```usda
#usda 1.0

def Xform "World"
{
    def CaeDataSet "Simulation" (
        prepend apiSchemas = ["CaeSidsUnstructuredAPI"]
    )
    {
        token cae:sids:elementType = "HEXA_8"
        rel field:temperature = <Arrays/Temperature>
        rel field:pressure    = <Arrays/Pressure>

        def Scope "Arrays"
        {
            def CaeCgnsFieldArray "Temperature"
            {
                asset[] fileNames = [@StaticMixer.cgns@]
                string fieldPath  = "/Base/StaticMixer/Flow Solution/Temperature"
            }
            def CaeCgnsFieldArray "Pressure"
            {
                asset[] fileNames = [@StaticMixer.cgns@]
                string fieldPath  = "/Base/StaticMixer/Flow Solution/Pressure"
            }
        }
    }
}
```

---

## Architecture — Data Delegate & Operator Commands

### Data Delegate

The **Data Delegate** system ([`docs/DataDelegate.md`](./docs/DataDelegate.md)) is the extensible I/O layer in Kit-CAE. It decouples *data format* from *algorithm*:

- `IDataDelegateRegistry` (singleton) is the central hub. Any extension can query it for a field array given a `CaeFieldArray` prim.
- `IDataDelegate` implementations know how to read one concrete format. Multiple delegates can be registered; the registry tries them in priority order.
- `IFieldArray` is a device-aware, reference-counted N-dimensional array that supports the **NumPy Array Interface** and the **CUDA Array Interface**, enabling zero-copy handoff to NumPy, CuPy, or NVIDIA Warp.

**Python usage:**

```python
from omni.cae.data import get_data_delegate_registry

registry = get_data_delegate_registry()
prim = stage.GetPrimAtPath("/World/Simulation/Arrays/Temperature")
temperature = registry.get_field_array(prim, time_code)   # → IFieldArray (NAI/CAI)

# Async variant (non-blocking)
temperature = await registry.get_field_array_async(prim, time_code)
```

### Operator Commands

**Operator Commands** ([`docs/OperatorCommands.md`](./docs/OperatorCommands.md)) are Kit commands (`omni.kit.commands`) that operate on `CaeDataSet` prims in a data-model-agnostic way. They are resolved at runtime using the applied API schemas and the USD prim type hierarchy.

| Command | Module | Description |
|---|---|---|
| `ComputeBounds` | `omni.cae.data.commands` | Bounding box of a dataset |
| `ComputeIJKExtents` | `omni.cae.data.commands` | Structured IJK extents (with optional ROI) |
| `ConvertToPointCloud` | `omni.cae.data.commands` | Dataset → `PointCloud` (coords + fields) |
| `ConvertToMesh` | `omni.cae.data.commands` | Dataset → surface `Mesh` |
| `Voxelize` | `omni.cae.data.commands` | Dataset → NanoVDB `wp.Volume` |
| `GenerateStreamlines` | `omni.cae.data.commands` | Particle advection over a vector field |
| `ConvertToVTKDataSet` | `omni.cae.vtk.commands` | Dataset → VTK dataset |
| `CreateIrregularVolumeSubset` | `omni.cae.index.commands` | Dataset → IndeX unstructured volume |

**Python usage:**

```python
from omni.cae.data.commands import ComputeBounds, ConvertToPointCloud

async def example(dataset_prim, time_code):
    # Bounding box
    bounds = await ComputeBounds.invoke(dataset_prim, timeCode=time_code)

    # Point cloud with two field arrays
    cloud = await ConvertToPointCloud.invoke(
        dataset_prim,
        fields=["Temperature", "Pressure"],
        timeCode=time_code
    )
    print(cloud.coords.shape)         # (N, 3) float32
    print(cloud.fields["Temperature"].shape)
```

---

## Combining with Kit Application Template (KAT) Apps

All Kit-CAE extensions can be imported into any [Kit Application Template](https://github.com/NVIDIA-Omniverse/kit-app-template)-based application with a compatible Kit SDK version. Verify compatibility by comparing the `kit-kernel` version in `tools/deps/kit-sdk.packman.xml`.

### Running Locally

```sh
# From your KAT application directory (Linux)
./repo.sh launch -n <your-app> -- \
    --ext-folder <path-to-kit-cae>/_build/linux-x86_64/release/exts \
    --ext-folder <path-to-kit-cae>/_build/linux-x86_64/release/apps \
    --enable omni.cae
```

Use `--enable omni.cae_vtk` for the VTK variant, or `--enable <ext-name>` for individual extensions.

### Packaging Together

1. Place Kit-CAE under your KAT app, e.g. `vendor/kit-cae`, and build it there.

2. Add to the end of your KAT app's `premake5.lua`:

   ```lua
   repo_build.prebuild_link {
       { "%{root}/vendor/kit-cae/_build/%{platform}/%{config}/apps",
         "%{root}/_build/%{platform}/%{config}/kit-cae/apps" },
       { "%{root}/vendor/kit-cae/_build/%{platform}/%{config}/exts",
         "%{root}/_build/%{platform}/%{config}/kit-cae/exts" },
   }
   ```

3. Update `settings.app.exts.folders` in each of your `.kit` files:

   ```toml
   [settings.app.exts]
   folders.'++' = [
       "${app}/../apps",
       "${app}/../exts",
       "${app}/../extscache/",
       "${app}/../kit-cae/apps",
       "${app}/../kit-cae/exts",
       "./vendor/kit-cae/_build/${platform}/${config}/apps",
       "./vendor/kit-cae/_build/${platform}/${config}/exts",
   ]
   ```

4. Build and package as usual: `repo.* build` then `repo.* package`.

---

## User Guide

The official step-by-step user guide is available on the NVIDIA documentation site:

📖 **[Kit-CAE User Guide](https://docs.omniverse.nvidia.com/guide-kit-cae/latest/index.html)**

It covers importing datasets, running algorithms, adjusting colormaps, using the streaming dashboard, and more.

---

## License & Third-Party Credits

Development with the Omniverse Kit SDK is subject to the
[NVIDIA Omniverse License Agreement](https://docs.omniverse.nvidia.com/install-guide/latest/common/NVIDIA_Omniverse_License_Agreement.html).

Kit-CAE also uses the following open-source libraries — review their licenses before use:

| Library | License file | Purpose |
|---|---|---|
| [CGNS](https://cgns.github.io/) | [`tpl_licenses/cgns-LICENSE.txt`](./tpl_licenses/cgns-LICENSE.txt) | CFD Notation System |
| [h5py](https://www.h5py.org/) | [`tpl_licenses/h5py-LICENSE.txt`](./tpl_licenses/h5py-LICENSE.txt) | Python interface for HDF5 |
| [HDF5](https://www.hdfgroup.org/solutions/hdf5/) | [`tpl_licenses/hdf5-LICENSE.txt`](./tpl_licenses/hdf5-LICENSE.txt) | High-performance data format |
| [VTK](https://vtk.org/) | [`tpl_licenses/vtk-LICENSE.txt`](./tpl_licenses/vtk-LICENSE.txt) | Visualization Toolkit |
| [Zlib](https://zlib.net/) | [`tpl_licenses/zlib-LICENSE.txt`](./tpl_licenses/zlib-LICENSE.txt) | Data compression |

---

## Contributing

This source code is provided **as-is**. We are not currently accepting outside contributions.

---

## Security

Please **do not** report security vulnerabilities through GitHub issues.

Report potential security vulnerabilities in NVIDIA products via:
- **Web:** [Security Vulnerability Submission Form](https://www.nvidia.com/object/submit-security-vulnerability.html)
- **Email:** psirt@nvidia.com

For more information, see [`SECURITY.md`](./SECURITY.md) and the [NVIDIA Product Security portal](https://www.nvidia.com/en-us/security).

