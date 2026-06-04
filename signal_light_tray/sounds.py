"""音效播放模块。

在需要用户介入的状态（attention / permission / blocked）变化时播放提示音。
"""

from __future__ import annotations

import sys
import winsound
from pathlib import Path
from threading import Lock

if getattr(sys, "frozen", False):
    _SOUNDS_DIR = Path(sys._MEIPASS) / "sounds"
else:
    _SOUNDS_DIR = Path(__file__).resolve().parent.parent / "sounds"

SOUND_MAP: dict[str, Path] = {}
for _file in _SOUNDS_DIR.glob("*"):
    if _file.suffix.lower() in {".wav"}:
        SOUND_MAP[_file.stem.lower()] = _file

_muted = False
_lock = Lock()


def is_muted() -> bool:
    return _muted


def set_muted(muted: bool) -> None:
    global _muted
    with _lock:
        _muted = muted


def toggle_mute() -> bool:
    global _muted
    with _lock:
        _muted = not _muted
    return _muted


def play_attention() -> None:
    """播放 '需要关注' 提示音。"""
    _play_if_not_muted("attention", winsound.SND_ASYNC)


def play_warning() -> None:
    """播放 '阻塞/失败' 警告音。"""
    _play_if_not_muted("warning", winsound.SND_ASYNC)


def _play_if_not_muted(sound_name: str, flags: int = winsound.SND_ASYNC) -> None:
    if _muted:
        return
    path = SOUND_MAP.get(sound_name)
    if path and path.exists():
        winsound.PlaySound(str(path), winsound.SND_FILENAME | flags)
