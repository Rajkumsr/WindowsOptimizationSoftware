"""
Apex Windows Optimizer - Base Engine & Low-Level Win32 Primitives
Provides logging, administrative privilege checks, process execution,
and direct registry manipulation (read, write, delete, and multi-user hive mounting).
"""

import os
import sys
import subprocess
import winreg
import ctypes
import tempfile
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple, Any

# Windows creation flag to completely suppress console window spawning
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


class BaseEngine:
    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        """
        log_callback: function(message: str, level: str) where level in ['INFO', 'SUCCESS', 'WARNING', 'ERROR']
        """
        self.log_callback = log_callback
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log_path = os.path.join(self.log_dir, f"ApexOptimizer_{timestamp}.log")
        self.is_cancelling = False

        # In-memory hardware cache to prevent repeated subprocess execution during live telemetry loops
        self._cached_chassis_type = None
        self._cached_is_laptop = None
        self._cached_battery_specs = None
        self._last_battery_specs_time = 0
        self._cached_battery_wmi_status = None
        self._last_battery_wmi_time = 0
        self._cached_gpu_telemetry = None
        self._last_gpu_telemetry_time = 0
        self._cached_cpu_pct = 0.0
        self._last_cpu_time = 0.0
        self._prev_idle_time = 0
        self._prev_kernel_time = 0
        self._prev_user_time = 0

        # Prime baseline for CPU measurement
        try:
            import psutil
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

    def log(self, message: str, level: str = "INFO"):
        formatted_time = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{formatted_time}] [{level}] {message}"
        try:
            with open(self.session_log_path, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception:
            pass
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(log_entry)

    @staticmethod
    def is_admin() -> bool:
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    @staticmethod
    def relaunch_as_admin():
        if sys.platform == 'win32':
            script = os.path.abspath(sys.argv[0])
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
            sys.exit(0)


    # -------------------------------------------------------------
    # PowerShell and Process Helpers
    # -------------------------------------------------------------
    def run_cmd(self, command: str, ignore_errors: bool = True) -> Tuple[int, str]:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=CREATE_NO_WINDOW
            )
            out = result.stdout.strip()
            err = result.stderr.strip()
            full = f"{out}\n{err}".strip()
            return result.returncode, full
        except Exception as e:
            if not ignore_errors:
                self.log(f"Command execution error: {e}", "ERROR")
            return -1, str(e)

    def run_ps(self, script: str) -> Tuple[int, str]:
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                text=True,
                timeout=180,
                creationflags=CREATE_NO_WINDOW
            )
            full = f"{result.stdout.strip()}\n{result.stderr.strip()}".strip()
            return result.returncode, full
        except Exception as e:
            return -1, str(e)

    def run_elevated_ps(self, script: str) -> Tuple[int, str]:
        """
        Executes a PowerShell script block with elevated Administrator privileges
        using the Windows UAC consent interface (Start-Process -Verb RunAs).
        Allows seamless execution of HKLM/WMI operations even if the main GUI
        was launched from an un-elevated terminal.
        """
        try:
            script_file = os.path.join(tempfile.gettempdir(), f"apex_elev_{datetime.now().strftime('%H%M%S')}.ps1")
            with open(script_file, "w", encoding="utf-8") as f:
                f.write(script)

            launcher_cmd = f"Start-Process powershell.exe -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"{script_file}\"'"
            c, out = self.run_ps(launcher_cmd)
            try:
                if os.path.exists(script_file):
                    os.remove(script_file)
            except Exception:
                pass
            return c, out
        except Exception as e:
            return -1, str(e)


    # -------------------------------------------------------------
    # Registry Management Helpers (Read, Write, Delete, Query)
    # -------------------------------------------------------------
    def get_reg(self, root, subkey: str, name: str, default=None) -> Any:
        """Reads a registry value safely."""
        try:
            key = winreg.OpenKey(root, subkey, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            val, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return val
        except Exception:
            return default

    def reg_key_exists(self, root, subkey: str) -> bool:
        """Checks if a registry key exists."""
        try:
            key = winreg.OpenKey(root, subkey, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def set_reg(self, root, subkey: str, name: str, value, val_type=winreg.REG_DWORD) -> bool:
        """Sets a registry value safely."""
        try:
            key = winreg.CreateKeyEx(root, subkey, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
            winreg.SetValueEx(key, name, 0, val_type, value)
            winreg.CloseKey(key)
            return True
        except Exception:
            hive = "HKLM" if root == winreg.HKEY_LOCAL_MACHINE else "HKCU"
            type_str = "REG_DWORD" if val_type == winreg.REG_DWORD else "REG_SZ"
            cmd = f'reg.exe add "{hive}\\{subkey}" /v "{name}" /t {type_str} /d "{value}" /f'
            code, out = self.run_cmd(cmd)
            if code != 0:
                self.log(f"Failed to set registry value {hive}\\{subkey}\\{name}: {out}", "ERROR")
            return code == 0

    def delete_reg_value(self, root, subkey: str, name: str) -> bool:
        """Deletes a single registry value."""
        try:
            key = winreg.OpenKey(root, subkey, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)
            return True
        except Exception:
            hive = "HKLM" if root == winreg.HKEY_LOCAL_MACHINE else "HKCU"
            code, out = self.run_cmd(f'reg.exe delete "{hive}\\{subkey}" /v "{name}" /f')
            if code != 0:
                self.log(f"Failed to delete registry value {hive}\\{subkey}\\{name}: {out}", "ERROR")
            return code == 0



    # -------------------------------------------------------------
    # Multi-User Hive Deployment (`C:\Users\Default\NTUSER.DAT`)
    # -------------------------------------------------------------
    def apply_to_all_user_hives(self, apply_fn: Callable[[str], None]):
        """
        Applies per-user registry tweaks across:
        1. HKCU (Current active user)
        2. All currently loaded user profiles in HKU
        3. The Default User profile hive (C:\\Users\\Default\\NTUSER.DAT) so future users inherit it!
        """
        # 1. Apply to HKCU
        apply_fn("HKCU")

        # 2. Iterate over loaded user hives in HKU
        try:
            hku = winreg.OpenKey(winreg.HKEY_USERS, "")
            num_subkeys = winreg.QueryInfoKey(hku)[0]
            for i in range(num_subkeys):
                sid = winreg.EnumKey(hku, i)
                # Ignore system / template keys
                if not sid.startswith("S-1-5-21-") or sid.endswith("_Classes"):
                    continue
                apply_fn(f"HKU\\{sid}")
            winreg.CloseKey(hku)
        except Exception:
            pass

        # 3. Mount Default User Template
        default_hive_path = os.path.expandvars(r"%SystemDrive%\Users\Default\NTUSER.DAT")
        if os.path.exists(default_hive_path) and self.is_admin():
            self.log("Mounting Default User Hive to apply settings to future user accounts...", "INFO")
            load_code, _ = self.run_cmd(f'reg.exe load "HKU\\APEX_DEFAULT" "{default_hive_path}"')
            if load_code == 0:
                try:
                    apply_fn("HKU\\APEX_DEFAULT")
                finally:
                    # Always unmount cleanly
                    self.run_cmd('reg.exe unload "HKU\\APEX_DEFAULT"')
                self.log("Default User Hive unmounted successfully.", "SUCCESS")

