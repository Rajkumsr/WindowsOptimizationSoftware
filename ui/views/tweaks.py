"""
Apex Windows Optimizer - System, Privacy, & Explorer Tweaks View
Modular renderers and action handlers for core registry, power policy,
privacy telemetry, and shell personalization.
"""

import threading
import tkinter as tk
from ui.theme import THEME, FONT_FAMILY
from ui.components import ModernCard, render_tweak_grid
from ui.views.common import render_section_hero, create_scrollable_container


def render_system_tweaks(app):
    """Renders the System & Speed tuning tab with kernel, network, and power options."""
    kernel_tweak_defs = [
        ("network_throttling", "Multimedia Network Throttling", "Sets NetworkThrottlingIndex to disabled (0xFFFFFFFF) so gaming and streaming packets are never prioritized down.", "NETWORK", "⚡ LOW PACKET JITTER"),
        ("system_responsiveness", "Foreground System Responsiveness", "Reserves 90% CPU priority for active foreground games and programs (SystemResponsiveness = 10).", "KERNEL", "🚀 90% CPU PRIORITY"),
        ("irp_stack_size", "Optimize IRP Stack Size", "Sets IRPStackSize to 30, significantly increasing throughput for local network and file sharing transfers.", "STORAGE", "📁 MAX NETWORK BUFFER"),
        ("fast_shutdown", "Accelerated Service Termination", "Reduces WaitToKillServiceTimeout to 5000ms, preventing stalled services from delaying shutdown.", "STARTUP", "⏱️ 5-SEC FAST KILL"),
        ("long_paths", "Enable NTFS Long File Paths", "Removes legacy MAX_PATH 260-character path limits in Windows file system.", "FILESYSTEM", "📂 32K PATH LIMIT"),
        ("block_oem_bloat", "Block OEM Firmware WPBT", "Blocks hardware vendors and UEFI firmware from automatically installing bundled promotional software at boot.", "FIRMWARE", "🛡️ WPBT ROOTKIT BLOCKED"),
        ("disable_p2p_update", "Disable P2P Update Seeding", "Stops Windows Delivery Optimization from using your upstream internet connection to upload updates to others.", "BANDWIDTH", "🌐 ZERO UPLOAD DRAIN"),
        ("f8_boot_menu", "Enable Classic F8 Boot Menu", "Restores the legacy F8 boot selection menu for easy recovery and Safe Mode access.", "BOOT", "⌨️ INSTANT SAFE MODE"),
        ("disable_hibernation", "Disable Hibernation (Desktop)", "Deletes hiberfil.sys to reclaim disk space equivalent to your total RAM size (desktops only).", "STORAGE", "💾 RECLAIM RAM-SIZE SSD"),
        ("svchost_split_threshold", "SvcHost Process Consolidation", "Groups individual Windows service host processes together on systems with <16GB RAM to reclaim 300MB+ physical memory.", "MEMORY", "🧠 SAVE 300MB+ RAM"),
        ("defender_cpu_cap", "Defender Background Scan CPU Cap", "Restricts Windows Defender scheduled background file scans to 25% CPU core usage to prevent 100% CPU system lockups.", "ANTIVIRUS", "🛡️ 25% CPU LIMIT")
    ]

    power_tweak_defs = [
        ("processor_eco", "Processor Efficiency on Battery", "Caps aggressive CPU boost to 85% on battery. Eliminates high heat, fan noise, and extends screen-on battery runtime by up to 25%.", "CPU ECO", "🔋 +25% BATTERY RUNTIME"),
        ("pcie_aspm", "PCIe Link State Power (ASPM)", "Places idle NVMe SSD lanes, discrete GPU, and motherboard interconnects into low-power states to cut idle motherboard battery drain.", "CHIPSET", "❄️ CUT MOTHERBOARD DRAIN"),
        ("fast_startup", "Disable Fast Startup Drain", "Stops Windows from saving an active kernel hibernation state at shutdown, eliminating 3-5% overnight battery discharge while powered off.", "BATTERY", "🛑 ZERO OVERNIGHT DRAIN")
    ]

    all_keys = [k[0] for k in kernel_tweak_defs] + [k[0] for k in power_tweak_defs]
    app.system_toggles.clear()

    update_hero = render_section_hero(
        app,
        "System Performance & Kernel Tuning",
        "Fine-tune low-level Windows kernel parameters, network throughput, startup timeouts, and hardware power policies.",
        all_keys,
        app.system_toggles,
        lambda: action_apply_system_tweaks(app),
        icon="⚡"
    )

    scroll_canvas, scroll_content = create_scrollable_container(app)

    # Group 1: Kernel & System Responsiveness
    group1_hdr = tk.Frame(scroll_content, bg=THEME["bg_app"])
    group1_hdr.pack(fill=tk.X, pady=(0, 6))
    tk.Label(
        group1_hdr,
        text="⚡ Kernel, Network & Storage Tuning",
        font=(FONT_FAMILY, 10, "bold"),
        fg=THEME["text_main"],
        bg=THEME["bg_app"]
    ).pack(side=tk.LEFT)

    render_tweak_grid(scroll_content, kernel_tweak_defs, app.live_states, app.system_toggles, on_change_callback=lambda k, s: update_hero())

    # Group 2: Power, Energy & Hardware Efficiency Tweaks
    group2_hdr = tk.Frame(scroll_content, bg=THEME["bg_app"])
    group2_hdr.pack(fill=tk.X, pady=(12, 6))
    tk.Label(
        group2_hdr,
        text="🔋 Hardware Power & Energy Conservation Tweaks",
        font=(FONT_FAMILY, 10, "bold"),
        fg=THEME["text_main"],
        bg=THEME["bg_app"]
    ).pack(side=tk.LEFT)
    tk.Label(
        group2_hdr,
        text="UNIVERSAL POWER POLICIES",
        font=(FONT_FAMILY, 8, "bold"),
        fg=THEME["success"],
        bg=THEME["success_bg"],
        padx=8,
        pady=2
    ).pack(side=tk.RIGHT)

    render_tweak_grid(scroll_content, power_tweak_defs, app.live_states, app.system_toggles, on_change_callback=lambda k, s: update_hero())


