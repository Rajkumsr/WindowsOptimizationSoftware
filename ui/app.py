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
- Fully Modular Views Architecture
"""

import os
import sys
import threading
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable
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
        app_id = "rajkumarpatil.apexwindowsoptimizer.pro.suite"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

# Ensure workspace root is in sys.path for direct execution
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

# Modular subsystem imports
import core.optimizer as core_optimizer
try:
    from ui.theme import THEME, FONT_FAMILY
    from ui.search_data import ALL_SEARCHABLE_TWEAKS
    from ui.components import (
        ToastManager,
        DonutGauge,
        ModernCard,
        ToggleSwitch,
        TweakTile,
        get_app_icon_path,
    )
    from ui.tray import ApexTrayManager
    import ui.views as views
except ImportError:
    from .theme import THEME, FONT_FAMILY
    from .search_data import ALL_SEARCHABLE_TWEAKS
    from .components import (
        ToastManager,
        DonutGauge,
        ModernCard,
        ToggleSwitch,
        TweakTile,
        get_app_icon_path,
    )
    from .tray import ApexTrayManager
    from . import views


class ApexOptimizerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Apex Windows Optimizer")
        self.root.geometry("1160x780")
        self.root.minsize(1020, 680)
        self.root.configure(bg=THEME["bg_app"])

        # Set Window and Taskbar Icon
        try:
            valid_icon = get_app_icon_path()
            if valid_icon:
                self.root.iconbitmap(default=valid_icon)
                if sys.platform == "win32":
                    try:
                        self.root.update_idletasks()
                        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
                        IMAGE_ICON = 1
                        LR_LOADFROMFILE = 0x00000010
                        WM_SETICON = 0x0080
                        h_icon_big = ctypes.windll.user32.LoadImageW(None, valid_icon, IMAGE_ICON, 48, 48, LR_LOADFROMFILE)
                        h_icon_small = ctypes.windll.user32.LoadImageW(None, valid_icon, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
                        if h_icon_big:
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 1, h_icon_big)
                        if h_icon_small:
                            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 0, h_icon_small)
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

        # Floating Toast Notification System
        self.toast = ToastManager(self.root)

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

        # Global Search Bar in Header
        search_frame = tk.Frame(header, bg=THEME["bg_input"], highlightbackground=THEME["border"], highlightthickness=1)
        search_frame.pack(side=tk.LEFT, padx=(24, 0), pady=4)

        tk.Label(
            search_frame,
            text="🔍",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_input"]
        ).pack(side=tk.LEFT, padx=(8, 4))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=(FONT_FAMILY, 9),
            fg=THEME["text_dim"],
            bg=THEME["bg_input"],
            insertbackground=THEME["primary"],
            relief="flat",
            width=25
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, 6), pady=4)
        self.search_entry.insert(0, "Search tweaks... (Ctrl+F)")
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<KeyRelease>", self._on_search_key_release)
        self.search_entry.bind("<Escape>", lambda e: self.clear_search())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus_set())

        self.search_clear_btn = tk.Label(
            search_frame,
            text="✕",
            font=(FONT_FAMILY, 8, "bold"),
            fg=THEME["text_dim"],
            bg=THEME["bg_input"],
            cursor="hand2"
        )
        self.search_clear_btn.bind("<Button-1>", lambda e: self.clear_search())

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

    def show_toast(self, title: str, message: str, toast_type: str = "success", duration_ms: int = 3500):
        """Displays a non-blocking in-app floating toast notification."""
        self.toast.show(title, message, toast_type, duration_ms)

    def _on_search_focus_in(self, event=None):
        if self.search_entry.get() == "Search tweaks... (Ctrl+F)":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=THEME["text_main"])
            self.search_clear_btn.pack(side=tk.RIGHT, padx=(0, 6))

    def _on_search_focus_out(self, event=None):
        if not self.search_entry.get().strip():
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, "Search tweaks... (Ctrl+F)")
            self.search_entry.config(fg=THEME["text_dim"])
            self.search_clear_btn.pack_forget()

    def _on_search_key_release(self, event=None):
        q = self.search_var.get().strip().lower()
        if q == "search tweaks... (ctrl+f)":
            q = ""
        if q:
            self.search_clear_btn.pack(side=tk.RIGHT, padx=(0, 6))
            self.render_search_results(q)
        else:
            self.search_clear_btn.pack_forget()
            if self.active_tab == "search":
                self.switch_tab("dashboard")

    def clear_search(self):
        self.search_var.set("")
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, "Search tweaks... (Ctrl+F)")
        self.search_entry.config(fg=THEME["text_dim"])
        self.search_clear_btn.pack_forget()
        self.root.focus_set()
        if self.active_tab == "search":
            self.switch_tab("dashboard")

    def render_search_results(self, query: str):
        views.render_search_results(self, query)

    # -------------------------------------------------------------
    # 2. Body: Sidebar + Main Content Frame
    # -------------------------------------------------------------
    def build_body(self):
        self.body_frame = tk.Frame(self.root, bg=THEME["bg_app"])
        self.body_frame.pack(fill=tk.BOTH, expand=True)

        # Left Sidebar Navigation Rail
        self.sidebar = tk.Frame(self.body_frame, bg=THEME["bg_sidebar"], width=230, padx=12, pady=12)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        nav_sections = [
            ("OVERVIEW", [
                ("dashboard", "📊 Dashboard")
            ]),
            ("OPTIMIZATIONS", [
                ("system", "⚡ System & Speed"),
                ("privacy", "🛡️ Privacy & Telemetry"),
                ("explorer", "🎨 Explorer & Shell"),
                ("gaming", "🎮 Gaming & GPU Boost"),
                ("battery", "🔋 Battery & Power")
            ]),
            ("SYSTEM TOOLS", [
                ("services", "⚙️ Services Optimizer"),
                ("debloat", "🗑️ App Debloater"),
                ("cleaner", "🧹 Disk & Cache Clean"),
                ("updater", "📦 Software Updater")
            ]),
            ("ACTIVITY & ABOUT", [
                ("terminal", "📝 Live Activity Log"),
                ("developer", "👨‍💻 Developer & About")
            ])
        ]

        for s_idx, (sec_title, items) in enumerate(nav_sections):
            tk.Label(
                self.sidebar,
                text=sec_title,
                font=(FONT_FAMILY, 7, "bold"),
                fg=THEME["text_dim"],
                bg=THEME["bg_sidebar"],
                anchor="w"
            ).pack(fill=tk.X, padx=8, pady=(8 if s_idx > 0 else 2, 2))

            for tab_id, label in items:
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
                    padx=10,
                    pady=4,
                    command=lambda tid=tab_id: self.switch_tab(tid)
                )
                btn.pack(fill=tk.X, pady=1)
                self.tab_buttons[tab_id] = btn

        # Persistent Sidebar Live Mini Telemetry Dock
        self.sidebar_dock = tk.Frame(
            self.sidebar,
            bg=THEME["bg_card"],
            padx=10,
            pady=8,
            highlightbackground=THEME["border"],
            highlightthickness=1
        )
        self.sidebar_dock.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 6))

        dock_top = tk.Frame(self.sidebar_dock, bg=THEME["bg_card"])
        dock_top.pack(fill=tk.X)
        tk.Label(
            dock_top,
            text="LIVE SYSTEM MONITOR",
            font=(FONT_FAMILY, 7, "bold"),
            fg=THEME["primary_light"],
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT)
        self.sidebar_dock_pulse = tk.Label(
            dock_top,
            text="● ACTIVE",
            font=(FONT_FAMILY, 7, "bold"),
            fg=THEME["success"],
            bg=THEME["bg_card"]
        )
        self.sidebar_dock_pulse.pack(side=tk.RIGHT)

        self.sidebar_ram_lbl = tk.Label(
            self.sidebar_dock,
            text="RAM: Initializing...",
            font=(FONT_FAMILY, 7),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        )
        self.sidebar_ram_lbl.pack(anchor="w", pady=(3, 1))

        self.sidebar_ram_bar = ttk.Progressbar(
            self.sidebar_dock,
            mode="determinate",
            length=180,
            style="TProgressbar"
        )
        self.sidebar_ram_bar.pack(fill=tk.X, pady=(0, 2))

        self.sidebar_sub_lbl = tk.Label(
            self.sidebar_dock,
            text="CPU: Calculating...",
            font=(FONT_FAMILY, 7),
            fg=THEME["text_dim"],
            bg=THEME["bg_card"]
        )
        self.sidebar_sub_lbl.pack(anchor="w")

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
            # 1. Update Persistent Sidebar Live Mini Telemetry Dock (Fast & Cached)
            try:
                if hasattr(self, 'sidebar_ram_lbl') and self.sidebar_ram_lbl.winfo_exists():
                    hw = self.engine.get_hardware_info()
                    tot_ram = hw.get("total_ram", "16 GB")
                    free_ram = hw.get("free_ram", "8 GB")
                    ram_pct_str = hw.get("ram_percent", "50%").replace("%", "").strip()
                    try:
                        ram_val = float(ram_pct_str)
                    except Exception:
                        ram_val = 50.0
                    cpu_val = hw.get("cpu_percent", 0.0)
                    self.sidebar_ram_lbl.config(text=f"RAM: {free_ram} Free of {tot_ram} ({ram_val:.0f}%)")
                    self.sidebar_ram_bar['value'] = ram_val
                    self.sidebar_sub_lbl.config(text=f"CPU: {cpu_val:.0f}% Load • Drive: {hw.get('system_drive', 'C:')}")
            except Exception:
                pass

            # 2. Update Dashboard Widgets if active
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
    # Modular View Renderers (Delegated to ui.views)
    # -------------------------------------------------------------
    def render_dashboard(self):
        views.render_dashboard(self)

    def render_system_tweaks(self):
        views.render_system_tweaks(self)

    def render_privacy_tweaks(self):
        views.render_privacy_tweaks(self)

    def render_explorer_tweaks(self):
        views.render_explorer_tweaks(self)

    def render_services_optimizer(self):
        views.render_services_optimizer(self)

    def render_debloater(self):
        views.render_debloater(self)

    def render_gaming_boost(self, refresh_gpu: bool = False):
        views.render_gaming_boost(self, refresh_gpu=refresh_gpu)

    def render_battery_page(self, refresh_specs: bool = False):
        views.render_battery_page(self, refresh_specs=refresh_specs)

    def render_disk_cleaner(self):
        views.render_disk_cleaner(self)

    def render_software_updater(self):
        views.render_software_updater(self)

    def render_terminal_log(self):
        views.render_terminal_log(self)

    def render_developer_page(self):
        views.render_developer_page(self)

    # -------------------------------------------------------------
    # View Helper Delegation (For backward compatibility)
    # -------------------------------------------------------------
    def render_section_hero(self, title: str, subtitle: str, tweak_keys: List[str], toggle_dict: Dict, on_apply: Callable, icon: str = "⚡") -> Callable:
        return views.render_section_hero(self, title, subtitle, tweak_keys, toggle_dict, on_apply, icon)

    def render_section_header(self, title: str, subtitle: str):
        views.render_section_header(self, title, subtitle)

    def create_scrollable_container(self) -> Tuple[tk.Canvas, tk.Frame]:
        return views.create_scrollable_container(self)

    # -------------------------------------------------------------
    # Modular Actions & Presets Delegation
    # -------------------------------------------------------------
    def run_quick_optimize(self):
        views.run_quick_optimize(self)

    def action_apply_system_tweaks(self):
        views.action_apply_system_tweaks(self)

    def action_apply_privacy_tweaks(self):
        views.action_apply_privacy_tweaks(self)

    def action_apply_explorer_tweaks(self):
        views.action_apply_explorer_tweaks(self)

    def action_apply_gaming_tweaks(self):
        views.action_apply_gaming_tweaks(self)

    def action_toggle_processor_eco(self, target_state: bool):
        views.action_toggle_processor_eco(self, target_state)

    def action_toggle_pcie_aspm(self, target_state: bool):
        views.action_toggle_pcie_aspm(self, target_state)

    def action_toggle_battery_alarm(self, target_state: bool):
        views.action_toggle_battery_alarm(self, target_state)

    def action_generate_battery_report(self):
        views.action_generate_battery_report(self)

    def action_toggle_fast_startup(self, enable: bool):
        views.action_toggle_fast_startup(self, enable)

    def preset_services_recommended(self):
        views.preset_services_recommended(self)

    def preset_services_gaming(self):
        views.preset_services_gaming(self)

    def preset_services_reset(self):
        views.preset_services_reset(self)

    def action_apply_services(self):
        views.action_apply_services(self)

    def action_remove_bloatware(self):
        views.action_remove_bloatware(self)

    def action_scan_junk(self):
        views.action_scan_junk(self)

    def action_execute_cleanup(self):
        views.action_execute_cleanup(self)

    def action_check_winget(self):
        views.action_check_winget(self)

    def action_run_winget_upgrade(self):
        views.action_run_winget_upgrade(self)

    def apply_gaming_preset(self):
        views.apply_gaming_preset(self)

    def apply_battery_preset(self):
        views.apply_battery_preset(self)

    def apply_privacy_preset(self):
        views.apply_privacy_preset(self)

    def apply_defaults_preset(self):
        views.apply_defaults_preset(self)

    def action_create_restore_point(self):
        views.action_create_restore_point(self)

    def action_export_reg(self):
        views.action_export_reg(self)

    def quick_flush_dns(self):
        views.quick_flush_dns(self)

    def quick_restart_explorer(self):
        views.quick_restart_explorer(self)

    def action_quick_boost(self):
        views.action_quick_boost(self)

    def action_flush_ram_only(self):
        views.action_flush_ram_only(self)

    def action_copy_log(self):
        views.action_copy_log(self)

    def action_save_log(self):
        views.action_save_log(self)

    def action_clear_log(self):
        views.action_clear_log(self)

    # -------------------------------------------------------------
    # Application & Tray Lifecycle Management
    # -------------------------------------------------------------
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
