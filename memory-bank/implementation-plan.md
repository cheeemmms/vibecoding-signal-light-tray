# Implementation Plan

> 实现计划。记录开发阶段、任务分解和待办事项。
> 当需要规划下一阶段工作或评估进度时打开此文件。

---

## Phase 1: 核心框架（当前）

### 已完成

| ID | 任务 | 文件 | 状态 |
|---|---|---|---|
| P1-01 | 项目骨架与 pyproject.toml | `pyproject.toml` | ✅ |
| P1-02 | 状态读取与聚合 | `signal_light_tray/state_reader.py` | ✅ |
| P1-03 | 音效播放模块 | `signal_light_tray/sounds.py` | ✅ |
| P1-04 | 托盘主程序（图标/菜单/轮询） | `signal_light_tray/app.py` | ✅ |
| P1-05 | `__main__.py` 入口 | `signal_light_tray/__main__.py` | ✅ |
| P1-06 | 投放 PNG 图标 | `signal_light_tray/icons/` | ✅ |
| P1-07 | 投放 WAV 音效 | `sounds/` | ✅ |
| P1-08 | 安装依赖并启动测试 | — | ✅ |
| P1-09 | Hook 写入逻辑（复用父项目） | `hook_writer.py` | ✅ |
| P1-10 | Claude Code hook 事件处理器 | `claude_code_hook.py` | ✅ |
| P1-11 | Hook 安装/卸载 | `hook_installer.py` + 右键菜单 | ✅ |
| P1-12 | Windows 批处理入口 | `scripts/claude-code-signal-hook.bat` | ✅ |

### 待验证

| ID | 任务 | 依赖 | 状态 |
|---|---|---|---|
| P1-13 | 配合 Claude Code 端到端测试 | 全部 | ✅ (2026-06-04) |

### Bug 修复（E2E 测试中发现）

| ID | 问题 | 文件 | 状态 |
|---|---|---|---|
| BUG-01 | TMPDIR 覆盖导致 TEMP 路径不一致 | `state_reader.py`, `hook_writer.py` | ✅ |
| BUG-02 | `hook_writer.py` 缺少 `import os` | `hook_writer.py` | ✅ |
| BUG-03 | Poll 线程在 `icon.visible=True` 前启动导致立即退出 | `app.py` | ✅ |
| BUG-04 | 右键菜单状态文本静态不变 | `app.py` | ✅ |

---

## Phase 2: 完善（规划中）

| ID | 任务 | 说明 |
|---|---|---|
| P2-01 | Hook 自动安装助手 | ✅ 已通过右键菜单实现 |
| P2-02 | 双击托盘打开状态面板 | 弹出小窗口显示当前各 session 的详细状态 |
| P2-03 | 开机自启 | ✅ 已通过启动文件夹 `.vbs` 脚本实现（`shell:startup`） |
| P2-04 | 打包为 exe | ✅ PyInstaller onefile, 15MB, 绿灯图标, 2026-06-04 |
| P2-05 | 空闲超时自动退出 | N 分钟无 session 活动后自动退出托盘 |

---

## Phase 3: 扩展（远期）

| ID | 任务 | 说明 |
|---|---|---|
| P3-01 | 状态历史记录 | 记录状态变化时间线，支持查看 |
| P3-02 | 自定义图标/音效设置界面 | GUI 配置面板 |
| P3-03 | 支持其他 Agent（Codex、aider 等） | 复用父项目的 hook 体系 |

---

## 技术债务

| ID | 问题 | 优先级 |
|---|---|---|
| TD-01 | `state_reader.py` 聚合逻辑与父项目 `runtime.py` 重复——若父项目逻辑变更需手动同步 | 中 |
| TD-02 | 无配置文件持久化静音偏好——每次启动静音状态重置 | 低 |
