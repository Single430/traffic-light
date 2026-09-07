# -*- coding: utf-8 -*-
"""Traffic Light plugin for QwenPaw.

Lifecycle manager: on QwenPaw startup, launch the two widget processes
(traffic_light.py display + light_watcher.py log watcher); on shutdown,
terminate them. Everything lives in this plugin directory.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STATUS_DIR = os.path.join(tempfile.gettempdir(), "qwenpaw_trafficlight")
PID_FILE = os.path.join(STATUS_DIR, "plugin_pids.json")

SCRIPTS = ["traffic_light.py", "light_watcher.py"]


def _log(api, msg, error=False):
    try:
        fn = api.runtime.log_error if error else api.runtime.log_info
        fn(f"[traffic-light] {msg}")
    except Exception:
        pass


def _find_pythonw():
    p = shutil.which("pythonw")
    if p:
        return p
    for cand in (
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"),
        r"C:\Python310\pythonw.exe",
        r"C:\Python311\pythonw.exe",
        r"C:\Python312\pythonw.exe",
    ):
        if os.path.exists(cand):
            return cand
    return None


def _alive(pid):
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            stderr=subprocess.DEVNULL)
        return str(pid) in out.decode(errors="ignore")
    except Exception:
        return False


def _load_pids():
    try:
        with open(PID_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_pids(d):
    os.makedirs(STATUS_DIR, exist_ok=True)
    with open(PID_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f)


def _find_running(script_name):
    """PID of an already-running pythonw executing script_name, else None."""
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" "
             "| Where-Object {$_.CommandLine -like '*%s*'} "
             "| Select-Object -ExpandProperty ProcessId" % script_name],
            stderr=subprocess.DEVNULL, timeout=15)
        for tok in out.decode(errors="ignore").split():
            if tok.isdigit():
                return int(tok)
    except Exception:
        pass
    return None


def startup(api):
    pyw = _find_pythonw()
    if not pyw:
        _log(api, "pythonw.exe not found; install Python 3 (python.org) "
                  "to enable the desktop traffic light.", error=True)
        return
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | \
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    pids = _load_pids()
    for name in SCRIPTS:
        old = pids.get(name)
        if old and _alive(old):
            continue  # already running (e.g. backend reload)
        adopted = _find_running(name)
        if adopted:
            pids[name] = adopted  # adopt instance started by other means
            _log(api, f"adopted running {name} pid={adopted}")
            continue
        script = os.path.join(HERE, name)
        try:
            proc = subprocess.Popen(
                [pyw, script],
                cwd=HERE,
                creationflags=flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
            pids[name] = proc.pid
            _log(api, f"started {name} pid={proc.pid}")
        except Exception as e:
            _log(api, f"failed to start {name}: {e}", error=True)
    _save_pids(pids)


def shutdown(api):
    pids = _load_pids()
    for name, pid in list(pids.items()):
        try:
            if _alive(pid):
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     f"Stop-Process -Id {pid} -Force"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=10)
                _log(api, f"stopped {name} pid={pid}")
        except Exception as e:
            _log(api, f"failed to stop {name} pid={pid}: {e}", error=True)
    _save_pids({})


class TrafficLightPlugin:
    def register(self, api):
        api.register_startup_hook(
            hook_name="traffic_light_start",
            callback=lambda: startup(api),
            priority=200,
        )
        api.register_shutdown_hook(
            hook_name="traffic_light_stop",
            callback=lambda: shutdown(api),
            priority=200,
        )


plugin = TrafficLightPlugin()
