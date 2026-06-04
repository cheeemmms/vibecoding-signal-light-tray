# 🚦 Signal Light Tray

> 把 AI 编程助手的工作状态，变成 Windows 任务栏里一眼可见的红绿灯。

[![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey?logo=windows)](https://www.microsoft.com/windows)
[![Status](https://img.shields.io/badge/status-alpha-orange)](https://github.com/cheeemmms/vibecoding-signal-light-tray)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

**场景**：你正在用 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 做 VibeCoding——AI 在终端里写代码，你切到浏览器查资料。突然 Claude Code 弹了个权限请求，但你切走了窗口，根本不知道。

Signal Light Tray 把 Agent 的状态从终端里"拎"出来，放到你永远不会错过的地方——**Windows 任务栏托盘**。

```
灰灯 "我在等 Claude Code 启动"      🟢 绿灯 "空闲，不用管我"
🔴 红灯 "Agent 工作中…"             🟡 黄灯 "喂，过来看一眼！"
```

---

## 📋 状态图例

| 图标 | 状态 | 含义 | 音效 |
|:---:|------|------|:---:|
| ⚫ 灰 | `offline` | 等待 Claude Code 连接 | — |
| 🟢 绿 | `idle` | 空闲，无需关注 | — |
| 🔴 红 | `working` | Agent 工作中（思考/执行工具） | — |
| 🟡 黄 | `attention` | 需要你介入（权限请求/通知/任务完成） | 🔊 提示音 |
| 🔴💡 红闪 | `blocked` | 阻塞，需要立即处理 | 🚨 警告音 |

> **设计哲学**：红灯 = Agent 在忙，黄灯 = 需要你，绿灯 = 都闲着。认知负担为零。

---

## ⚡ 快速开始

### 你需要有的

- Windows 10 或 11
- Python 3.11 或更高版本
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI（已经在用）

### 三步跑起来

```bash
# 1. 克隆仓库
git clone https://github.com/cheeemmms/vibecoding-signal-light-tray.git
cd vibecoding-signal-light-tray

# 2. 安装
pip install -e .

# 3. 启动
python -m signal_light_tray
```

此时任务栏会出现一个 **灰色圆形图标**——它在等 Claude Code 连上来。

右键图标 → **安装 Hook**，搞定。之后每次 Claude Code 启动，托盘图标就会自动跟着变了。

---

## 🤖 用 AI Agent 帮你装

把下面这句话**原样**发给你的 AI 编程助手（Claude Code、Cursor、Codex 等）：

```
请帮我安装并配置 Signal Light Tray：
https://github.com/cheeemmms/vibecoding-signal-light-tray

按照仓库里的 AI_AGENT_SETUP.md 一步步操作，每步完成后验证结果。
```

Agent 会自动：
1. 检查你的 Python 版本和系统平台
2. 克隆仓库并安装依赖
3. 安装 Claude Code hook
4. 启动托盘程序并验证一切正常

> 💡 原理：仓库根目录的 [`AI_AGENT_SETUP.md`](AI_AGENT_SETUP.md) 是一份**面向 AI 的结构化安装指令**——每一步都有命令 + 预期输出 + 错误处理指引。AI Agent 不需要猜，直接按步骤执行即可。

---

## ✨ 功能一览

| 功能 | 说明 |
|------|------|
| 🚦 五态信号灯 | offline · idle · working · attention · blocked |
| 🔊 智能音效 | 需要介入时自动播放提示音，正常工作时静默 |
| 💡 红灯闪烁 | blocked 状态以 0.3s 交替闪烁，一眼区分"忙"和"卡住了" |
| 🔇 一键静音 | 右键菜单随时开关声音 |
| 🔌 一键安装 Hook | 托盘右键 → 安装 Hook，无需手动编辑 JSON |
| 📦 单文件 EXE | `dist/signal-light-tray.exe`，给不用 Python 的朋友也能跑 |
| 🪟 开机自启 | 放入启动文件夹，开机自动运行 |

> ✈️ **作者的小巧思**：提示音（`attention.wav`）来自空客 A320 自动驾驶断开提示音，警告音（`warning.wav`）来自客舱广播提示音。当 Agent 需要你接管时，用飞机自动驾驶断开的音效来提醒——"AI 把驾驶杆交还给你了"，是不是很应景？

---

## 🎛️ 右键菜单

```
┌──────────────────────────┐
│ 状态：工作中               │  ← 动态显示当前状态
├──────────────────────────┤
│ 🔇 静音                  │  ← 切换，✓ 表示已静音
├──────────────────────────┤
│ 安装 Hook                │  ← 自动写入 Claude Code 配置
│ 卸载 Hook                │
├──────────────────────────┤
│ 退出                     │
└──────────────────────────┘
```

---

## 🏗️ 工作原理

```
Claude Code 终端                Hook 事件 (stdin JSON)
      │                              │
      │  SessionStart                ▼
      │  UserPromptSubmit    ┌──────────────────┐
      │  PreToolUse          │ claude_code_hook  │  信号映射
      │  PostToolUse         │     .py           │  event → signal
      │  PermissionRequest   └────────┬─────────┘
      │  Stop / SessionEnd            │
      │                               ▼
      │                      ┌──────────────────┐
      └──────────────────────│ sessions.json    │  %TEMP%\signal-light\
                             │ (共享状态文件)    │  多 session 聚合
                             └────────┬─────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │ 500ms 轮询                │                           │
          ▼                           ▼                           ▼
   ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
   │ state_reader │          │   sounds.py  │          │   app.py     │
   │ 读取 + 聚合   │──────────│  音效播放     │          │  pystray UI  │
   └──────────────┘          └──────────────┘          └──────────────┘
```

三个进程通过 `%TEMP%\signal-light\sessions.json` 松耦合通信，无需网络、无需数据库、无需系统服务。

---

## 📦 详细安装

<details>
<summary><b>方式一：pip 安装（推荐，需要 Python）</b></summary>

```bash
git clone https://github.com/cheeemmms/vibecoding-signal-light-tray.git
cd vibecoding-signal-light-tray
pip install -e .
python -m signal_light_tray
```

</details>

<details>
<summary><b>方式二：直接运行 EXE（无需 Python）</b></summary>

去 [Releases](https://github.com/cheeemmms/vibecoding-signal-light-tray/releases) 下载 `signal-light-tray.exe`，双击运行。

> EXE 由 PyInstaller 打包，约 15MB，内置所有依赖和图标音效资源。

</details>

<details>
<summary><b>方式三：开机自启</b></summary>

将 `signal-light-tray.vbs` 放入启动文件夹：

1. 按 `Win + R`，输入 `shell:startup`，回车
2. 把 `signal-light-tray.vbs` 复制进去
3. 下次开机自动启动

</details>

---

## 🛠️ 项目结构

```
vibecoding-signal-light-tray/
├── signal_light_tray/           # 主包
│   ├── app.py                   # 托盘 UI 主程序 (pystray)
│   ├── state_reader.py          # 状态文件读取 + 多 session 聚合
│   ├── sounds.py                # 音效播放 (winsound)
│   ├── claude_code_hook.py      # Claude Code hook 事件处理器
│   ├── hook_writer.py           # 会话状态写入 sessions.json
│   ├── hook_installer.py        # Hook 安装/卸载/状态检查
│   ├── __main__.py              # python -m 入口
│   └── icons/                   # PNG 图标 (gray/green/red/yellow)
├── sounds/                      # WAV 音效文件
├── scripts/
│   └── claude-code-signal-hook.bat  # Windows 批处理入口
├── dist/
│   └── signal-light-tray.exe    # PyInstaller 打包的独立 EXE
├── AI_AGENT_SETUP.md            # AI Agent 结构化安装指令
├── pyproject.toml
└── README.md
```

---

## ❓ 常见问题

<details>
<summary><b>托盘图标一直是灰色？</b></summary>

灰色 = 程序没读到 Claude Code 的状态文件。检查：
1. 右键托盘 → 确认已点击"安装 Hook"
2. 重新启动 Claude Code（Hook 只在 session 启动时生效）
3. 确认 `%TEMP%\signal-light\sessions.json` 文件是否存在

</details>

<details>
<summary><b>没有声音？</b></summary>

1. 右键托盘 → 确认没有开启静音（显示 `🔇 静音` 说明当前有声音）
2. 确认 `sounds/` 目录下有 `attention.wav` 和 `warning.wav`
3. 检查系统音量是否静音

</details>

<details>
<summary><b>能和多个 Claude Code session 一起用吗？</b></summary>

可以。多个 session 的状态会聚合——优先级是 `blocked > permission > attention > working > idle`。只要有一个 session 阻塞了，灯就闪红。

</details>

<details>
<summary><b>支持 WSL 里的 Claude Code 吗？</b></summary>

支持。`claude_code_hook.py` 同时支持 Windows 原生和 WSL 环境。WSL 下 `python -m signal_light_tray.claude_code_hook` 需要在 Windows 侧的 Python 环境中运行。

</details>

<details>
<summary><b>能换成其他 AI 编程工具吗（Cursor、Codex、aider）？</b></summary>

目前只支持 Claude Code，因为它依赖 Claude Code 的 hook 事件体系。未来版本会考虑扩展支持。

</details>

---

## 🙏 致谢

- 本项目核心架构和信号聚合逻辑借鉴自 [vibe-coding-cn](https://github.com/tradecatlabs/vibe-coding-cn)，感谢 [TradeCat Labs](https://github.com/tradecatlabs) 的优秀工作。
- 托盘图标由 [pystray](https://github.com/moses-palmer/pystray) 驱动。

---

## 📄 许可证

MIT License — 详见 [LICENSE](LICENSE) 文件。
