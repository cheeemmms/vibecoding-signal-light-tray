# Progress

> 进度日志。记录每次变更的内容和当前项目状态快照。
> 当需要了解"最近做了什么"或"当前有什么问题"时打开此文件。

---

## 当前状态

**阶段**：Phase 1 核心框架 — 已完成 ✅

**E2E 测试**：✅ 已通过（2026-06-04）

**可用性**：完全自包含，无需父项目。依赖已安装，素材就位，Hook 已集成，开机自启已配置，可直接使用。

---

## 变更日志

### 2026-06-04 — E2E 调试与优化

- **E2E 测试通过**（P1-13 完成）：
  - 托盘图标正确显示四种颜色（灰/绿/红/黄）
  - 提示音正确触发（permission → attention.wav, blocked/idle → warning.wav）
  - 右键菜单动态更新状态文本
  - Hook 事件 → 信号 → 聚合 → 图标全链路正常工作
- **Bug 修复**：
  - 修复 TMPDIR 覆盖导致 TEMP 路径不一致（`state_reader.py`, `hook_writer.py`）
    - Claude Code 注入 `TMPDIR` → `tempfile.gettempdir()` 返回错误路径
    - 改为优先使用 `TEMP` 环境变量
  - 修复 `hook_writer.py` 缺少 `import os`
  - 修复 Poll 线程竞态条件（`app.py`）
    - 原代码在 `icon.run()` 前启动线程，此时 `icon.visible=False`，线程立即退出
    - 改为使用 pystray 的 `setup` 回调，在 `icon.visible=True` 后启动轮询
  - 修复右键菜单状态文本静态不变（`app.py`）
    - `pystray.MenuItem` 文本在创建时静态求值 → 改为 `lambda` 动态求值
- **灯光/音效规则调整**：
  - `done` 图标：黄 → 绿（任务完成即用户可输入）
  - 提示音精简：仅 `permission`(attention.wav)、`blocked`(warning.wav)、`idle`(warning.wav) 触发
  - `attention` 和 `working`/`thinking` 状态不再有提示音
- **开机自启配置**：
  - 创建 `signal-light-tray.vbs` 放入 Windows 启动文件夹
  - 使用 `pythonw.exe` 无窗口静默启动
  - 关闭方式：`Win+R` → `shell:startup` → 删除 `.vbs` 文件
- **残留测试数据清理**：清除 `test-stdin-001` 过期会话，避免干扰状态聚合

### 2026-06-03（第三阶段 — Hook 集成）

- 不再依赖父项目 `vibecoding-signal-light`，内置完整的 session 写入功能
- 新建 `hook_writer.py`：复用父项目 `runtime.py` 的 `apply_session_signal` 逻辑
  - 写入 `%TEMP%\signal-light\sessions.json`
  - Windows 文件锁（`msvcrt`），原子写入（tmp + replace）
  - Session TTL 清理、聚合、turn_end 处理
- 新建 `claude_code_hook.py`：Claude Code hook 事件处理器
  - 读取 stdin JSON → 映射事件到信号名 → 写入 sessions.json
  - 事件映射：12 种 hook 事件（SessionStart ~ SessionEnd）
  - Stop 特殊处理：`max_tokens` / `error` → blocked
- 新建 `hook_installer.py`：安装/卸载 Claude Code hook
  - 修改 `~/.claude/settings.json`，注册 12 个 hook 事件
  - 备份原配置，merge 已有配置不破坏
- 新建 `scripts/claude-code-signal-hook.bat`：Windows 批处理，Claude Code 调用入口
- 修改 `app.py`：右键菜单新增"安装 Hook"/"卸载 Hook"
- 测试：
  - hook_writer 端到端状态机测试通过（7 个事件）
  - stdin 模拟 Claude Code 调用通过
  - hook 安装器：安装→验证→卸载→验证通过

### 2026-06-03（第二阶段）

- 素材就位：
  - 图标：`signal_light_tray/icons/` — `gray.png`, `green.png`, `red.png`, `yellow.png`
  - 音效：`sounds/` — `attention.wav`, `warning.wav`
- 修复 `pyproject.toml`：
  - 移除缺失的 `README.md` 引用
  - 添加 `[tool.setuptools.packages.find]` 显式限定包目录
- 安装依赖成功：`pystray==0.19.5`, `Pillow==12.2.0`
- 验证：
  - 模块导入正常，`SOUND_MAP` 正确加载 `attention.wav`/`warning.wav`
  - 状态机聚合测试全部通过（11 个用例）
- 注意：`red_dim.png` 未提供，blocked 闪烁回退使用 `gray.png`

### 2026-06-03（第一阶段）

- 创建项目骨架
  - 目录：`signal_light_tray/`, `icons/`, `sounds/`, `memory-bank/`
  - 配置：`pyproject.toml`（依赖 pystray + Pillow, Python >=3.11）
  - 忽略：`.gitignore`
- 实现 `state_reader.py`
  - 读取 `%TEMP%\signal-light\sessions.json`
  - 多 session 聚合：blocked > permission > attention/done > working/thinking/tool_done > idle
  - Session TTL 过期清理
  - 文件不存在时返回 `offline`
- 实现 `sounds.py`
  - `winsound` 异步播放 WAV
  - 全局静音开关 `toggle_mute()`
  - 扫描 `sounds/` 目录自动加载
- 实现 `app.py`
  - pystray 托盘图标，启动显示灰灯
  - 后台轮询线程（500ms 间隔）
  - 状态变化时切换图标 + 触发音效
  - blocked 闪烁：0.3s 交替 red/red_dim
  - 右键菜单：状态显示、静音切换、退出
- 创建 memory-bank 文档
  - `architecture.md`：系统架构与数据流
  - `design-document.md`：产品设计与 UX 决策
  - `implementation-plan.md`：阶段与任务分解

---

## 已知问题

| ID | 问题 | 影响 | 计划 |
|---|---|---|---|
| 1 | `red_dim.png` 未提供 | blocked 闪烁回退使用 `gray.png`，视觉效果不够明显 | 提供 64x64 暗红色 PNG |
| 2 | 静音状态不持久化 | 重启托盘后静音状态丢失 | 写入配置文件 |
| 3 | `scripts/claude-code-signal-hook.bat` 未使用 | 死代码，hook 安装器注册的是直接 `python -m` 命令 | 清理或移除 |
| 4 | `state_reader.py` 与 `hook_writer.py` 聚合逻辑重复 | 父项目逻辑变更时需手动同步 | 抽取公共模块 |

---

## 运行前提

1. 安装 Python >= 3.11
2. 安装依赖：`pip install -e .`
3. 将 PNG 图标放入 `signal_light_tray/icons/`（已完成）
4. 将 WAV 音效放入 `sounds/`（已完成）
5. **（重要）首次使用先安装 Hook**：右键托盘 → "安装 Hook"，或命令：
   `python -c "from signal_light_tray.hook_installer import install; install()"`
6. 运行：`signal-light-tray` 或 `python -m signal_light_tray`
