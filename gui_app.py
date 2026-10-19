"""
Apex Windows Optimizer - Modern Tkinter User Interface
A sleek, state-of-the-art dark-themed Windows optimization and debloating suite.
Features:
- High-DPI Display Scaling Awareness
- Live System Resource Telemetry (Dynamic RAM/CPU gauges)
- Real Windows State Detection (Toggles reflect actual live registry settings)
- Reversible Bi-directional Toggles (Optimize or Revert to Windows Default)
- Multi-User Hive Deployment for all accounts & future profiles
- Scoped Smooth Mousewheel Scrolling
"""

import os
import sys
import threading
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Dict, List, Tuple
import webbrowser

# Enable High-DPI Awareness and register AppUserModelID for Windows Taskbar
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    try:
        # Decouple from python host so Taskbar binds to our custom app icon
        app_id = "rajkumarpatil.apexwindowsoptimizer.pro.suite"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

# Import the core optimization engine
import core_optimizer

# -------------------------------------------------------------
# Color Palette & Visual Theme
# -------------------------------------------------------------
THEME = {
    "bg_app": "#0D0F17",         # Deep obsidian window background
    "bg_sidebar": "#131622",     # Sleek dark sidebar
    "bg_card": "#1A1E2E",        # Card / panel background
    "bg_card_alt": "#21263A",    # Hover / secondary card
    "bg_input": "#12141F",       # Input & terminal background
    "border": "#282E47",         # Subtle border line
    "border_highlight": "#3A4366",
    
    # Accents
    "primary": "#6366F1",        # Indigo primary accent
    "primary_hover": "#4F46E5",
    "primary_light": "#818CF8",
    "success": "#10B981",        # Emerald green
    "success_bg": "#064E3B",
    "warning": "#F59E0B",        # Amber
    "warning_bg": "#78350F",
    "danger": "#EF4444",         # Crimson
    "danger_bg": "#7F1D1D",
    
    # Typography
    "text_main": "#F9FAFB",      # Bright white text
    "text_muted": "#9CA3AF",     # Neutral gray text
    "text_dim": "#6B7280",       # Dark muted text
    "accent_cyan": "#06B6D4"     # Cyan metrics
}

FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"

class ModernCard(tk.Frame):
    """A card container with border and background styling."""
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=THEME["bg_card"],
            highlightbackground=THEME["border"],
            highlightthickness=1,
            padx=16,
            pady=14,
            **kwargs
        )

