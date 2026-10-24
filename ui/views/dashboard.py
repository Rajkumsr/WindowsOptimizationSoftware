"""
Apex Windows Optimizer - Dashboard View
Contains the main system health diagnostics, live DonutGauge, 1-click preset profiles,
instant system boost, and quick maintenance tools.
"""

import threading
import tkinter as tk
from ui.theme import THEME, FONT_FAMILY
from ui.components import ModernCard, DonutGauge


def render_dashboard(app):
    """Renders the main system health overview and 1-click optimization cards."""
    title_frame = tk.Frame(app.content_container, bg=THEME["bg_app"])
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
    grid_frame = tk.Frame(app.content_container, bg=THEME["bg_app"])
    grid_frame.pack(fill=tk.X, pady=(0, 16))

    # 1. System Health Donut Gauge Card
    score_info = app.engine.calculate_health_score(app.live_states)
    c1 = ModernCard(grid_frame)
    c1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

    c1_top = tk.Frame(c1, bg=THEME["bg_card"])
    c1_top.pack(fill=tk.X)
    tk.Label(c1_top, text="🛡️  System Health", font=(FONT_FAMILY, 8, "bold"), fg=THEME["primary_light"], bg=THEME["bg_card"]).pack(side=tk.LEFT)
    tk.Label(c1_top, text="Win Accent", font=(FONT_FAMILY, 7, "bold"), fg=THEME["primary"], bg=THEME["bg_card"]).pack(side=tk.RIGHT)

    gauge_row = tk.Frame(c1, bg=THEME["bg_card"])
    gauge_row.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    app.dash_gauge = DonutGauge(gauge_row, size=78, thickness=7)
    app.dash_gauge.pack(side=tk.LEFT, padx=(0, 8))
    app.dash_gauge.set_score(score_info["score"], score_info["rating"], score_info["color"], animate=True)

    g_info = tk.Frame(gauge_row, bg=THEME["bg_card"])
    g_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    app.dash_score_lbl = tk.Label(g_info, text=f"{score_info['score']}%", font=(FONT_FAMILY, 14, "bold"), fg=score_info["color"], bg=THEME["bg_card"])
    app.dash_score_lbl.pack(anchor="w")
    app.dash_rating_lbl = tk.Label(g_info, text=score_info["rating"], font=(FONT_FAMILY, 7, "bold"), fg=score_info["color"], bg=THEME["bg_card"])
    app.dash_rating_lbl.pack(anchor="w")
    app.dash_tweaks_lbl = tk.Label(g_info, text=f"{score_info['applied_count']}/{score_info['total_count']} Active", font=(FONT_FAMILY, 8), fg=THEME["text_muted"], bg=THEME["bg_card"])
    app.dash_tweaks_lbl.pack(anchor="w", pady=(2, 0))

    # 2. CPU Card (Live Load)
    c2 = ModernCard(grid_frame)
    c2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
    tk.Label(c2, text="⚡  Processor (CPU)", font=(FONT_FAMILY, 8, "bold"), fg=THEME["accent_cyan"], bg=THEME["bg_card"]).pack(anchor="w")
    app.dash_cpu_lbl = tk.Label(c2, text=f"{app.hw_info.get('cpu_percent', 0):.0f}% Load", font=(FONT_FAMILY, 13, "bold"), fg=THEME["text_main"], bg=THEME["bg_card"])
    app.dash_cpu_lbl.pack(anchor="w", pady=(2, 0))
    tk.Label(c2, text=app.hw_info["cpu_name"], font=(FONT_FAMILY, 8), fg=THEME["text_muted"], bg=THEME["bg_card"], wraplength=170, justify="left").pack(anchor="w", pady=(2, 0))

    # 3. RAM Card (Live)
    c3 = ModernCard(grid_frame)
    c3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
    tk.Label(c3, text="🧠  Physical Memory (Live)", font=(FONT_FAMILY, 8, "bold"), fg=THEME["success"], bg=THEME["bg_card"]).pack(anchor="w")
    app.ram_val_lbl = tk.Label(c3, text=f"{app.hw_info['free_ram']} Free of {app.hw_info['total_ram']}", font=(FONT_FAMILY, 11, "bold"), fg=THEME["text_main"], bg=THEME["bg_card"], wraplength=170, justify="left")
    app.ram_val_lbl.pack(anchor="w", pady=(4, 0))
    tk.Label(c3, text=f"{app.hw_info['ram_percent']} Utilized", font=(FONT_FAMILY, 8), fg=THEME["text_muted"], bg=THEME["bg_card"]).pack(anchor="w", pady=(2, 0))

    # 4. Uptime & Chassis Card
    c4 = ModernCard(grid_frame)
    c4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tk.Label(c4, text="⏱️  System Uptime & Drive", font=(FONT_FAMILY, 8, "bold"), fg=THEME["warning"], bg=THEME["bg_card"]).pack(anchor="w")
    app.dash_uptime_lbl = tk.Label(c4, text=f"Uptime: {app.hw_info.get('uptime', 'Active')}", font=(FONT_FAMILY, 11, "bold"), fg=THEME["text_main"], bg=THEME["bg_card"])
    app.dash_uptime_lbl.pack(anchor="w", pady=(4, 0))
    tk.Label(c4, text=f"{app.hw_info['system_drive']} ({app.hw_info['drive_type']}) • {app.hw_info['chassis_type']}", font=(FONT_FAMILY, 8), fg=THEME["text_muted"], bg=THEME["bg_card"], wraplength=170, justify="left").pack(anchor="w", pady=(2, 0))

    # 1-Click Scenario Preset Profiles Card
    presets_card = ModernCard(app.content_container)
    presets_card.pack(fill=tk.X, pady=(0, 16))

    p_top = tk.Frame(presets_card, bg=THEME["bg_card"])
    p_top.pack(fill=tk.X, pady=(0, 8))
    tk.Label(
        p_top,
        text="🎛️  1-Click Scenario Preset Profiles",
        font=(FONT_FAMILY, 11, "bold"),
        fg=THEME["text_main"],
        bg=THEME["bg_card"]
    ).pack(side=tk.LEFT)
    tk.Label(
        p_top,
        text="Instant preset configurations tailored for your specific task",
        font=(FONT_FAMILY, 8),
        fg=THEME["text_muted"],
        bg=THEME["bg_card"]
    ).pack(side=tk.LEFT, padx=(10, 0))

    p_row = tk.Frame(presets_card, bg=THEME["bg_card"])
    p_row.pack(fill=tk.X)

    presets = [
        ("🎮 Gaming & FPS Mode", "Low latency & GPU priority", lambda: apply_gaming_preset(app)),
        ("🔋 Battery Saver Mode", "Max runtime on DC & PCIe ASPM", lambda: apply_battery_preset(app)),
        ("🛡️ Maximum Privacy", "Zero telemetry & tracking", lambda: apply_privacy_preset(app)),
        ("🔄 Windows Defaults", "Restore stock settings", lambda: apply_defaults_preset(app))
    ]

    for title, subtitle, cmd in presets:
        btn_frame = tk.Frame(p_row, bg=THEME["bg_card_alt"], highlightbackground=THEME["border"], highlightthickness=1, padx=10, pady=8)
        btn_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        b = tk.Button(
            btn_frame,
            text=title,
            font=(FONT_FAMILY, 9, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card_alt"],
            activebackground=THEME["border"],
            relief="flat",
            cursor="hand2",
            command=cmd
        )
        b.pack(anchor="w")

        tk.Label(
            btn_frame,
            text=subtitle,
            font=(FONT_FAMILY, 7),
            fg=THEME["text_muted"],
            bg=THEME["bg_card_alt"]
        ).pack(anchor="w")

    # Hero Card: 1-Click Instant System Boost & Quick Optimize
    hero_card = ModernCard(app.content_container)
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
        command=lambda: action_quick_boost(app)
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
        command=lambda: run_quick_optimize(app)
    )
    opt_btn.pack(fill=tk.X)

    # Quick System Tools & Rollback Card
    action_card = ModernCard(app.content_container)
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
        ("🛡️ Create System Restore Point", app.action_create_restore_point),
        ("🧠 Purge Standby RAM", lambda: action_flush_ram_only(app)),
        ("📁 Export Registry Backup", app.action_export_reg),
        ("🌐 Flush DNS Cache", app.quick_flush_dns),
        ("🔄 Restart Explorer Shell", app.quick_restart_explorer)
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


