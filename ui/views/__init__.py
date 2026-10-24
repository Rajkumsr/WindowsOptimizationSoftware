"""
Apex Windows Optimizer - UI Views Subsystem
Modular page renderers and action controllers for the application tabs.
"""

from ui.views.common import (
    render_section_hero,
    render_section_header,
    create_scrollable_container,
)

from ui.views.dashboard import (
    render_dashboard,
    run_quick_optimize,
    apply_gaming_preset,
    apply_battery_preset,
    apply_privacy_preset,
    apply_defaults_preset,
    action_quick_boost,
    action_flush_ram_only,
)

from ui.views.tweaks import (
    render_system_tweaks,
    render_privacy_tweaks,
    render_explorer_tweaks,
    action_apply_system_tweaks,
    action_apply_privacy_tweaks,
    action_apply_explorer_tweaks,
)

from ui.views.gaming import (
    render_gaming_boost,
    action_apply_gaming_tweaks,
)

from ui.views.battery import (
    render_battery_page,
    action_toggle_processor_eco,
    action_toggle_pcie_aspm,
    action_toggle_battery_alarm,
    action_generate_battery_report,
    action_toggle_fast_startup,
)

from ui.views.tools import (
    render_services_optimizer,
    preset_services_recommended,
    preset_services_gaming,
    preset_services_reset,
    action_apply_services,
    render_debloater,
    action_remove_bloatware,
    render_disk_cleaner,
    action_scan_junk,
    action_execute_cleanup,
    render_software_updater,
    action_check_winget,
    action_run_winget_upgrade,
)

from ui.views.terminal import (
    render_terminal_log,
    action_copy_log,
    action_save_log,
    action_clear_log,
)

from ui.views.developer import (
    render_developer_page,
    action_create_restore_point,
    action_export_reg,
    quick_flush_dns,
    quick_restart_explorer,
)

from ui.views.search import (
    render_search_results,
    apply_search_toggle,
)

__all__ = [
    # Common
    "render_section_hero",
    "render_section_header",
    "create_scrollable_container",
    # Dashboard
    "render_dashboard",
    "run_quick_optimize",
    "apply_gaming_preset",
    "apply_battery_preset",
    "apply_privacy_preset",
    "apply_defaults_preset",
    "action_quick_boost",
    "action_flush_ram_only",
    # Tweaks
    "render_system_tweaks",
    "render_privacy_tweaks",
    "render_explorer_tweaks",
    "action_apply_system_tweaks",
    "action_apply_privacy_tweaks",
    "action_apply_explorer_tweaks",
    # Gaming
    "render_gaming_boost",
    "action_apply_gaming_tweaks",
    # Battery
    "render_battery_page",
    "action_toggle_processor_eco",
    "action_toggle_pcie_aspm",
    "action_toggle_battery_alarm",
    "action_generate_battery_report",
    "action_toggle_fast_startup",
    # Tools
    "render_services_optimizer",
    "preset_services_recommended",
    "preset_services_gaming",
    "preset_services_reset",
    "action_apply_services",
    "render_debloater",
    "action_remove_bloatware",
    "render_disk_cleaner",
    "action_scan_junk",
    "action_execute_cleanup",
    "render_software_updater",
    "action_check_winget",
    "action_run_winget_upgrade",
    # Terminal
    "render_terminal_log",
    "action_copy_log",
    "action_save_log",
    "action_clear_log",
    # Developer
    "render_developer_page",
    "action_create_restore_point",
    "action_export_reg",
    "quick_flush_dns",
    "quick_restart_explorer",
    # Search
    "render_search_results",
    "apply_search_toggle",
]
