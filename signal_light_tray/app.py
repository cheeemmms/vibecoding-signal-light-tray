"""Windows 托盘虚拟红绿灯主程序。

通过 pystray 在任务栏托盘显示图标，轮询 Claude Code hook 写入的会话状态文件，
根据聚合状态切换托盘图标并在需要用户介入时播放音效。
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

from PIL import Image
import pystray

from signal_light_tray.state_reader import read_aggregate_state
from signal_light_tray.sounds import play_attention, play_warning, is_muted, toggle_mute
from signal_light_tray.hook_installer import install as install_hook, uninstall as uninstall_hook, status as hook_status

# ── 图标文件路径 ──────────────────────────────────────────
if getattr(sys, "frozen", False):
    _ICONS_DIR = Path(sys._MEIPASS) / "signal_light_tray" / "icons"
else:
    _ICONS_DIR = Path(__file__).resolve().parent / "icons"

ICON_MAP = {
    "offline": _ICONS_DIR / "gray.png",
    "idle": _ICONS_DIR / "green.png",
    "working": _ICONS_DIR / "red.png",
    "thinking": _ICONS_DIR / "red.png",
    "tool_done": _ICONS_DIR / "red.png",
    "attention": _ICONS_DIR / "yellow.png",
    "permission": _ICONS_DIR / "yellow.png",
    "done": _ICONS_DIR / "green.png",
    "blocked": _ICONS_DIR / "red.png",
}

# blocked 状态闪烁使用暗红（降亮度），如果不存在则用灰灯回退
_BLOCKED_DIM_ICON = _ICONS_DIR / "red_dim.png"

STATE_LABELS = {
    "offline": "离线 - 等待 Claude Code 连接",
    "idle": "空闲",
    "working": "工作中",
    "thinking": "思考中",
    "tool_done": "工具执行完成",
    "attention": "需要关注",
    "permission": "请求权限",
    "done": "空闲 - 可以输入",
    "blocked": "阻塞 - 需要处理",
}

POLL_INTERVAL = 0.5


def _load_icon(state: str, dim: bool = False) -> Image.Image | None:
    """加载状态对应的图标文件，失败返回 None。"""
    if state == "blocked" and dim and _BLOCKED_DIM_ICON.exists():
        path = _BLOCKED_DIM_ICON
    else:
        path = ICON_MAP.get(state)
    if path and path.exists():
        return Image.open(path)
    return None


class SignalLightTray:
    """托盘虚拟红绿灯应用。"""

    def __init__(self) -> None:
        self._current_state = "offline"
        self._blocked_flash_toggle = False  # blocked 状态闪烁切换标志
        self._icon = self._load_default_icon()
        self._tray: pystray.Icon | None = None

    def _load_default_icon(self) -> Image.Image:
        icon = _load_icon("offline")
        if icon is None:
            # 极端情况：没有任何图标文件 -> 生成纯色方块
            icon = Image.new("RGB", (64, 64), (128, 128, 128))
        return icon

    # ── 菜单 ──────────────────────────────────────────────

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                lambda _: f"状态：{STATE_LABELS.get(self._current_state, self._current_state)}",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda _: "🔇 静音" if not is_muted() else "🔊 取消静音",
                self._on_toggle_mute,
                checked=lambda item: is_muted(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("安装 Hook", self._on_install_hook),
            pystray.MenuItem("卸载 Hook", self._on_uninstall_hook),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._on_exit),
        )

    def _on_toggle_mute(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        muted = toggle_mute()
        item.text = "🔊 取消静音" if muted else "🔇 静音"

    def _on_install_hook(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        try:
            msg = install_hook()
        except Exception as e:
            msg = f"安装失败：{e}"
        icon.notify(msg, title="Signal Light Tray")

    def _on_uninstall_hook(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        try:
            msg = uninstall_hook()
        except Exception as e:
            msg = f"卸载失败：{e}"
        icon.notify(msg, title="Signal Light Tray")

    def _on_exit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        icon.stop()

    # ── 状态轮询 ──────────────────────────────────────────

    def _poll_loop(self, icon: pystray.Icon) -> None:
        """后台线程：轮询状态文件，更新图标与音效。"""
        previous = ""
        while icon.visible:
            try:
                state = read_aggregate_state()
            except Exception:
                state = "offline"

            if state != previous and state == "permission":
                play_attention()
            elif state != previous and state == "blocked":
                play_warning()
            elif state != previous and state == "idle":
                play_warning()

            previous = state
            self._current_state = state
            icon.update_menu()

            if state == "blocked":
                self._update_blocked_flash(icon)
            else:
                self._update_static_icon(icon, state)
                time.sleep(POLL_INTERVAL)

    def _update_static_icon(self, icon: pystray.Icon, state: str) -> None:
        new_icon = _load_icon(state)
        if new_icon is not None:
            icon.icon = new_icon

    def _update_blocked_flash(self, icon: pystray.Icon) -> None:
        """blocked 状态以 0.3s 交替闪烁红灯。"""
        icon_on = _load_icon("blocked", dim=False)
        icon_off = _load_icon("blocked", dim=True)
        if icon_on is None:
            icon_on = self._load_default_icon()
        if icon_off is None:
            icon_off = _load_icon("offline") or self._load_default_icon()

        for _ in range(2):  # 每轮约 0.6s，然后重新检查状态
            if read_aggregate_state() != "blocked":
                return
            self._blocked_flash_toggle = not self._blocked_flash_toggle
            icon.icon = icon_on if self._blocked_flash_toggle else icon_off
            time.sleep(0.3)

    # ── 启动 ──────────────────────────────────────────────

    def _on_setup(self, icon: pystray.Icon) -> None:
        """pystray 图标就绪回调。设置 visible=True 并启动轮询线程。"""
        icon.visible = True
        threading.Thread(target=self._poll_loop, args=(icon,), daemon=True).start()

    def run(self) -> None:
        self._tray = pystray.Icon(
            "signal_light_tray",
            icon=self._icon,
            title="Signal Light Tray",
            menu=self._build_menu(),
        )
        self._tray.run(setup=self._on_setup)


def main() -> None:
    app = SignalLightTray()
    app.run()


if __name__ == "__main__":
    main()
