"""
Apex Windows Optimizer - UI Subsystem Package
"""

from .app import ApexOptimizerApp, main
from .theme import THEME, FONT_FAMILY
from .components import ModernCard, ToggleSwitch, DonutGauge, ToastManager, get_app_icon_path
from .tray import ApexTrayManager
from .search_data import ALL_SEARCHABLE_TWEAKS

__all__ = [
    "ApexOptimizerApp",
    "main",
    "THEME",
    "FONT_FAMILY",
    "ModernCard",
    "ToggleSwitch",
    "DonutGauge",
    "ToastManager",
    "get_app_icon_path",
    "ApexTrayManager",
    "ALL_SEARCHABLE_TWEAKS"
]