def run_quick_optimize(app):
    def worker():
        app.set_status("Applying One-Click Optimization...", is_busy=True)
        app.engine.log("=== Initiating One-Click Quick Optimization ===", "INFO")
        
        # Step 1: Safety Snapshot
        app.engine.create_restore_point("Apex Quick Optimize Snapshot")

        # Step 2: System tweaks
        sys_opts = {k: True for k in ["network_throttling", "system_responsiveness", "fast_shutdown", "long_paths", "block_oem_bloat", "disable_p2p_update"]}
        app.engine.apply_system_performance_tweaks(sys_opts)

        # Step 3: Privacy tweaks
        priv_opts = {k: True for k in ["disable_telemetry", "disable_lockscreen_ads", "disable_recall", "optimize_edge", "suppress_oobe_telemetry"]}
        app.engine.apply_privacy_telemetry_tweaks(priv_opts)

        # Step 4: Explorer tweaks
        exp_opts = {k: True for k in ["show_extensions", "open_this_pc", "classic_context_menu", "disable_start_bing", "taskbar_end_task", "clean_taskbar", "fast_menu_delay", "disable_sticky_keys"]}
        app.engine.apply_explorer_ui_tweaks(exp_opts, deploy_to_all_profiles=True)

        # Step 5: Tasks
        app.engine.disable_telemetry_tasks()

        # Refresh live states
        app.live_states = app.engine.detect_all_tweak_states()

        app.engine.log("=== One-Click Quick Optimization Completed Successfully! ===", "SUCCESS")
        app.set_status("One-Click Optimization finished.", is_busy=False)
        app.root.after(0, lambda: app.show_toast("Quick Optimization Complete", "Applied core performance, privacy, and shell tweaks. Ready to fly!", "boost"))

    threading.Thread(target=worker, daemon=True).start()


