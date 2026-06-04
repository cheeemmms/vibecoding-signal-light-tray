# AI Agent Setup Instructions

> **面向 AI Agent 的结构化安装指令。**
> 如果你是 AI 编程助手（Claude Code、Cursor、Codex 等），请严格按以下步骤执行，每完成一步验证其结果，验证失败时按"失败处理"指引操作。

---

## 任务概述

安装并配置 **Signal Light Tray**——一个 Windows 任务栏托盘工具，将 Claude Code AI Agent 的工作状态（离线/空闲/工作中/需要关注/阻塞）以红绿灯图标直观展示。

- **目标平台**：Windows 10 / 11
- **依赖**：Python 3.11+
- **安装方式**：pip 本地安装
- **集成目标**：Claude Code（通过 hook 事件连接）

---

## 安装步骤

### Step 1: 检查 Python 环境

```bash
python --version
```

**预期输出**：`Python 3.11.x` 或更高版本（3.12、3.13 均可）

**失败处理**：
- 若命令不存在 → 引导用户安装 Python 3.11+（https://www.python.org/downloads/），安装时勾选"Add Python to PATH"
- 若版本低于 3.11 → 引导用户升级 Python

---

### Step 2: 检查系统平台

```bash
python -c "import sys; print(sys.platform)"
```

**预期输出**：`win32`

**失败处理**：
- 若输出不是 `win32` → 告知用户本项目仅支持 Windows。终止安装。

---

### Step 3: 克隆仓库

```bash
git clone https://github.com/cheeemmms/vibecoding-signal-light-tray.git
cd vibecoding-signal-light-tray
```

**预期输出**：成功克隆，`cd` 后当前目录为仓库根目录。

**失败处理**：
- 若 git 不可用 → 引导用户安装 Git（https://git-scm.com/download/win）或手动下载 ZIP 并解压
- 若仓库 URL 不可达 → 检查网络连接，确认 URL 正确

---

### Step 4: 安装 Python 依赖

```bash
pip install -e .
```

**预期输出**：安装成功，无错误。关键依赖 `pystray>=0.19.0` 和 `Pillow>=10.0.0` 会被自动安装。

**失败处理**：
- 若 `pip` 不可用 → `python -m pip install -e .`
- 若缺少编译工具（Pillow 需要）→ `pip install --only-binary :all: Pillow` 或引导用户安装 Microsoft Visual C++ Build Tools
- 若权限不足 → 尝试 `pip install --user -e .` 或引导用户以管理员身份运行

---

### Step 5: 验证安装

```bash
python -c "from signal_light_tray.app import main; from signal_light_tray.state_reader import read_aggregate_state; from signal_light_tray.sounds import play_attention; from signal_light_tray.hook_installer import install; print('ALL_OK')"
```

**预期输出**：`ALL_OK`

**失败处理**：
- 若有 ImportError → 返回 Step 4 重装依赖
- 若有其他错误 → 列出完整错误信息，请用户反馈到 GitHub Issues

---

### Step 6: 安装 Claude Code Hook

```bash
python -c "from signal_light_tray.hook_installer import install; print(install())"
```

**预期输出**：`Hook 安装成功`

**验证**：
```bash
python -c "from signal_light_tray.hook_installer import status; print(status())"
```

**预期输出**：`已安装`

**失败处理**：
- 若提示找不到配置文件 → Claude Code 可能尚未初始化，运行一次 `claude` 命令即可自动生成 `~/.claude/settings.json`
- 若权限不足 → 检查 `~/.claude/` 目录权限

---

### Step 7: 启动托盘程序

```bash
python -m signal_light_tray
```

**预期结果**：
- Windows 任务栏托盘区出现灰色圆形图标
- 右键图标可弹出菜单（状态：离线 / 静音 / 安装Hook / 卸载Hook / 退出）

**验证方式**：
- 图标出现 = 成功
- 右键菜单正常弹出 = 完全正常

**注意**：此命令会阻塞终端（程序持续运行）。如需后台运行，可使用 `start pythonw -m signal_light_tray`。

---

### Step 8 (可选): 配置开机自启

将 `signal-light-tray.vbs` 复制到 Windows 启动文件夹：

```powershell
Copy-Item "signal-light-tray.vbs" -Destination "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\"
```

**验证**：重启电脑后托盘图标自动出现。

---

### Step 9: 端到端验证

现在启动 Claude Code 并进行一次对话：

1. 打开终端，运行 `claude`
2. 观察任务栏托盘图标：
   - 启动时：图标变红（`working` / `thinking`）
   - 工具执行完：图标可能短暂变黄（`tool_done`）
   - 空闲时：图标变绿（`idle`）
3. 右键托盘图标 → 状态文本应与 Claude Code 活动一致

**如果图标始终为灰色**：确认 Step 6 的 hook 安装成功，并重启 Claude Code session。

---

## 卸载

```bash
python -c "from signal_light_tray.hook_installer import uninstall; print(uninstall())"
pip uninstall signal-light-tray
```

---

## 关键信息速查

| 项目 | 值 |
|------|-----|
| 包名 | `signal-light-tray` |
| 入口命令 | `python -m signal_light_tray` |
| 状态文件路径 | `%TEMP%\signal-light\sessions.json` |
| 图标目录 | `signal_light_tray/icons/` |
| 音效目录 | `sounds/` |
| 支持的事件 | SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, Notification, Stop, SessionEnd 等 |
| 仓库 | https://github.com/starlight36/vibecoding-signal-light-tray |
| 借鉴来源 | https://github.com/tradecatlabs/vibe-coding-cn |
