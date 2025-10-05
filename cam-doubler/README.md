# cam-doubler (MVP pass-through, 2× output)

This MVP takes any webcam input and outputs a virtual camera at ~2× the input FPS by inserting a mid frame
(duplicate or simple blend). No AI yet. Uses `pyvirtualcam` to write into the OBS Virtual Camera driver.

## Requirements
- Windows 10/11
- Python 3.10+ (64-bit)
- OBS Studio installed (so the "OBS Virtual Camera" driver exists)

## Quick start
````powershell
cd cam-doubler
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python python/main.py
````

In Zoom/Teams/Discord/OBS, choose **OBS Virtual Camera** as your camera source.

## Controls (flags)
- `--device INDEX`       : camera index (default 0)
- `--width 1280 --height 720`
- `--prefer_fps 30`      : initial guess; code adapts dynamically
- `--mid blend|duplicate`: how to synthesize the midpoint (default duplicate)
- `--preview`            : show a small preview window (ESC to quit)

## How it works (MVP)
- Captures frames via OpenCV (MSMF backend on Windows).
- Measures input period and sets output period to half (2× cadence).
- For each pair (prev, curr), schedules two outputs: MID then REAL.
- MID is a duplicate (default) or a simple blend (A+B)/2.
- Sends frames to the OBS Virtual Camera via `pyvirtualcam` at the paced cadence.

## Next steps (v2)
- Replace `mid` with hardware interpolation (NVIDIA FRUC) through a small DLL.
- Optional HQ mode (RIFE/TensorRT) for higher quality.
- Add a tray UI and device/fps switching.
