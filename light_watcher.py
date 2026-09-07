# -*- coding: utf-8 -*-
"""Drive the desktop traffic light by tailing QwenPaw's backend log.

Turn start  -> new activity lines appear in qwenpaw.log  -> yellow (running)
Turn finish -> "console stream done" line                -> green (idle)
A manual waiting/error (via set_status.py) is respected for MANUAL_HOLD_S
so agents can still raise the red blinking light explicitly.
"""
import json
import os
import tempfile
import time

LOG = os.path.join(os.path.expanduser("~"), ".qwenpaw", "qwenpaw.log")
STATUS_DIR = os.path.join(tempfile.gettempdir(), "qwenpaw_trafficlight")
STATUS_FILE = os.path.join(STATUS_DIR, "status.json")

DONE_MARK = "console stream done"
# lines that only appear when an agent turn is actively running
ACTIVITY_MARKS = (
    "governance decision",
    "scroll: compact timing",
    "builder: built agent",
    "Usage for session",
    "Saved session state",
)
# background subsystems whose log noise must never light the lamp
IGNORE_MARKS = ("reme\\", "MQTT [")
# scheduled (cron) jobs run a full agent too but must not light the lamp:
# everything between these two log lines is suppressed
CRON_START = "cron execute:"
CRON_END = "cron _execute_once"
POLL_S = 1.0
MANUAL_HOLD_S = 600.0

STATE_COLOR = {"running": "yellow", "waiting": "red", "idle": "green",
               "done": "green", "error": "red"}

_last_written = None


def write_status(state, message):
    global _last_written
    payload = {"state": state, "color": STATE_COLOR[state], "message": message,
               "source": "watcher", "ts": time.time()}
    blob = json.dumps(payload, ensure_ascii=False)
    if blob == _last_written:
        return
    os.makedirs(STATUS_DIR, exist_ok=True)
    tmp = STATUS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(blob)
    os.replace(tmp, STATUS_FILE)
    _last_written = blob


def manual_hold():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return (d.get("source") == "manual"
                and d.get("state") in ("waiting", "error")
                and time.time() - d.get("ts", 0) < MANUAL_HOLD_S)
    except Exception:
        return False


def main():
    offset = 0
    busy = False
    in_cron = False
    try:
        offset = os.path.getsize(LOG)  # start at EOF: whatever is happening
    except OSError:                    # right now is unknown -> assume idle
        pass

    while True:
        try:
            size = os.path.getsize(LOG)
            if size < offset:          # rotated/truncated
                offset = 0
            if size > offset:
                with open(LOG, "rb") as f:
                    f.seek(offset)
                    chunk = f.read(size - offset)
                offset = size
                text = chunk.decode("utf-8", errors="ignore")
                for line in text.splitlines():
                    if CRON_START in line:
                        in_cron = True
                    elif CRON_END in line:
                        in_cron = False
                    elif DONE_MARK in line:
                        busy = False
                    elif in_cron:
                        continue
                    elif any(m in line for m in IGNORE_MARKS):
                        continue
                    elif any(m in line for m in ACTIVITY_MARKS):
                        busy = True
        except OSError:
            pass

        if not manual_hold():
            write_status("running" if busy else "idle",
                         "agent working" if busy else "all idle")
        time.sleep(POLL_S)


def main_supervised():
    """Never die silently: log the crash and restart."""
    log = os.path.join(STATUS_DIR, "watcher_error.log")
    while True:
        try:
            main()
        except Exception:
            try:
                os.makedirs(STATUS_DIR, exist_ok=True)
                import traceback
                with open(log, "a", encoding="utf-8") as f:
                    f.write("\n=== %s ===\n" % time.strftime("%F %T"))
                    traceback.print_exc(file=f)
            except Exception:
                pass
            time.sleep(5)


if __name__ == "__main__":
    main_supervised()
