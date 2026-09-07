# Traffic Light Status · QwenPaw 红绿灯状态灯

[English](README.en.md) | 简体中文

一个置顶桌面的红绿灯小挂件，让你切到任何窗口也能一眼知道 QwenPaw 智能体的状态：

![](.\assets\screenshot-status.png)

| 灯             | 含义                           |
| -------------- | ------------------------------ |
| 🟢 绿灯         | 全部空闲 / 任务完成            |
| 🟡 黄灯         | 有智能体正在干活               |
| 🔴 红灯（闪烁） | 有智能体被卡住，需要你回来处理 |

交给智能体一个长任务后切去干别的，黄灯变绿 = 回来看结果；红灯闪烁 = 它在等你。

## 工作原理

- 插件随 QwenPaw 启动拉起两个轻量进程（显示端 + 日志监听端），随 QwenPaw 退出自动关闭

- 监听端实时跟踪 QwenPaw 后端日志判定"有任务在跑 / 一轮回复结束"，定时任务（cron）与后台记忆任务已过滤，不会误报

- 智能体也可以用一行命令显式报红灯：

  ```bash
  python set_status.py waiting "缺少 API key"
  ```

## 安装

前提：Windows 10/11 + 系统安装过 [Python 3](https://www.python.org/downloads/)（默认安装即可，含 tkinter，无需第三方库）。

```bash
qwenpaw plugin install https://github.com/Single430/traffic-light/archive/refs/heads/main.zip
```

或在 QwenPaw Console 的插件管理界面安装。安装后重启 QwenPaw。

> 插件操作需要在 QwenPaw 离线状态下进行（官方限制）。

## 使用

- 左键拖动移动位置，右键菜单：查看当前状态 / 退出（同时停止监听端）
- 无任何配置项，装上即用

## 卸载

```bash
qwenpaw plugin uninstall traffic-light
```

## 文件说明

```
traffic-light/
├── plugin.json        # 插件清单
├── plugin.py          # 生命周期管理（启动拉起 / 关闭回收）
├── traffic_light.py   # 显示端（tkinter 置顶挂件）
├── light_watcher.py   # 监听端（tail 后端日志驱动灯色）
└── set_status.py      # 手动状态上报（智能体可调用）
```

## License

Apache-2.0
