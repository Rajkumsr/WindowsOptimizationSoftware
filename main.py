"""
Apex Windows Optimizer - Main Entry Point & Automation CLI
Launches the Apex Windows Performance & Privacy Suite in either:
1. Modern Interactive Tkinter GUI Mode (default)
2. Headless Automation CLI Mode (--optimize, --cleanup, --gaming, --winget, --boost)
"""

import sys
import os
import ctypes
import argparse
from datetime import datetime

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


def run_cli_mode(args):
    """Executes requested optimization operations headlessly with live console output."""
    from core.optimizer import OptimizationEngine

    def cli_logger(message: str, level: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{level:7s}]"
        print(f"{prefix} {message}")

    print("=" * 72)
    print("      >> APEX WINDOWS OPTIMIZER PRO - AUTOMATION ENGINE <<")
    print("                  Created by Rajkumar Patil")
    print("=" * 72)

    engine = OptimizationEngine(log_callback=cli_logger)
    hw = engine.get_hardware_info()
    print(f"System: {hw.get('cpu_name', 'PC')} | RAM: {hw.get('total_ram', 'N/A')} | Chassis: {hw.get('chassis_type', 'Workstation')}")
    print("-" * 72)

    # 1. System & Privacy Optimization
    if args.optimize:
        print("\n>>> [1/4] Applying System, Privacy, & Shell Optimizations...")
        all_states = engine.detect_all_tweak_states()
        # Enable recommended optimizations
        opt_targets = {k: True for k in all_states.keys() if k != "fast_startup"}
        opt_targets["fast_startup"] = False  # False means fast startup is disabled (no phantom drain)
        c1 = engine.apply_system_performance_tweaks(opt_targets)
        c2 = engine.apply_privacy_telemetry_tweaks(opt_targets)
        c3 = engine.apply_explorer_ui_tweaks(opt_targets, deploy_to_all_profiles=True)
        engine.disable_telemetry_tasks()
        print(f"    Completed: {c1 + c2 + c3} settings optimized across all user profiles.")

    # 2. Gaming Optimizations
    if args.gaming:
        print("\n>>> [2/4] Applying Gaming & Low-Latency GPU Optimizations...")
        game_opts = {
            "enable_hags": True,
            "windowed_optimizations": True,
            "mmcss_priority": True,
            "disable_gamedvr": True,
            "enable_game_mode": True,
            "disable_mouse_acceleration": True,
            "network_gaming_latency": True,
            "reset_hpet": True,
            "disable_power_throttling": True,
            "ultimate_performance": True
        }
        count = engine.apply_gaming_tweaks(game_opts)
        print(f"    Completed: {count} gaming optimizations applied.")

    # 3. Deep Disk & Component Store Cleanup
    if args.cleanup:
        print("\n>>> [3/4] Running Deep Disk Cleanup & WinSxS Component Reduction...")
        targets = [t["id"] for t in engine.get_cleanup_targets()]
        freed_bytes, freed_str = engine.execute_cleanup(targets)
        print(f"    Completed: Reclaimed {freed_str} of disk storage.")

    # 4. Instant System Boost
    if args.boost:
        print("\n>>> Running 1-Click Instant System Boost...")
        ok, summary = engine.quick_boost()
        print(f"    Completed: {summary}")

    # 5. Software Updates via WinGet
    if args.winget:
        print("\n>>> [4/4] Upgrading Installed Applications via WinGet...")
        c, out = engine.run_winget_upgrade_all()
        print(f"    WinGet completed with status code {c}.")

    print("\n" + "=" * 72)
    print("  [SUCCESS] All requested optimization routines completed successfully.")
    print("=" * 72)

    # Optional System Restart
    if args.restart:
        print("\nRestart requested. Rebooting system in 10 seconds (shutdown /r /t 10)...")
        os.system("shutdown.exe /r /t 10 /c \"Apex Windows Optimizer: Restarting to finalize changes.\"")


def main():
    parser = argparse.ArgumentParser(
        description="Apex Windows Optimizer Pro - Advanced System Tuning & Automation Suite",
        add_help=True
    )
    parser.add_argument("--optimize", "-o", action="store_true", help="Apply system performance, privacy, and Explorer tweaks headlessly.")
    parser.add_argument("--cleanup", "-c", action="store_true", help="Execute deep disk cleanup and WinSxS component store purge via DISM.")
    parser.add_argument("--gaming", "-g", action="store_true", help="Apply gaming, GPU, and low-latency network tweaks.")
    parser.add_argument("--winget", "-w", action="store_true", help="Update all installed software applications via WinGet.")
    parser.add_argument("--boost", "-b", action="store_true", help="Execute instant system boost (RAM purge + temp cache purge).")
    parser.add_argument("--restart", "-r", action="store_true", help="Restart the computer after requested operations complete.")
    parser.add_argument("--no-elevate", action="store_true", help="Bypass automatic administrative UAC elevation prompt.")
    parser.add_argument("--gui", action="store_true", help="Explicitly launch the interactive graphical user interface.")

    args, unknown = parser.parse_known_args()

    # Automatically request administrative elevation so HKLM registry, WMI, and services have full permissions
    if getattr(sys, "frozen", False):
        # Standalone executable is already manifested with --uac-admin elevation
        pass
    elif sys.platform == "win32" and not is_admin() and not args.no_elevate:
        try:
            script = os.path.abspath(__file__)
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
            if ret > 32:
                sys.exit(0)
        except Exception:
            pass  # Fallback to standard execution if user denies UAC prompt

    # If non-interactive operation switches are specified, run headlessly without GUI
    if args.optimize or args.cleanup or args.gaming or args.winget or args.boost:
        run_cli_mode(args)
        sys.exit(0)

    # Otherwise, launch modern interactive Tkinter GUI
    from ui import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()
