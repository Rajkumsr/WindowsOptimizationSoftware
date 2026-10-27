"""
Apex Windows Optimizer - Battery Health & Power Management View
Modular renderer and action handlers for real-time battery telemetry,
cell degradation diagnostics, hardware specifications, and Windows power schemes.
"""

import threading
import tkinter as tk
from tkinter import messagebox
from ui.theme import THEME, FONT_FAMILY
from ui.components import ModernCard, ToggleSwitch
from ui.views.common import render_section_header, create_scrollable_container


def render_battery_page(app, refresh_specs: bool = False):
    """Renders the Battery Health & Power Management tab."""
    # Clear existing container widgets to prevent duplicate split screen on refresh
    for widget in app.content_container.winfo_children():
        widget.destroy()

    render_section_header(
        app,
        "Battery Health & Power Management",
        "Real-time battery telemetry, cell degradation diagnostics, hardware specifications, and Windows power schemes."
    )

    scroll_canvas, scroll_content = create_scrollable_container(app)

    telem = app.engine.get_battery_telemetry(refresh_specs=refresh_specs)
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
            font=(FONT_FAMILY, 22, "bold"),
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
        meter_bg.pack(fill=tk.X, pady=(0, 12))
        meter_bg.pack_propagate(False)

        fill_width_pct = max(0.02, min(1.0, pct / 100.0))
        meter_fill = tk.Frame(meter_bg, bg=pct_color)
        meter_fill.place(relx=0, rely=0, relwidth=fill_width_pct, relheight=1.0)

        # Telemetry Pill Grid
        pills_row = tk.Frame(telem_card, bg=THEME["bg_card"])
        pills_row.pack(fill=tk.X, pady=(0, 4))

        pills_data = [
            ("Power Source", "⚡ AC Wall Power" if telem.get("ac_online") else "🔋 DC Battery Power", THEME["accent_cyan"] if telem.get("ac_online") else THEME["warning"]),
            ("Estimated Runtime", telem.get("remaining_time_str", "Calculating..."), THEME["text_main"]),
            ("Rate / Power Draw", telem.get("rate_text", "Direct AC"), THEME["success"] if "+" in telem.get("rate_text", "") else (THEME["warning"] if "-" in telem.get("rate_text", "") else THEME["text_muted"])),
            ("Battery Voltage", f"{telem.get('voltage_v', 0.0):.2f} V" if telem.get('voltage_v', 0) > 0 else "N/A", THEME["text_main"]),
            ("Battery Saver", "Active (Power Saving)" if telem.get("battery_saver_active") else "Disabled (Standard)", THEME["success"] if telem.get("battery_saver_active") else THEME["text_muted"])
        ]

        for i, (label, val, val_color) in enumerate(pills_data):
            pill = tk.Frame(pills_row, bg=THEME["bg_input"], padx=10, pady=8, highlightbackground=THEME["border"], highlightthickness=1)
            pill.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 6, 0))
            tk.Label(pill, text=label.upper(), font=(FONT_FAMILY, 7, "bold"), fg=THEME["text_dim"], bg=THEME["bg_input"]).pack(anchor="w")
            tk.Label(pill, text=val, font=(FONT_FAMILY, 9, "bold"), fg=val_color, bg=THEME["bg_input"]).pack(anchor="w", pady=(2, 0))
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

        tk.Label(
            telem_card,
            text="Desktop PC detected. This system draws direct wall current from the Power Supply Unit (PSU) with no chemical battery cell.",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        ).pack(anchor="w", pady=(4, 0))

    # ---------------------------------------------------------
    # Card 2: Battery Health & Cell Degradation Diagnostics
    # ---------------------------------------------------------
    if has_battery:
        health_card = ModernCard(scroll_content)
        health_card.pack(fill=tk.X, pady=(0, 14))

        h_top = tk.Frame(health_card, bg=THEME["bg_card"])
        h_top.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            h_top,
            text="🛡️ Battery Health & Hardware Specifications",
            font=(FONT_FAMILY, 11, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT)

        health_pct = telem.get("health_percent", 100.0)
        wear_pct = telem.get("wear_percent", 0.0)
        h_color = THEME["success"] if health_pct >= 80 else (THEME["warning"] if health_pct >= 60 else THEME["danger"])
        h_bg = THEME["success_bg"] if health_pct >= 80 else (THEME["warning_bg"] if health_pct >= 60 else THEME["bg_card_alt"])

        tk.Label(
            h_top,
            text=f"HEALTH: {health_pct}%  •  WEAR: {wear_pct}%",
            font=(FONT_FAMILY, 8, "bold"),
            fg=h_color,
            bg=h_bg,
            padx=10,
            pady=3,
            relief="flat"
        ).pack(side=tk.RIGHT)

        # Health visualization bar (Full Capacity vs Design Capacity)
        h_meter_bg = tk.Frame(health_card, bg=THEME["bg_input"], height=10)
        h_meter_bg.pack(fill=tk.X, pady=(0, 12))
        h_meter_bg.pack_propagate(False)

        h_fill_pct = max(0.02, min(1.0, health_pct / 100.0))
        h_meter_fill = tk.Frame(h_meter_bg, bg=h_color)
        h_meter_fill.place(relx=0, rely=0, relwidth=h_fill_pct, relheight=1.0)

        # 6-Item Hardware Specs Grid
        spec_grid = tk.Frame(health_card, bg=THEME["bg_card"])
        spec_grid.pack(fill=tk.X)

        des_cap = telem.get("design_capacity", 0)
        full_cap = telem.get("full_capacity", 0)
        cur_cap = telem.get("current_capacity", 0)
        cycles = telem.get("cycle_count", 0)
        chem = telem.get("chemistry", "Lithium-Ion")
        mfg = telem.get("manufacturer", "OEM")
        serial = telem.get("serial_number", "N/A")

        specs_list = [
            ("Full Charge Capacity", f"{full_cap:,} mWh" if full_cap > 0 else "N/A"),
            ("Factory Design Capacity", f"{des_cap:,} mWh" if des_cap > 0 else "N/A"),
            ("Current Charge Level", f"{cur_cap:,} mWh" if cur_cap > 0 else "N/A"),
            ("Charge Cycles", f"{cycles} Cycles" if cycles > 0 else "N/A (BMS direct)"),
            ("Battery Chemistry", chem),
            ("Manufacturer & Serial", f"{mfg} ({serial})")
        ]

        row1 = tk.Frame(spec_grid, bg=THEME["bg_card"])
        row1.pack(fill=tk.X, pady=(0, 6))
        for i, (label, val) in enumerate(specs_list[:3]):
            box = tk.Frame(row1, bg=THEME["bg_input"], padx=10, pady=8, highlightbackground=THEME["border"], highlightthickness=1)
            box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 6, 0))
            tk.Label(box, text=label.upper(), font=(FONT_FAMILY, 7, "bold"), fg=THEME["text_dim"], bg=THEME["bg_input"]).pack(anchor="w")
            tk.Label(box, text=val, font=(FONT_FAMILY, 9, "bold"), fg=THEME["text_main"], bg=THEME["bg_input"]).pack(anchor="w", pady=(2, 0))

        row2 = tk.Frame(spec_grid, bg=THEME["bg_card"])
        row2.pack(fill=tk.X)
        for i, (label, val) in enumerate(specs_list[3:]):
            box = tk.Frame(row2, bg=THEME["bg_input"], padx=10, pady=8, highlightbackground=THEME["border"], highlightthickness=1)
            box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 6, 0))
            tk.Label(box, text=label.upper(), font=(FONT_FAMILY, 7, "bold"), fg=THEME["text_dim"], bg=THEME["bg_input"]).pack(anchor="w")
            tk.Label(box, text=val, font=(FONT_FAMILY, 9, "bold"), fg=THEME["text_main"], bg=THEME["bg_input"]).pack(anchor="w", pady=(2, 0))

    # ---------------------------------------------------------
    # Card 3: Active Windows Power Plan & Scheme Selector
    # ---------------------------------------------------------
    scheme_info = telem.get("power_scheme", app.engine.get_power_schemes())
    active_plan_name = scheme_info.get("active_name", "Balanced")
    active_plan_guid = scheme_info.get("active_guid", "")
    is_ryzen = scheme_info.get("is_ryzen", False)

    plan_card = ModernCard(scroll_content)
    plan_card.pack(fill=tk.X, pady=(0, 14))

    plan_top = tk.Frame(plan_card, bg=THEME["bg_card"])
    plan_top.pack(fill=tk.X, pady=(0, 6))

    tk.Label(
        plan_top,
        text="⚡  Active Windows Power Plan",
        font=(FONT_FAMILY, 11, "bold"),
        fg=THEME["text_main"],
        bg=THEME["bg_card"]
    ).pack(side=tk.LEFT)

    if is_ryzen:
        plan_tag_text = "🔥 AMD RYZEN™ CPPC TUNED (1ms Clock Response)"
        plan_tag_fg = "#FFFFFF"
        plan_tag_bg = "#D9381E"
    elif "ultimate" in active_plan_name.lower():
        plan_tag_text = "🚀 ULTIMATE PERFORMANCE"
        plan_tag_fg = THEME["primary"]
        plan_tag_bg = THEME["bg_card_alt"]
    elif "high" in active_plan_name.lower():
        plan_tag_text = "⚡ HIGH PERFORMANCE"
        plan_tag_fg = THEME["warning"]
        plan_tag_bg = THEME["warning_bg"]
    else:
        plan_tag_text = "⚖️ BALANCED (Default Windows Power Allocation)"
        plan_tag_fg = THEME["success"]
        plan_tag_bg = THEME["success_bg"]

    tk.Label(
        plan_top,
        text=plan_tag_text,
        font=(FONT_FAMILY, 8, "bold"),
        fg=plan_tag_fg,
        bg=plan_tag_bg,
        padx=10,
        pady=3,
        relief="flat"
    ).pack(side=tk.RIGHT)

    plan_content_row = tk.Frame(plan_card, bg=THEME["bg_card"])
    plan_content_row.pack(fill=tk.X, pady=(4, 8))

    # Main active plan display
    plan_display = tk.Frame(plan_content_row, bg=THEME["bg_input"], padx=14, pady=10, highlightbackground=THEME["border"], highlightthickness=1)
    plan_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    tk.Label(
        plan_display,
        text=active_plan_name,
        font=(FONT_FAMILY, 12, "bold"),
        fg=THEME["text_main"],
        bg=THEME["bg_input"]
    ).pack(anchor="w")

    tk.Label(
        plan_display,
        text=f"GUID: {active_plan_guid}",
        font=(FONT_FAMILY, 7),
        fg=THEME["text_dim"],
        bg=THEME["bg_input"]
    ).pack(anchor="w", pady=(2, 0))

    # Quick Scheme Switcher Buttons (if multiple schemes installed)
    all_schemes = scheme_info.get("all_schemes", [])
    if len(all_schemes) > 1:
        switch_box = tk.Frame(plan_content_row, bg=THEME["bg_card"])
        switch_box.pack(side=tk.RIGHT)

        tk.Label(
            switch_box,
            text="SWITCH PLAN:",
            font=(FONT_FAMILY, 7, "bold"),
            fg=THEME["text_dim"],
            bg=THEME["bg_card"]
        ).pack(anchor="w", pady=(0, 4))

        btn_row = tk.Frame(switch_box, bg=THEME["bg_card"])
        btn_row.pack(fill=tk.X)

        for s in all_schemes:
            s_name = s["name"]
            s_guid = s["guid"]
            s_active = s["is_active"]

            btn_title = s_name.replace("AMD Ryzen™ ", "Ryzen ")
            btn_bg = THEME["primary"] if s_active else THEME["bg_card_alt"]
            btn_fg = "#FFFFFF" if s_active else THEME["text_muted"]

            def make_switch_handler(target_guid=s_guid, target_name=s_name):
                def handler():
                    def worker():
                        app.set_status(f"Activating {target_name}...", is_busy=True)
                        ok, msg = app.engine.set_active_power_scheme(target_guid)
                        app.set_status(f"{target_name} active.", is_busy=False)
                        app.root.after(0, lambda: app.show_toast("Power Scheme Switched", f"Active plan is now: {target_name}", "success"))
                        app.root.after(0, lambda: render_battery_page(app))
                    threading.Thread(target=worker, daemon=True).start()
                return handler

            b = tk.Button(
                btn_row,
                text=f"{'● ' if s_active else ''}{btn_title}",
                font=(FONT_FAMILY, 8, "bold" if s_active else "normal"),
                fg=btn_fg,
                bg=btn_bg,
                activebackground=THEME["primary_hover"],
                activeforeground="#FFFFFF",
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=4,
                command=make_switch_handler()
            )
            b.pack(side=tk.LEFT, padx=(0, 6))

    expl_text = (
        "💡 Plan Relationship: Windows & vendor driver profiles manage core frequency scaling for this plan. "
        "Power conservation policies configure CPU efficiency capping, PCIe ASPM link states, and shutdown hibernation "
        "in the System & Speed section."
    )
    tk.Label(
        plan_card,
        text=expl_text,
        font=(FONT_FAMILY, 8),
        fg=THEME["text_muted"],
        bg=THEME["bg_card"],
        justify="left",
        wraplength=760
    ).pack(anchor="w", pady=(2, 0))

    # ---------------------------------------------------------
    # Card 4: Battery Protection & Official Diagnostic Tools
    # ---------------------------------------------------------
    if has_battery:
        guard_card = ModernCard(scroll_content)
        guard_card.pack(fill=tk.X, pady=(0, 14))

        guard_top = tk.Frame(guard_card, bg=THEME["bg_card"])
        guard_top.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            guard_top,
            text="Smart Battery Health Guard & Cell Protection",
            font=(FONT_FAMILY, 10, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT)

        t_guard = ToggleSwitch(
            guard_card,
            title="Smart 80% / 20% Battery Health Alert Guard",
            description="Alerts you with an audio chime and notification when your battery reaches 80% while charging (to unplug and avoid cell wear) or drops below 20%.",
            default=getattr(app, "battery_alarm_enabled", False),
            command=lambda s: action_toggle_battery_alarm(app, s)
        )
        t_guard.pack(fill=tk.X, pady=(4, 4))

    # Card 5: Official Windows Battery Diagnostic & Wear Report
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
        command=lambda: action_generate_battery_report(app)
    ).pack(side=tk.LEFT)

    tk.Button(
        btn_row,
        text="🔄 Refresh Battery Telemetry",
        font=(FONT_FAMILY, 8),
        fg=THEME["text_muted"],
        bg=THEME["bg_card"],
        activebackground=THEME["bg_card_alt"],
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=6,
        command=lambda: render_battery_page(app, refresh_specs=True)
    ).pack(side=tk.RIGHT)


