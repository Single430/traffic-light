# -*- coding: utf-8 -*-
"""QwenPaw agent status traffic light - always-on-top desktop indicator.

Traffic-light look: dark rounded housing, vertical red/yellow/green lamps.
Reads status from %TEMP%\\qwenpaw_trafficlight\\status.json.
Run with pythonw for no console window.
"""
import json
import os
import tempfile
import tkinter as tk

STATUS_DIR = os.path.join(tempfile.gettempdir(), "qwenpaw_trafficlight")
STATUS_FILE = os.path.join(STATUS_DIR, "status.json")

HOUSING = "#3b3f4c"      # dark blue-grey housing
HOUSING_EDGE = "#2c2f3a"
BG = "#1e1e1e"

# active / dimmed colors per lamp
LAMPS = {
    "red":    ("#ff5a5a", "#57302f"),
    "yellow": ("#ffd964", "#59503a"),
    "green":  ("#8ee66a", "#37552f"),
}
ORDER = ["red", "yellow", "green"]

STATE_LABEL = {
    "idle": "idle",
    "running": "running",
    "waiting": "NEED YOU",
    "done": "done",
    "error": "error",
}
# which lamp lights up per state
STATE_LAMP = {
    "idle": "green",
    "done": "green",
    "running": "yellow",
    "waiting": "red",
    "error": "red",
}
DEFAULT = {"state": "idle", "message": "idle"}

W, H = 96, 220
LAMP_R = 24


def read_status():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return {**DEFAULT, **d}
    except Exception:
        return DEFAULT.copy()


def rounded_rect(c, x1, y1, x2, y2, r, **kw):
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return c.create_polygon(pts, smooth=True, **kw)


class TrafficLight:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Agent Status")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(bg=BG)
        # make window background transparent-ish via chroma key
        self.root.wm_attributes("-transparentcolor", BG)
        self.root.geometry(f"{W}x{H}+20+300")

        c = tk.Canvas(self.root, width=W, height=H, bg=BG,
                      highlightthickness=0, bd=0)
        c.pack()
        self.canvas = c

        # housing
        rounded_rect(c, 8, 10, W - 8, H - 14, 30,
                     fill=HOUSING, outline=HOUSING_EDGE, width=2)
        # top cap
        c.create_oval(W / 2 - 14, 2, W / 2 + 14, 18,
                      fill=HOUSING_EDGE, outline="")

        # lamps
        self.lamp_items = {}
        for i, name in enumerate(ORDER):
            cy = 52 + i * 60
            x1, y1 = W / 2 - LAMP_R, cy - LAMP_R
            x2, y2 = W / 2 + LAMP_R, cy + LAMP_R
            # socket ring
            c.create_oval(x1 - 3, y1 - 3, x2 + 3, y2 + 3,
                          fill=HOUSING_EDGE, outline="")
            lamp = c.create_oval(x1, y1, x2, y2,
                                 fill=LAMPS[name][1], outline="")
            # glossy highlight (upper-left small arc)
            hl = c.create_oval(x1 + 6, y1 + 5, x1 + 18, y1 + 15,
                               fill="#ffffff", outline="", stipple="gray50")
            self.lamp_items[name] = (lamp, hl)

        # drag support
        c.bind("<Button-1>", self._start_drag)
        c.bind("<B1-Motion>", self._on_drag)
        c.bind("<Button-3>", self._show_menu)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Show status", command=self._popup_status)
        self.menu.add_command(label="Quit (stop light + watcher)",
                              command=self._quit_all)

        self._blink_on = True
        self._tick()

    def _start_drag(self, e):
        self._dx = e.x
        self._dy = e.y

    def _on_drag(self, e):
        x = self.root.winfo_pointerx() - self._dx
        y = self.root.winfo_pointery() - self._dy
        self.root.geometry(f"+{x}+{y}")

    def _show_menu(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)

    def _quit_all(self):
        # stop the watcher too, so the whole feature is off until the
        # plugin starts it again (next QwenPaw launch)
        try:
            import subprocess
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\""
                 " | Where-Object {$_.CommandLine -like '*light_watcher*'}"
                 " | ForEach-Object {Stop-Process -Id $_.ProcessId -Force}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=10)
        except Exception:
            pass
        self.root.destroy()

    def _popup_status(self):
        s = read_status()
        from tkinter import messagebox
        messagebox.showinfo("Agent Status",
                            f"state: {s['state']}\nmessage: {s['message']}",
                            parent=self.root)

    def _set_lamps(self, active):
        for name, (lamp, hl) in self.lamp_items.items():
            on = (name == active)
            self.canvas.itemconfig(lamp, fill=LAMPS[name][0] if on
                                   else LAMPS[name][1])
            self.canvas.itemconfig(hl, state="normal" if on else "hidden")

    def _tick(self):
        s = read_status()
        state = s.get("state", "idle")
        lamp = STATE_LAMP.get(state, "green")
        blink = state in ("waiting", "error")
        if blink:
            self._blink_on = not self._blink_on
            self._set_lamps(lamp if self._blink_on else None)
            delay = 400
        else:
            self._set_lamps(lamp)
            delay = 600
        self.root.after(delay, self._tick)


if __name__ == "__main__":
    os.makedirs(STATUS_DIR, exist_ok=True)
    TrafficLight().root.mainloop()
