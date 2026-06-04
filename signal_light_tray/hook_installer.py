"""安装 Claude Code hook 到 settings.json。

将 `python -m signal_light_tray.claude_code_hook` 注册到 Claude Code 的 hook 配置中。
该命令可在 WSL 和 Windows 原生环境下执行。
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

HOOK_COMMAND = "python -m signal_light_tray.claude_code_hook"

CLAUDE_CODE_EVENTS = {
    "SessionStart": 5,
    "UserPromptSubmit": 5,
    "PreToolUse": 5,
    "PostToolUse": 5,
    "PostToolUseFailure": 5,
    "PreCompact": 5,
    "SubagentStart": 5,
    "SubagentStop": 5,
    "PermissionRequest": 10,
    "Notification": 5,
    "Stop": 5,
    "SessionEnd": 5,
}


def install() -> str:
    """安装 Claude Code hook，返回结果消息。"""
    config_path = _claude_config_path()

    # 备份
    if config_path.exists():
        _backup_config(config_path)

    config = _load_config(config_path)
    hooks = config.setdefault("hooks", {})

    for event, timeout in CLAUDE_CODE_EVENTS.items():
        existing = hooks.get(event, [])
        hooks[event] = _merge_hooks(existing, HOOK_COMMAND, timeout)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return "Hook 安装成功"


def uninstall() -> str:
    """卸载 Claude Code hook，返回结果消息。"""
    config_path = _claude_config_path()
    if not config_path.exists():
        return "未找到 Claude Code 配置，无需卸载"

    config = _load_config(config_path)
    hooks = config.get("hooks")
    if not isinstance(hooks, dict):
        return "未找到 hook 配置，无需卸载"

    changed = False
    for event in list(hooks.keys()):
        entries = hooks[event]
        if isinstance(entries, list):
            cleaned = _remove_signal_light_hooks(entries, HOOK_COMMAND)
            if len(cleaned) != len(entries):
                changed = True
            if cleaned:
                hooks[event] = cleaned
            else:
                del hooks[event]

    if not changed:
        return "未找到本项目的 hook 配置，无需卸载"

    if hooks:
        config["hooks"] = hooks
    else:
        del config["hooks"]

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return "Hook 卸载成功"


def status() -> str:
    """检查 hook 安装状态。"""
    config_path = _claude_config_path()
    if not config_path.exists():
        return "Claude Code 配置未初始化"

    config = _load_config(config_path)
    hooks = config.get("hooks")
    if not isinstance(hooks, dict):
        return "未安装"

    for event in CLAUDE_CODE_EVENTS:
        entries = hooks.get(event)
        if not isinstance(entries, list):
            return "未安装（事件不完整）"
        if not _has_signal_light_hook(entries, HOOK_COMMAND):
            return "未安装（事件不完整）"

    return "已安装"


# ── 内部函数 ────────────────────────────────────────────


def _claude_config_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def _load_config(path: Path) -> dict:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    return parsed


def _backup_config(path: Path) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(path.name + f".bak-signal-light-{stamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def _merge_hooks(existing: list, command: str, timeout: int) -> list:
    """合并 hook 条目，替换已有的 signal-light hook。"""
    if not existing:
        return [_make_hook_group(command, timeout)]

    result = []
    replaced = False
    for group in existing:
        if not isinstance(group, dict):
            result.append(group)
            continue

        entry_hooks = group.get("hooks")
        if not isinstance(entry_hooks, list):
            result.append(group)
            continue

        # 清理该组中的 signal-light hook
        new_hooks = []
        for hook in entry_hooks:
            if isinstance(hook, dict) and _is_signal_light_hook(hook, command):
                if not replaced:
                    new_hooks.append({
                        "type": "command",
                        "command": command,
                        "timeout": timeout,
                    })
                    replaced = True
                continue
            new_hooks.append(hook)

        if new_hooks:
            new_group = dict(group)
            new_group["hooks"] = new_hooks
            result.append(new_group)

    if not replaced:
        result.append(_make_hook_group(command, timeout))

    return result


def _make_hook_group(command: str, timeout: int) -> dict:
    return {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": command,
                "timeout": timeout,
            }
        ],
    }


def _is_signal_light_hook(hook: dict, command: str) -> bool:
    """检查 hook 条目是否属于本项目的 hook。"""
    cmd = hook.get("command", "")
    return isinstance(cmd, str) and (
        cmd == command
        or "signal_light_tray" in cmd
        or "claude-code-signal-hook" in cmd
        or "vibecoding-signal-light" in cmd
    )


def _has_signal_light_hook(entries: list, command: str) -> bool:
    for group in entries:
        if not isinstance(group, dict):
            continue
        entry_hooks = group.get("hooks")
        if not isinstance(entry_hooks, list):
            continue
        for hook in entry_hooks:
            if isinstance(hook, dict) and _is_signal_light_hook(hook, command):
                return True
    return False


def _remove_signal_light_hooks(entries: list, command: str) -> list:
    result = []
    for group in entries:
        if not isinstance(group, dict):
            result.append(group)
            continue
        entry_hooks = group.get("hooks")
        if not isinstance(entry_hooks, list):
            result.append(group)
            continue

        new_hooks = [h for h in entry_hooks if not (
            isinstance(h, dict) and _is_signal_light_hook(h, command)
        )]
        if new_hooks:
            new_group = dict(group)
            new_group["hooks"] = new_hooks
            result.append(new_group)

    return result
