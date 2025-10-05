# Dev helper: create venv, install, run
$ErrorActionPreference = "Stop"
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python python\main.py --preview
