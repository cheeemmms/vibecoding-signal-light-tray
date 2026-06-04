"""读取由 Claude Code hook 写入的会话状态并聚合为单一信号。

复用自 vibecoding-signal-light 项目的 runtime.py 聚合逻辑。
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

_TEMP_DIR = os.environ.get("TEMP") or os.environ.get("TMP") or tempfile.gettempdir()
STATE_DIR = Path(_TEMP_DIR) / "signal-light"
SESSION_FILE = STATE_DIR / "sessions.json"
SESSION_TTL_SECONDS = int(os.environ.get("SIGNAL_LIGHT_SESSION_TTL_SECONDS", "86400"))

# 聚合优先级集合（复用原项目定义）
RED_SIGNALS = {"blocked"}
YELLOW_SIGNALS = {"permission", "attention", "done"}
WORKING_SIGNALS = {"thinking", "working", "tool_done"}


def read_aggregate_state() -> str:
    """读取 sessions.json 并返回聚合后的状态名。"""
    if not SESSION_FILE.exists():
        return "offline"

    try:
        content = SESSION_FILE.read_text(encoding="utf-8")
        state = json.loads(content)
    except (json.JSONDecodeError, OSError):
        return "offline"

    sessions = state.get("sessions", {})
    if not isinstance(sessions, dict):
        return "offline"

    now = time.time()
    _prune_sessions(sessions, now)

    if not sessions:
        return "idle"

    return aggregate_sessions(sessions)


def aggregate_sessions(sessions: dict[str, Any]) -> str:
    """将多个 session 信号聚合为全局状态。"""
    signals: list[str] = []
    for value in sessions.values():
        if isinstance(value, dict):
            signal_name = value.get("signal")
            if isinstance(signal_name, str):
                signals.append(signal_name)

    if any(s in RED_SIGNALS for s in signals):
        return "blocked"
    if any(s == "permission" for s in signals):
        return "permission"
    if any(s in YELLOW_SIGNALS for s in signals):
        return "attention"
    if any(s in WORKING_SIGNALS for s in signals):
        return "working"
    return "idle"


def _prune_sessions(sessions: dict[str, Any], now: float) -> None:
    """移除过期的 session 记录。"""
    expired = [
        key
        for key, value in sessions.items()
        if isinstance(value, dict)
        and isinstance(value.get("updated_at"), (int, float))
        and now - value["updated_at"] > SESSION_TTL_SECONDS
    ]
    for key in expired:
        sessions.pop(key, None)
