#!/usr/bin/env sh
# A Time To Catch - installs everything the game needs, then starts it.
cd "$(dirname "$0")"
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
"$PY" -m pip install -r requirements.txt && "$PY" main.py