def apply_gaming_preset(app):
    """1-Click Scenario Preset: Gaming & FPS Mode."""
    def worker():
        app.set_status("Applying 1-Click Gaming & FPS Mode Preset...", is_busy=True)
        app.engine.apply_system_performance_tweaks({
            "network_throttling": True,
            "system_responsiveness": True,
            "fast_shutdown": True
        })
        app.engine.apply_gaming_tweaks({
            "hags": True,
            "windowed_optimizations": True,
            "game_mmcss": True,
            "power_throttling": True,
            "ultimate_performance": True
        })
        app.engine.apply_privacy_telemetry_tweaks({"disable_telemetry": True})
        app.live_states = app.engine.detect_all_tweak_states()
        app.set_status("Gaming & FPS Mode Preset successfully applied.", is_busy=False)
        if app.active_tab == "dashboard":
            app.root.after(0, lambda: app.switch_tab("dashboard"))
        app.root.after(0, lambda: app.show_toast(
            "Gaming & FPS Preset Applied",
            "Enabled Hardware GPU Scheduling (HAGS), MMCSS audio/network priority, and Ultimate Performance plan.",
            "boost"
        ))
    threading.Thread(target=worker, daemon=True).start()


def apply_battery_preset(app):
    """1-Click Scenario Preset: Battery Saver Mode."""
    def worker():
        app.set_status("Applying 1-Click Battery Saver Preset...", is_busy=True)
        app.engine.toggle_processor_eco(True)
        app.engine.toggle_pcie_aspm(True)
        app.engine.set_fast_startup(False)
        app.engine.apply_privacy_telemetry_tweaks({
            "disable_telemetry": True,
            "optimize_edge": True
        })
        app.engine.disable_telemetry_tasks()
        app.live_states = app.engine.detect_all_tweak_states()
        app.set_status("Battery Saver Preset successfully applied.", is_busy=False)
        if app.active_tab == "dashboard":
            app.root.after(0, lambda: app.switch_tab("dashboard"))
        app.root.after(0, lambda: app.show_toast(
            "Battery Saver Preset Applied",
            "Capped CPU turbo boost to 85% on DC, activated PCIe ASPM power savings, and prevented hybrid battery drain.",
            "success"
        ))
    threading.Thread(target=worker, daemon=True).start()