class ToggleSwitch(tk.Frame):
    """An interactive modern toggle switch with title, description, and status chip."""
    def __init__(self, parent, title: str, description: str = "", default: bool = True, command=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_card"], **kwargs)
        self.state = default
        self.command = command

        # Text labels on the left
        text_frame = tk.Frame(self, bg=THEME["bg_card"])
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        header_row = tk.Frame(text_frame, bg=THEME["bg_card"])
        header_row.pack(fill=tk.X)

        self.title_lbl = tk.Label(
            header_row,
            text=title,
            font=(FONT_FAMILY, 10, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"],
            anchor="w"
        )
        self.title_lbl.pack(side=tk.LEFT)

        # Status badge chip
        self.badge_lbl = tk.Label(
            header_row,
            text="",
            font=(FONT_FAMILY, 7, "bold"),
            padx=6,
            pady=1,
            relief="flat"
        )
        self.badge_lbl.pack(side=tk.LEFT, padx=(10, 0))

        if description:
            self.desc_lbl = tk.Label(
                text_frame,
                text=description,
                font=(FONT_FAMILY, 8),
                fg=THEME["text_muted"],
                bg=THEME["bg_card"],
                anchor="w",
                wraplength=480,
                justify="left"
            )
            self.desc_lbl.pack(fill=tk.X, pady=(3, 0))

        # Switch pill canvas on the right
        self.canvas = tk.Canvas(
            self,
            width=46,
            height=24,
            bg=THEME["bg_card"],
            highlightthickness=0,
            cursor="hand2"
        )
        self.canvas.pack(side=tk.RIGHT, padx=(12, 0))
        self.canvas.bind("<Button-1>", self.toggle)
        self.render()

    def render(self):
        self.canvas.delete("all")
        if self.state:
            # Active (ON) state
            self.canvas.create_oval(2, 2, 22, 22, fill=THEME["primary"], outline="")
            self.canvas.create_oval(24, 2, 44, 22, fill=THEME["primary"], outline="")
            self.canvas.create_rectangle(12, 2, 34, 22, fill=THEME["primary"], outline="")
            # Knob
            self.canvas.create_oval(24, 4, 42, 20, fill="#FFFFFF", outline="")
            # Badge
            self.badge_lbl.config(
                text="OPTIMIZED",
                fg=THEME["success"],
                bg=THEME["success_bg"]
            )
        else:
            # Inactive (OFF) state
            self.canvas.create_oval(2, 2, 22, 22, fill=THEME["border"], outline="")
            self.canvas.create_oval(24, 2, 44, 22, fill=THEME["border"], outline="")
            self.canvas.create_rectangle(12, 2, 34, 22, fill=THEME["border"], outline="")
            # Knob
            self.canvas.create_oval(4, 4, 22, 20, fill=THEME["text_muted"], outline="")
            # Badge
            self.badge_lbl.config(
                text="DEFAULT",
                fg=THEME["text_dim"],
                bg=THEME["bg_input"]
            )

    def toggle(self, event=None):
        self.state = not self.state
        self.render()
        if self.command:
            self.command(self.state)

    def get(self) -> bool:
        return self.state

    def set(self, val: bool):
        self.state = val
        self.render()


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

            icon_candidates = [
                os.path.join(getattr(sys, "_MEIPASS", ""), "assets", "app_icon.ico"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "app_icon.ico")
            ]
            valid_icon = None
            for ic in icon_candidates:
                if ic and os.path.exists(ic):
                    valid_icon = ic
                    break

            if valid_icon:
                img = Image.open(valid_icon)
            else:
                img = Image.new("RGBA", (64, 64), color=(99, 102, 241, 255))

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


class ApexOptimizerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Apex Windows Optimizer")
        self.root.geometry("1160x780")
        self.root.minsize(1020, 680)
        self.root.configure(bg=THEME["bg_app"])

        # Set Window and Taskbar Icon
        try:
            icon_candidates = [
                os.path.join(getattr(sys, "_MEIPASS", ""), "assets", "app_icon.ico"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "app_icon.ico")
            ]
            valid_icon = None
            for ic in icon_candidates:
                if ic and os.path.exists(ic):
                    valid_icon = ic
                    break

            if valid_icon:
                # 1. Standard Tkinter window icon
                self.root.iconbitmap(default=valid_icon)

                # 2. Direct Win32 WM_SETICON to guarantee Windows Taskbar button updates immediately
                if sys.platform == "win32":
                    try:
                        self.root.update_idletasks()
                        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                        if not hwnd:
                            hwnd = self.root.winfo_id()

                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        ICON_SMALL = 0
                        ICON_BIG = 1

                        h_icon_big = ctypes.windll.user32.LoadImageW(None, valid_icon, IMAGE_ICON, 48, 48, LR_LOADFROMFILE)
                        h_icon_small = ctypes.windll.user32.LoadImageW(None, valid_icon, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)

                        if h_icon_big:
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon_big)
                        if h_icon_small:
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon_small)
                    except Exception:
                        pass
        except Exception:
            pass

        # Core optimization backend engine
        self.engine = core_optimizer.OptimizationEngine(log_callback=self.on_log_message)
        self.hw_info = self.engine.get_hardware_info()
        self.live_states = self.engine.detect_all_tweak_states()

        # UI State containers
        self.active_tab = "dashboard"
        self.tab_buttons = {}
        self.system_toggles = {}
        self.privacy_toggles = {}
        self.explorer_toggles = {}
        self.gaming_toggles = {}
        self.debloat_checks = {}
        self.cleanup_checks = {}
        self.cleanup_sizes = {}
        self.service_selections = {}
        self.multi_user_deploy_var = tk.BooleanVar(value=True)
        self.battery_alarm_enabled = False
        self._last_alarm_notified = None

        # System Tray & Window Lifecycle Management
        self.tray_manager = ApexTrayManager(self)
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

        self.setup_styles()
        self.build_header()
        self.build_body()
        self.build_status_bar()

        # Initial view
        self.switch_tab("dashboard")

        # Start live background telemetry loop
        self.schedule_live_telemetry()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar",
            troughcolor=THEME["bg_input"],
            background=THEME["primary"],
            bordercolor=THEME["border"],
            lightcolor=THEME["primary"],
            darkcolor=THEME["primary_hover"]
        )

    # -------------------------------------------------------------
    # 1. Header Bar
    # -------------------------------------------------------------
    def build_header(self):
        header = tk.Frame(self.root, bg=THEME["bg_sidebar"], height=64, padx=20, pady=10)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        # Brand Logo and Title
        brand_frame = tk.Frame(header, bg=THEME["bg_sidebar"])
        brand_frame.pack(side=tk.LEFT, fill=tk.Y)

        title_lbl = tk.Label(
            brand_frame,
            text="APEX OPTIMIZER",
            font=(FONT_FAMILY, 14, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_sidebar"]
        )
        title_lbl.pack(side=tk.LEFT, anchor="w")

        v_lbl = tk.Label(
            brand_frame,
            text="PRO v2.0",
            font=(FONT_FAMILY, 8, "bold"),
            fg=THEME["primary_light"],
            bg=THEME["bg_sidebar"]
        )
        v_lbl.pack(side=tk.LEFT, padx=(8, 0), pady=(4, 0))

        # Badges and Quick Tools on the Right
        tools_frame = tk.Frame(header, bg=THEME["bg_sidebar"])
        tools_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Chassis Pill Badge
        chassis_text = f"💻 {self.hw_info['chassis_type']}" if self.hw_info["is_laptop"] else f"🖥️ {self.hw_info['chassis_type']}"
        chassis_badge = tk.Label(
            tools_frame,
            text=chassis_text,
            font=(FONT_FAMILY, 8, "bold"),
            fg=THEME["accent_cyan"],
            bg=THEME["bg_card"],
            padx=10,
            pady=4,
            highlightbackground=THEME["border"],
            highlightthickness=1
        )
        chassis_badge.pack(side=tk.LEFT, padx=(0, 10))

        # Admin Status Badge or Elevation Button
        is_admin = self.engine.is_admin()
        if is_admin:
            admin_badge = tk.Label(
                tools_frame,
                text="🛡️ ADMINISTRATOR",
                font=(FONT_FAMILY, 8, "bold"),
                fg=THEME["success"],
                bg=THEME["success_bg"],
                padx=10,
                pady=4,
                relief="flat"
            )
            admin_badge.pack(side=tk.LEFT, padx=(0, 12))
        else:
            elevate_btn = tk.Button(
                tools_frame,
                text="⚠️ RUN AS ADMIN",
                font=(FONT_FAMILY, 8, "bold"),
                fg="#FFFFFF",
                bg=THEME["warning"],
                activebackground=THEME["warning_bg"],
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=3,
                command=self.engine.relaunch_as_admin
            )
            elevate_btn.pack(side=tk.LEFT, padx=(0, 12))

        # Quick Action Buttons
        tray_btn = tk.Button(
            tools_frame,
            text="📌 Minimize to Tray",
            font=(FONT_FAMILY, 8, "bold"),
            fg=THEME["accent_cyan"],
            bg=THEME["bg_card"],
            activebackground=THEME["bg_card_alt"],
            activeforeground=THEME["text_main"],
            relief="flat",
            cursor="hand2",
            padx=9,
            pady=3,
            command=lambda: self.minimize_to_tray(show_toast=True)
        )
        tray_btn.pack(side=tk.LEFT, padx=(0, 6))

        dns_btn = tk.Button(
            tools_frame,
            text="🌐 Flush DNS",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            activebackground=THEME["bg_card_alt"],
            activeforeground=THEME["text_main"],
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=3,
            command=self.quick_flush_dns
        )
        dns_btn.pack(side=tk.LEFT, padx=(0, 6))

        exp_btn = tk.Button(
            tools_frame,
            text="🔄 Restart Explorer",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            activebackground=THEME["bg_card_alt"],
            activeforeground=THEME["text_main"],
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=3,
            command=self.quick_restart_explorer
        )
        exp_btn.pack(side=tk.LEFT)

    # -------------------------------------------------------------
    # 2. Body: Sidebar + Main Content Frame
    # -------------------------------------------------------------
    def build_body(self):
        self.body_frame = tk.Frame(self.root, bg=THEME["bg_app"])
        self.body_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Sidebar
        self.sidebar = tk.Frame(self.body_frame, bg=THEME["bg_sidebar"], width=230, padx=10, pady=12)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("system", "⚡  System & Speed"),
            ("privacy", "🛡️  Privacy & Telemetry"),
            ("explorer", "🎨  Explorer & Shell"),
            ("services", "⚙️  Services Optimizer"),
            ("debloat", "🗑️  App Debloater"),
            ("gaming", "🎮  Gaming & GPU Boost"),
            ("battery", "🔋  Battery & Power Saver"),
            ("cleaner", "🧹  Disk & Cache Clean"),
            ("updater", "📦  Software Updater"),
            ("terminal", "📝  Live Activity Log"),
            ("developer", "👨‍💻  Developer & About")
        ]

        for tab_id, label in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=label,
                font=(FONT_FAMILY, 9),
                fg=THEME["text_muted"],
                bg=THEME["bg_sidebar"],
                activebackground=THEME["bg_card"],
                activeforeground=THEME["text_main"],
                anchor="w",
                relief="flat",
                cursor="hand2",
                padx=14,
                pady=7,
                command=lambda tid=tab_id: self.switch_tab(tid)
            )
            btn.pack(fill=tk.X, pady=1)
            self.tab_buttons[tab_id] = btn

        # Pinned Sidebar Developer Card
        dev_footer = tk.Frame(self.sidebar, bg=THEME["bg_card"], padx=10, pady=10, highlightbackground=THEME["border"], highlightthickness=1)
        dev_footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        tk.Label(
            dev_footer,
            text="DEVELOPED BY",
            font=(FONT_FAMILY, 7, "bold"),
            fg=THEME["text_dim"],
            bg=THEME["bg_card"]
        ).pack(anchor="w")

        tk.Button(
            dev_footer,
            text="Rajkumar Patil",
            font=(FONT_FAMILY, 9, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"],
            activebackground=THEME["bg_card_alt"],
            activeforeground=THEME["accent_cyan"],
            anchor="w",
            relief="flat",
            cursor="hand2",
            padx=0,
            pady=0,
            command=lambda: self.switch_tab("developer")
        ).pack(anchor="w", pady=(2, 6))

        social_btns = tk.Frame(dev_footer, bg=THEME["bg_card"])
        social_btns.pack(fill=tk.X)

        tk.Button(
            social_btns,
            text="🐙 GitHub",
            font=(FONT_FAMILY, 7, "bold"),
            fg="#FFFFFF",
            bg="#24292E",
            activebackground="#2F363D",
            relief="flat",
            cursor="hand2",
            padx=4,
            pady=3,
            command=lambda: webbrowser.open_new_tab("https://github.com/Rajkumsr")
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        tk.Button(
            social_btns,
            text="💼 LinkedIn",
            font=(FONT_FAMILY, 7, "bold"),
            fg="#FFFFFF",
            bg="#0A66C2",
            activebackground="#004182",
            relief="flat",
            cursor="hand2",
            padx=4,
            pady=3,
            command=lambda: webbrowser.open_new_tab("https://www.linkedin.com/in/rajkumar-patil-2b13a5180")
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Main Scrollable / Switchable Content Area
        self.content_container = tk.Frame(self.body_frame, bg=THEME["bg_app"], padx=20, pady=16)
        self.content_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------
    # 3. Status Bar
    # -------------------------------------------------------------
    def build_status_bar(self):
        status_bar = tk.Frame(self.root, bg=THEME["bg_sidebar"], height=32, padx=16)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        status_bar.pack_propagate(False)

        self.status_label = tk.Label(
            status_bar,
            text="Ready. System normal.",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_sidebar"]
        )
        self.status_label.pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(status_bar, mode="indeterminate", length=160, style="TProgressbar")
        self.progress_bar.pack(side=tk.RIGHT, padx=10)

    def switch_tab(self, tab_id: str):
        self.active_tab = tab_id
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(
                    bg=THEME["primary"],
                    fg="#FFFFFF",
                    font=(FONT_FAMILY, 9, "bold")
                )
            else:
                btn.configure(
                    bg=THEME["bg_sidebar"],
                    fg=THEME["text_muted"],
                    font=(FONT_FAMILY, 9)
                )

        # Clear existing views
        for widget in self.content_container.winfo_children():
            widget.destroy()

        # Render corresponding view
        if tab_id == "dashboard":
            self.render_dashboard()
        elif tab_id == "system":
            self.render_system_tweaks()
        elif tab_id == "privacy":
            self.render_privacy_tweaks()
        elif tab_id == "explorer":
            self.render_explorer_tweaks()
        elif tab_id == "services":
            self.render_services_optimizer()
        elif tab_id == "debloat":
            self.render_debloater()
        elif tab_id == "gaming":
            self.render_gaming_boost()
        elif tab_id == "battery":
            self.render_battery_page()
        elif tab_id == "cleaner":
            self.render_disk_cleaner()
        elif tab_id == "updater":
            self.render_software_updater()
        elif tab_id == "terminal":
            self.render_terminal_log()
        elif tab_id == "developer":
            self.render_developer_page()

    def set_status(self, text: str, is_busy: bool = False):
        self.status_label.config(text=text)
        if is_busy:
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()

    def on_log_message(self, message: str, level: str):
        self.root.after(0, lambda: self._append_to_terminal(message, level))

    def _append_to_terminal(self, message: str, level: str):
        if hasattr(self, 'terminal_text') and self.terminal_text.winfo_exists():
            tag = "INFO"
            if level == "SUCCESS":
                tag = "SUCCESS"
            elif level == "WARNING":
                tag = "WARNING"
            elif level == "ERROR":
                tag = "ERROR"

            time_str = datetime.now().strftime("%H:%M:%S")
            self.terminal_text.insert(tk.END, f"[{time_str}] ", "TIME")
            self.terminal_text.insert(tk.END, f"[{level}] ", tag)
            self.terminal_text.insert(tk.END, f"{message}\n", "MSG")
            self.terminal_text.see(tk.END)

    # -------------------------------------------------------------
    # Periodic Live Telemetry (RAM & Hardware)
    # -------------------------------------------------------------
    def schedule_live_telemetry(self):
        def _update():
            if self.active_tab == "dashboard":
                hw = self.engine.get_hardware_info()
                if hasattr(self, 'ram_val_lbl') and self.ram_val_lbl.winfo_exists():
                    self.ram_val_lbl.config(text=f"{hw['free_ram']} Free of {hw['total_ram']}")
                if hasattr(self, 'dash_cpu_lbl') and self.dash_cpu_lbl.winfo_exists():
                    self.dash_cpu_lbl.config(text=f"{hw.get('cpu_percent', 0):.0f}% Load")
                if hasattr(self, 'dash_uptime_lbl') and self.dash_uptime_lbl.winfo_exists():
                    self.dash_uptime_lbl.config(text=f"Uptime: {hw.get('uptime', 'Active')}")
                if hasattr(self, 'dash_score_lbl') and self.dash_score_lbl.winfo_exists():
                    score_info = self.engine.calculate_health_score(self.live_states)
                    self.dash_score_lbl.config(text=f"{score_info['score']}%", fg=score_info["color"])
                    if hasattr(self, 'dash_rating_lbl') and self.dash_rating_lbl.winfo_exists():
                        self.dash_rating_lbl.config(text=score_info["rating"], fg=score_info["color"])

            # Check Battery Health Alarm if enabled
            if getattr(self, "battery_alarm_enabled", False):
                try:
                    telem = self.engine.get_battery_telemetry()
                    if telem.get("has_battery", False):
                        pct = telem.get("percent", 0)
                        ac = telem.get("ac_online", False)
                        if ac and pct >= 80 and self._last_alarm_notified != "high":
                            self._last_alarm_notified = "high"
                            try:
                                import winsound
                                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                            except Exception:
                                pass
                            self.on_log_message(f"Battery Health Guard: Battery reached {pct}% on charger. Unplug to prevent high-voltage cell wear.", "WARNING")
                            messagebox.showinfo(
                                "Battery Health Guard",
                                f"⚡ Battery Reached {pct}%\n\nYour battery is charged to 80%+. Please unplug the AC charger to protect lithium-ion cells from continuous high-voltage degradation."
                            )
                        elif not ac and pct <= 20 and self._last_alarm_notified != "low":
                            self._last_alarm_notified = "low"
                            try:
                                import winsound
                                winsound.MessageBeep(winsound.MB_ICONHAND)
                            except Exception:
                                pass
                            self.on_log_message(f"Battery Low: Battery has dropped to {pct}%. Connect charger to avoid deep discharge.", "WARNING")
                            messagebox.showwarning(
                                "Battery Low Warning",
                                f"🪫 Low Battery ({pct}%)\n\nPlease connect your charger to avoid deep discharge cell damage."
                            )
                        elif 25 < pct < 78:
                            self._last_alarm_notified = None
                except Exception:
                    pass

            self.root.after(2500, _update)

        self.root.after(2500, _update)

    # -------------------------------------------------------------
    # TAB 1: Dashboard
    # -------------------------------------------------------------
    def render_dashboard(self):
        title_frame = tk.Frame(self.content_container, bg=THEME["bg_app"])
        title_frame.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            title_frame,
            text="System Overview & Health Diagnostics",
            font=(FONT_FAMILY, 15, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_app"]
        ).pack(anchor="w")

        tk.Label(
            title_frame,
            text="Real-time system health score, live hardware telemetry, and one-click rapid tuning.",
            font=(FONT_FAMILY, 9),
            fg=THEME["text_muted"],
            bg=THEME["bg_app"]
        ).pack(anchor="w", pady=(2, 0))

        # Metrics Grid (4 cards in a row)
        grid_frame = tk.Frame(self.content_container, bg=THEME["bg_app"])
        grid_frame.pack(fill=tk.X, pady=(0, 16))

        # 1. System Health & Optimization Rating Card
        score_info = self.engine.calculate_health_score(self.live_states)
        c1 = ModernCard(grid_frame)
        c1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        tk.Label(c1, text="🛡️  System Health Score", font=(FONT_FAMILY, 8, "bold"), fg=THEME["primary_light"], bg=THEME["bg_card"]).pack(anchor="w")
        
        score_row = tk.Frame(c1, bg=THEME["bg_card"])
        score_row.pack(fill=tk.X, pady=(4, 2))
        self.dash_score_lbl = tk.Label(score_row, text=f"{score_info['score']}%", font=(FONT_FAMILY, 16, "bold"), fg=score_info["color"], bg=THEME["bg_card"])
        self.dash_score_lbl.pack(side=tk.LEFT)
        self.dash_rating_lbl = tk.Label(score_row, text=score_info["rating"], font=(FONT_FAMILY, 9, "bold"), fg=score_info["color"], bg=THEME["bg_card"])
        self.dash_rating_lbl.pack(side=tk.LEFT, padx=(8, 0))

        self.dash_tweaks_lbl = tk.Label(
            c1,
            text=f"{score_info['applied_count']} of {score_info['total_count']} Essential Tweaks Active",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        )
        self.dash_tweaks_lbl.pack(anchor="w")

        # 2. CPU Card (Live Load)
        c2 = ModernCard(grid_frame)
        c2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        tk.Label(c2, text="⚡  Processor (CPU)", font=(FONT_FAMILY, 8, "bold"), fg=THEME["accent_cyan"], bg=THEME["bg_card"]).pack(anchor="w")
        self.dash_cpu_lbl = tk.Label(c2, text=f"{self.hw_info.get('cpu_percent', 0):.0f}% Load", font=(FONT_FAMILY, 13, "bold"), fg=THEME["text_main"], bg=THEME["bg_card"])
        self.dash_cpu_lbl.pack(anchor="w", pady=(2, 0))
        tk.Label(c2, text=self.hw_info["cpu_name"], font=(FONT_FAMILY, 8), fg=THEME["text_muted"], bg=THEME["bg_card"], wraplength=170, justify="left").pack(anchor="w", pady=(2, 0))

        # 3. RAM Card (Live)
        c3 = ModernCard(grid_frame)
        c3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        tk.Label(c3, text="🧠  Physical Memory (Live)", font=(FONT_FAMILY, 8, "bold"), fg=THEME["success"], bg=THEME["bg_card"]).pack(anchor="w")
        self.ram_val_lbl = tk.Label(c3, text=f"{self.hw_info['free_ram']} Free of {self.hw_info['total_ram']}", font=(FONT_FAMILY, 11, "bold"), fg=THEME["text_main"], bg=THEME["bg_card"], wraplength=170, justify="left")
        self.ram_val_lbl.pack(anchor="w", pady=(4, 0))
        tk.Label(c3, text=f"{self.hw_info['ram_percent']} Utilized", font=(FONT_FAMILY, 8), fg=THEME["text_muted"], bg=THEME["bg_card"]).pack(anchor="w", pady=(2, 0))

        # 4. Uptime & Chassis Card
        c4 = ModernCard(grid_frame)
        c4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(c4, text="⏱️  System Uptime & Drive", font=(FONT_FAMILY, 8, "bold"), fg=THEME["warning"], bg=THEME["bg_card"]).pack(anchor="w")
        self.dash_uptime_lbl = tk.Label(c4, text=f"Uptime: {self.hw_info.get('uptime', 'Active')}", font=(FONT_FAMILY, 11, "bold"), fg=THEME["text_main"], bg=THEME["bg_card"])
        self.dash_uptime_lbl.pack(anchor="w", pady=(4, 0))
        tk.Label(c4, text=f"{self.hw_info['system_drive']} ({self.hw_info['drive_type']}) • {self.hw_info['chassis_type']}", font=(FONT_FAMILY, 8), fg=THEME["text_muted"], bg=THEME["bg_card"], wraplength=170, justify="left").pack(anchor="w", pady=(2, 0))

        # Hero Card: 1-Click Instant System Boost & Quick Optimize
        hero_card = ModernCard(self.content_container)
        hero_card.pack(fill=tk.X, pady=(0, 16))

        h_left = tk.Frame(hero_card, bg=THEME["bg_card"])
        h_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            h_left,
            text="⚡  1-Click Instant System Boost & RAM Working Set Purge",
            font=(FONT_FAMILY, 13, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(anchor="w")

        tk.Label(
            h_left,
            text="Instantly clears trapped standby memory, temporary caches, and speeds up system responsiveness:\n"
                 "• Purge RAM Standby List and process working sets (instantly frees 1 GB - 3 GB memory)\n"
                 "• Clean system and user temporary caches without closing running programs\n"
                 "• Flush Windows DNS resolver cache to eliminate browsing latency\n"
                 "• Real-time recalibration of Windows Health Score",
            font=(FONT_FAMILY, 9),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            justify="left"
        ).pack(anchor="w", pady=(6, 0))

        h_right = tk.Frame(hero_card, bg=THEME["bg_card"])
        h_right.pack(side=tk.RIGHT, padx=10)

        boost_btn = tk.Button(
            h_right,
            text="⚡ 1-CLICK BOOST & PURGE RAM",
            font=(FONT_FAMILY, 10, "bold"),
            fg="#FFFFFF",
            bg=THEME["success"],
            activebackground=THEME["accent_cyan"],
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=10,
            command=self.action_quick_boost
        )
        boost_btn.pack(fill=tk.X, pady=(0, 8))

        opt_btn = tk.Button(
            h_right,
            text="🚀 QUICK OPTIMIZE TWEAKS",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg=THEME["primary"],
            activebackground=THEME["primary_hover"],
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
            command=self.run_quick_optimize
        )
        opt_btn.pack(fill=tk.X)

        # Quick System Tools & Rollback Card
        action_card = ModernCard(self.content_container)
        action_card.pack(fill=tk.X)

        tk.Label(
            action_card,
            text="Quick System Tools & Maintenance",
            font=(FONT_FAMILY, 11, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(anchor="w", pady=(0, 10))

        btn_row = tk.Frame(action_card, bg=THEME["bg_card"])
        btn_row.pack(fill=tk.X)

        actions = [
            ("🛡️ Create System Restore Point", self.action_create_restore_point),
            ("🧠 Purge Standby RAM", self.action_flush_ram_only),
            ("📁 Export Registry Backup", self.action_export_reg),
            ("🌐 Flush DNS Cache", self.quick_flush_dns),
            ("🔄 Restart Explorer Shell", self.quick_restart_explorer)
        ]

        for text, cmd in actions:
            b = tk.Button(
                btn_row,
                text=text,
                font=(FONT_FAMILY, 9),
                fg=THEME["text_main"],
                bg=THEME["bg_card_alt"],
                activebackground=THEME["border"],
                relief="flat",
                cursor="hand2",
                padx=12,
                pady=8,
                command=cmd
            )
            b.pack(side=tk.LEFT, padx=(0, 8))

    # -------------------------------------------------------------
    # TAB 2: System & Speed
    # -------------------------------------------------------------
    def render_system_tweaks(self):
        self.render_section_header(
            "System Performance & Kernel Tuning",
            "Fine-tune low-level Windows kernel parameters, network throughput, and startup timeouts. Toggles reflect current system state."
        )

        scroll_canvas, scroll_content = self.create_scrollable_container()

        tweak_defs = [
            ("network_throttling", "Disable Multimedia Network Throttling", "Sets NetworkThrottlingIndex to disabled (0xFFFFFFFF) so gaming and streaming packets are never prioritized down."),
            ("system_responsiveness", "Foreground System Responsiveness", "Reserves 90% CPU priority for active foreground games and programs (SystemResponsiveness = 10)."),
            ("irp_stack_size", "Optimize IRP Stack Size", "Sets IRPStackSize to 30, significantly increasing throughput for local network and file sharing transfers."),
            ("fast_shutdown", "Accelerated Service Termination", "Reduces WaitToKillServiceTimeout to 5000ms, preventing stalled services from delaying shutdown."),
            ("long_paths", "Enable NTFS Long File Paths", "Removes legacy MAX_PATH 260-character path limits in Windows file system."),
            ("block_oem_bloat", "Block OEM Firmware WPBT Software", "Blocks hardware vendors and UEFI firmware from automatically installing bundled promotional software at boot."),
            ("disable_p2p_update", "Disable P2P Update Seeding", "Stops Windows Delivery Optimization from using your upstream internet connection to upload updates to others."),
            ("f8_boot_menu", "Enable Classic F8 Boot Menu", "Restores the legacy F8 boot selection menu for easy recovery and Safe Mode access."),
            ("disable_hibernation", "Disable Hibernation (Desktop PC)", "Deletes hiberfil.sys to reclaim disk space equivalent to your total RAM size (desktops only).")
        ]

        self.system_toggles.clear()
        for key, title, desc in tweak_defs:
            card = ModernCard(scroll_content)
            card.pack(fill=tk.X, pady=(0, 8))
            current_state = self.live_states.get(key, True)
            toggle = ToggleSwitch(card, title, desc, default=current_state)
            toggle.pack(fill=tk.X)
            self.system_toggles[key] = toggle

        # Action Button
        btn_frame = tk.Frame(self.content_container, bg=THEME["bg_app"])
        btn_frame.pack(fill=tk.X, pady=(12, 0))

        tk.Button(
            btn_frame,
            text="APPLY SYSTEM CHANGES",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg=THEME["primary"],
            activebackground=THEME["primary_hover"],
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            command=self.action_apply_system_tweaks
        ).pack(side=tk.RIGHT)

    # -------------------------------------------------------------
    # TAB 3: Privacy & Telemetry
    # -------------------------------------------------------------
    def render_privacy_tweaks(self):
        self.render_section_header(
            "Privacy, Telemetry & Background Tracking",
            "Eliminate background diagnostic data collection, advertising IDs, and invasive telemetry. Toggles reflect current state."
        )

        scroll_canvas, scroll_content = self.create_scrollable_container()

        tweak_defs = [
            ("disable_telemetry", "Disable Diagnostic Telemetry & CEIP", "Disables DiagTrack, feedback notifications, Windows Error Reporting telemetry, and Customer Experience Program."),
            ("disable_lockscreen_ads", "Disable Lock Screen Spotlight Ads", "Prevents Microsoft Spotlight from displaying sponsored tips, recommendations, and advertisements on the lock screen."),
            ("disable_recall", "Disable Microsoft Recall AI Tracking", "Blocks automated continuous screenshot captures and AI analysis from the Recall subsystem."),
            ("optimize_edge", "Optimize Microsoft Edge Background Mode", "Stops Microsoft Edge from running in the background when closed and disables startup boost and shopping assistant."),
            ("suppress_oobe_telemetry", "Suppress OOBE Diagnostic Experiences", "Bypasses consumer data harvesting prompts and privacy opt-ins during updates."),
            ("disable_office_telemetry", "Disable Microsoft Office Telemetry", "Disables telemetry logging, Customer Experience feedback, and diagnostic data upload for Office 2013-365.")
        ]

        self.privacy_toggles.clear()
        for key, title, desc in tweak_defs:
            card = ModernCard(scroll_content)
            card.pack(fill=tk.X, pady=(0, 8))
            current_state = self.live_states.get(key, True)
            toggle = ToggleSwitch(card, title, desc, default=current_state)
            toggle.pack(fill=tk.X)
            self.privacy_toggles[key] = toggle

        # Action Button
        btn_frame = tk.Frame(self.content_container, bg=THEME["bg_app"])
        btn_frame.pack(fill=tk.X, pady=(12, 0))

        tk.Button(
            btn_frame,
            text="APPLY PRIVACY CHANGES",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg=THEME["primary"],
            activebackground=THEME["primary_hover"],
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            command=self.action_apply_privacy_tweaks
        ).pack(side=tk.RIGHT)

    # -------------------------------------------------------------
    # TAB 4: Explorer & Shell
    # -------------------------------------------------------------
    def render_explorer_tweaks(self):
        self.render_section_header(
            "Explorer & Shell Personalization",
            "Streamline File Explorer, remove clutter, and restore productivity-focused desktop behaviors."
        )

        scroll_canvas, scroll_content = self.create_scrollable_container()

        # Multi-user deployment banner
        multi_card = ModernCard(scroll_content)
        multi_card.pack(fill=tk.X, pady=(0, 10))

        chk = tk.Checkbutton(
            multi_card,
            text="Deploy settings to all user profiles & future accounts (Default User Hive)",
            variable=self.multi_user_deploy_var,
            font=(FONT_FAMILY, 9, "bold"),
            fg=THEME["accent_cyan"],
            bg=THEME["bg_card"],
            selectcolor=THEME["bg_card_alt"],
            activebackground=THEME["bg_card"],
            activeforeground=THEME["accent_cyan"],
            cursor="hand2"
        )
        chk.pack(anchor="w")

        tk.Label(
            multi_card,
            text="When enabled, mounts C:\\Users\\Default\\NTUSER.DAT so any new account created on this PC automatically inherits your chosen settings.",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        ).pack(anchor="w", padx=24, pady=(2, 0))

        tweak_defs = [
            ("show_extensions", "Show File Name Extensions", "Always display file extensions (.exe, .txt, .pdf, .zip) to prevent spoofing and improve visibility."),
            ("show_hidden", "Show Hidden Files & Folders", "Make hidden system files and folders visible in File Explorer."),
            ("open_this_pc", "Open File Explorer to 'This PC'", "Launches File Explorer directly into 'This PC' with drives listed, rather than the slow Quick Access view."),
            ("classic_context_menu", "Restore Classic Context Menu (Windows 11)", "Restores the traditional, responsive Windows 10 right-click menu without having to click 'Show more options'."),
            ("disable_start_bing", "Disable Bing Web Search in Start Menu", "Restricts Start Menu search queries to local files and apps, eliminating unwanted web recommendations."),
            ("taskbar_end_task", "Enable 'End Task' on Taskbar", "Adds a direct 'End Task' context menu option when right-clicking running apps on the taskbar."),
            ("clean_taskbar", "Clean Taskbar Clutter (Hide Widgets & Copilot)", "Hides news widgets, task view, and Copilot buttons from the taskbar to maximize active window space."),
            ("fast_menu_delay", "Accelerate UI Menu Animation Response", "Reduces MenuShowDelay to 10ms for instant dropdowns and context menus."),
            ("disable_sticky_keys", "Disable 5x Shift Sticky Keys Prompt", "Prevents accidental activation dialogs when tapping Shift repeatedly in games or editing.")
        ]

        self.explorer_toggles.clear()
        for key, title, desc in tweak_defs:
            card = ModernCard(scroll_content)
            card.pack(fill=tk.X, pady=(0, 8))
            current_state = self.live_states.get(key, True)
            toggle = ToggleSwitch(card, title, desc, default=current_state)
            toggle.pack(fill=tk.X)
            self.explorer_toggles[key] = toggle

        # Action Button
        btn_frame = tk.Frame(self.content_container, bg=THEME["bg_app"])
        btn_frame.pack(fill=tk.X, pady=(12, 0))

        tk.Button(
            btn_frame,
            text="APPLY EXPLORER CHANGES",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg=THEME["primary"],
            activebackground=THEME["primary_hover"],
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            command=self.action_apply_explorer_tweaks
        ).pack(side=tk.RIGHT)

    # -------------------------------------------------------------
    # TAB 5: Services Optimizer
    # -------------------------------------------------------------
    def render_services_optimizer(self):
        self.render_section_header(
            "Windows Services Optimization",
            "Safely configure background services to reduce idle CPU and RAM footprint without breaking dependencies."
        )

        catalog = self.engine.get_services_catalog()
        scroll_canvas, scroll_content = self.create_scrollable_container()

        self.service_selections.clear()

        # Preset Controls Header
        preset_card = ModernCard(scroll_content)
        preset_card.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            preset_card,
            text="Optimization Presets:",
            font=(FONT_FAMILY, 9, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT, padx=(0, 10))

        presets = [
            ("Recommended (Safe)", self.preset_services_recommended),
            ("Maximum Gaming", self.preset_services_gaming),
            ("Reset All to Demand", self.preset_services_reset)
        ]

        for p_name, p_cmd in presets:
            tk.Button(
                preset_card,
                text=p_name,
                font=(FONT_FAMILY, 8),
                fg=THEME["text_main"],
                bg=THEME["bg_card_alt"],
                activebackground=THEME["border"],
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=4,
                command=p_cmd
            ).pack(side=tk.LEFT, padx=(0, 8))

        # Services List
        for svc in catalog:
            card = ModernCard(scroll_content)
            card.pack(fill=tk.X, pady=(0, 6))

            info_f = tk.Frame(card, bg=THEME["bg_card"])
            info_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            tk.Label(
                info_f,
                text=f"{svc['display']} ({svc['name']})",
                font=(FONT_FAMILY, 9, "bold"),
                fg=THEME["text_main"],
                bg=THEME["bg_card"]
            ).pack(anchor="w")

            tk.Label(
                info_f,
                text=f"[{svc['category']}] {svc['desc']}",
                font=(FONT_FAMILY, 8),
                fg=THEME["text_muted"],
                bg=THEME["bg_card"]
            ).pack(anchor="w", pady=(2, 0))

            # Mode selector dropdown
            mode_var = tk.StringVar(value=svc["mode"])
            self.service_selections[svc["name"]] = mode_var

            mode_menu = tk.OptionMenu(card, mode_var, "disabled", "demand", "auto")
            mode_menu.config(
                bg=THEME["bg_input"],
                fg=THEME["text_main"],
                activebackground=THEME["border"],
                activeforeground=THEME["text_main"],
                font=(FONT_FAMILY, 8),
                highlightthickness=0,
                relief="flat",
                width=8
            )
            mode_menu.pack(side=tk.RIGHT, padx=10)

        # Action Button
        btn_frame = tk.Frame(self.content_container, bg=THEME["bg_app"])
        btn_frame.pack(fill=tk.X, pady=(12, 0))

        tk.Button(
            btn_frame,
            text="APPLY SERVICE CONFIGURATION",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg=THEME["primary"],
            activebackground=THEME["primary_hover"],
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            command=self.action_apply_services
        ).pack(side=tk.RIGHT)

    def preset_services_recommended(self):
        for svc, var in self.service_selections.items():
            if svc in ["DiagTrack", "dmwappushservice", "diagnosticshub.standardcollector.service", "RetailDemo", "RemoteRegistry"]:
                var.set("disabled")
            else:
                var.set("demand")

    def preset_services_gaming(self):
        for svc, var in self.service_selections.items():
            var.set("disabled")

    def preset_services_reset(self):
        for svc, var in self.service_selections.items():
            var.set("demand")

    # -------------------------------------------------------------
    # TAB 6: App Debloater
    # -------------------------------------------------------------
    def render_debloater(self):
        self.render_section_header(
            "UWP & Windows Bloatware Cleaner",
            "Safely uninstall unwanted preinstalled Microsoft and third-party apps for all current and future accounts."
        )

        scroll_canvas, scroll_content = self.create_scrollable_container()

        targets = self.engine.get_debloat_targets()
        self.debloat_checks.clear()

        # Selection Control Row
        sel_card = ModernCard(scroll_content)
        sel_card.pack(fill=tk.X, pady=(0, 10))

        tk.Button(
            sel_card,
            text="Select All Recommended",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_main"],
            bg=THEME["bg_card_alt"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=lambda: [var.set(True) for var in self.debloat_checks.values()]
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            sel_card,
            text="Deselect All",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_main"],
            bg=THEME["bg_card_alt"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=lambda: [var.set(False) for var in self.debloat_checks.values()]
        ).pack(side=tk.LEFT)

        for target in targets:
            card = ModernCard(scroll_content)
            card.pack(fill=tk.X, pady=(0, 6))

            var = tk.BooleanVar(value=True if target["id"] in ["copilot", "bing_search", "widgets", "web_exp", "bing_news", "solitaire"] else False)
            self.debloat_checks[target["pattern"]] = var

            chk = tk.Checkbutton(
                card,
                text=f"{target['name']}",
                variable=var,
                font=(FONT_FAMILY, 10, "bold"),
                fg=THEME["text_main"],
                bg=THEME["bg_card"],
                selectcolor=THEME["bg_card_alt"],
                activebackground=THEME["bg_card"],
                activeforeground=THEME["text_main"],
                cursor="hand2"
            )
            chk.pack(anchor="w")

            tk.Label(
                card,
                text=f"{target['desc']}  (Pattern: {target['pattern']})",
                font=(FONT_FAMILY, 8),
                fg=THEME["text_muted"],
                bg=THEME["bg_card"]
            ).pack(anchor="w", padx=24, pady=(2, 0))

        # Action Button
        btn_frame = tk.Frame(self.content_container, bg=THEME["bg_app"])
        btn_frame.pack(fill=tk.X, pady=(12, 0))

        tk.Button(
            btn_frame,
            text="UNINSTALL SELECTED APPS",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg=THEME["danger"],
            activebackground=THEME["danger_bg"],
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            command=self.action_remove_bloatware
        ).pack(side=tk.RIGHT)

    # -------------------------------------------------------------
    # TAB 7: Gaming & GPU Boost
    # -------------------------------------------------------------
    def render_gaming_boost(self):
        self.render_section_header(
            "Gaming & GPU Performance Boost",
            "Unlock ultra-low input latency, dedicated multimedia priority, and maximum hardware clocks. Toggles reflect current state."
        )

        scroll_canvas, scroll_content = self.create_scrollable_container()

        tweak_defs = [
            ("mmcss_priority", "MMCSS Multimedia Priority (Games & Audio)", "Configures GPU Priority = 8, Priority = 6, and Scheduling Category = High for ultra-smooth frame delivery."),
            ("enable_hags", "Hardware-Accelerated GPU Scheduling (HAGS)", "Passes memory scheduling directly to GPU VRAM for reduced latency (reboot required)."),
            ("windowed_optimizations", "Optimizations for Windowed Games", "Enables the modern flip model presentation for DirectX 10/11 windowed games."),
            ("reset_hpet", "Reset HPET Override Timer Dependency", "Removes explicit useplatformclock overrides, fixing micro-stuttering and timer desync."),
            ("disable_power_throttling", "Disable CPU Power Throttling", "Prevents Windows power throttling from lowering CPU frequencies under intense gaming loads (Desktop)."),
            ("ultimate_performance", "Unlock Ultimate Performance Power Scheme", "Duplicates and activates Windows' hidden Ultimate Performance power plan for 0% latency throttling.")
        ]

        self.gaming_toggles.clear()
        for key, title, desc in tweak_defs:
            card = ModernCard(scroll_content)
            card.pack(fill=tk.X, pady=(0, 8))
            current_state = self.live_states.get(key, True)
            toggle = ToggleSwitch(card, title, desc, default=current_state)
            toggle.pack(fill=tk.X)
            self.gaming_toggles[key] = toggle

        # Action Button
        btn_frame = tk.Frame(self.content_container, bg=THEME["bg_app"])
        btn_frame.pack(fill=tk.X, pady=(12, 0))

        tk.Button(
            btn_frame,
            text="APPLY GAMING BOOST",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg=THEME["primary"],
            activebackground=THEME["primary_hover"],
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            command=self.action_apply_gaming_tweaks
        ).pack(side=tk.RIGHT)

    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # TAB 8: Battery Health & Power Optimization (Universal)
    # -------------------------------------------------------------
    def render_battery_page(self):
        # Clear existing container widgets to prevent duplicate split screen on refresh
        for widget in self.content_container.winfo_children():
            widget.destroy()

        self.render_section_header(
            "Battery Health & Power Optimization",
            "Universal laptop power preservation, CPU thermal capping, idle standby drain fixes, and battery diagnostics."
        )

        scroll_canvas, scroll_content = self.create_scrollable_container()

        telem = self.engine.get_battery_telemetry()
        has_battery = telem.get("has_battery", False)

        # ---------------------------------------------------------
        # Card 1: Real-Time Power & Battery Telemetry
        # ---------------------------------------------------------
        telem_card = ModernCard(scroll_content)
        telem_card.pack(fill=tk.X, pady=(0, 14))

        t_top = tk.Frame(telem_card, bg=THEME["bg_card"])
        t_top.pack(fill=tk.X, pady=(0, 10))

        if has_battery:
            pct = telem.get("percent", 0)
            pct_color = THEME["success"] if pct >= 60 else (THEME["warning"] if pct >= 25 else THEME["danger"])

            tk.Label(
                t_top,
                text=f"🔋 {pct}%",
                font=(FONT_FAMILY, 20, "bold"),
                fg=pct_color,
                bg=THEME["bg_card"]
            ).pack(side=tk.LEFT)

            if telem.get("ac_online", False):
                if telem.get("is_charging", False):
                    ac_badge_text = "⚡ CHARGING (AC CONNECTED)"
                    ac_badge_fg = THEME["success"]
                    ac_badge_bg = THEME["success_bg"]
                else:
                    ac_badge_text = "🔌 FULLY CHARGED (PLUGGED IN)"
                    ac_badge_fg = THEME["accent_cyan"]
                    ac_badge_bg = THEME["bg_card_alt"]
            else:
                ac_badge_text = "🔋 DISCHARGING ON BATTERY"
                ac_badge_fg = THEME["warning"]
                ac_badge_bg = THEME["warning_bg"]

            tk.Label(
                t_top,
                text=ac_badge_text,
                font=(FONT_FAMILY, 8, "bold"),
                fg=ac_badge_fg,
                bg=ac_badge_bg,
                padx=10,
                pady=4,
                relief="flat"
            ).pack(side=tk.RIGHT)

            meter_bg = tk.Frame(telem_card, bg=THEME["bg_input"], height=14)
            meter_bg.pack(fill=tk.X, pady=(0, 10))
            meter_bg.pack_propagate(False)

            fill_width_pct = max(0.02, min(1.0, pct / 100.0))
            meter_fill = tk.Frame(meter_bg, bg=pct_color)
            meter_fill.place(relx=0, rely=0, relwidth=fill_width_pct, relheight=1.0)
        else:
            tk.Label(
                t_top,
                text="🖥️ Direct AC Wall Current",
                font=(FONT_FAMILY, 16, "bold"),
                fg=THEME["accent_cyan"],
                bg=THEME["bg_card"]
            ).pack(side=tk.LEFT)

            tk.Label(
                t_top,
                text="🖥️ DESKTOP WORKSTATION",
                font=(FONT_FAMILY, 8, "bold"),
                fg=THEME["accent_cyan"],
                bg=THEME["bg_card_alt"],
                padx=10,
                pady=4,
                relief="flat"
            ).pack(side=tk.RIGHT)

        # Telemetry Details row
        details_frame = tk.Frame(telem_card, bg=THEME["bg_card"])
        details_frame.pack(fill=tk.X)

        tk.Label(
            details_frame,
            text=f"💻 {telem.get('model_name', 'Windows System')}",
            font=(FONT_FAMILY, 9),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT)

        tk.Label(
            details_frame,
            text=f"⚡ {telem.get('status_text', 'Active')}",
            font=(FONT_FAMILY, 8, "bold"),
            fg=THEME["accent_cyan"] if telem.get("ac_online") else THEME["warning"],
            bg=THEME["bg_card"]
        ).pack(side=tk.RIGHT)

        # ---------------------------------------------------------
        # Card 2: Universal Laptop Eco Power & Battery Lifespan Suite
        # ---------------------------------------------------------
        eco_card = ModernCard(scroll_content)
        eco_card.pack(fill=tk.X, pady=(0, 14))

        eco_top = tk.Frame(eco_card, bg=THEME["bg_card"])
        eco_top.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            eco_top,
            text="Universal Laptop Battery & Power Conservation Suite",
            font=(FONT_FAMILY, 11, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT)

        tk.Label(
            eco_top,
            text="⚡ UNIVERSAL COMPATIBILITY",
            font=(FONT_FAMILY, 8, "bold"),
            fg=THEME["success"],
            bg=THEME["success_bg"],
            padx=10,
            pady=3,
            relief="flat"
        ).pack(side=tk.RIGHT)

        tk.Label(
            eco_card,
            text="Native Windows kernel and hardware power policies to extend screen-on time, prevent idle standby discharge, and protect battery cell health on all Windows laptops.",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            justify="left",
            wraplength=640
        ).pack(anchor="w", pady=(0, 12))

        if not has_battery:
            desktop_box = tk.Frame(
                eco_card,
                bg=THEME["bg_input"],
                padx=14,
                pady=12,
                highlightbackground=THEME["border"],
                highlightthickness=1
            )
            desktop_box.pack(fill=tk.X, pady=(4, 10))

            tk.Label(
                desktop_box,
                text="🖥️ DESKTOP SYSTEM DETECTED",
                font=(FONT_FAMILY, 9, "bold"),
                fg=THEME["text_main"],
                bg=THEME["bg_input"],
                anchor="w"
            ).pack(fill=tk.X)

            tk.Label(
                desktop_box,
                text="Your system runs on continuous direct AC wall current via the Power Supply Unit (PSU). Portable battery conservation tweaks are not needed for desktop systems.",
                font=(FONT_FAMILY, 8),
                fg=THEME["text_muted"],
                bg=THEME["bg_input"],
                anchor="w",
                wraplength=640,
                justify="left"
            ).pack(fill=tk.X, pady=(4, 0))
        else:
            # Toggle 1: Processor Eco Boost Capping (DC)
            t1 = ToggleSwitch(
                eco_card,
                title="Processor Efficiency & Thermal Capping on Battery (DC)",
                description="Caps aggressive CPU boost to 85% on battery. Eliminates high heat, fan noise, and extends screen-on battery runtime by up to 25%.",
                default=telem.get("processor_eco_active", False),
                command=lambda s: self.action_toggle_processor_eco(s)
            )
            t1.pack(fill=tk.X, pady=(4, 8))

            # Toggle 2: PCIe Link State Power Management (ASPM)
            t2 = ToggleSwitch(
                eco_card,
                title="PCIe & Chipset Link State Power Management (ASPM)",
                description="Places idle NVMe SSD lanes, discrete GPU, and motherboard interconnects into low-power states to cut idle motherboard battery drain.",
                default=telem.get("pcie_aspm_active", False),
                command=lambda s: self.action_toggle_pcie_aspm(s)
            )
            t2.pack(fill=tk.X, pady=(4, 8))

            # Toggle 3: Disable Windows Fast Startup (Prevent Shutdown Battery Drain)
            fast_start_active = telem.get("fast_startup_enabled", True)
            t3 = ToggleSwitch(
                eco_card,
                title="Disable Windows Fast Startup (Stop Phantom Shutdown Drain)",
                description="Stops Windows from saving an active kernel hibernation state at shutdown, eliminating 3-5% overnight battery discharge while powered off.",
                default=not fast_start_active,
                command=lambda s: self.action_toggle_fast_startup(not s)
            )
            t3.pack(fill=tk.X, pady=(4, 8))

            # Toggle 4: Smart 80% / 20% Battery Health Audio & Toast Alarm
            t4 = ToggleSwitch(
                eco_card,
                title="Smart 80% / 20% Battery Health Alert Guard",
                description="Alerts you with an audio chime and notification when your battery reaches 80% while charging (to unplug and avoid cell wear) or drops below 20%.",
                default=getattr(self, "battery_alarm_enabled", False),
                command=lambda s: self.action_toggle_battery_alarm(s)
            )
            t4.pack(fill=tk.X, pady=(4, 4))

        # ---------------------------------------------------------
        # Card 3: Windows Battery Diagnostic & Wear Report
        # ---------------------------------------------------------
        diag_card = ModernCard(scroll_content)
        diag_card.pack(fill=tk.X, pady=(0, 14))

        diag_top = tk.Frame(diag_card, bg=THEME["bg_card"])
        diag_top.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            diag_top,
            text="Official Windows Battery Health & Wear Diagnostics",
            font=(FONT_FAMILY, 10, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT)

        tk.Label(
            diag_card,
            text="Generates Microsoft's in-depth hardware diagnostics report containing design capacity, full charge capacity,\nexact battery degradation wear percentage, and comprehensive historical charge cycles.",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            justify="left"
        ).pack(anchor="w", pady=(0, 12))

        btn_row = tk.Frame(diag_card, bg=THEME["bg_card"])
        btn_row.pack(fill=tk.X)

        tk.Button(
            btn_row,
            text="📊 GENERATE BATTERY WEAR REPORT",
            font=(FONT_FAMILY, 9, "bold"),
            fg=THEME["accent_cyan"],
            bg=THEME["bg_card_alt"],
            activebackground=THEME["border"],
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.action_generate_battery_report
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_row,
            text="🔄 Refresh Status",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            activebackground=THEME["bg_card_alt"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
            command=lambda: self.switch_tab("battery")
        ).pack(side=tk.RIGHT)

    # -------------------------------------------------------------
    # TAB 9: Disk & Cache Clean (Real BeardSweeper)
    # -------------------------------------------------------------
    def render_disk_cleaner(self):
        self.render_section_header(
            "Deep Disk & Cache Cleaner",
            "Scan and safely eradicate gigabytes of leftover temporary files, installer caches, and crash dumps."
        )

        ctrl_card = ModernCard(self.content_container)
        ctrl_card.pack(fill=tk.X, pady=(0, 12))

        self.cleaner_summary_lbl = tk.Label(
            ctrl_card,
            text="Click 'Scan Junk' to calculate exact reclaimable storage space.",
            font=(FONT_FAMILY, 9, "bold"),
            fg=THEME["accent_cyan"],
            bg=THEME["bg_card"]
        )
        self.cleaner_summary_lbl.pack(side=tk.LEFT)

        scan_btn = tk.Button(
            ctrl_card,
            text="🔍 SCAN JUNK FILES",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg=THEME["primary"],
            activebackground=THEME["primary_hover"],
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.action_scan_junk
        )
        scan_btn.pack(side=tk.RIGHT)

        scroll_canvas, scroll_content = self.create_scrollable_container()

        targets = self.engine.get_cleanup_targets()
        self.cleanup_checks.clear()
        self.cleanup_labels = {}

        for target in targets:
            card = ModernCard(scroll_content)
            card.pack(fill=tk.X, pady=(0, 6))

            var = tk.BooleanVar(value=True)
            self.cleanup_checks[target["id"]] = var

            top_row = tk.Frame(card, bg=THEME["bg_card"])
            top_row.pack(fill=tk.X)

            chk = tk.Checkbutton(
                top_row,
                text=target["name"],
                variable=var,
                font=(FONT_FAMILY, 9, "bold"),
                fg=THEME["text_main"],
                bg=THEME["bg_card"],
                selectcolor=THEME["bg_card_alt"],
                activebackground=THEME["bg_card"],
                activeforeground=THEME["text_main"],
                cursor="hand2"
            )
            chk.pack(side=tk.LEFT)

            size_lbl = tk.Label(
                top_row,
                text="Not scanned",
                font=(FONT_FAMILY, 9, "bold"),
                fg=THEME["text_muted"],
                bg=THEME["bg_card"]
            )
            size_lbl.pack(side=tk.RIGHT)
            self.cleanup_labels[target["id"]] = size_lbl

            tk.Label(
                card,
                text=f"{target['desc']}  ({target['path']})",
                font=(FONT_FAMILY, 8),
                fg=THEME["text_dim"],
                bg=THEME["bg_card"]
            ).pack(anchor="w", padx=24, pady=(2, 0))

        # Action Button
        btn_frame = tk.Frame(self.content_container, bg=THEME["bg_app"])
        btn_frame.pack(fill=tk.X, pady=(12, 0))

        tk.Button(
            btn_frame,
            text="CLEAN SELECTED ITEMS",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg=THEME["success"],
            activebackground=THEME["success_bg"],
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            command=self.action_execute_cleanup
        ).pack(side=tk.RIGHT)

    # -------------------------------------------------------------
    # TAB 9: Software Updater (WinGet)
    # -------------------------------------------------------------
    def render_software_updater(self):
        self.render_section_header(
            "Software & Package Manager (WinGet)",
            "Query and silently update all installed applications to their latest secure versions via Windows Package Manager."
        )

        card = ModernCard(self.content_container)
        card.pack(fill=tk.BOTH, expand=True)

        btn_row = tk.Frame(card, bg=THEME["bg_card"])
        btn_row.pack(fill=tk.X, pady=(0, 10))

        tk.Button(
            btn_row,
            text="🔍 Check for Updates",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg=THEME["primary"],
            activebackground=THEME["primary_hover"],
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.action_check_winget
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            btn_row,
            text="🚀 Upgrade All Apps",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg=THEME["success"],
            activebackground=THEME["success_bg"],
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.action_run_winget_upgrade
        ).pack(side=tk.LEFT)

        self.updater_text = tk.Text(
            card,
            bg=THEME["bg_input"],
            fg=THEME["text_main"],
            font=("Consolas", 9),
            relief="flat",
            wrap=tk.WORD,
            highlightbackground=THEME["border"],
            highlightthickness=1,
            padx=10,
            pady=10
        )
        self.updater_text.pack(fill=tk.BOTH, expand=True)
        self.updater_text.insert(tk.END, "Click 'Check for Updates' to query installed packages and available updates via WinGet...\n")

    # -------------------------------------------------------------
    # TAB 10: Live Activity Log Terminal
    # -------------------------------------------------------------
    def render_terminal_log(self):
        self.render_section_header(
            "Live Activity & Command Log",
            "Real-time stream of all system optimization actions, registry changes, and PowerShell results."
        )

        toolbar = ModernCard(self.content_container)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        tk.Button(
            toolbar,
            text="📋 Copy Log",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_main"],
            bg=THEME["bg_card_alt"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.action_copy_log
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            toolbar,
            text="💾 Save Log to File",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_main"],
            bg=THEME["bg_card_alt"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.action_save_log
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            toolbar,
            text="🗑️ Clear Terminal",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card_alt"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.action_clear_log
        ).pack(side=tk.LEFT)

        term_frame = tk.Frame(self.content_container, bg=THEME["bg_input"])
        term_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(term_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.terminal_text = tk.Text(
            term_frame,
            bg=THEME["bg_input"],
            fg=THEME["text_main"],
            font=("Consolas", 9),
            relief="flat",
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            highlightbackground=THEME["border"],
            highlightthickness=1,
            padx=12,
            pady=12
        )
        self.terminal_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.terminal_text.yview)

        self.terminal_text.tag_config("TIME", foreground=THEME["text_dim"])
        self.terminal_text.tag_config("INFO", foreground=THEME["accent_cyan"])
        self.terminal_text.tag_config("SUCCESS", foreground=THEME["success"])
        self.terminal_text.tag_config("WARNING", foreground=THEME["warning"])
        self.terminal_text.tag_config("ERROR", foreground=THEME["danger"])
        self.terminal_text.tag_config("MSG", foreground=THEME["text_main"])

        if os.path.exists(self.engine.session_log_path):
            try:
                with open(self.engine.session_log_path, "r", encoding="utf-8") as f:
                    for line in f.readlines():
                        line = line.strip()
                        if line:
                            parts = line.split(" ", 2)
                            if len(parts) >= 3 and parts[1].startswith("[") and parts[1].endswith("]"):
                                lvl = parts[1][1:-1]
                                self.terminal_text.insert(tk.END, f"{parts[0]} ", "TIME")
                                self.terminal_text.insert(tk.END, f"{parts[1]} ", lvl)
                                self.terminal_text.insert(tk.END, f"{parts[2]}\n", "MSG")
                            else:
                                self.terminal_text.insert(tk.END, f"{line}\n", "MSG")
            except Exception:
                pass

    # -------------------------------------------------------------
    # TAB 12: Developer Profile & About (Rajkumar Patil)
    # -------------------------------------------------------------
    def render_developer_page(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()

        self.render_section_header(
            "Developer Profile & About",
            "Software architecture, project credentials, and developer connections."
        )

        scroll_canvas, scroll_content = self.create_scrollable_container()

        # ---------------------------------------------------------
        # Card 1: Lead Developer Profile Card
        # ---------------------------------------------------------
        profile_card = ModernCard(scroll_content)
        profile_card.pack(fill=tk.X, pady=(0, 16))

        top_row = tk.Frame(profile_card, bg=THEME["bg_card"])
        top_row.pack(fill=tk.X, pady=(0, 12))

        # Avatar Badge Frame
        avatar_frame = tk.Frame(top_row, bg=THEME["primary"], width=54, height=54)
        avatar_frame.pack(side=tk.LEFT, padx=(0, 16))
        avatar_frame.pack_propagate(False)

        tk.Label(
            avatar_frame,
            text="RP",
            font=(FONT_FAMILY, 16, "bold"),
            fg="#FFFFFF",
            bg=THEME["primary"]
        ).pack(expand=True)

        name_box = tk.Frame(top_row, bg=THEME["bg_card"])
        name_box.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            name_box,
            text="Rajkumar Patil",
            font=(FONT_FAMILY, 16, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(anchor="w")

        tk.Label(
            name_box,
            text="Creator & Lead Developer • Apex Windows Optimizer",
            font=(FONT_FAMILY, 9),
            fg=THEME["accent_cyan"],
            bg=THEME["bg_card"]
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            top_row,
            text="⭐ VERIFIED AUTHOR",
            font=(FONT_FAMILY, 8, "bold"),
            fg=THEME["success"],
            bg=THEME["success_bg"],
            padx=10,
            pady=4,
            relief="flat"
        ).pack(side=tk.RIGHT)

        bio_text = (
            "Apex Windows Optimizer was engineered by Rajkumar Patil to deliver a modern, transparent, and completely\n"
            "safe optimization suite for Windows systems. Built from the ground up featuring live registry state inspection,\n"
            "multi-user profile deployment, automated rollback snapshotting, hardware AC power bypass, and zero bloat."
        )
        tk.Label(
            profile_card,
            text=bio_text,
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            justify="left",
            wraplength=640
        ).pack(anchor="w", pady=(0, 14))

        # ---------------------------------------------------------
        # Card 2: Social & Professional Connect Cards (Grid)
        # ---------------------------------------------------------
        social_grid = tk.Frame(scroll_content, bg=THEME["bg_app"])
        social_grid.pack(fill=tk.X, pady=(0, 16))

        # GitHub Card
        github_card = ModernCard(social_grid)
        github_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        gh_header = tk.Frame(github_card, bg=THEME["bg_card"])
        gh_header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            gh_header,
            text="🐙 GitHub Profile",
            font=(FONT_FAMILY, 11, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT)

        tk.Label(
            gh_header,
            text="@Rajkumsr",
            font=(FONT_FAMILY, 8, "bold"),
            fg=THEME["text_muted"],
            bg=THEME["bg_card_alt"],
            padx=8,
            pady=2
        ).pack(side=tk.RIGHT)

        tk.Label(
            github_card,
            text="Explore source code repositories, open-source utilities, and latest projects by Rajkumar Patil.",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            wraplength=280,
            justify="left"
        ).pack(anchor="w", pady=(0, 14))

        tk.Button(
            github_card,
            text="🌐 Open GitHub (github.com/Rajkumsr)",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg="#24292E",
            activebackground="#2F363D",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
            command=lambda: webbrowser.open_new_tab("https://github.com/Rajkumsr")
        ).pack(anchor="w")

        # LinkedIn Card
        linkedin_card = ModernCard(social_grid)
        linkedin_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        li_header = tk.Frame(linkedin_card, bg=THEME["bg_card"])
        li_header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            li_header,
            text="💼 LinkedIn Network",
            font=(FONT_FAMILY, 11, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT)

        tk.Label(
            li_header,
            text="Professional",
            font=(FONT_FAMILY, 8, "bold"),
            fg="#60A5FA",
            bg="#1E3A8A",
            padx=8,
            pady=2
        ).pack(side=tk.RIGHT)

        tk.Label(
            linkedin_card,
            text="Connect professionally with Rajkumar Patil, follow technical updates, and collaborate on software development.",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            wraplength=280,
            justify="left"
        ).pack(anchor="w", pady=(0, 14))

        tk.Button(
            linkedin_card,
            text="🔗 Connect on LinkedIn",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#FFFFFF",
            bg="#0A66C2",
            activebackground="#004182",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
            command=lambda: webbrowser.open_new_tab("https://www.linkedin.com/in/rajkumar-patil-2b13a5180")
        ).pack(anchor="w")

        # ---------------------------------------------------------
        # Card 3: Software Specifications & Credits
        # ---------------------------------------------------------
        info_card = ModernCard(scroll_content)
        info_card.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            info_card,
            text="Software Specifications & Architecture",
            font=(FONT_FAMILY, 11, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(anchor="w", pady=(0, 10))

        specs = [
            ("Application Version", "Apex Windows Optimizer PRO v2.0"),
            ("Lead Developer", "Rajkumar Patil"),
            ("GitHub Repository", "https://github.com/Rajkumsr"),
            ("LinkedIn Profile", "https://www.linkedin.com/in/rajkumar-patil-2b13a5180"),
            ("Runtime Architecture", "64-bit Native Windows (Python 3.13 / Tkinter GUI)"),
            ("Display Scaling", "Per-Monitor v2 High-DPI Awareness (Crisp 4K Rendering)"),
            ("Power Management", "Kernel32 Zero-Overhead Telemetry & Windows Powercfg Eco Tuning"),
            ("Deployment Scope", "Multi-User Default Hive Deployment (HKU\\APEX_DEFAULT)")
        ]

        for label, val in specs:
            row = tk.Frame(info_card, bg=THEME["bg_card"])
            row.pack(fill=tk.X, pady=3)
            tk.Label(
                row,
                text=label,
                font=(FONT_FAMILY, 8, "bold"),
                fg=THEME["text_muted"],
                bg=THEME["bg_card"],
                width=24,
                anchor="w"
            ).pack(side=tk.LEFT)
            tk.Label(
                row,
                text=val,
                font=(FONT_FAMILY, 8),
                fg=THEME["text_main"],
                bg=THEME["bg_card"],
                anchor="w"
            ).pack(side=tk.LEFT)

        # Footer Heart Note
        footer_frame = tk.Frame(scroll_content, bg=THEME["bg_app"])
        footer_frame.pack(fill=tk.X, pady=(10, 20))

        tk.Label(
            footer_frame,
            text="Crafted with ❤️ by Rajkumar Patil • Apex Windows Optimizer",
            font=(FONT_FAMILY, 9),
            fg=THEME["text_dim"],
            bg=THEME["bg_app"]
        ).pack(anchor="center")

    # -------------------------------------------------------------
    # UI Helper Functions
    # -------------------------------------------------------------
    def render_section_header(self, title: str, subtitle: str):
        title_frame = tk.Frame(self.content_container, bg=THEME["bg_app"])
        title_frame.pack(fill=tk.X, pady=(0, 14))

        tk.Label(
            title_frame,
            text=title,
            font=(FONT_FAMILY, 14, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_app"]
        ).pack(anchor="w")

        tk.Label(
            title_frame,
            text=subtitle,
            font=(FONT_FAMILY, 9),
            fg=THEME["text_muted"],
            bg=THEME["bg_app"]
        ).pack(anchor="w", pady=(2, 0))

    def create_scrollable_container(self) -> Tuple[tk.Canvas, tk.Frame]:
        container = tk.Frame(self.content_container, bg=THEME["bg_app"])
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, bg=THEME["bg_app"], highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=THEME["bg_app"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scoped mousewheel binding
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        def _bind_wheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_wheel(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)

        return canvas, scrollable_frame

    # -------------------------------------------------------------
    # Async Execution Actions
    # -------------------------------------------------------------
    def run_quick_optimize(self):
        def worker():
            self.set_status("Applying One-Click Optimization...", is_busy=True)
            self.engine.log("=== Initiating One-Click Quick Optimization ===", "INFO")
            
            # Step 1: Safety Snapshot
            self.engine.create_restore_point("Apex Quick Optimize Snapshot")

            # Step 2: System tweaks
            sys_opts = {k: True for k in ["network_throttling", "system_responsiveness", "fast_shutdown", "long_paths", "block_oem_bloat", "disable_p2p_update"]}
            self.engine.apply_system_performance_tweaks(sys_opts)

            # Step 3: Privacy tweaks
            priv_opts = {k: True for k in ["disable_telemetry", "disable_lockscreen_ads", "disable_recall", "optimize_edge", "suppress_oobe_telemetry"]}
            self.engine.apply_privacy_telemetry_tweaks(priv_opts)

            # Step 4: Explorer tweaks
            exp_opts = {k: True for k in ["show_extensions", "open_this_pc", "classic_context_menu", "disable_start_bing", "taskbar_end_task", "clean_taskbar", "fast_menu_delay", "disable_sticky_keys"]}
            self.engine.apply_explorer_ui_tweaks(exp_opts, deploy_to_all_profiles=True)

            # Step 5: Tasks
            self.engine.disable_telemetry_tasks()

            # Refresh live states
            self.live_states = self.engine.detect_all_tweak_states()

            self.engine.log("=== One-Click Quick Optimization Completed Successfully! ===", "SUCCESS")
            self.set_status("One-Click Optimization finished.", is_busy=False)
            messagebox.showinfo("Optimization Complete", "One-Click System Optimization completed successfully!\nA restart is recommended to apply all changes.")

        threading.Thread(target=worker, daemon=True).start()

    def action_apply_system_tweaks(self):
        opts = {k: v.get() for k, v in self.system_toggles.items()}
        def worker():
            self.set_status("Applying system changes...", is_busy=True)
            count = self.engine.apply_system_performance_tweaks(opts)
            self.live_states = self.engine.detect_all_tweak_states()
            self.set_status(f"System changes applied ({count} updated).", is_busy=False)
            messagebox.showinfo("Apex Optimizer", f"Successfully updated {count} system settings.")
        threading.Thread(target=worker, daemon=True).start()

    def action_apply_privacy_tweaks(self):
        opts = {k: v.get() for k, v in self.privacy_toggles.items()}
        def worker():
            self.set_status("Applying privacy changes...", is_busy=True)
            count = self.engine.apply_privacy_telemetry_tweaks(opts)
            self.engine.disable_telemetry_tasks()
            self.live_states = self.engine.detect_all_tweak_states()
            self.set_status(f"Privacy changes applied ({count} updated).", is_busy=False)
            messagebox.showinfo("Apex Optimizer", f"Successfully updated {count} privacy & telemetry policies.")
        threading.Thread(target=worker, daemon=True).start()

    def action_apply_explorer_tweaks(self):
        opts = {k: v.get() for k, v in self.explorer_toggles.items()}
        deploy_all = self.multi_user_deploy_var.get()
        def worker():
            self.set_status("Applying shell customizations...", is_busy=True)
            count = self.engine.apply_explorer_ui_tweaks(opts, deploy_to_all_profiles=deploy_all)
            self.live_states = self.engine.detect_all_tweak_states()
            self.set_status(f"Explorer changes applied ({count} updated).", is_busy=False)
            messagebox.showinfo("Apex Optimizer", f"Successfully applied {count} Explorer and UI customizations.")
        threading.Thread(target=worker, daemon=True).start()

    def action_apply_gaming_tweaks(self):
        opts = {k: v.get() for k, v in self.gaming_toggles.items()}
        def worker():
            self.set_status("Applying gaming optimizations...", is_busy=True)
            count = self.engine.apply_gaming_tweaks(opts)
            self.live_states = self.engine.detect_all_tweak_states()
            self.set_status(f"Gaming optimizations applied ({count} updated).", is_busy=False)
            messagebox.showinfo("Apex Optimizer", f"Applied {count} Gaming and GPU optimizations.")
        threading.Thread(target=worker, daemon=True).start()

    def action_toggle_processor_eco(self, target_state: bool):
        def worker():
            self.set_status("Configuring Processor Eco Capping...", is_busy=True)
            ok, msg = self.engine.toggle_processor_eco(target_state)
            self.set_status(msg, is_busy=False)
            self.root.after(0, lambda: self.switch_tab("battery"))
        threading.Thread(target=worker, daemon=True).start()

    def action_toggle_pcie_aspm(self, target_state: bool):
        def worker():
            self.set_status("Configuring PCIe Power Management...", is_busy=True)
            ok, msg = self.engine.toggle_pcie_aspm(target_state)
            self.set_status(msg, is_busy=False)
            self.root.after(0, lambda: self.switch_tab("battery"))
        threading.Thread(target=worker, daemon=True).start()

    def action_toggle_battery_alarm(self, target_state: bool):
        self.battery_alarm_enabled = target_state
        state_str = "Enabled (80% / 20% Alerts Active)" if target_state else "Disabled"
        self.engine.log(f"Smart Battery Health Alert Guard: {state_str}.", "SUCCESS")
        self.set_status(f"Battery Health Alarm: {state_str}.", is_busy=False)

    def action_generate_battery_report(self):
        def worker():
            self.set_status("Generating official Windows battery diagnostics...", is_busy=True)
            ok, res = self.engine.generate_battery_report()
            self.set_status("Battery report generated.", is_busy=False)
            if not ok:
                messagebox.showerror("Battery Report Error", f"Failed to generate battery report: {res}")
        threading.Thread(target=worker, daemon=True).start()

    def action_toggle_fast_startup(self, enable: bool):
        def worker():
            self.set_status("Configuring Fast Startup...", is_busy=True)
            self.engine.set_fast_startup(enable)
            self.set_status("Fast Startup setting updated.", is_busy=False)
            self.root.after(0, lambda: self.switch_tab("battery"))
        threading.Thread(target=worker, daemon=True).start()

    def action_apply_services(self):
        selected = [(svc, var.get()) for svc, var in self.service_selections.items()]
        def worker():
            self.set_status("Configuring service startup modes...", is_busy=True)
            count = self.engine.optimize_services(selected)
            self.set_status(f"Services configured ({count} updated).", is_busy=False)
            messagebox.showinfo("Apex Optimizer", f"Successfully updated {count} Windows service startup modes.")
        threading.Thread(target=worker, daemon=True).start()

    def action_remove_bloatware(self):
        patterns = [pattern for pattern, var in self.debloat_checks.items() if var.get()]
        if not patterns:
            messagebox.showwarning("Apex Optimizer", "No apps selected for removal.")
            return

        if not messagebox.askyesno("Confirm Debloat", f"Are you sure you want to uninstall and unprovision {len(patterns)} selected app(s)?"):
            return

        def worker():
            self.set_status("Debloating packages...", is_busy=True)
            count = self.engine.remove_appx_packages(patterns)
            self.set_status(f"Debloat complete ({count} removed).", is_busy=False)
            messagebox.showinfo("Apex Optimizer", f"Completed removal of selected bloatware packages ({count} removed).")
        threading.Thread(target=worker, daemon=True).start()

    def action_scan_junk(self):
        def worker():
            self.set_status("Scanning junk files...", is_busy=True)
            self.cleaner_summary_lbl.config(text="Scanning file systems and caches...")
            sizes = self.engine.scan_cleanup_sizes()
            total_bytes = sum(b for b, _ in sizes.values())
            self.cleanup_sizes = sizes

            for cid, (b, s_str) in sizes.items():
                if cid in self.cleanup_labels:
                    color = THEME["success"] if b == 0 else THEME["warning"]
                    self.cleanup_labels[cid].config(text=s_str, fg=color)

            summary = f"Scan Complete! Found {self.engine.format_bytes(total_bytes)} of reclaimable junk files."
            self.cleaner_summary_lbl.config(text=summary)
            self.set_status(summary, is_busy=False)
        threading.Thread(target=worker, daemon=True).start()

    def action_execute_cleanup(self):
        selected_ids = [cid for cid, var in self.cleanup_checks.items() if var.get()]
        if not selected_ids:
            messagebox.showwarning("Apex Optimizer", "No categories selected for cleanup.")
            return

        def worker():
            self.set_status("Cleaning selected junk files...", is_busy=True)
            freed, s_str = self.engine.execute_cleanup(selected_ids)
            self.set_status(f"Clean complete! Reclaimed {s_str}.", is_busy=False)
            messagebox.showinfo("Apex Optimizer", f"Deep Clean complete!\nSuccessfully freed: {s_str}")
            self.action_scan_junk()
        threading.Thread(target=worker, daemon=True).start()

    def action_check_winget(self):
        def worker():
            self.set_status("Querying WinGet for app updates...", is_busy=True)
            ok, out = self.engine.check_winget_updates()
            self.updater_text.delete("1.0", tk.END)
            self.updater_text.insert(tk.END, out + "\n")
            self.set_status("WinGet query finished.", is_busy=False)
        threading.Thread(target=worker, daemon=True).start()

    def action_run_winget_upgrade(self):
        def worker():
            self.set_status("Upgrading packages via WinGet...", is_busy=True)
            self.updater_text.insert(tk.END, "\n[Apex] Starting WinGet upgrade all...\n")
            c, out = self.engine.run_winget_upgrade_all()
            self.updater_text.insert(tk.END, out + "\n")
            self.set_status(f"WinGet upgrade completed (code {c}).", is_busy=False)
            messagebox.showinfo("WinGet Updater", "Application upgrade cycle completed.")
        threading.Thread(target=worker, daemon=True).start()

    def action_create_restore_point(self):
        def worker():
            self.set_status("Creating System Restore Point...", is_busy=True)
            res = self.engine.create_restore_point("Apex Manual Restore Point")
            self.set_status("Restore point process finished.", is_busy=False)
            if res:
                messagebox.showinfo("Restore Protection", "System Restore Point created successfully.")
            else:
                messagebox.showwarning("Restore Protection", "Restore point creation could not be completed. Check activity log.")
        threading.Thread(target=worker, daemon=True).start()

    def action_export_reg(self):
        def worker():
            self.set_status("Exporting registry backup...", is_busy=True)
            res = self.engine.export_registry_backup()
            self.set_status("Registry export finished.", is_busy=False)
            if res:
                messagebox.showinfo("Registry Backup", "Registry hives HKLM and HKCU exported successfully.")
        threading.Thread(target=worker, daemon=True).start()

    def quick_flush_dns(self):
        def worker():
            self.set_status("Flushing DNS cache...", is_busy=True)
            self.engine.flush_dns()
            self.set_status("DNS cache flushed.", is_busy=False)
        threading.Thread(target=worker, daemon=True).start()

    def quick_restart_explorer(self):
        def worker():
            self.set_status("Restarting Explorer shell...", is_busy=True)
            self.engine.restart_explorer()
            self.set_status("Explorer shell restarted.", is_busy=False)
        threading.Thread(target=worker, daemon=True).start()

    def action_quick_boost(self):
        def worker():
            self.set_status("Executing 1-Click Instant System Boost...", is_busy=True)
            ok, summary = self.engine.quick_boost()
            self.set_status("1-Click Boost completed successfully.", is_busy=False)
            if self.active_tab == "dashboard":
                self.root.after(0, lambda: self.switch_tab("dashboard"))
            if hasattr(self, 'tray_manager') and self.tray_manager:
                self.tray_manager.notify("1-Click Boost complete! Memory freed and temp caches wiped.", "Apex Windows Optimizer")
            messagebox.showinfo("1-Click Instant System Boost", summary)
        threading.Thread(target=worker, daemon=True).start()

    def action_flush_ram_only(self):
        def worker():
            self.set_status("Purging RAM Standby list and process working sets...", is_busy=True)
            ok, count, freed_mb = self.engine.flush_ram_working_sets()
            self.set_status(f"Flushed {count} processes, freed {freed_mb:.1f} MB RAM.", is_busy=False)
            if self.active_tab == "dashboard":
                self.root.after(0, lambda: self.switch_tab("dashboard"))
            messagebox.showinfo("RAM Working Set Purge", f"Successfully flushed working sets for {count} active processes.\n\nReclaimed: {freed_mb:.1f} MB of RAM.")
        threading.Thread(target=worker, daemon=True).start()

    def on_window_close(self):
        """Intercepts window close: minimizes to system tray instead of abrupt termination."""
        if hasattr(self, "tray_manager") and self.tray_manager and self.tray_manager.is_active():
            self.minimize_to_tray(show_toast=True)
        else:
            self.quit_completely()

    def minimize_to_tray(self, show_toast: bool = False):
        self.root.withdraw()
        if show_toast and hasattr(self, "tray_manager") and self.tray_manager:
            self.tray_manager.notify(
                "Apex Windows Optimizer is running minimized in your system tray. Right-click or double-click to reopen.",
                "Apex Windows Optimizer Pro"
            )

    def restore_from_tray(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit_completely(self):
        if hasattr(self, "tray_manager") and self.tray_manager:
            self.tray_manager.stop()
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def action_copy_log(self):
        content = self.terminal_text.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Apex Optimizer", "Activity log copied to clipboard.")

    def action_save_log(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"ApexOptimizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        if file_path:
            content = self.terminal_text.get("1.0", tk.END)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Apex Optimizer", f"Log saved to: {file_path}")

    def action_clear_log(self):
        self.terminal_text.delete("1.0", tk.END)


def main():
    # If launched directly without admin rights, request UAC elevation automatically
    if sys.platform == "win32" and not ctypes.windll.shell32.IsUserAnAdmin() and "--no-elevate" not in sys.argv:
        try:
            script = os.path.abspath(__file__)
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
            if ret > 32:
                sys.exit(0)
        except Exception:
            pass

    root = tk.Tk()
    app = ApexOptimizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
