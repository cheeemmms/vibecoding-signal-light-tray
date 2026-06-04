# Architecture

> 系统架构文档。描述模块划分、进程间通信、数据流和技术决策。
> 当需要理解代码结构或做架构变更时打开此文件。

---

## 系统边界

```
┌──────────────────────────────────────────────────────┐
│                    外部系统                            │
│  ┌──────────────┐                                    │
│  │  Claude Code  │  触发 Hook 事件                     │
│  └──────┬───────┘                                    │
│         │ 调用 scripts/claude-code-signal-hook.bat    │
│         ▼                                            │
└─────────┼──────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────┐
│                 本项目 (signal-light-tray)             │
│                                                       │
│  ┌──────────────────────┐  ┌───────────────────┐     │
│  │  claude_code_hook.py  │  │  hook_installer.py │    │
│  │  stdin 解析 + 信号映射  │  │  安装到 settings.json│  │
│  └──────────┬───────────┘  └───────────────────┘     │
│             │ 调用                                     │
│             ▼                                         │
│  ┌──────────────────────┐                            │
│  │  hook_writer.py       │  写入 sessions.json       │
│  └──────────┬───────────┘                            │
│             │                                         │
│             ▼                                         │
│  ┌──────────────────────┐                            │
│  │ %TEMP%\signal-light\ │  共享状态文件               │
│  │  sessions.json       │                            │
│  └──────────┬───────────┘                            │
│             │ 轮询读取 (500ms)                         │
│             ▼                                         │
│  ┌─────────────────┐   ┌───────────────────┐         │
│  │  state_reader.py │   │  sounds.py        │         │
│  │  读取 + 聚合      │   │  winsound 播放    │         │
│  └───────┬─────────┘   └────────┬──────────┘         │
│          │ 状态                  │ 状态变化时触发      │
│          ▼                       ▼                    │
│  ┌─────────────────────────────────────┐             │
│  │  app.py (SignalLightTray)           │             │
│  │  ┌──────────────┐  ┌─────────────┐ │             │
│  │  │ 后台轮询线程   │  │ pystray 图标 │ │             │
│  │  │ (daemon)      │  │ + 右键菜单   │ │             │
│  │  └──────────────┘  └─────────────┘ │             │
│  └─────────────────────────────────────┘             │
│                                                       │
│  icons/  ← PNG 图标                                   │
│  sounds/ ← WAV 音效                                   │
└──────────────────────────────────────────────────────┘
```

---

## 模块依赖图

```
app.py
  ├── state_reader.py    (无内部依赖)
  ├── sounds.py          (无内部依赖)
  ├── hook_installer.py  (无内部依赖)
  ├── pystray            (第三方)
  └── Pillow             (第三方)

claude_code_hook.py
  └── hook_writer.py     (无内部依赖)

hook_writer.py           (无内部依赖)
```

**设计原则**：`state_reader`、`sounds`、`hook_writer`、`hook_installer` 各自独立，不互相引用，仅由 `app.py` 或 `claude_code_hook.py` 编排调用。

---

## 进程模型

| 进程 | 角色 | 生命周期 |
|---|---|---|
| Claude Code | 触发 Hook | 用户启动/关闭 |
| `claude_code_hook.py` | 解析事件 + 写状态文件 | Hook 触发时瞬时执行（~0.2s 退出） |
| `signal-light-tray` | 读状态 + 托盘 UI | 用户手动启动，持续驻留后台 |

三者通过 `%TEMP%\signal-light\sessions.json` 松耦合通信。

---

## 状态文件格式

路径：`%TEMP%\signal-light\sessions.json`

```json
{
  "sessions": {
    "<session_id>": {
      "signal": "working",
      "updated_at": 1712345678.0
    }
  }
}
```

- 由本项目的 `hook_writer.py` 写入（也可由父项目 `vibecoding-signal-light` 的 `runtime.py` 写入）
- 由本项目的 `state_reader.py` 读取
- 多 session 聚合逻辑：`blocked > permission > attention/done > working/thinking/tool_done > idle`
- 超过 `SESSION_TTL_SECONDS`（默认 86400 秒）的 session 自动清理

---

## 状态机

```
           ┌─────────┐
    启动 ──► offline  │  (灰灯，无 session 文件或读取失败)
           └────┬────┘
                │ 检测到 session 文件
                ▼
           ┌─────────┐
           │  idle   │  (绿灯)
           └────┬────┘
                │ Hook: UserPromptSubmit / PreToolUse
                ▼
      ┌────────────────────┐
      │ working / thinking  │  (红灯)
      │ / tool_done         │
      └────────┬───────────┘
               │ Hook: Notification / Stop / done
               ▼
      ┌────────────────────┐
      │ attention /         │  (黄灯 + 提示音)
      │ permission / done   │
      └────────┬───────────┘
               │ Hook: PostToolUseFailure / max_tokens
               ▼
      ┌─────────┐
      │ blocked │  (红灯闪烁 + 警告音)
      └─────────┘
```

所有状态均可回归 `idle`：当 session 结束或 `turn_end` 触发时。

---

## 依赖

| 包 | 版本 | 用途 |
|---|---|---|
| `pystray` | >=0.19 | 系统托盘图标与菜单 |
| `Pillow` | >=10.0 | PNG 图标加载 |
| `winsound` | 内置 | WAV 音效播放 |

无需额外系统服务、数据库或网络连接。

---

## 可扩展点

- `sounds.py` 中 `SOUND_MAP` 自动扫描 `sounds/` 目录，新增音效只需放入文件
- 图标映射在 `app.py` 的 `ICON_MAP` 字典，新增状态只需添加映射项
- 聚合逻辑独立在 `state_reader.py`，不影响 UI 层
