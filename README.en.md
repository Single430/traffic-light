# Traffic Light Status · QwenPaw Plugin

English | [简体中文](README.md)

An always-on-top desktop traffic light that shows what your QwenPaw agents
are doing — visible from any window:

![](.\assets\screenshot-status.png)

| Lamp             | Meaning                           |
| ---------------- | --------------------------------- |
| 🟢 Green          | everything idle / done            |
| 🟡 Yellow         | an agent is working               |
| 🔴 Red (blinking) | an agent is blocked and needs you |

Hand an agent a long task, switch away, and just glance at the lamp:
green = come back for the result, blinking red = it's waiting for you.

## How it works

- The plugin starts two lightweight processes with QwenPaw (display +
  log watcher) and stops them when QwenPaw exits

- The watcher tails QwenPaw's backend log to tell "a turn is running"
  from "the reply is done"; cron jobs and background memory tasks are
  filtered out so they never cause false alarms

- Agents can raise the red light explicitly with one command:

  ```bash
  python set_status.py waiting "missing API key"
  ```

## Install

Requirements: Windows 10/11 + system [Python 3](https://www.python.org/downloads/)
(default install; tkinter included; no third-party packages needed).

```bash
qwenpaw plugin install https://github.com/Single430/traffic-light/archive/refs/heads/main.zip
```

or install from the QwenPaw Console plugin manager, then restart QwenPaw.

> Plugin operations require QwenPaw to be offline (official limitation).

## Usage

- Left-drag to move; right-click menu: show status / quit (also stops the watcher)
- Zero configuration — works out of the box

## Uninstall

```bash
qwenpaw plugin uninstall traffic-light
```

## Files

```
traffic-light/
├── plugin.json        # plugin manifest
├── plugin.py          # lifecycle manager (start/stop with QwenPaw)
├── traffic_light.py   # display (tkinter always-on-top widget)
├── light_watcher.py   # watcher (drives lamp from backend log)
└── set_status.py      # manual status reporting (callable by agents)
```

## License

Apache-2.0
