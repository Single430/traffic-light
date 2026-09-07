# -*- coding: utf-8 -*-
"""Update the traffic light status. Usage:
  python set_status.py running "training epoch 3"
  python set_status.py waiting "need your input"
  python set_status.py done "task finished"
  python set_status.py error "train failed"
  python set_status.py idle
"""
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WIDGET = os.path.join(HERE, "traffic_light.py")
BAT = os.path.join(HERE, "run_trafficlight.bat")


def light_running():
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq pythonw.exe"],
            stderr=subprocess.DEVNULL)
        return b"pythonw.exe" in out
    except Exception:
        return True  # can't tell -> don't spawn duplicates


def ensure_light():
    """Auto-start the widget (detached) if it is not running."""
    if light_running() or not os.path.exists(WIDGET):
        return
    if os.path.exists(BAT):
        subprocess.Popen(["explorer.exe", BAT],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["pythonw", WIDGET],
                         creationflags=getattr(subprocess, "DETACHED_PROCESS", 0),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

MAP = {
    "idle": "green",
    "done": "green",
    "running": "yellow",
    "waiting": "red",
    "error": "red",
}


def set_status(state, message=""):
    d = os.path.join(tempfile.gettempdir(), "qwenpaw_trafficlight")
    os.makedirs(d, exist_ok=True)
    if state not in MAP:
        print(f"unknown state {state!r}; use one of {sorted(MAP)}")
        return 2
    payload = {"state": state, "color": MAP[state], "message": message or state,
               "source": "manual", "ts": time.time()}
    path = os.path.join(d, "status.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, path)
    print(f"status -> {state}: {message}")
    return 0


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "idle"
    message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    ensure_light()
    sys.exit(set_status(state, message))