def action_toggle_processor_eco(app, target_state: bool):
    """Toggles processor maximum power capping on battery."""
    def worker():
        app.set_status("Configuring Processor Eco Capping...", is_busy=True)
        ok, msg = app.engine.toggle_processor_eco(target_state)
        app.set_status(msg, is_busy=False)
        app.root.after(0, lambda: app.switch_tab("battery"))
    threading.Thread(target=worker, daemon=True).start()


def action_toggle_pcie_aspm(app, target_state: bool):
    """Toggles PCIe Active State Power Management."""
    def worker():
        app.set_status("Configuring PCIe Power Management...", is_busy=True)
        ok, msg = app.engine.toggle_pcie_aspm(target_state)
        app.set_status(msg, is_busy=False)
        app.root.after(0, lambda: app.switch_tab("battery"))
    threading.Thread(target=worker, daemon=True).start()


def action_toggle_battery_alarm(app, target_state: bool):
    """Enables or disables smart 80/20 battery alarms."""
    app.battery_alarm_enabled = target_state
    state_str = "Enabled (80% / 20% Alerts Active)" if target_state else "Disabled"
    app.engine.log(f"Smart Battery Health Alert Guard: {state_str}.", "SUCCESS")
    app.set_status(f"Battery Health Alarm: {state_str}.", is_busy=False)


def action_generate_battery_report(app):
    """Invokes powercfg to generate an official HTML battery diagnostics report."""
    def worker():
        app.set_status("Generating official Windows battery diagnostics...", is_busy=True)
        ok, res = app.engine.generate_battery_report()
        app.set_status("Battery report generated." if ok else "Battery report generation failed.", is_busy=False)
        if not ok:
            app.root.after(0, lambda: messagebox.showerror("Battery Report Error", f"Failed to generate battery report: {res}"))
    threading.Thread(target=worker, daemon=True).start()


def action_toggle_fast_startup(app, enable: bool):
    """Toggles Windows Fast Startup kernel hibernation at shutdown."""
    def worker():
        app.set_status("Configuring Fast Startup...", is_busy=True)
        app.engine.set_fast_startup(enable)
        app.set_status("Fast Startup setting updated.", is_busy=False)
        app.root.after(0, lambda: app.switch_tab("battery"))
    threading.Thread(target=worker, daemon=True).start()
