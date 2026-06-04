"""Claude Code hook 事件处理器。

由 Claude Code 在 hook 触发时调用，读取 stdin 中的 JSON 事件数据，
映射为信号名并写入 sessions.json。
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Mapping

from signal_light_tray.hook_writer import apply_session_signal

EVENT_TO_SIGNAL = {
    "SessionStart": "session_start",
    "UserPromptSubmit": "thinking",
    "PreToolUse": "working",
    "PostToolUse": "tool_done",
    "PostToolUseFailure": "blocked",
    "PreCompact": "working",
    "SubagentStart": "working",
    "SubagentStop": "tool_done",
    "Stop": "turn_end",
    "Notification": "attention",
    "PermissionRequest": "permission",
    "SessionEnd": "session_end",
}

STOP_REASON_SIGNAL = {
    "max_tokens": "blocked",
    "error": "blocked",
}


def read_hook_input(stdin_text: str) -> dict[str, Any]:
    """解析 Claude Code 传入的 hook 事件数据。"""
    payload: dict[str, Any] = {}

    if stdin_text.strip():
        try:
            parsed = json.loads(stdin_text)
            if isinstance(parsed, Mapping):
                payload = dict(parsed)
        except json.JSONDecodeError:
            payload = {"raw": stdin_text}

    return payload


def choose_signal(payload: dict[str, Any]) -> str:
    """将 hook 事件映射为信号名。"""
    # 允许 payload 中显式指定信号名
    explicit = payload.get("signal") or payload.get("signal_name")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().lower()

    event_name = payload.get("hook_event_name") or payload.get("event") or ""
    if not event_name:
        return "attention"

    if event_name == "Stop":
        stop_reason = payload.get("stop_reason")
        if isinstance(stop_reason, str) and stop_reason in STOP_REASON_SIGNAL:
            return STOP_REASON_SIGNAL[stop_reason]

    return EVENT_TO_SIGNAL.get(event_name, "attention")


def session_key(payload: dict[str, Any]) -> str:
    """确定 session 标识。"""
    sid = payload.get("session_id")
    if isinstance(sid, str) and sid.strip():
        return sid.strip()

    for key in ("CLAUDE_CODE_SESSION_ID", "CLAUDE_SESSION_ID"):
        value = os.environ.get(key)
        if value:
            return value.strip()

    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd.strip():
        return f"cwd:{cwd.strip()}"

    return "global"


def main() -> int:
    stdin_text = sys.stdin.read()
    payload = read_hook_input(stdin_text)
    signal_name = choose_signal(payload)
    key = session_key(payload)

    aggregate = apply_session_signal(key, signal_name)
    # 输出用于调试
    print(f"session={key} signal={signal_name} aggregate={aggregate}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
