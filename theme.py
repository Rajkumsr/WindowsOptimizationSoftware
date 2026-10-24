"""
Apex Windows Optimizer - Theme & Windows System Synchronization
Dynamically extracts official Windows Personalization accent palette, dark/light theme,
and Win32 system color metrics directly from Windows Registry, DWM, and User32 APIs.
"""

import sys
import ctypes
import winreg
from typing import Dict

def load_windows_system_theme() -> Dict[str, str]:
    """
    Extracts the official Windows Personalization accent palette, dark/light theme,
    and system color metrics directly from Windows Registry, DWM, and User32 APIs.
    All colors dynamically synchronize with the user's active Windows configuration.
    """
    # 1. Detect Dark or Light mode from Windows Personalization
    is_dark = True
    if sys.platform == "win32":
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            app_light, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
            is_dark = (app_light == 0)
            winreg.CloseKey(k)
        except Exception:
            pass

    # Baseline colors mapped to Windows dark/light mode
    if is_dark:
        theme = {
            "is_dark": True,
            "bg_app": "#0D0F17",         # Deep obsidian window background
            "bg_sidebar": "#131622",     # Sleek dark sidebar
            "bg_card": "#1A1E2E",        # Card / panel background
            "bg_card_alt": "#21263A",    # Hover / secondary card
            "bg_input": "#12141F",       # Input & terminal background
            "border": "#282E47",         # Subtle border line
            "border_highlight": "#3A4366",
            "primary": "#0078D4",        # Windows classic blue default
            "primary_hover": "#0067C0",
            "primary_light": "#4CC2FF",
            "accent_cyan": "#99EBFF",
            "accent_contrast": "#F7630C",
            "success": "#10B981",        # Emerald green
            "success_bg": "#064E3B",
            "warning": "#F59E0B",        # Amber
            "warning_bg": "#78350F",
            "danger": "#EF4444",         # Crimson
            "danger_bg": "#7F1D1D",
            "text_main": "#F9FAFB",      # Bright white text
            "text_muted": "#9CA3AF",     # Neutral gray text
            "text_dim": "#6B7280"        # Dark muted text
        }
    else:
        theme = {
            "is_dark": False,
            "bg_app": "#F3F4F6",         # Light window background
            "bg_sidebar": "#E5E7EB",     # Light sidebar
            "bg_card": "#FFFFFF",        # White card
            "bg_card_alt": "#F9FAFB",    # Off-white card
            "bg_input": "#FFFFFF",       # Input background
            "border": "#D1D5DB",         # Light border line
            "border_highlight": "#9CA3AF",
            "primary": "#0078D4",
            "primary_hover": "#0067C0",
            "primary_light": "#4CC2FF",
            "accent_cyan": "#0284C7",
            "accent_contrast": "#EA580C",
            "success": "#059669",
            "success_bg": "#D1FAE5",
            "warning": "#D97706",
            "warning_bg": "#FEF3C7",
            "danger": "#DC2626",
            "danger_bg": "#FEE2E2",
            "text_main": "#111827",
            "text_muted": "#4B5563",
            "text_dim": "#9CA3AF"
        }

    if sys.platform != "win32":
        return theme

    # 2. Query AccentPalette from Windows Explorer (Official Fluent UI 8-color palette)
    found_accent = False
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent")
        pal, _ = winreg.QueryValueEx(k, "AccentPalette")
        winreg.CloseKey(k)
        if len(pal) >= 32:
            colors = ['#{:02X}{:02X}{:02X}'.format(pal[i], pal[i+1], pal[i+2]) for i in range(0, 32, 4)]
            theme["accent_cyan"] = colors[0]       # Lightest shade
            theme["primary_light"] = colors[1]     # Lighter shade
            theme["border_highlight"] = colors[2]  # Light shade / highlight
            theme["primary"] = colors[3]           # Base primary Windows accent
            theme["primary_hover"] = colors[4]     # Darker hover accent
            if len(colors) > 7:
                theme["accent_contrast"] = colors[7] # Windows contrast accent
            found_accent = True
    except Exception:
        pass

    # 3. Fallback: Query DWM AccentColor / ColorizationColor if AccentPalette was not read
    if not found_accent:
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM")
            try:
                acc, _ = winreg.QueryValueEx(k, "AccentColor")
                r = acc & 0xFF
                g = (acc >> 8) & 0xFF
                b = (acc >> 16) & 0xFF
                theme["primary"] = f"#{r:02X}{g:02X}{b:02X}"
                theme["primary_hover"] = f"#{max(0, r-30):02X}{max(0, g-30):02X}{max(0, b-30):02X}"
                theme["primary_light"] = f"#{min(255, r+50):02X}{min(255, g+50):02X}{min(255, b+50):02X}"
            except Exception:
                c_val, _ = winreg.QueryValueEx(k, "ColorizationColor")
                r = (c_val >> 16) & 0xFF
                g = (c_val >> 8) & 0xFF
                b = c_val & 0xFF
                theme["primary"] = f"#{r:02X}{g:02X}{b:02X}"
                theme["primary_hover"] = f"#{max(0, r-30):02X}{max(0, g-30):02X}{max(0, b-30):02X}"
                theme["primary_light"] = f"#{min(255, r+50):02X}{min(255, g+50):02X}{min(255, b+50):02X}"
            winreg.CloseKey(k)
        except Exception:
            pass

    # 4. Pull Win32 GetSysColor system metrics for muted text
    try:
        c = ctypes.windll.user32.GetSysColor(17) # COLOR_GRAYTEXT
        r, g, b = c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF
        gray_hex = f"#{r:02X}{g:02X}{b:02X}"
        if gray_hex not in ("#000000", "#FFFFFF"):
            theme["text_muted"] = gray_hex
    except Exception:
        pass

    return theme

THEME = load_windows_system_theme()
FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"
