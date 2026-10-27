"""
Apex Windows Optimizer - Gaming & GPU Boost View
Modular renderer and action handlers for GPU hardware telemetry,
driver priority, latency reduction, and DirectX flip optimizations.
"""

import threading
import tkinter as tk
from ui.theme import THEME, FONT_FAMILY
from ui.components import ModernCard, render_tweak_grid
from ui.views.common import render_section_hero, create_scrollable_container


def render_gaming_boost(app, refresh_gpu: bool = False):
    """Renders the Gaming & GPU Boost tab with hardware telemetry and low-latency tweaks."""
    gfx_tweak_defs = [
        ("enable_hags", "Hardware Accelerated GPU Scheduling", "Enables the Windows HAGS setting. A compatible GPU/driver and restart may be required; performance effects vary.", "GPU HAGS", "HAGS SETTING"),
        ("windowed_optimizations", "Windowed Game Optimizations", "Enables the modern flip model presentation for DirectX 10/11 windowed games.", "FLIP MODEL", "🚀 TEAR-FREE FLIP"),
        ("mmcss_priority", "MMCSS Multimedia GPU Priority", "Configures GPU Priority = 8, Priority = 6, and High scheduling category for ultra-smooth frame delivery.", "MMCSS", "🎮 HIGH FRAME RATE")
    ]

    latency_tweak_defs = [
        ("disable_gamedvr", "Disable Xbox Game Bar & DVR", "Disables Windows Game DVR background capture settings. The effect depends on current capture configuration and apps.", "GAME DVR", "BACKGROUND CAPTURE OFF"),
        ("enable_game_mode", "Windows Native Game Mode", "Enables Windows Game Mode policy settings. Scheduling behavior depends on Windows, hardware, and workload.", "GAME MODE", "GAME MODE SETTING"),
        ("disable_mouse_acceleration", "1:1 Raw Mouse Input", "Disables Windows 'Enhanced Pointer Precision' for true 1:1 muscle memory mouse tracking in competitive games.", "RAW INPUT", "🎯 ZERO ACCEL DRIFT"),
        ("network_gaming_latency", "Configure TCP Acknowledgment Settings", "Applies TcpAckFrequency and TCPNoDelay values to network adapters. Latency effects depend on the network and application.", "TCP SETTINGS", "NETWORK ADAPTER POLICY"),
        ("reset_hpet", "Reset HPET Override Timer", "Removes an explicit useplatformclock override from the boot configuration. Effect on timing depends on hardware and Windows.", "HPET", "REMOVE OVERRIDE"),
        ("disable_power_throttling", "Disable CPU Power Throttling", "Changes the Windows power-throttling policy on desktops. It does not guarantee a specific processor frequency.", "THROTTLING", "POWER POLICY"),
        ("ultimate_performance", "Ultimate Performance Power Plan", "Duplicates and activates Windows' Ultimate Performance plan when supported. Power use and performance effects vary.", "POWER PLAN", "ACTIVATE POWER PLAN")
    ]

    all_keys = [k[0] for k in gfx_tweak_defs] + [k[0] for k in latency_tweak_defs]
    app.gaming_toggles.clear()

    update_hero = render_section_hero(
        app,
        "Gaming & GPU Performance Boost",
        "Unlock ultra-low input latency, dedicated multimedia priority, maximum hardware clocks, and real-time GPU/fan monitoring.",
        all_keys,
        app.gaming_toggles,
        lambda: action_apply_gaming_tweaks(app),
        icon="🎮"
    )

    scroll_canvas, scroll_content = create_scrollable_container(app)

    gpu_info = app.engine.get_gpu_telemetry(force_refresh=refresh_gpu)

    # ---------------------------------------------------------
    # Card 1: Live GPU & Display Hardware Telemetry
    # ---------------------------------------------------------
    gpu_card = ModernCard(scroll_content)
    gpu_card.pack(fill=tk.X, pady=(0, 14))

    g_top = tk.Frame(gpu_card, bg=THEME["bg_card"])
    g_top.pack(fill=tk.X, pady=(0, 8))

    tk.Label(
        g_top,
        text=f"🎮  {gpu_info.get('name', 'Graphics Processor')}",
        font=(FONT_FAMILY, 12, "bold"),
        fg=THEME["text_main"],
        bg=THEME["bg_card"]
    ).pack(side=tk.LEFT)

    tag_text = "⚡ DISCRETE GPU" if gpu_info.get("is_discrete") else "⚡ ACTIVE GRAPHICS"
    tk.Label(
        g_top,
        text=tag_text,
        font=(FONT_FAMILY, 8, "bold"),
        fg=THEME["accent_cyan"],
        bg=THEME["bg_card_alt"],
        padx=10,
        pady=3,
        relief="flat"
    ).pack(side=tk.RIGHT)

    # Display & Hardware Specs Sub-line
    res_str = gpu_info.get("resolution", "1920 × 1080")
    hz_val = gpu_info.get("refresh_rate", 60)
    vram_str = gpu_info.get("vram_str", "Shared VRAM")

    tk.Label(
        gpu_card,
        text=f"🖥️ Display: {res_str} @ {hz_val} Hz   •   📁 Memory: {vram_str}",
        font=(FONT_FAMILY, 9),
        fg=THEME["text_muted"],
        bg=THEME["bg_card"]
    ).pack(anchor="w", pady=(0, 10))

    # 3 Metric Tiles (Fan Speed with 🪭 symbol, Driver Version, Architecture)
    tiles_row = tk.Frame(gpu_card, bg=THEME["bg_card"])
    tiles_row.pack(fill=tk.X)

    tiles_data = [
        ("🪭 FAN SPEED / COOLING", gpu_info.get("fan_speed_str", "🪭 Active Dynamic Flow"), THEME["accent_cyan"]),
        ("GPU DRIVER VERSION", gpu_info.get("driver_version", "N/A"), THEME["text_main"]),
        ("PROCESSOR ARCHITECTURE", gpu_info.get("video_processor", "Hardware GPU"), THEME["text_muted"])
    ]

    for i, (label, val, val_col) in enumerate(tiles_data):
        tile = tk.Frame(tiles_row, bg=THEME["bg_input"], padx=10, pady=8, highlightbackground=THEME["border"], highlightthickness=1)
        tile.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 8, 0))
        tk.Label(tile, text=label, font=(FONT_FAMILY, 7, "bold"), fg=THEME["text_dim"], bg=THEME["bg_input"]).pack(anchor="w")
        tk.Label(tile, text=val, font=(FONT_FAMILY, 9, "bold"), fg=val_col, bg=THEME["bg_input"]).pack(anchor="w", pady=(2, 0))

    # Group 1: Core Graphics & Driver Tuning
    g1_hdr = tk.Frame(scroll_content, bg=THEME["bg_app"])
    g1_hdr.pack(fill=tk.X, pady=(12, 6))
    tk.Label(g1_hdr, text="⚡ Core Graphics & Driver Tuning", font=(FONT_FAMILY, 10, "bold"), fg=THEME["text_main"], bg=THEME["bg_app"]).pack(side=tk.LEFT)

    render_tweak_grid(scroll_content, gfx_tweak_defs, app.live_states, app.gaming_toggles, on_change_callback=lambda k, s: update_hero())

    # Group 2: Latency, Anti-Stutter & Input Response
    g2_hdr = tk.Frame(scroll_content, bg=THEME["bg_app"])
    g2_hdr.pack(fill=tk.X, pady=(14, 6))
    tk.Label(g2_hdr, text="🎯 Input Latency, Anti-Stutter & Frame-Drop Prevention", font=(FONT_FAMILY, 10, "bold"), fg=THEME["text_main"], bg=THEME["bg_app"]).pack(side=tk.LEFT)

    render_tweak_grid(scroll_content, latency_tweak_defs, app.live_states, app.gaming_toggles, on_change_callback=lambda k, s: update_hero())


def action_apply_gaming_tweaks(app):
    """Executes gaming optimizations asynchronously."""
    opts = {k: v.get() for k, v in app.gaming_toggles.items()}
    def worker():
        app.set_status("Applying gaming optimizations...", is_busy=True)
        count = app.engine.apply_gaming_tweaks(opts)
        app.live_states = app.engine.detect_all_tweak_states()
        app.set_status(f"Gaming optimizations applied ({count} updated).", is_busy=False)
        app.root.after(0, lambda: app.show_toast("Gaming Tweaks Applied", f"Applied {count} Gaming and GPU performance optimizations.", "boost"))
    threading.Thread(target=worker, daemon=True).start()
