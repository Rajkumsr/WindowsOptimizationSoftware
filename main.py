"""
Apex Windows Optimizer - Main Entry Point
Launches the Apex Windows Performance & Privacy Suite.
"""

import sys
import os
import ctypes

# Enable High-DPI Awareness and register AppUserModelID for Windows Taskbar
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    try:
        # Decouples process from Python host and binds taskbar button directly to our app icon
        app_id = "rajkumarpatil.apexwindowsoptimizer.pro.suite"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def main():
    # Automatically request administrative elevation so HKLM registry, WMI, and services have full permissions
    if getattr(sys, "frozen", False):
        # Standalone executable is already manifested with --uac-admin elevation
        pass
    elif sys.platform == "win32" and not is_admin() and "--no-elevate" not in sys.argv:
        try:
            script = os.path.abspath(__file__)
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
            if ret > 32:
                sys.exit(0)
        except Exception:
            pass  # Fallback to standard execution if user denies UAC prompt

    import gui_app
    gui_app.main()

if __name__ == "__main__":
    main()
