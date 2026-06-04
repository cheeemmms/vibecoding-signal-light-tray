# Design Document

> 产品设计文档。记录用户需求、交互设计、UX 决策及其理由。
> 当需要回顾"为什么这样设计"或增加新功能时打开此文件。

---

## 项目愿景

将 AI 编程助手（Claude Code）的工作状态从终端内的文字流，转化为 Windows 任务栏托盘中一眼可感知的颜色信号。让开发者不必频繁切回终端也能了解 Agent 状态。

---

## 用户故事

| ID | 作为… | 我想要… | 以便… |
|---|---|---|---|
| US-01 | VibeCoding 用户 | 在任务栏托盘中看到一个颜色图标 | 一眼就知道 Claude Code 当前状态 |
| US-02 | VibeCoding 用户 | 当 Claude Code 需要我介入时听到提示音 | 不会错过权限请求或阻塞 |
| US-03 | VibeCoding 用户 | 右键托盘图标呼出菜单 | 可以静音或退出程序 |
| US-04 | VibeCoding 用户 | Claude Code 未运行时看到灰色图标 | 知道程序已就绪但无活动 session |

---

## 状态 → 托盘表现映射

| 聚合状态 | 图标 | 闪烁 | 音效 | 用户感知 |
|---|---|---|---|---|
| `offline` | `gray.png` | — | — | "已就绪，等待 Claude Code" |
| `idle` | `green.png` | — | — | "空闲，不用管" |
| `working` | `red.png` | — | — | "Agent 工作中" |
| `thinking` | `red.png` | — | — | "Agent 思考中" |
| `tool_done` | `red.png` | — | — | "工具执行完毕，继续工作" |
| `attention` | `yellow.png` | — | `attention.wav` | "需要你看一眼" |
| `permission` | `yellow.png` | — | `attention.wav` | "请求授权" |
| `done` | `yellow.png` | — | `attention.wav` | "任务完成" |
| `blocked` | `red.png` ↔ `red_dim.png` | 0.3s 交替 | `warning.wav` | "阻塞，需要处理" |

### 设计决策

- **working/thinking/tool_done 都显示红灯且无音效**：它们属于"Agent 正常工作"的子状态，不需要打扰用户。
- **attention/permission/done 都显示黄灯**：三者都表示"Agent 暂停，等待用户回应"。统一为黄灯降低认知负担。
- **blocked 红灯闪烁**：与 working 的红灯区分——闪烁=告急，常亮=正常。
- **音效仅在状态变化且目标状态为介入类时播放**：避免重复触发（如 blocked→blocked 不重复响）。

---

## 右键菜单（MVP）

```
┌─────────────────────┐
│ 状态：工作中          │  ← 不可选，动态显示当前状态
├─────────────────────┤
│ 🔇 静音             │  ← 切换，checked 表示已静音
├─────────────────────┤
│ 退出                │
└─────────────────────┘
```

### 待定功能（未来迭代）

- 开机自启
- 状态历史 / 统计
- 自定义音效
- 测试模式（模拟各状态）

---

## 图标规格

| 属性 | 值 |
|---|---|
| 格式 | PNG |
| 建议尺寸 | 64×64 px |
| 背景 | 透明 |
| 文件 | `gray.png`, `green.png`, `red.png`, `red_dim.png`, `yellow.png` |

`red_dim.png` 是 `red.png` 的降亮度版本（约 50% 亮度），用于 blocked 闪烁交替帧。若未提供，程序回退到 `gray.png`。

---

## 音效规格

| 属性 | 值 |
|---|---|
| 格式 | WAV |
| 播放方式 | `winsound.SND_ASYNC`（非阻塞） |
| 文件 | `attention.wav`（提示音）, `warning.wav`（警告音） |

音效文件放在 `sounds/` 目录，`sounds.py` 启动时自动扫描目录，按文件名（去掉扩展名）作为键名。

---

## 与父项目的边界

| 职责 | vibecoding-signal-light | signal-light-tray |
|---|---|---|
| Hook 安装 | ✅ `install-hooks --agent claude-code` | — |
| Hook 事件映射 → 信号名 | ✅ `claude_code_hook.py` | — |
| 多 session 聚合 | ✅ `runtime.py` | 内联复用相同逻辑 |
| 状态文件读写 | ✅ 写入 | ✅ 读写（内置 `hook_writer.py`） |
| 实体 GPIO 控制 | ✅ `hardware.py` | — |
| 虚拟托盘显示 | — | ✅ |
| 音效播放 | — | ✅ |