def render_privacy_tweaks(app):
    """Renders the Privacy & Telemetry tab with background tracking blockers."""
    tweak_defs = [
        ("disable_telemetry", "Telemetry & CEIP Tracking", "Disables DiagTrack, feedback notifications, Windows Error Reporting telemetry, and Customer Experience Program.", "DIAGNOSTICS", "🛡️ ZERO TELEMETRY LOGS"),
        ("disable_lockscreen_ads", "Lock Screen Spotlight Ads", "Prevents Microsoft Spotlight from displaying sponsored tips, recommendations, and advertisements on the lock screen.", "ADS", "🔒 CLEAN LOCK SCREEN"),
        ("disable_recall", "Recall AI Activity Tracking", "Blocks automated continuous screenshot captures and AI analysis from the Recall subsystem.", "AI PRIVACY", "🚫 NO SCREENSHOT LOGS"),
        ("optimize_edge", "Edge Background Harvester", "Stops Microsoft Edge from running in the background when closed and disables startup boost and shopping assistant.", "BROWSER", "⚡ SAVE 400MB RAM"),
        ("suppress_oobe_telemetry", "OOBE Diagnostic Prompts", "Bypasses consumer data harvesting prompts and privacy opt-ins during updates.", "PROMPTS", "🛑 NO HARVEST PROMPTS"),
        ("disable_office_telemetry", "Microsoft Office Telemetry", "Disables telemetry logging, Customer Experience feedback, and diagnostic data upload for Office 2013-365.", "OFFICE", "📊 CLEAN OFFICE LOGS")
    ]

    all_keys = [k[0] for k in tweak_defs]
    app.privacy_toggles.clear()

    update_hero = render_section_hero(
        app,
        "Privacy, Telemetry & Background Tracking",
        "Eliminate background diagnostic data collection, advertising IDs, and invasive telemetry. Toggles reflect current state.",
        all_keys,
        app.privacy_toggles,
        lambda: action_apply_privacy_tweaks(app),
        icon="🛡️"
    )

    scroll_canvas, scroll_content = create_scrollable_container(app)
    render_tweak_grid(scroll_content, tweak_defs, app.live_states, app.privacy_toggles, on_change_callback=lambda k, s: update_hero())


