"""
Apex Windows Optimizer - System Tools View
Modular renderers and action handlers for Services Optimizer, App Debloater,
Deep Disk & Cache Cleaner, and Software Updater (WinGet).
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from ui.theme import THEME, FONT_FAMILY
from ui.components import ModernCard
from ui.views.common import render_section_header, create_scrollable_container


# -------------------------------------------------------------
# 1. Services Optimizer
# -------------------------------------------------------------
def render_services_optimizer(app):
    """Renders the Services Optimizer tab with service catalog and presets."""
    render_section_header(
        app,
        "Windows Services Optimization",
        "Safely configure background services to reduce idle CPU and RAM footprint without breaking dependencies."
    )

    catalog = app.engine.get_services_catalog()
    scroll_canvas, scroll_content = create_scrollable_container(app)

    app.service_selections.clear()

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
        ("Recommended (Safe)", lambda: preset_services_recommended(app)),
        ("Maximum Gaming", lambda: preset_services_gaming(app)),
        ("Reset All to Demand", lambda: preset_services_reset(app))
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

        top_row = tk.Frame(info_f, bg=THEME["bg_card"])
        top_row.pack(anchor="w")

        chip_lbl = tk.Label(
            top_row,
            text=svc["category"].upper(),
            font=(FONT_FAMILY, 7, "bold"),
            fg=THEME["accent_cyan"],
            bg=THEME["bg_card_alt"],
            padx=6,
            pady=1
        )
        chip_lbl.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(
            top_row,
            text=f"{svc['display']} ({svc['name']})",
            font=(FONT_FAMILY, 9, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT)

        tk.Label(
            info_f,
            text=svc['desc'],
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            wraplength=580,
            justify="left"
        ).pack(anchor="w", pady=(3, 0))

        # Mode selector dropdown
        mode_var = tk.StringVar(value=svc["mode"])
        app.service_selections[svc["name"]] = mode_var

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
    btn_frame = tk.Frame(app.content_container, bg=THEME["bg_app"])
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
        command=lambda: action_apply_services(app)
    ).pack(side=tk.RIGHT)


def preset_services_recommended(app):
    """Applies recommended safe service states."""
    for svc, var in app.service_selections.items():
        if svc in ["DiagTrack", "dmwappushservice", "diagnosticshub.standardcollector.service", "RetailDemo", "RemoteRegistry"]:
            var.set("disabled")
        else:
            var.set("demand")


def preset_services_gaming(app):
    """Sets all catalog services to disabled for maximum game headroom."""
    for svc, var in app.service_selections.items():
        var.set("disabled")


def preset_services_reset(app):
    """Resets all catalog services to demand (Manual) startup."""
    for svc, var in app.service_selections.items():
        var.set("demand")


def action_apply_services(app):
    """Executes service configuration asynchronously."""
    selected = [(svc, var.get()) for svc, var in app.service_selections.items()]
    def worker():
        app.set_status("Configuring service startup modes...", is_busy=True)
        count = app.engine.optimize_services(selected)
        app.set_status(f"Services configured ({count} updated).", is_busy=False)
        app.root.after(0, lambda: app.show_toast("Services Configured", f"Successfully updated {count} Windows service startup modes.", "success"))
    threading.Thread(target=worker, daemon=True).start()


# -------------------------------------------------------------
# 2. App Debloater
# -------------------------------------------------------------
def render_debloater(app):
    """Renders the UWP bloatware cleaner tab with filtering and bulk actions."""
    render_section_header(
        app,
        "UWP & Windows Bloatware Cleaner",
        "Safely uninstall unwanted preinstalled Microsoft and third-party apps for all current and future accounts."
    )

    scroll_canvas, scroll_content = create_scrollable_container(app)

    targets = app.engine.get_debloat_targets()
    app.debloat_checks.clear()

    # Selection Control Row
    sel_card = ModernCard(scroll_content)
    sel_card.pack(fill=tk.X, pady=(0, 10))

    def select_by_ids(id_list):
        for t in targets:
            p = t["pattern"]
            if p in app.debloat_checks:
                app.debloat_checks[p].set(t["id"] in id_list)

    tk.Button(
        sel_card,
        text="✨ Select Recommended",
        font=(FONT_FAMILY, 8, "bold"),
        fg=THEME["accent_cyan"],
        bg=THEME["bg_card_alt"],
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=4,
        command=lambda: [var.set(True) for var in app.debloat_checks.values()]
    ).pack(side=tk.LEFT, padx=(0, 6))

    tk.Button(
        sel_card,
        text="🤖 AI & Web Feeds",
        font=(FONT_FAMILY, 8),
        fg=THEME["text_main"],
        bg=THEME["bg_card_alt"],
        relief="flat",
        cursor="hand2",
        padx=8,
        pady=4,
        command=lambda: select_by_ids(["copilot", "bing_search", "widgets", "web_exp", "cortana"])
    ).pack(side=tk.LEFT, padx=(0, 6))

    tk.Button(
        sel_card,
        text="🎮 Games & Ads",
        font=(FONT_FAMILY, 8),
        fg=THEME["text_main"],
        bg=THEME["bg_card_alt"],
        relief="flat",
        cursor="hand2",
        padx=8,
        pady=4,
        command=lambda: select_by_ids(["solitaire", "candy_crush", "bing_news", "bing_weather", "feedback_hub"])
    ).pack(side=tk.LEFT, padx=(0, 6))

    tk.Button(
        sel_card,
        text="Deselect All",
        font=(FONT_FAMILY, 8),
        fg=THEME["text_muted"],
        bg=THEME["bg_card_alt"],
        relief="flat",
        cursor="hand2",
        padx=8,
        pady=4,
        command=lambda: [var.set(False) for var in app.debloat_checks.values()]
    ).pack(side=tk.LEFT)

    for target in targets:
        card = ModernCard(scroll_content)
        card.pack(fill=tk.X, pady=(0, 6))

        var = tk.BooleanVar(value=True if target["id"] in ["copilot", "bing_search", "widgets", "web_exp", "bing_news", "solitaire"] else False)
        app.debloat_checks[target["pattern"]] = var

        top_row = tk.Frame(card, bg=THEME["bg_card"])
        top_row.pack(fill=tk.X)

        # Category detection for chip
        tid = target["id"]
        if tid in ["copilot", "bing_search", "widgets", "web_exp", "cortana"]:
            cat_tag = "AI & FEEDS"
        elif tid in ["solitaire", "candy_crush", "bing_news", "bing_weather"]:
            cat_tag = "PROMO & GAMES"
        else:
            cat_tag = "UTILITY"

        cat_chip = tk.Label(
            top_row,
            text=cat_tag,
            font=(FONT_FAMILY, 7, "bold"),
            fg=THEME["accent_cyan"],
            bg=THEME["bg_card_alt"],
            padx=6,
            pady=1
        )
        cat_chip.pack(side=tk.LEFT, padx=(0, 8))

        chk = tk.Checkbutton(
            top_row,
            text=f"{target['name']}",
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

        tk.Label(
            card,
            text=f"{target['desc']}  (Pattern: {target['pattern']})",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        ).pack(anchor="w", padx=24, pady=(2, 0))

    # Action Button
    btn_frame = tk.Frame(app.content_container, bg=THEME["bg_app"])
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
        command=lambda: action_remove_bloatware(app)
    ).pack(side=tk.RIGHT)


def action_remove_bloatware(app):
    """Executes removal of selected UWP bloatware packages."""
    patterns = [pattern for pattern, var in app.debloat_checks.items() if var.get()]
    if not patterns:
        messagebox.showwarning("Apex Optimizer", "No apps selected for removal.")
        return

    if not messagebox.askyesno("Confirm Debloat", f"Are you sure you want to uninstall and unprovision {len(patterns)} selected app(s)?"):
        return

    def worker():
        app.set_status("Debloating packages...", is_busy=True)
        count = app.engine.remove_appx_packages(patterns)
        app.set_status(f"Debloat complete ({count} removed).", is_busy=False)
        messagebox.showinfo("Apex Optimizer", f"Completed removal of selected bloatware packages ({count} removed).")
    threading.Thread(target=worker, daemon=True).start()


# -------------------------------------------------------------
# 3. Disk & Cache Cleaner
# -------------------------------------------------------------
def render_disk_cleaner(app):
    """Renders the Disk & Cache Clean tab with live scan sizing."""
    render_section_header(
        app,
        "Deep Disk & Cache Cleaner",
        "Scan and safely eradicate gigabytes of leftover temporary files, installer caches, and crash dumps."
    )

    ctrl_card = ModernCard(app.content_container, pady=12)
    ctrl_card.pack(fill=tk.X, pady=(0, 12))

    top_ctrl = tk.Frame(ctrl_card, bg=THEME["bg_card"])
    top_ctrl.pack(fill=tk.X)

    app.cleaner_summary_lbl = tk.Label(
        top_ctrl,
        text="Click 'Scan Junk' to calculate exact reclaimable storage space.",
        font=(FONT_FAMILY, 9, "bold"),
        fg=THEME["accent_cyan"],
        bg=THEME["bg_card"]
    )
    app.cleaner_summary_lbl.pack(side=tk.LEFT)

    btn_box = tk.Frame(top_ctrl, bg=THEME["bg_card"])
    btn_box.pack(side=tk.RIGHT)

    tk.Button(
        btn_box,
        text="Select All",
        font=(FONT_FAMILY, 8),
        fg=THEME["text_main"],
        bg=THEME["bg_card_alt"],
        relief="flat",
        cursor="hand2",
        padx=8,
        pady=4,
        command=lambda: [v.set(True) for v in app.cleanup_checks.values()]
    ).pack(side=tk.LEFT, padx=(0, 6))

    tk.Button(
        btn_box,
        text="Deselect All",
        font=(FONT_FAMILY, 8),
        fg=THEME["text_muted"],
        bg=THEME["bg_card_alt"],
        relief="flat",
        cursor="hand2",
        padx=8,
        pady=4,
        command=lambda: [v.set(False) for v in app.cleanup_checks.values()]
    ).pack(side=tk.LEFT, padx=(0, 8))

    scan_btn = tk.Button(
        btn_box,
        text="🔍 SCAN JUNK FILES",
        font=(FONT_FAMILY, 8, "bold"),
        fg="#FFFFFF",
        bg=THEME["primary"],
        activebackground=THEME["primary_hover"],
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=4,
        command=lambda: action_scan_junk(app)
    )
    scan_btn.pack(side=tk.LEFT)

    # Visual Storage Breakdown Bar
    app.storage_meter = ttk.Progressbar(ctrl_card, mode="determinate", length=600, style="TProgressbar")
    app.storage_meter.pack(fill=tk.X, pady=(10, 2))

    scroll_canvas, scroll_content = create_scrollable_container(app)

    targets = app.engine.get_cleanup_targets()
    app.cleanup_checks.clear()
    app.cleanup_labels = {}

    for target in targets:
        card = ModernCard(scroll_content)
        card.pack(fill=tk.X, pady=(0, 6))

        var = tk.BooleanVar(value=True)
        app.cleanup_checks[target["id"]] = var

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
        app.cleanup_labels[target["id"]] = size_lbl

        tk.Label(
            card,
            text=f"{target['desc']}  ({target['path']})",
            font=(FONT_FAMILY, 8),
            fg=THEME["text_dim"],
            bg=THEME["bg_card"]
        ).pack(anchor="w", padx=24, pady=(2, 0))

    # Action Button
    btn_frame = tk.Frame(app.content_container, bg=THEME["bg_app"])
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
        command=lambda: action_execute_cleanup(app)
    ).pack(side=tk.RIGHT)


def action_scan_junk(app):
    """Scans disk junk categories and updates sizes."""
    def worker():
        app.set_status("Scanning junk files...", is_busy=True)
        app.cleaner_summary_lbl.config(text="Scanning file systems and caches...")
        sizes = app.engine.scan_cleanup_sizes()
        total_bytes = sum(b for b, _ in sizes.values())
        app.cleanup_sizes = sizes

        for cid, (b, s_str) in sizes.items():
            if cid in app.cleanup_labels:
                color = THEME["success"] if b == 0 else THEME["warning"]
                app.cleanup_labels[cid].config(text=s_str, fg=color)

        summary = f"Scan Complete! Found {app.engine.format_bytes(total_bytes)} of reclaimable junk files."
        app.cleaner_summary_lbl.config(text=summary)
        if hasattr(app, 'storage_meter') and app.storage_meter.winfo_exists():
            total_mb = total_bytes / (1024 * 1024)
            pct = min(100, max(5, int((total_mb / 2000.0) * 100))) if total_mb > 0 else 0
            app.storage_meter['value'] = pct
        app.set_status(summary, is_busy=False)
    threading.Thread(target=worker, daemon=True).start()


def action_execute_cleanup(app):
    """Performs deep disk cleaning on selected targets."""
    selected_ids = [cid for cid, var in app.cleanup_checks.items() if var.get()]
    if not selected_ids:
        messagebox.showwarning("Apex Optimizer", "No categories selected for cleanup.")
        return

    def worker():
        app.set_status("Cleaning selected junk files...", is_busy=True)
        freed, s_str = app.engine.execute_cleanup(selected_ids)
        app.set_status(f"Clean complete! Reclaimed {s_str}.", is_busy=False)
        messagebox.showinfo("Apex Optimizer", f"Deep Clean complete!\nSuccessfully freed: {s_str}")
        action_scan_junk(app)
    threading.Thread(target=worker, daemon=True).start()


# -------------------------------------------------------------
# 4. Software Updater (WinGet)
# -------------------------------------------------------------
def render_software_updater(app):
    """Renders the WinGet Software Updater tab."""
    render_section_header(
        app,
        "Software & Package Manager (WinGet)",
        "Query and silently update all installed applications to their latest secure versions via Windows Package Manager."
    )

    card = ModernCard(app.content_container)
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
        command=lambda: action_check_winget(app)
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
        command=lambda: action_run_winget_upgrade(app)
    ).pack(side=tk.LEFT)

    app.updater_text = tk.Text(
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
    app.updater_text.pack(fill=tk.BOTH, expand=True)
    app.updater_text.insert(tk.END, "Click 'Check for Updates' to query installed packages and available updates via WinGet...\n")


def action_check_winget(app):
    """Queries WinGet for outdated installed packages."""
    def worker():
        app.set_status("Querying WinGet for app updates...", is_busy=True)
        ok, out = app.engine.check_winget_updates()
        app.updater_text.delete("1.0", tk.END)
        app.updater_text.insert(tk.END, out + "\n")
        app.set_status("WinGet query finished.", is_busy=False)
    threading.Thread(target=worker, daemon=True).start()


def action_run_winget_upgrade(app):
    """Executes automated upgrade of all apps via WinGet."""
    def worker():
        app.set_status("Upgrading packages via WinGet...", is_busy=True)
        app.updater_text.insert(tk.END, "\n[Apex] Starting WinGet upgrade all...\n")
        c, out = app.engine.run_winget_upgrade_all()
        app.updater_text.insert(tk.END, out + "\n")
        app.set_status(f"WinGet upgrade completed (code {c}).", is_busy=False)
        messagebox.showinfo("WinGet Updater", "Application upgrade cycle completed.")
    threading.Thread(target=worker, daemon=True).start()
