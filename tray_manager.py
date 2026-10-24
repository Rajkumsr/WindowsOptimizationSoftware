"""
Apex Windows Optimizer - System Tray Notification Area Manager
Integrates with Windows Notification Area (System Tray) using pystray and Pillow,
providing background operation, quick boost actions, and power monitor notifications.
"""

from ui_components import get_app_icon_path

class ApexTrayManager:
    """Manages the Windows Notification Area (System Tray) icon and quick action menu."""
    def __init__(self, app):
        self.app = app
        self.icon = None
        self._running = False
        self.setup_tray()

    def setup_tray(self):
        try:
            import pystray
            from PIL import Image

            icon_path = get_app_icon_path()
            if icon_path:
                img = Image.open(icon_path)
            else:
                img = Image.new("RGBA", (64, 64), color=(0, 120, 212, 255))

            menu = pystray.Menu(
                pystray.MenuItem("🟢 Open Apex Optimizer", self.on_open_app, default=True),
                pystray.MenuItem("⚡ 1-Click Boost & Purge RAM", self.on_quick_boost),
                pystray.MenuItem("🔋 Battery & Power Saver", self.on_open_battery),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("❌ Exit Optimizer", self.on_exit)
            )

            self.icon = pystray.Icon("ApexWindowsOptimizer", img, "Apex Windows Optimizer Pro", menu)
            self.icon.run_detached()
            self._running = True
        except Exception:
            self._running = False

    def is_active(self) -> bool:
        return self._running and (self.icon is not None)

    def notify(self, message: str, title: str = "Apex Windows Optimizer"):
        if self.icon and self._running:
            try:
                self.icon.notify(message, title)
            except Exception:
                pass

    def on_open_app(self, icon=None, item=None):
        self.app.root.after(0, self.app.restore_from_tray)

    def on_quick_boost(self, icon=None, item=None):
        self.app.root.after(0, self.app.action_quick_boost)

    def on_open_battery(self, icon=None, item=None):
        self.app.root.after(0, lambda: self.app.switch_tab("battery"))
        self.app.root.after(20, self.app.restore_from_tray)

    def on_exit(self, icon=None, item=None):
        self.stop()
        self.app.root.after(0, self.app.quit_completely)

    def stop(self):
        if self.icon and self._running:
            self._running = False
            try:
                self.icon.stop()
            except Exception:
                pass