def render_explorer_tweaks(app):
    """Renders the Explorer & Shell Personalization tab."""
    tweak_defs = [
        ("show_extensions", "Show File Name Extensions", "Always display file extensions (.exe, .txt, .pdf, .zip) to prevent spoofing and improve visibility.", "EXTENSIONS", "📄 VISIBLE EXTENSIONS"),
        ("show_hidden", "Show Hidden Files & Folders", "Make hidden system files and folders visible in File Explorer.", "FILESYSTEM", "👁️ UNHIDE FILES"),
        ("open_this_pc", "Open Explorer to 'This PC'", "Launches File Explorer directly into 'This PC' with drives listed, rather than the slow Quick Access view.", "NAVIGATION", "💻 DIRECT DRIVES VIEW"),
        ("classic_context_menu", "Classic Right-Click Menu", "Restores the traditional, responsive Windows 10 right-click menu without having to click 'Show more options'.", "CONTEXT MENU", "⚡ 1-CLICK ACTIONS"),
        ("disable_start_bing", "Disable Bing in Start Menu", "Restricts Start Menu search queries to local files and apps, eliminating unwanted web recommendations.", "START MENU", "🔍 INSTANT LOCAL SEARCH"),
        ("taskbar_end_task", "Taskbar 'End Task' Option", "Adds a direct 'End Task' context menu option when right-clicking running apps on the taskbar.", "TASKBAR", "🛑 1-CLICK FORCE QUIT"),
        ("clean_taskbar", "Clean Taskbar Clutter", "Hides news widgets, task view, and Copilot buttons from the taskbar to maximize active window space.", "SHELL", "🧹 REMOVE COPILOT/WIDGETS"),
        ("fast_menu_delay", "Accelerate Menu Animations", "Reduces MenuShowDelay to 10ms for instant dropdowns and context menus.", "ANIMATIONS", "⏱️ 10MS INSTANT POPUP"),
        ("disable_sticky_keys", "Disable 5x Shift Sticky Keys", "Prevents accidental activation dialogs when tapping Shift repeatedly in games or editing.", "ACCESSIBILITY", "🎮 NO GAME INTERRUPTIONS")
    ]

    all_keys = [k[0] for k in tweak_defs]
    app.explorer_toggles.clear()

    update_hero = render_section_hero(
        app,
        "Explorer & Shell Personalization",
        "Streamline File Explorer, remove clutter, and restore productivity-focused desktop behaviors.",
        all_keys,
        app.explorer_toggles,
        lambda: action_apply_explorer_tweaks(app),
        icon="🎨"
    )

    scroll_canvas, scroll_content = create_scrollable_container(app)

    # Multi-user deployment banner
    multi_card = ModernCard(scroll_content)
    multi_card.pack(fill=tk.X, pady=(0, 10))

    chk = tk.Checkbutton(
        multi_card,
        text="Deploy settings to all user profiles & future accounts (Default User Hive)",
        variable=app.multi_user_deploy_var,
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

    render_tweak_grid(scroll_content, tweak_defs, app.live_states, app.explorer_toggles, on_change_callback=lambda k, s: update_hero())


def action_apply_system_tweaks(app):
    """Executes system and kernel tweaks asynchronously."""
    opts = {k: v.get() for k, v in app.system_toggles.items()}
    def worker():
        app.set_status("Applying system changes...", is_busy=True)
        count = app.engine.apply_system_performance_tweaks(opts)
        app.live_states = app.engine.detect_all_tweak_states()
        app.set_status(f"System changes applied ({count} updated).", is_busy=False)
        app.root.after(0, lambda: app.show_toast("System Settings Updated", f"Successfully updated {count} system performance configurations.", "success"))
    threading.Thread(target=worker, daemon=True).start()


def action_apply_privacy_tweaks(app):
    """Executes privacy and telemetry tweaks asynchronously."""
    opts = {k: v.get() for k, v in app.privacy_toggles.items()}
    def worker():
        app.set_status("Applying privacy changes...", is_busy=True)
        count = app.engine.apply_privacy_telemetry_tweaks(opts)
        app.engine.disable_telemetry_tasks()
        app.live_states = app.engine.detect_all_tweak_states()
        app.set_status(f"Privacy changes applied ({count} updated).", is_busy=False)
        app.root.after(0, lambda: app.show_toast("Privacy Policies Applied", f"Successfully updated {count} telemetry & privacy policies.", "success"))
    threading.Thread(target=worker, daemon=True).start()


def action_apply_explorer_tweaks(app):
    """Executes Explorer tweaks asynchronously with optional multi-user hive deployment."""
    opts = {k: v.get() for k, v in app.explorer_toggles.items()}
    deploy_all = app.multi_user_deploy_var.get()
    def worker():
        app.set_status("Applying shell customizations...", is_busy=True)
        count = app.engine.apply_explorer_ui_tweaks(opts, deploy_to_all_profiles=deploy_all)
        app.live_states = app.engine.detect_all_tweak_states()
        app.set_status(f"Explorer changes applied ({count} updated).", is_busy=False)
        app.root.after(0, lambda: app.show_toast("Explorer Tweaks Applied", f"Applied {count} Explorer and UI customizations.", "success"))
    threading.Thread(target=worker, daemon=True).start()
