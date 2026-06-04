"""将会话状态写入 sessions.json，复用自 vibecoding-signal-light 项目的 runtime.py。

Claude Code hook 触发时由 claude_code_hook.py 调用，将事件映射后的信号写入共享状态文件。
"""

from __future__ import annotations

import json
import msvcrt
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

_TEMP_DIR = os.environ.get("TEMP") or os.environ.get("TMP") or tempfile.gettempdir()
STATE_DIR = Path(_TEMP_DIR) / "signal-light"
SESSION_FILE = STATE_DIR / "sessions.json"
LOCK_FILE = STATE_DIR / "state.lock"
SESSION_TTL_SECONDS = 86400

RED_SIGNALS = {"blocked"}
YELLOW_SIGNALS = {"permission", "attention", "done"}
WORKING_SIGNALS = {"thinking", "working", "tool_done"}
TURN_END_SIGNALS = {"turn_end"}
TURN_END_KEEP_SIGNALS = {"permission", "blocked"}
SESSION_END_SIGNALS = {"session_end"}
SESSION_CLEAR_SIGNALS = {"off"}


def apply_session_signal(session_key: str, signal_name: str) -> str:
    """更新一个 session 的状态，然后返回聚合后的全局状态。"""
    with _state_lock():
        state = _read_session_state()
        sessions = state.setdefault("sessions", {})
        now = time.time()
        _prune_sessions(sessions, now)

        if signal_name in SESSION_END_SIGNALS:
            sessions.pop(session_key, None)
        elif signal_name in SESSION_CLEAR_SIGNALS:
            sessions.pop(session_key, None)
        elif signal_name in TURN_END_SIGNALS:
            current = sessions.get(session_key)
            current_signal = current.get("signal") if isinstance(current, dict) else None
            if current_signal not in TURN_END_KEEP_SIGNALS:
                sessions.pop(session_key, None)
        else:
            # attention/done 不应：
            # 1. 覆盖正在工作中的信号（避免 Notification 导致红黄跳动）
            # 2. 在 session 不存在时新建条目（避免 turn_end 清除后又被 Notification 复活为黄灯）
            if signal_name in ("attention", "done"):
                current = sessions.get(session_key)
                if isinstance(current, dict) and current.get("signal") in WORKING_SIGNALS:
                    aggregate = _aggregate_sessions(sessions)
                    _write_session_state(state)
                    return aggregate
                if current is None:
                    # session 不存在时不创建，直接返回当前聚合结果
                    aggregate = _aggregate_sessions(sessions)
                    _write_session_state(state)
                    return aggregate
            sessions[session_key] = {
                "signal": signal_name,
                "updated_at": now,
            }

        aggregate = _aggregate_sessions(sessions)
        _write_session_state(state)
        return aggregate


def clear_session_state() -> None:
    """清除所有 session 状态。"""
    with _state_lock():
        _write_session_state({"sessions": {}})


@contextmanager
def _state_lock() -> Iterator[None]:
    """Windows 文件锁，防止多进程同时写入。"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(LOCK_FILE, "a") as lock_file:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            yield
    except OSError:
        # 锁文件无法打开时降级为无锁写入
        yield


def _read_session_state() -> dict[str, Any]:
    try:
        state = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"sessions": {}}

    if not isinstance(state, dict):
        return {"sessions": {}}
    if not isinstance(state.get("sessions"), dict):
        state["sessions"] = {}
    return state


def _write_session_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SESSION_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(SESSION_FILE)


def _prune_sessions(sessions: dict[str, Any], now: float) -> None:
    expired = []
    for session_key, value in sessions.items():
        if not isinstance(value, dict):
            expired.append(session_key)
            continue
        updated_at = value.get("updated_at")
        if not isinstance(updated_at, (int, float)) or now - updated_at > SESSION_TTL_SECONDS:
            expired.append(session_key)

    for session_key in expired:
        sessions.pop(session_key, None)


def _aggregate_sessions(sessions: dict[str, Any]) -> str:
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
    if any(s in WORKING_SIGNALS for s in signals):
        return "working"
    if any(s in YELLOW_SIGNALS for s in signals):
        return "attention"
    return "idle"