def apply_privacy_preset(app):
    """1-Click Scenario Preset: Maximum Privacy."""
    def worker():
        app.set_status("Applying 1-Click Maximum Privacy Preset...", is_busy=True)
        privacy_opts = {
            "disable_telemetry": True,
            "disable_lockscreen_ads": True,
            "disable_recall": True,
            "optimize_edge": True,
            "suppress_oobe_telemetry": True,
            "disable_office_telemetry": True
        }
        app.engine.apply_privacy_telemetry_tweaks(privacy_opts)
        app.engine.disable_telemetry_tasks()
        app.engine.apply_system_performance_tweaks({"disable_p2p_update": True})
        app.engine.apply_explorer_ui_tweaks({"disable_bing_search": True})
        app.live_states = app.engine.detect_all_tweak_states()
        app.set_status("Maximum Privacy Preset successfully applied.", is_busy=False)
        if app.active_tab == "dashboard":
            app.root.after(0, lambda: app.switch_tab("dashboard"))
        app.root.after(0, lambda: app.show_toast(
            "Maximum Privacy Preset Applied",
            "Telemetry, Microsoft Recall AI tracking, Bing Start search, and background diagnostic tasks disabled.",
            "success"
        ))
    threading.Thread(target=worker, daemon=True).start()


def apply_defaults_preset(app):
    """1-Click Scenario Preset: Revert to Windows Stock Defaults."""
    def worker():
        app.set_status("Reverting to Windows Stock Defaults...", is_busy=True)
        app.engine.apply_system_performance_tweaks({
            "network_throttling": False,
            "system_responsiveness": False,
            "fast_shutdown": False,
            "irp_stack_size": False,
            "disable_p2p_update": False
        })
        app.engine.apply_gaming_tweaks({
            "power_throttling": False,
            "game_mmcss": False
        })
        app.engine.toggle_processor_eco(False)
        app.engine.toggle_pcie_aspm(False)
        app.live_states = app.engine.detect_all_tweak_states()
        app.set_status("Reverted to Windows stock defaults.", is_busy=False)
        if app.active_tab == "dashboard":
            app.root.after(0, lambda: app.switch_tab("dashboard"))
        app.root.after(0, lambda: app.show_toast(
            "Windows Defaults Restored",
            "Managed system, power, and gaming settings restored to default Windows stock configuration.",
            "info"
        ))
    threading.Thread(target=worker, daemon=True).start()


def action_quick_boost(app):
    def worker():
        app.set_status("Executing 1-Click Instant System Boost...", is_busy=True)
        ok, summary = app.engine.quick_boost()
        app.set_status("1-Click Boost completed successfully.", is_busy=False)
        if app.active_tab == "dashboard":
            app.root.after(0, lambda: app.switch_tab("dashboard"))
        if hasattr(app, 'tray_manager') and app.tray_manager:
            app.tray_manager.notify("1-Click Boost complete! Memory freed and temp caches wiped.", "Apex Windows Optimizer")
        app.root.after(0, lambda: app.show_toast("1-Click Boost Complete", "Freed standby RAM memory, wiped temp caches, and flushed DNS cache.", "boost"))
    threading.Thread(target=worker, daemon=True).start()


def action_flush_ram_only(app):
    def worker():
        app.set_status("Purging RAM Standby list and process working sets...", is_busy=True)
        ok, count, freed_mb = app.engine.flush_ram_working_sets()
        app.set_status(f"Flushed {count} processes, freed {freed_mb:.1f} MB RAM.", is_busy=False)
        if app.active_tab == "dashboard":
            app.root.after(0, lambda: app.switch_tab("dashboard"))
        app.root.after(0, lambda: app.show_toast("RAM Working Set Purge", f"Flushed working sets for {count} processes. Reclaimed {freed_mb:.1f} MB RAM.", "success"))
    threading.Thread(target=worker, daemon=True).start()
