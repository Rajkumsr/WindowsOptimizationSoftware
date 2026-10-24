"""
Apex Windows Optimizer - Developer Profile & System Maintenance View
Modular renderer and action handlers for developer profile, credentials,
restore point creation, registry backup, and quick explorer/DNS maintenance.
"""

import threading
import webbrowser
import tkinter as tk
from ui.theme import THEME, FONT_FAMILY
from ui.components import ModernCard
from ui.views.common import render_section_header, create_scrollable_container


def render_developer_page(app):
    """Renders the Developer Profile & About tab with architecture specs and contact links."""
    for widget in app.content_container.winfo_children():
        widget.destroy()

    render_section_header(
        app,
        "Developer Profile & About",
        "Software architecture, project credentials, and developer connections."
    )

    scroll_canvas, scroll_content = create_scrollable_container(app)

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


def action_create_restore_point(app):
    """Creates a Windows System Restore point asynchronously."""
    def worker():
        app.set_status("Creating System Restore Point...", is_busy=True)
        res = app.engine.create_restore_point("Apex Manual Restore Point")
        app.set_status("Restore point process finished.", is_busy=False)
        if res:
            app.root.after(0, lambda: app.show_toast("Restore Protection", "System Restore Point created successfully.", "success"))
        else:
            app.root.after(0, lambda: app.show_toast("Restore Protection", "Restore point creation could not be completed. Check activity log.", "warning"))
    threading.Thread(target=worker, daemon=True).start()


def action_export_reg(app):
    """Exports registry backup snapshot asynchronously."""
    def worker():
        app.set_status("Exporting registry backup...", is_busy=True)
        res = app.engine.export_registry_backup()
        app.set_status("Registry export finished.", is_busy=False)
        if res:
            app.root.after(0, lambda: app.show_toast("Registry Backup", "Registry hives HKLM and HKCU exported successfully.", "success"))
        else:
            app.root.after(0, lambda: app.show_toast("Registry Backup", "Registry export could not be completed. Check activity log.", "danger"))
    threading.Thread(target=worker, daemon=True).start()


def quick_flush_dns(app):
    """Executes ipconfig /flushdns asynchronously."""
    def worker():
        app.set_status("Flushing DNS cache...", is_busy=True)
        app.engine.flush_dns()
        app.set_status("DNS cache flushed.", is_busy=False)
        app.root.after(0, lambda: app.show_toast("DNS Resolver", "Windows DNS cache flushed successfully.", "info"))
    threading.Thread(target=worker, daemon=True).start()


def quick_restart_explorer(app):
    """Restarts explorer.exe asynchronously."""
    def worker():
        app.set_status("Restarting Explorer shell...", is_busy=True)
        app.engine.restart_explorer()
        app.set_status("Explorer shell restarted.", is_busy=False)
        app.root.after(0, lambda: app.show_toast("Explorer Shell", "Windows Explorer shell restarted successfully.", "info"))
    threading.Thread(target=worker, daemon=True).start()
