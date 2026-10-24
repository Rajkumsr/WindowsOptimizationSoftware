"""
Apex Windows Optimizer - Searchable Tweaks Registry
Predefined index of all configurable tweaks across system, privacy, shell, gaming, and battery.
Used by the global Ctrl+F live search engine.
"""

ALL_SEARCHABLE_TWEAKS = [
    ("network_throttling", "system", "Disable Multimedia Network Throttling", "Sets NetworkThrottlingIndex to disabled so gaming and streaming packets are never prioritized down."),
    ("system_responsiveness", "system", "Foreground System Responsiveness", "Reserves 90% CPU priority for active foreground games and programs."),
    ("irp_stack_size", "system", "Optimize IRP Stack Size", "Sets IRPStackSize to 30, significantly increasing local network transfer throughput."),
    ("fast_shutdown", "system", "Accelerated Service Termination", "Reduces WaitToKillServiceTimeout to 5000ms, preventing stalled services from delaying shutdown."),
    ("long_paths", "system", "Enable NTFS Long File Paths", "Removes legacy MAX_PATH 260-character path limits in Windows file system."),
    ("block_oem_bloat", "system", "Block OEM Firmware WPBT Software", "Blocks hardware vendors and UEFI firmware from automatically installing bundled promotional software at boot."),
    ("disable_p2p_update", "system", "Disable P2P Update Seeding", "Stops Windows Delivery Optimization from using your upstream bandwidth to seed updates to others."),
    ("f8_boot_menu", "system", "Enable Classic F8 Boot Menu", "Restores the legacy F8 boot selection menu for easy recovery and Safe Mode access."),
    ("disable_hibernation", "system", "Disable Hibernation (Desktop PC)", "Deletes hiberfil.sys to reclaim disk space equivalent to your total RAM size on desktop PCs."),
    ("disable_telemetry", "privacy", "Disable Diagnostic Telemetry & CEIP", "Disables DiagTrack, feedback notifications, Windows Error Reporting telemetry, and Customer Experience Program."),
    ("disable_lockscreen_ads", "privacy", "Disable Lock Screen Spotlight Ads", "Prevents Microsoft Spotlight from displaying sponsored tips, recommendations, and advertisements on the lock screen."),
    ("disable_recall", "privacy", "Disable Microsoft Recall AI Tracking", "Blocks automated continuous screenshot captures and AI analysis from the Recall subsystem."),
    ("optimize_edge", "privacy", "Optimize Microsoft Edge Background Mode", "Stops Microsoft Edge from running in the background when closed and disables startup boost and shopping assistant."),
    ("suppress_oobe_telemetry", "privacy", "Suppress OOBE Diagnostic Experiences", "Bypasses consumer data harvesting prompts and privacy opt-ins during updates."),
    ("disable_office_telemetry", "privacy", "Disable Microsoft Office Telemetry", "Disables telemetry logging, Customer Experience feedback, and diagnostic data upload for Office 2013-365."),
    ("show_file_extensions", "explorer", "Always Show File Extensions", "Always displays .exe, .zip, .bat file extensions to prevent spoofing."),
    ("open_to_this_pc", "explorer", "Open File Explorer to 'This PC'", "Opens File Explorer directly to drive list instead of Quick Access / Home."),
    ("win11_classic_menu", "explorer", "Windows 11 Classic Context Menu", "Restores the classic full right-click context menu instantly."),
    ("disable_bing_search", "explorer", "Disable Bing Web Search in Start Menu", "Keeps Windows Start Menu search purely local and instantaneous."),
    ("taskbar_end_task", "explorer", "Enable 'End Task' on Taskbar Right-Click", "Enables direct process termination from taskbar right-click."),
    ("hide_taskbar_widgets", "explorer", "Hide Taskbar Widgets & News", "Removes MSN widgets icon from the Windows 11 taskbar."),
    ("hide_copilot_button", "explorer", "Hide Windows Copilot Taskbar Button", "Hides Copilot AI icon from the taskbar."),
    ("reduce_menu_delay", "explorer", "Accelerate Menu Show Delay (10ms)", "Reduces UI menu show latency for snappy navigation."),
    ("disable_sticky_keys", "explorer", "Disable Sticky Keys 5x Shift Prompt", "Stops the annoying 5x Shift dialog during gaming."),
    ("hags", "gaming", "Hardware-Accelerated GPU Scheduling (HAGS)", "Transfers frame scheduling directly to GPU VRAM for reduced render latency."),
    ("windowed_optimizations", "gaming", "Optimizations for Windowed Games", "Enables modern DXGI flip presentation model for windowed gaming."),
    ("game_mmcss", "gaming", "Multimedia Class Scheduler (MMCSS) Priority", "Configures maximum thread and GPU priority for gaming tasks."),
    ("power_throttling", "gaming", "Disable Execution Power Throttling", "Prevents Windows from downclocking background CPU cores during games."),
    ("ultimate_performance", "gaming", "Activate Ultimate Performance Power Scheme", "Activates Windows' hidden latency-free power plan."),
    ("hpet_reset", "gaming", "Reset High Precision Event Timer (HPET)", "Removes explicit timer overrides to prevent micro-stuttering."),
    ("disable_gamedvr", "gaming", "Disable Xbox Game Bar & Background DVR", "Stops 60fps background video recording from consuming GPU encoder cycles and disk throughput."),
    ("enable_game_mode", "gaming", "Enable Windows Native Game Mode", "Prioritizes CPU and GPU resources for active game processes and halts background updates."),
    ("disable_mouse_acceleration", "gaming", "Disable Mouse Pointer Acceleration (1:1 Input)", "Disables Windows Enhanced Pointer Precision for true 1:1 raw mouse tracking in competitive games."),
    ("network_gaming_latency", "gaming", "Lower Gaming Ping (Disable Nagle's Algorithm)", "Eliminates network packet buffering delay for instantaneous packet delivery in online games."),
    ("processor_eco", "system", "Processor Eco Boost Capping on Battery", "Limits CPU turbo boost to 85% on battery to eliminate thermal spikes and extend runtime."),
    ("pcie_aspm", "system", "PCIe Link State Power Management (ASPM)", "Puts idle PCIe lanes into maximum power savings on DC power."),
    ("fast_startup", "system", "Disable Windows Fast Startup", "Stops hybrid kernel hibernation and eliminates 3-5% overnight battery discharge.")
]
