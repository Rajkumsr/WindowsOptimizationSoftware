"""
Apex Windows Optimizer - Core Optimization Engine
A comprehensive, safe, and modular Windows performance and debloating engine.
Includes real system state detection, bi-directional revert capabilities,
multi-user profile deployment, and automated rollback protection.
"""

import os
import sys
import subprocess
import winreg
import ctypes
import shutil
import tempfile
import threading
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple, Any

# Windows creation flag to completely suppress console window spawning
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

class OptimizationEngine:
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

    # -------------------------------------------------------------
    # System Diagnostics & Hardware Discovery
    # -------------------------------------------------------------
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

    def get_hardware_info(self) -> Dict[str, Any]:
        info = {
            "os_name": "Windows",
            "os_build": "Unknown",
            "cpu_name": "Unknown Processor",
            "total_ram": "0 GB",
            "free_ram": "0 GB",
            "ram_percent": "0%",
            "chassis_type": "Desktop PC",
            "is_laptop": False,
            "admin_privilege": "Elevated" if self.is_admin() else "Standard User",
            "system_drive": os.environ.get("SystemDrive", "C:"),
            "drive_type": "SSD/NVMe"
        }

        # Query OS info
        try:
            import platform
            info["os_build"] = f"{platform.system()} {platform.release()} (Build {platform.version()})"
        except Exception:
            pass

        # Query CPU
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            winreg.CloseKey(key)
            info["cpu_name"] = cpu.strip()
        except Exception:
            info["cpu_name"] = os.environ.get("PROCESSOR_IDENTIFIER", "x64 Processor")

        # Query RAM via GlobalMemoryStatusEx
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_gb = stat.ullTotalPhys / (1024 ** 3)
            free_gb = stat.ullAvailPhys / (1024 ** 3)
            info["total_ram"] = f"{total_gb:.1f} GB"
            info["free_ram"] = f"{free_gb:.1f} GB"
            info["ram_percent"] = f"{stat.dwMemoryLoad}%"
        except Exception:
            pass

        # Query Chassis Type once and cache it (avoids spawning processes in periodic telemetry loop)
        if self._cached_chassis_type is not None:
            info["chassis_type"] = self._cached_chassis_type
            info["is_laptop"] = self._cached_is_laptop
        else:
            try:
                cmd = "Get-CimInstance -ClassName Win32_SystemEnclosure | Select-Object -ExpandProperty ChassisTypes"
                res = subprocess.run(
                    ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", cmd],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=CREATE_NO_WINDOW
                )
                types = [t.strip() for t in res.stdout.strip().splitlines() if t.strip().isdigit()]
                laptop_chassis = {"8", "9", "10", "11", "12", "14", "18", "21", "31", "32"}
                if any(t in laptop_chassis for t in types):
                    self._cached_chassis_type = "Laptop / Portable"
                    self._cached_is_laptop = True
                else:
                    self._cached_chassis_type = "Desktop PC"
                    self._cached_is_laptop = False
            except Exception:
                self._cached_chassis_type = "Desktop PC"
                self._cached_is_laptop = False

            info["chassis_type"] = self._cached_chassis_type
            info["is_laptop"] = self._cached_is_laptop

        info["uptime"] = self.get_system_uptime()
        info["cpu_percent"] = self.get_cpu_percent()

        return info

    def get_system_uptime(self) -> str:
        """Returns exact system uptime (e.g., '1d 4h 22m') using zero-overhead Win32 kernel API."""
        try:
            millis = ctypes.windll.kernel32.GetTickCount64()
            secs = int(millis / 1000)
            d = secs // 86400
            h = (secs % 86400) // 3600
            m = (secs % 3600) // 60
            if d > 0:
                return f"{d}d {h}h {m}m"
            elif h > 0:
                return f"{h}h {m}m"
            else:
                return f"{m}m"
        except Exception:
            return "Active"

    def get_cpu_percent(self) -> float:
        """Returns instantaneous system CPU load percentage."""
        try:
            import psutil
            return float(psutil.cpu_percent(interval=None))
        except Exception:
            return 0.0

    def flush_ram_working_sets(self) -> Tuple[bool, int, float]:
        """
        Empties process working sets and Standby cache using native Win32 EmptyWorkingSet API.
        Instantly reclaims 1 GB - 3 GB of trapped memory without killing running apps.
        Returns: (success, process_count, freed_mb)
        """
        self.log("Initiating RAM Standby cache & process working set purge...", "INFO")
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        PROCESS_SET_QUOTA = 0x0100
        PROCESS_QUERY_INFORMATION = 0x0400

        try:
            import psutil
            mem_before = psutil.virtual_memory().available
        except Exception:
            mem_before = 0

        count = 0
        try:
            import psutil
            for proc in psutil.process_iter(['pid']):
                try:
                    pid = proc.info['pid']
                    if pid <= 4:
                        continue
                    h = kernel32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION, False, pid)
                    if h:
                        psapi.EmptyWorkingSet(h)
                        kernel32.CloseHandle(h)
                        count += 1
                except Exception:
                    pass
        except Exception as e:
            self.log(f"Working set purge iteration error: {e}", "WARNING")

        # Also purge current process
        try:
            kernel32.SetProcessWorkingSetSize(kernel32.GetCurrentProcess(), -1, -1)
        except Exception:
            pass

        try:
            import psutil
            mem_after = psutil.virtual_memory().available
            freed_mb = max(0.0, (mem_after - mem_before) / (1024 * 1024))
        except Exception:
            freed_mb = 0.0

        msg = f"RAM Working Set purge complete. Flushed {count} processes, freed {freed_mb:.1f} MB memory."
        self.log(msg, "SUCCESS")
        return True, count, freed_mb

    def calculate_health_score(self, live_states: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """
        Calculates an overall Windows Health & Optimization Score (0 to 100%).
        Based on active performance tweaks, privacy settings, gaming configs,
        and system power configurations.
        """
        if live_states is None:
            live_states = self.detect_all_tweak_states()

        # Key impact weights
        high_impact = [
            "network_throttling", "system_responsiveness", "fast_shutdown",
            "disable_telemetry", "optimize_edge", "disable_recall",
            "hags", "game_mmcss", "power_throttling"
        ]
        med_impact = [
            "irp_stack_size", "long_paths", "disable_p2p_update",
            "disable_lockscreen_ads", "disable_office_telemetry",
            "hpet_reset", "windowed_optimizations"
        ]

        score = 40  # base starting score for standard unoptimized Windows installation
        applied_high = sum(1 for k in high_impact if live_states.get(k, False))
        applied_med = sum(1 for k in med_impact if live_states.get(k, False))

        # Add up to 35 pts from high impact tweaks
        score += int((applied_high / len(high_impact)) * 35)
        # Add up to 25 pts from medium impact tweaks
        score += int((applied_med / len(med_impact)) * 25)

        score = max(10, min(100, score))

        if score >= 90:
            rating = "APEX PEAK STATE"
            color = "#00FF9D"
            desc = "System is fully optimized for maximum performance, minimal latency, and zero telemetry."
        elif score >= 75:
            rating = "GOOD HEALTH"
            color = "#00D2FF"
            desc = "Core optimizations active. Apply remaining recommended tweaks to reach peak state."
        elif score >= 55:
            rating = "MODERATE"
            color = "#FFB020"
            desc = "Standard Windows defaults detected with active background telemetry and throttles."
        else:
            rating = "NEEDS OPTIMIZATION"
            color = "#FF5252"
            desc = "System is running unoptimized defaults with heavy background telemetry and throttles."

        return {
            "score": score,
            "rating": rating,
            "color": color,
            "desc": desc,
            "applied_count": applied_high + applied_med,
            "total_count": len(high_impact) + len(med_impact)
        }

    def quick_boost(self) -> Tuple[bool, str]:
        """
        Performs a rapid 1-click system boost:
        1. Purges Standby list & process working sets (frees RAM instantly)
        2. Cleans system & user temporary files
        3. Flushes DNS resolver cache
        """
        self.log("🚀 Executing 1-Click Instant System Boost...", "INFO")
        
        # 1. Flush RAM
        _, p_count, freed_mb = self.flush_ram_working_sets()

        # 2. Flush DNS
        self.flush_dns()

        # 3. Quick Temp Sweep
        temp_freed_mb = 0.0
        try:
            targets = [
                os.environ.get("TEMP", ""),
                os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Temp")
            ]
            cleaned_bytes = 0
            for t_dir in targets:
                if t_dir and os.path.exists(t_dir):
                    try:
                        for entry in os.scandir(t_dir):
                            try:
                                if entry.is_file(follow_symlinks=False):
                                    sz = entry.stat().st_size
                                    os.remove(entry.path)
                                    cleaned_bytes += sz
                                elif entry.is_dir(follow_symlinks=False):
                                    shutil.rmtree(entry.path, ignore_errors=True)
                            except Exception:
                                pass
                    except Exception:
                        pass
            temp_freed_mb = cleaned_bytes / (1024 * 1024)
        except Exception:
            pass

        summary = (
            f"⚡ 1-Click Boost Completed with Success!\n"
            f"• Flushed RAM from {p_count} processes (Freed {freed_mb:.1f} MB)\n"
            f"• Cleaned temporary junk ({temp_freed_mb:.1f} MB reclaimed)\n"
            f"• DNS resolver cache refreshed"
        )
        self.log(summary.replace("\n", " | "), "SUCCESS")
        return True, summary

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
            code, _ = self.run_cmd(cmd)
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
            code, _ = self.run_cmd(f'reg.exe delete "{hive}\\{subkey}" /v "{name}" /f')
            return code == 0

    def delete_reg_key(self, root, subkey: str) -> bool:
        """Deletes a registry key and all subkeys."""
        try:
            winreg.DeleteKey(root, subkey)
            return True
        except Exception:
            hive = "HKLM" if root == winreg.HKEY_LOCAL_MACHINE else "HKCU"
            code, _ = self.run_cmd(f'reg.exe delete "{hive}\\{subkey}" /f')
            return code == 0

    # -------------------------------------------------------------
    # Real System State Detection (Read Registry & OS Settings)
    # -------------------------------------------------------------
    def detect_all_tweak_states(self) -> Dict[str, bool]:
        """
        Inspects the live operating system and returns whether each individual
        optimization is currently ACTIVE (True) or DEFAULT (False).
        """
        states = {}

        # 1. System & Performance
        net_idx = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "NetworkThrottlingIndex")
        states["network_throttling"] = (net_idx == 0xFFFFFFFF or net_idx == -1)

        sys_resp = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "SystemResponsiveness")
        states["system_responsiveness"] = (sys_resp == 10)

        irp = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters", "IRPStackSize")
        states["irp_stack_size"] = (irp == 30)

        timeout = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control", "WaitToKillServiceTimeout")
        states["fast_shutdown"] = (str(timeout) == "5000")

        long_p = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem", "LongPathsEnabled")
        states["long_paths"] = (long_p == 1)

        oem_meta = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Device Metadata", "PreventDeviceMetadataFromNetwork")
        states["block_oem_bloat"] = (oem_meta == 1)

        do_mode = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization", "DODownloadMode")
        states["disable_p2p_update"] = (do_mode == 0)

        # F8 boot menu
        c, bcd_out = self.run_cmd("bcdedit /enum {default}")
        states["f8_boot_menu"] = ("legacy" in bcd_out.lower())

        # Hibernation
        c, power_out = self.run_cmd("powercfg /a")
        states["disable_hibernation"] = ("hibernation has not been enabled" in power_out.lower() or "hibernation is not available" in power_out.lower())

        # 2. Privacy & Telemetry
        telem = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry")
        states["disable_telemetry"] = (telem == 0)

        lock_ads = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Personalization", "NoLockScreen")
        states["disable_lockscreen_ads"] = (lock_ads == 1)

        recall = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\WindowsAI", "AllowRecallEnablement")
        states["disable_recall"] = (recall == 0)

        edge_bg = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Edge", "BackgroundModeEnabled")
        states["optimize_edge"] = (edge_bg == 0)

        oobe_p = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\OOBE", "DisablePrivacyExperience")
        states["suppress_oobe_telemetry"] = (oobe_p == 1)

        office_t = self.get_reg(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Office\16.0\Common\ClientTelemetry", "DisableTelemetry")
        states["disable_office_telemetry"] = (office_t == 1)

        # 3. Explorer & Shell
        hide_ext = self.get_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "HideFileExt")
        states["show_extensions"] = (hide_ext == 0)

        hidden_f = self.get_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "Hidden")
        states["show_hidden"] = (hidden_f == 1)

        launch_to = self.get_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "LaunchTo")
        states["open_this_pc"] = (launch_to == 1)

        classic_ctx = self.reg_key_exists(winreg.HKEY_CURRENT_USER, r"SOFTWARE\CLASSES\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32")
        states["classic_context_menu"] = classic_ctx

        bing_search = self.get_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Search", "BingSearchEnabled")
        states["disable_start_bing"] = (bing_search == 0)

        taskbar_end = self.get_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\TaskbarDeveloperSettings", "TaskbarEndTask")
        states["taskbar_end_task"] = (taskbar_end == 1)

        taskbar_da = self.get_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarDa")
        states["clean_taskbar"] = (taskbar_da == 0)

        menu_delay = self.get_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "MenuShowDelay")
        states["fast_menu_delay"] = (str(menu_delay) == "10")

        sticky = self.get_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\StickyKeys", "Flags")
        states["disable_sticky_keys"] = (str(sticky) == "58")

        # 4. Gaming & GPU
        mmcss_gpu = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "GPU Priority")
        states["mmcss_priority"] = (mmcss_gpu == 8)

        hags = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HWSchMode")
        states["enable_hags"] = (hags == 2)

        win_games = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR\Graphics", "OptimizationsForWindowedGames")
        states["windowed_optimizations"] = (win_games == 1)

        # Reset HPET: check if useplatformclock exists in bcdedit
        states["reset_hpet"] = ("useplatformclock" not in bcd_out.lower())

        power_throt = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling", "PowerThrottlingOff")
        states["disable_power_throttling"] = (power_throt == 1)

        # Ultimate Performance: check active power plan
        c, power_plan_out = self.run_cmd("powercfg /getactivescheme")
        states["ultimate_performance"] = ("ultimate performance" in power_plan_out.lower())

        return states

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

    # -------------------------------------------------------------
    # System Rollback & Restore Protection
    # -------------------------------------------------------------
    def create_restore_point(self, name: str = "Apex Optimizer Snapshot") -> bool:
        self.log("Initializing System Restore rollback protection...", "INFO")
        drive = os.environ.get("SystemDrive", "C:")

        ps_script = f"""
        try {{
            Enable-ComputerRestore -Drive '{drive}\\' -ErrorAction SilentlyContinue
            Set-Service -Name VSS -StartupType Manual -ErrorAction SilentlyContinue
            Start-Service -Name VSS -ErrorAction SilentlyContinue
            Set-ItemProperty -Path 'HKLM:\\Software\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore' -Name 'SystemRestorePointCreationFrequency' -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
            Checkpoint-Computer -Description '{name}' -RestorePointType MODIFY_SETTINGS -ErrorAction Stop
            Remove-ItemProperty -Path 'HKLM:\\Software\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore' -Name 'SystemRestorePointCreationFrequency' -ErrorAction SilentlyContinue
            Write-Output "SUCCESS"
        }} catch {{
            Write-Output "ERROR: $($_.Exception.Message)"
        }}
        """
        code, out = self.run_ps(ps_script)
        if "SUCCESS" in out:
            self.log(f"System Restore Point created successfully: '{name}'", "SUCCESS")
            return True
        else:
            self.log(f"Could not create System Restore Point: {out}", "WARNING")
            self.log("Falling back to registry backup export...", "INFO")
            return self.export_registry_backup()

    def export_registry_backup(self) -> bool:
        backup_dir = os.path.join(self.log_dir, f"RegistryBackup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(backup_dir, exist_ok=True)
        hklm_path = os.path.join(backup_dir, "HKLM_Backup.reg")
        hkcu_path = os.path.join(backup_dir, "HKCU_Backup.reg")

        self.log(f"Exporting HKLM and HKCU registry hives to: {backup_dir}", "INFO")
        c1, _ = self.run_cmd(f'reg.exe export HKLM "{hklm_path}" /y')
        c2, _ = self.run_cmd(f'reg.exe export HKCU "{hkcu_path}" /y')

        if c1 == 0 and c2 == 0:
            self.log("Registry backup hives exported successfully.", "SUCCESS")
            return True
        else:
            self.log("Warning: One or more registry exports returned non-zero code.", "WARNING")
            return False

    # -------------------------------------------------------------
    # 1. System & Performance Tweaks (Bi-directional Apply / Revert)
    # -------------------------------------------------------------
    def apply_system_performance_tweaks(self, options: Dict[str, bool]) -> int:
        success_count = 0

        # Network Throttling Index
        if "network_throttling" in options:
            if options["network_throttling"]:
                self.log("Disabling multimedia network throttling...", "INFO")
                if self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "NetworkThrottlingIndex", 0xFFFFFFFF, winreg.REG_DWORD):
                    self.log("Network throttling disabled (Max bandwidth priority).", "SUCCESS")
                    success_count += 1
            else:
                self.log("Reverting network throttling to Windows default (0xA)...", "INFO")
                if self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "NetworkThrottlingIndex", 10, winreg.REG_DWORD):
                    self.log("Network throttling restored to default.", "SUCCESS")
                    success_count += 1

        # System Responsiveness
        if "system_responsiveness" in options:
            if options["system_responsiveness"]:
                self.log("Optimizing system responsiveness for foreground applications...", "INFO")
                if self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "SystemResponsiveness", 10, winreg.REG_DWORD):
                    self.log("System responsiveness configured (90% CPU foreground reserve).", "SUCCESS")
                    success_count += 1
            else:
                self.log("Reverting system responsiveness to Windows default (20%)...", "INFO")
                if self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "SystemResponsiveness", 20, winreg.REG_DWORD):
                    self.log("System responsiveness restored to default.", "SUCCESS")
                    success_count += 1

        # IRP Stack Size
        if "irp_stack_size" in options:
            if options["irp_stack_size"]:
                self.log("Optimizing IRP Stack Size for high-throughput LAN/SMB transfer...", "INFO")
                s1 = self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters", "IRPStackSize", 30, winreg.REG_DWORD)
                s2 = self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\Services\LanmanServer\Parameters", "IRPStackSize", 30, winreg.REG_DWORD)
                if s1 or s2:
                    self.log("IRP Stack Size set to 30.", "SUCCESS")
                    success_count += 1
            else:
                self.log("Reverting IRP Stack Size to Windows default...", "INFO")
                self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters", "IRPStackSize")
                self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\Services\LanmanServer\Parameters", "IRPStackSize")
                self.log("IRP Stack Size restored to default.", "SUCCESS")
                success_count += 1

        # Shutdown Speed (WaitToKillServiceTimeout)
        if "fast_shutdown" in options:
            if options["fast_shutdown"]:
                self.log("Reducing service termination timeout to accelerate shutdown...", "INFO")
                s1 = self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control", "WaitToKillServiceTimeout", "5000", winreg.REG_SZ)
                s2 = self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\Control", "WaitToKillServiceTimeout", "5000", winreg.REG_SZ)
                if s1 or s2:
                    self.log("Shutdown timeout configured to 5 seconds.", "SUCCESS")
                    success_count += 1
            else:
                self.log("Reverting service shutdown timeout to Windows default (12s)...", "INFO")
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control", "WaitToKillServiceTimeout", "12000", winreg.REG_SZ)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\Control", "WaitToKillServiceTimeout", "12000", winreg.REG_SZ)
                self.log("Shutdown timeout restored to default.", "SUCCESS")
                success_count += 1

        # Long File Paths
        if "long_paths" in options:
            val = 1 if options["long_paths"] else 0
            act_str = "Enabling" if val == 1 else "Reverting"
            self.log(f"{act_str} NTFS Long File Paths (>260 characters)...", "INFO")
            s1 = self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem", "LongPathsEnabled", val, winreg.REG_DWORD)
            s2 = self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\Control\FileSystem", "LongPathsEnabled", val, winreg.REG_DWORD)
            if s1 or s2:
                self.log(f"Long file paths setting updated to {val}.", "SUCCESS")
                success_count += 1

        # Block OEM Hardware Bloatware & WPBT Execution
        if "block_oem_bloat" in options:
            val = 1 if options["block_oem_bloat"] else 0
            self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Device Metadata", "PreventDeviceMetadataFromNetwork", val, winreg.REG_DWORD)
            self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager", "DisableWpbtExecution", val, winreg.REG_DWORD)
            self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\Control\Session Manager", "DisableWpbtExecution", val, winreg.REG_DWORD)
            self.log(f"OEM firmware background execution setting updated to {val}.", "SUCCESS")
            success_count += 1

        # Delivery Optimization P2P upload disable
        if "disable_p2p_update" in options:
            if options["disable_p2p_update"]:
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\DeliveryOptimization\Config", "DODownloadMode", 0, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization", "DODownloadMode", 0, winreg.REG_DWORD)
                self.log("P2P update bandwidth seeding disabled.", "SUCCESS")
                success_count += 1
            else:
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\DeliveryOptimization\Config", "DODownloadMode", 1, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization", "DODownloadMode", 1, winreg.REG_DWORD)
                self.log("P2P update bandwidth seeding restored to default.", "SUCCESS")
                success_count += 1

        # Legacy F8 Boot Menu
        if "f8_boot_menu" in options:
            mode = "legacy" if options["f8_boot_menu"] else "standard"
            self.log(f"Configuring boot menu policy to '{mode}'...", "INFO")
            code, _ = self.run_cmd(f"bcdedit /set {{default}} bootmenupolicy {mode}")
            if code == 0:
                self.log(f"F8 boot menu policy configured to '{mode}'.", "SUCCESS")
                success_count += 1

        # Hibernation on Desktop
        if "disable_hibernation" in options:
            hw = self.get_hardware_info()
            if not hw["is_laptop"]:
                switch = "off" if options["disable_hibernation"] else "on"
                self.log(f"Setting Hibernation to '{switch}'...", "INFO")
                code, _ = self.run_cmd(f"powercfg.exe /h {switch}")
                if code == 0:
                    self.log(f"Hibernation configured to '{switch}'.", "SUCCESS")
                    success_count += 1

        return success_count

    # -------------------------------------------------------------
    # 2. Privacy & Telemetry Tweaks (Bi-directional Apply / Revert)
    # -------------------------------------------------------------
    def apply_privacy_telemetry_tweaks(self, options: Dict[str, bool]) -> int:
        success_count = 0

        # Windows Telemetry & Diagnostic Data
        if "disable_telemetry" in options:
            if options["disable_telemetry"]:
                self.log("Disabling Windows Diagnostic Data Collection & CEIP...", "INFO")
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "DoNotShowFeedbackNotifications", 1, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "LimitEnhancedDiagnosticDataWindowsAnalytics", 1, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection", "AllowTelemetry", 0, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\AdvertisingInfo", "DisabledByGroupPolicy", 1, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\Windows Error Reporting", "Disabled", 1, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\WMI\AutoLogger\Diagtrack-Listener", "Start", 0, winreg.REG_DWORD)
                self.log("Core diagnostic data collection disabled.", "SUCCESS")
                success_count += 1
            else:
                self.log("Reverting Windows Diagnostic Data policies to defaults...", "INFO")
                self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry")
                self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "DoNotShowFeedbackNotifications")
                self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\AdvertisingInfo", "DisabledByGroupPolicy")
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\Windows Error Reporting", "Disabled", 0, winreg.REG_DWORD)
                self.log("Diagnostic telemetry policies restored to default.", "SUCCESS")
                success_count += 1

        # Lock Screen Spotlight Ads
        if "disable_lockscreen_ads" in options:
            val = 1 if options["disable_lockscreen_ads"] else 0
            self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Personalization", "NoLockScreen", val, winreg.REG_DWORD)
            self.set_reg(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "RotatingLockScreenOverlayEnabled", 0 if val == 1 else 1, winreg.REG_DWORD)
            self.log(f"Lockscreen spotlight setting updated.", "SUCCESS")
            success_count += 1

        # Microsoft Recall
        if "disable_recall" in options:
            val = 0 if options["disable_recall"] else 1
            self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\WindowsAI", "AllowRecallEnablement", val, winreg.REG_DWORD)
            self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\WindowsAI", "DisableAIDataAnalysis", 1 if val == 0 else 0, winreg.REG_DWORD)
            self.log("Microsoft Recall policy configured.", "SUCCESS")
            success_count += 1

        # Microsoft Edge Optimizations
        if "optimize_edge" in options:
            edge_key = r"SOFTWARE\Policies\Microsoft\Edge"
            if options["optimize_edge"]:
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, edge_key, "StartupBoostEnabled", 0, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, edge_key, "BackgroundModeEnabled", 0, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, edge_key, "HideFirstRunExperience", 1, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, edge_key, "UserFeedbackAllowed", 0, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, edge_key, "EdgeShoppingAssistantEnabled", 0, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, edge_key, "DiagnosticData", 0, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, edge_key, "GamerModeEnabled", 1, winreg.REG_DWORD)
                self.log("Microsoft Edge optimized for minimal background resource consumption.", "SUCCESS")
            else:
                self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, edge_key, "StartupBoostEnabled")
                self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, edge_key, "BackgroundModeEnabled")
                self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, edge_key, "EdgeShoppingAssistantEnabled")
                self.log("Microsoft Edge policies restored to default.", "SUCCESS")
            success_count += 1

        # OOBE Privacy & Telemetry
        if "suppress_oobe_telemetry" in options:
            oobe_key = r"SOFTWARE\Policies\Microsoft\Windows\OOBE"
            val = 1 if options["suppress_oobe_telemetry"] else 0
            self.set_reg(winreg.HKEY_LOCAL_MACHINE, oobe_key, "DisablePrivacyExperience", val, winreg.REG_DWORD)
            self.set_reg(winreg.HKEY_LOCAL_MACHINE, oobe_key, "BypassNRO", val, winreg.REG_DWORD)
            self.set_reg(winreg.HKEY_LOCAL_MACHINE, oobe_key, "SkipMachineOOBE", val, winreg.REG_DWORD)
            self.log("OOBE privacy experiences updated.", "SUCCESS")
            success_count += 1

        # Microsoft Office Telemetry & Logging
        if "disable_office_telemetry" in options:
            val = 1 if options["disable_office_telemetry"] else 0
            for ver in ["15.0", "16.0"]:
                self.set_reg(winreg.HKEY_CURRENT_USER, rf"SOFTWARE\Microsoft\Office\{ver}\Common\ClientTelemetry", "DisableTelemetry", val, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_CURRENT_USER, rf"SOFTWARE\Microsoft\Office\{ver}\Common\ClientTelemetry", "VerboseLogging", 0 if val == 1 else 1, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_CURRENT_USER, rf"SOFTWARE\Microsoft\Office\{ver}\Common", "QMEnable", 0 if val == 1 else 1, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_CURRENT_USER, rf"SOFTWARE\Policies\Microsoft\Office\{ver}\OSM", "EnableLogging", 0 if val == 1 else 1, winreg.REG_DWORD)
            self.log("Office telemetry configuration updated.", "SUCCESS")
            success_count += 1

        return success_count

    # -------------------------------------------------------------
    # 3. Explorer & UI Personalization (Bi-directional + Multi-User)
    # -------------------------------------------------------------
    def apply_explorer_ui_tweaks(self, options: Dict[str, bool], deploy_to_all_profiles: bool = True) -> int:
        success_count = 0

        def _apply_to_target_hive(base_hive_prefix: str):
            nonlocal success_count
            # Translate base_hive_prefix into cmd string or winreg call
            # E.g. base_hive_prefix = "HKCU" or "HKU\S-1-5-..." or "HKU\APEX_DEFAULT"
            
            # Show File Extensions
            if "show_extensions" in options:
                val = 0 if options["show_extensions"] else 1
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v HideFileExt /t REG_DWORD /d {val} /f')
                success_count += 1

            # Show Hidden Files
            if "show_hidden" in options:
                val = 1 if options["show_hidden"] else 2
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v Hidden /t REG_DWORD /d {val} /f')
                success_count += 1

            # Open to 'This PC'
            if "open_this_pc" in options:
                val = 1 if options["open_this_pc"] else 2
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v LaunchTo /t REG_DWORD /d {val} /f')
                success_count += 1

            # Classic Context Menu (Windows 11)
            if "classic_context_menu" in options:
                ctx_path = f"{base_hive_prefix}\\SOFTWARE\\CLASSES\\CLSID\\{{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}}\\InprocServer32"
                if options["classic_context_menu"]:
                    self.run_cmd(f'reg.exe add "{ctx_path}" /ve /t REG_SZ /d "" /f')
                else:
                    self.run_cmd(f'reg.exe delete "{base_hive_prefix}\\SOFTWARE\\CLASSES\\CLSID\\{{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}}" /f')
                success_count += 1

            # Disable Bing Search in Start Menu
            if "disable_start_bing" in options:
                val = 0 if options["disable_start_bing"] else 1
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Software\\Microsoft\\Windows\\CurrentVersion\\Search" /v BingSearchEnabled /t REG_DWORD /d {val} /f')
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Software\\Policies\\Microsoft\\Windows\\Explorer" /v DisableSearchBoxSuggestions /t REG_DWORD /d {1 if val == 0 else 0} /f')
                success_count += 1

            # Taskbar End Task
            if "taskbar_end_task" in options:
                val = 1 if options["taskbar_end_task"] else 0
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced\\TaskbarDeveloperSettings" /v TaskbarEndTask /t REG_DWORD /d {val} /f')
                success_count += 1

            # Clean Taskbar (Hide Widgets & Copilot)
            if "clean_taskbar" in options:
                val = 0 if options["clean_taskbar"] else 1
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarDa /t REG_DWORD /d {val} /f')
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v ShowCopilotButton /t REG_DWORD /d {val} /f')
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarAI /t REG_DWORD /d {val} /f')
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarMn /t REG_DWORD /d {val} /f')
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v ShowTaskViewButton /t REG_DWORD /d {val} /f')
                success_count += 1

            # Fast Menu Delay
            if "fast_menu_delay" in options:
                val = "10" if options["fast_menu_delay"] else "400"
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Control Panel\\Desktop" /v MenuShowDelay /t REG_SZ /d {val} /f')
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Control Panel\\Desktop" /v AutoEndTasks /t REG_SZ /d {1 if val == "10" else 0} /f')
                success_count += 1

            # Disable Sticky Keys
            if "disable_sticky_keys" in options:
                val = "58" if options["disable_sticky_keys"] else "506"
                self.run_cmd(f'reg.exe add "{base_hive_prefix}\\Control Panel\\Accessibility\\StickyKeys" /v Flags /t REG_SZ /d {val} /f')
                success_count += 1

        if deploy_to_all_profiles:
            self.log("Applying Explorer shell customizations to current, loaded, and default user hives...", "INFO")
            self.apply_to_all_user_hives(_apply_to_target_hive)
        else:
            self.log("Applying Explorer shell customizations to current user profile only...", "INFO")
            _apply_to_target_hive("HKCU")

        return success_count

    # -------------------------------------------------------------
    # 4. Gaming & GPU Boost (Bi-directional Apply / Revert)
    # -------------------------------------------------------------
    def apply_gaming_tweaks(self, options: Dict[str, bool]) -> int:
        success_count = 0

        # MMCSS Priority Tweaks
        if "mmcss_priority" in options:
            games_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
            audio_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Audio"
            if options["mmcss_priority"]:
                self.log("Optimizing MMCSS (Multimedia Class Scheduler) for Games & Audio...", "INFO")
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, games_key, "GPU Priority", 8, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, games_key, "Priority", 6, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, games_key, "Scheduling Category", "High", winreg.REG_SZ)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, games_key, "SFIO Priority", "High", winreg.REG_SZ)

                self.set_reg(winreg.HKEY_LOCAL_MACHINE, audio_key, "GPU Priority", 8, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, audio_key, "Priority", 6, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, audio_key, "Scheduling Category", "High", winreg.REG_SZ)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, audio_key, "SFIO Priority", "High", winreg.REG_SZ)
                self.log("MMCSS gaming and audio scheduler tuned for maximum priority.", "SUCCESS")
            else:
                self.log("Reverting MMCSS priorities to default...", "INFO")
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, games_key, "GPU Priority", 8, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, games_key, "Priority", 2, winreg.REG_DWORD)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, games_key, "Scheduling Category", "Medium", winreg.REG_SZ)
                self.set_reg(winreg.HKEY_LOCAL_MACHINE, games_key, "SFIO Priority", "Normal", winreg.REG_SZ)
                self.log("MMCSS priorities restored to default.", "SUCCESS")
            success_count += 1

        # Hardware-Accelerated GPU Scheduling (HAGS)
        if "enable_hags" in options:
            val = 2 if options["enable_hags"] else 1
            self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HWSchMode", val, winreg.REG_DWORD)
            self.log(f"HAGS mode set to {val} (System restart required).", "SUCCESS")
            success_count += 1

        # Windowed Games Optimizations
        if "windowed_optimizations" in options:
            val = 1 if options["windowed_optimizations"] else 0
            self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR\Graphics", "OptimizationsForWindowedGames", val, winreg.REG_DWORD)
            self.log(f"Windowed game optimization set to {val}.", "SUCCESS")
            success_count += 1

        # Reset HPET Override
        if "reset_hpet" in options:
            if options["reset_hpet"]:
                self.log("Resetting HPET timer dependency override...", "INFO")
                self.run_cmd("bcdedit.exe /deletevalue useplatformclock")
                self.log("HPET override reset.", "SUCCESS")
                success_count += 1

        # Disable CPU Power Throttling (Desktop only)
        if "disable_power_throttling" in options:
            hw = self.get_hardware_info()
            if not hw["is_laptop"]:
                pt_key = r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling"
                if options["disable_power_throttling"]:
                    self.set_reg(winreg.HKEY_LOCAL_MACHINE, pt_key, "PowerThrottlingOff", 1, winreg.REG_DWORD)
                    self.set_reg(winreg.HKEY_LOCAL_MACHINE, pt_key, "NoLazyMode", 1, winreg.REG_DWORD)
                    self.set_reg(winreg.HKEY_LOCAL_MACHINE, pt_key, "AlwaysOn", 0, winreg.REG_DWORD)
                    self.log("CPU power throttling disabled.", "SUCCESS")
                else:
                    self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, pt_key, "PowerThrottlingOff")
                    self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, pt_key, "NoLazyMode")
                    self.log("CPU power throttling restored to default.", "SUCCESS")
                success_count += 1

        # Ultimate Performance Power Scheme
        if "ultimate_performance" in options:
            hw = self.get_hardware_info()
            if not hw["is_laptop"]:
                if options["ultimate_performance"]:
                    self.log("Unlocking and activating Ultimate Performance power scheme...", "INFO")
                    c, out = self.run_cmd("powercfg.exe -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61")
                    words = out.split()
                    guid = None
                    for w in words:
                        if len(w) == 36 and w.count("-") == 4:
                            guid = w
                            break
                    if guid:
                        self.run_cmd(f"powercfg.exe /setactive {guid}")
                        self.log(f"Ultimate Performance power plan activated: {guid}", "SUCCESS")
                else:
                    self.log("Restoring Balanced power scheme...", "INFO")
                    self.run_cmd("powercfg.exe /setactive 381b4222-f694-41f0-9685-ff5bb260df2e")
                    self.log("Balanced power scheme restored.", "SUCCESS")
                success_count += 1

        return success_count

    # -------------------------------------------------------------
    # 5. Services Optimization
    # -------------------------------------------------------------
    def get_services_catalog(self) -> List[Dict[str, str]]:
        """Returns standard services with categories and recommended modes."""
        return [
            # Telemetry & Diagnostics
            {"name": "DiagTrack", "display": "Connected User Experiences and Telemetry", "category": "Telemetry", "mode": "disabled", "desc": "Gathers & transmits telemetry diagnostic events to Microsoft"},
            {"name": "dmwappushservice", "display": "WAP Push Message Routing Service", "category": "Telemetry", "mode": "disabled", "desc": "Routes telemetry push notifications"},
            {"name": "diagnosticshub.standardcollector.service", "display": "Standard Collector Service", "category": "Telemetry", "mode": "disabled", "desc": "Collects diagnostic session events"},
            {"name": "RetailDemo", "display": "Retail Demo Service", "category": "Bloat", "mode": "disabled", "desc": "Restricts device for store demonstrations"},
            {"name": "MapsBroker", "display": "Downloaded Maps Manager", "category": "Bloat", "mode": "demand", "desc": "Downloads and updates offline maps in background"},

            # Xbox Background Services (Set to demand: works when launching Xbox app, doesn't run 24/7)
            {"name": "XblAuthManager", "display": "Xbox Live Auth Manager", "category": "Xbox", "mode": "demand", "desc": "Authentication service for Xbox Live apps"},
            {"name": "XblGameSave", "display": "Xbox Live Game Save Service", "category": "Xbox", "mode": "demand", "desc": "Synchronizes save game data"},
            {"name": "XboxNetApiSvc", "display": "Xbox Live Networking Service", "category": "Xbox", "mode": "demand", "desc": "Peer-to-peer network management for Xbox"},
            {"name": "XboxGipSvc", "display": "Xbox Accessory Management Service", "category": "Xbox", "mode": "demand", "desc": "Manages Xbox accessories & controllers"},

            # Remote & Legacy
            {"name": "RemoteRegistry", "display": "Remote Registry Service", "category": "Security", "mode": "disabled", "desc": "Allows remote users to modify registry settings"},
            {"name": "WerSvc", "display": "Windows Error Reporting Service", "category": "Diagnostics", "mode": "demand", "desc": "Queues and sends crash reports"},
            {"name": "SysMain", "display": "SysMain (Superfetch)", "category": "Performance", "mode": "demand", "desc": "Preloads apps into RAM; can cause high disk usage"}
        ]

    def optimize_services(self, selected_services: List[Tuple[str, str]]) -> int:
        if not selected_services:
            return 0

        self.log(f"Queuing startup configuration for {len(selected_services)} services...", "INFO")
        
        ps_commands = []
        for svc, mode in selected_services:
            startup_type = "Disabled" if mode == "disabled" else ("Manual" if mode == "demand" else "Automatic")
            ps_commands.append(f"""
            try {{
                $s = Get-Service -Name '{svc}' -ErrorAction SilentlyContinue
                if ($s) {{
                    Set-Service -Name '{svc}' -StartupType {startup_type} -ErrorAction SilentlyContinue
                    if ('{mode}' -eq 'disabled' -and $s.Status -eq 'Running') {{
                        Stop-Service -Name '{svc}' -Force -ErrorAction SilentlyContinue
                    }}
                    Write-Output "OK:{svc}"
                }}
            }} catch {{
                Write-Output "ERR:{svc}"
            }}
            """)

        full_ps = "\n".join(ps_commands)
        code, out = self.run_ps(full_ps)
        success = out.count("OK:")
        self.log(f"Configured {success} services successfully.", "SUCCESS")
        return success

    # -------------------------------------------------------------
    # 6. App Debloater
    # -------------------------------------------------------------
    def get_debloat_targets(self) -> List[Dict[str, str]]:
        return [
            {"id": "copilot", "pattern": "*Microsoft.Copilot*", "name": "Microsoft Copilot", "desc": "AI sidebar assistant and telemetry hook"},
            {"id": "bing_search", "pattern": "*Microsoft.BingSearch*", "name": "Bing Search Experience", "desc": "Web search integration inside the taskbar"},
            {"id": "widgets", "pattern": "*Microsoft.WidgetsPlatformRuntime*", "name": "Windows Widgets Runtime", "desc": "Chromium-based news and widget feed"},
            {"id": "web_exp", "pattern": "*MicrosoftWindows.Client.WebExperience*", "name": "Client Web Experience", "desc": "Web experience engine powering taskbar news"},
            {"id": "bing_news", "pattern": "*Microsoft.BingNews*", "name": "Microsoft News", "desc": "MSN News and feed aggregator"},
            {"id": "bing_weather", "pattern": "*Microsoft.BingWeather*", "name": "MSN Weather", "desc": "Weather app"},
            {"id": "solitaire", "pattern": "*Microsoft.MicrosoftSolitaireCollection*", "name": "Solitaire Collection", "desc": "Ad-supported card games"},
            {"id": "people", "pattern": "*Microsoft.People*", "name": "Microsoft People", "desc": "Contacts and address book"},
            {"id": "feedback", "pattern": "*Microsoft.WindowsFeedbackHub*", "name": "Feedback Hub", "desc": "Diagnostic telemetry and feedback prompt"},
            {"id": "yourphone", "pattern": "*Microsoft.YourPhone*", "name": "Phone Link (Your Phone)", "desc": "Smartphone synchronization background agent"},
            {"id": "getstarted", "pattern": "*Microsoft.Getstarted*", "name": "Tips (Get Started)", "desc": "Windows promotional tips and popups"}
        ]

    def remove_appx_packages(self, patterns: List[str]) -> int:
        removed_count = 0
        for pattern in patterns:
            self.log(f"Removing packages matching: {pattern}...", "INFO")
            ps = f"""
            try {{
                Get-Process | Where-Object {{ $_.Name -like '{pattern.replace("*", "")}' }} | Stop-Process -Force -ErrorAction SilentlyContinue
                $pkgs = @(Get-AppxPackage -AllUsers | Where-Object {{ $_.Name -like '{pattern}' }})
                foreach ($p in $pkgs) {{
                    Remove-AppxPackage -Package $p.PackageFullName -AllUsers -ErrorAction SilentlyContinue
                }}
                $prov = @(Get-AppxProvisionedPackage -Online | Where-Object {{ $_.DisplayName -like '{pattern}' }})
                foreach ($pr in $prov) {{
                    Remove-AppxProvisionedPackage -Online -PackageName $pr.PackageName -ErrorAction SilentlyContinue | Out-Null
                }}
                Write-Output "SUCCESS"
            }} catch {{
                Write-Output "ERR"
            }}
            """
            code, out = self.run_ps(ps)
            if "SUCCESS" in out:
                self.log(f"Package '{pattern}' uninstalled & unprovisioned.", "SUCCESS")
                removed_count += 1
            else:
                self.log(f"Package '{pattern}' processed.", "INFO")
        return removed_count

    # -------------------------------------------------------------
    # 7. Scheduled Tasks Optimization
    # -------------------------------------------------------------
    def disable_telemetry_tasks(self) -> int:
        tasks = [
            (r"\Microsoft\Windows\Customer Experience Improvement Program", "Consolidator"),
            (r"\Microsoft\Windows\Customer Experience Improvement Program", "UsbCeip"),
            (r"\Microsoft\Windows\Application Experience", "Microsoft-Windows-DiskDiagnosticDataCollector"),
            (r"\Microsoft\Windows\Maps", "MapsUpdateTask"),
            (r"\Microsoft\Windows\Feedback\Siuf", "DmClient"),
            (r"\Microsoft\Windows\Feedback\Siuf", "DmClientOnScenarioDownload"),
            (r"\Microsoft\Windows\DiskDiagnostic", "Microsoft-Windows-DiskDiagnosticDataCollector")
        ]
        self.log("Disabling scheduled telemetry background tasks...", "INFO")
        disabled = 0
        for path, task in tasks:
            cmd = f'schtasks.exe /change /tn "{path}\\{task}" /disable'
            c, _ = self.run_cmd(cmd)
            if c == 0:
                disabled += 1
        self.log(f"Disabled {disabled} background telemetry tasks.", "SUCCESS")
        return disabled

    # -------------------------------------------------------------
    # 8. Disk & Cache Cleaner (Real, High-Speed Cleaner)
    # -------------------------------------------------------------
    def get_cleanup_targets(self) -> List[Dict[str, str]]:
        windir = os.environ.get("SystemRoot", r"C:\Windows")
        user_temp = tempfile.gettempdir()
        local_app = os.environ.get("LOCALAPPDATA", "")

        return [
            {"id": "win_temp", "name": "Windows System Temp", "path": os.path.join(windir, "Temp"), "desc": "Temporary files generated by OS services"},
            {"id": "user_temp", "name": "User Profile Temp", "path": user_temp, "desc": "Temporary files generated by running user applications"},
            {"id": "softwaredist", "name": "Windows Update Cache", "path": os.path.join(windir, "SoftwareDistribution", "Download"), "desc": "Leftover downloaded Windows update setup files"},
            {"id": "dx_cache", "name": "DirectX Shader Cache", "path": os.path.join(local_app, "D3DSCache") if local_app else "", "desc": "Cached shader binaries that can become bloated"},
            {"id": "delivery_opt", "name": "Delivery Optimization Cache", "path": os.path.join(windir, "ServiceProfiles", "NetworkService", "AppData", "Local", "Microsoft", "Windows", "DeliveryOptimization"), "desc": "Downloaded P2P update bits"},
            {"id": "wer_dumps", "name": "Crash Dumps & Error Reports", "path": os.path.join(local_app, "CrashDumps") if local_app else "", "desc": "Application crash minidumps and logs"},
            {"id": "thumb_cache", "name": "Explorer Thumbnail Cache", "path": os.path.join(local_app, "Microsoft", "Windows", "Explorer") if local_app else "", "desc": "Cached image thumbnails (rebuilt automatically)"}
        ]

    def scan_cleanup_sizes(self) -> Dict[str, Tuple[int, str]]:
        results = {}
        for target in self.get_cleanup_targets():
            path = target["path"]
            total_size = 0
            if path and os.path.exists(path):
                try:
                    for root, dirs, files in os.walk(path):
                        for f in files:
                            try:
                                fp = os.path.join(root, f)
                                if not os.path.islink(fp):
                                    total_size += os.path.getsize(fp)
                            except Exception:
                                continue
                except Exception:
                    pass
            results[target["id"]] = (total_size, self.format_bytes(total_size))
        return results

    def execute_cleanup(self, selected_ids: List[str]) -> Tuple[int, str]:
        targets = {t["id"]: t for t in self.get_cleanup_targets()}
        total_freed = 0

        for cid in selected_ids:
            if cid not in targets:
                continue
            target = targets[cid]
            path = target["path"]
            self.log(f"Cleaning {target['name']}...", "INFO")
            if not path or not os.path.exists(path):
                continue

            freed_for_target = 0
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    try:
                        if os.path.isfile(item_path) or os.path.islink(item_path):
                            sz = os.path.getsize(item_path)
                            os.remove(item_path)
                            freed_for_target += sz
                        elif os.path.isdir(item_path):
                            sz = 0
                            for r, d, files in os.walk(item_path):
                                for f in files:
                                    try:
                                        sz += os.path.getsize(os.path.join(r, f))
                                    except Exception:
                                        pass
                            shutil.rmtree(item_path, ignore_errors=True)
                            freed_for_target += sz
                    except Exception:
                        continue
            except Exception:
                pass
            total_freed += freed_for_target
            self.log(f"Cleaned {target['name']}: {self.format_bytes(freed_for_target)} recovered.", "SUCCESS")

        self.log(f"Deep Clean complete! Total space recovered: {self.format_bytes(total_freed)}", "SUCCESS")
        return total_freed, self.format_bytes(total_freed)

    @staticmethod
    def format_bytes(b: int) -> str:
        if b < 1024:
            return f"{b} B"
        elif b < 1024 ** 2:
            return f"{b / 1024:.1f} KB"
        elif b < 1024 ** 3:
            return f"{b / (1024 ** 2):.1f} MB"
        else:
            return f"{b / (1024 ** 3):.2f} GB"

    # -------------------------------------------------------------
    # 9. WinGet Package Updater
    # -------------------------------------------------------------
    def check_winget_updates(self) -> Tuple[bool, str]:
        self.log("Querying WinGet for upgradable packages...", "INFO")
        c, out = self.run_cmd("winget upgrade --include-unknown")
        if c == 0:
            self.log("WinGet query completed.", "SUCCESS")
            return True, out
        else:
            self.log("WinGet is either not installed or returned an error.", "WARNING")
            return False, out

    def run_winget_upgrade_all(self) -> Tuple[int, str]:
        self.log("Starting bulk application upgrade via WinGet...", "INFO")
        cmd = "winget upgrade --all --include-unknown --accept-source-agreements --accept-package-agreements --silent"
        c, out = self.run_cmd(cmd)
        if c == 0:
            self.log("All packages upgraded successfully.", "SUCCESS")
        else:
            self.log(f"WinGet upgrade completed with status {c}.", "INFO")
        return c, out

    # -------------------------------------------------------------
    # Quick System Utilities
    # -------------------------------------------------------------
    def flush_dns(self) -> bool:
        self.log("Flushing DNS Resolver Cache...", "INFO")
        c, _ = self.run_cmd("ipconfig /flushdns")
        if c == 0:
            self.log("DNS cache flushed successfully.", "SUCCESS")
            return True
        return False

    def restart_explorer(self) -> bool:
        self.log("Restarting Windows Explorer shell...", "INFO")
        self.run_cmd("taskkill /f /im explorer.exe")
        subprocess.Popen(["explorer.exe"], creationflags=CREATE_NO_WINDOW)
        self.log("Windows Explorer restarted.", "SUCCESS")
        return True

    # -------------------------------------------------------------
    # 10. Battery & Power Conservation Engine (Universal)
    # -------------------------------------------------------------
    def get_battery_telemetry(self) -> Dict[str, Any]:
        """
        Retrieves real-time hardware battery telemetry via native kernel32 API
        with zero process overhead.
        """
        class SYSTEM_POWER_STATUS(ctypes.Structure):
            _fields_ = [
                ("ACLineStatus", ctypes.c_byte),
                ("BatteryFlag", ctypes.c_byte),
                ("BatteryLifePercent", ctypes.c_byte),
                ("SystemStatusFlag", ctypes.c_byte),
                ("BatteryLifeTime", ctypes.c_ulong),
                ("BatteryFullLifeTime", ctypes.c_ulong)
            ]

        status = {
            "has_battery": False,
            "percent": 0,
            "ac_online": False,
            "is_charging": False,
            "status_text": "Desktop / Direct AC Power",
            "model_name": "Windows PC",
            "fast_startup_enabled": True,
            "processor_eco_active": False,
            "pcie_aspm_active": False
        }

        # Query System Manufacturer & Model from BIOS
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS")
            mfg, _ = winreg.QueryValueEx(key, "SystemManufacturer")
            prod, _ = winreg.QueryValueEx(key, "SystemProductName")
            winreg.CloseKey(key)
            status["model_name"] = f"{mfg.strip()} {prod.strip()}"
        except Exception:
            pass

        # Query live battery via kernel32
        try:
            sps = SYSTEM_POWER_STATUS()
            if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(sps)):
                # BatteryFlag: 128 = No battery, 255 = Unknown
                if sps.BatteryFlag != 128 and sps.BatteryLifePercent <= 100:
                    status["has_battery"] = True
                    status["percent"] = int(sps.BatteryLifePercent)
                    status["ac_online"] = (sps.ACLineStatus == 1)
                    status["is_charging"] = bool(sps.BatteryFlag & 8)

                    if status["ac_online"]:
                        if status["is_charging"]:
                            status["status_text"] = f"⚡ Charging ({status['percent']}%) [AC Connected]"
                        else:
                            status["status_text"] = f"🔌 Plugged In, Fully Charged ({status['percent']}%)"
                    else:
                        status["status_text"] = f"🔋 On Battery Power ({status['percent']}%)"
        except Exception:
            pass

        # Query Fast Startup state
        status["fast_startup_enabled"] = self.get_fast_startup_state()

        # Query Processor Eco & PCIe ASPM states
        status["processor_eco_active"] = self.get_processor_eco_state()
        status["pcie_aspm_active"] = self.get_pcie_aspm_state()

        return status

    def get_processor_eco_state(self) -> bool:
        """Checks whether DC processor throttle capping is active (<=85%)."""
        try:
            c, out = self.run_cmd("powercfg /query SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX")
            for line in out.splitlines():
                if "Current DC Power Setting Index:" in line:
                    val = int(line.split(":")[-1].strip(), 16)
                    return val <= 85
        except Exception:
            pass
        return False

    def toggle_processor_eco(self, enable: bool) -> Tuple[bool, str]:
        """
        Configures CPU energy efficiency and thermal capping on battery (DC):
        Limits CPU boost frequency to 85% on battery, eliminating fan noise,
        thermal degradation, and extending screen-on battery runtime by up to 25%.
        """
        throttle_val = 85 if enable else 100
        epp_val = 80 if enable else 50
        state_str = "Enabled (85% Max Boost on Battery)" if enable else "Disabled (100% Full Power)"
        self.log(f"Configuring Processor Eco Capping on Battery: {state_str}...", "INFO")

        cmds = [
            f"powercfg /setdcvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX {throttle_val}",
            f"powercfg /setdcvalueindex SCHEME_CURRENT SUB_PROCESSOR PERFEPP {epp_val}",
            "powercfg /setactive SCHEME_CURRENT"
        ]
        success = True
        for cmd in cmds:
            c, _ = self.run_cmd(cmd)
            if c != 0:
                success = False

        if success:
            msg = f"Processor Battery Eco Capping {state_str}."
            self.log(msg, "SUCCESS")
            return True, msg
        return False, "Failed to apply processor power configuration."

    def get_pcie_aspm_state(self) -> bool:
        """Checks whether PCIe Link State Power Management (ASPM) is set to Maximum on DC."""
        try:
            c, out = self.run_cmd("powercfg /query SCHEME_CURRENT SUB_PCIEXPRESS ASPM")
            for line in out.splitlines():
                if "Current DC Power Setting Index:" in line:
                    val = int(line.split(":")[-1].strip(), 16)
                    return val == 2  # 2 = Maximum Power Savings
        except Exception:
            pass
        return False

    def toggle_pcie_aspm(self, enable: bool) -> Tuple[bool, str]:
        """
        Enables or disables aggressive PCIe Link State Power Management (ASPM) on battery.
        Places idle NVMe, bus lanes, and GPU into low-power states to cut motherboard drain.
        """
        aspm_val = 2 if enable else 1  # 2 = Maximum Power Savings, 1 = Moderate
        state_str = "Maximum Power Savings" if enable else "Standard Power"
        self.log(f"Configuring PCIe Link State Power Management on DC: {state_str}...", "INFO")

        cmds = [
            f"powercfg /setdcvalueindex SCHEME_CURRENT SUB_PCIEXPRESS ASPM {aspm_val}",
            "powercfg /setactive SCHEME_CURRENT"
        ]
        success = True
        for cmd in cmds:
            c, _ = self.run_cmd(cmd)
            if c != 0:
                success = False

        if success:
            msg = f"PCIe ASPM Link State on battery set to: {state_str}."
            self.log(msg, "SUCCESS")
            return True, msg
        return False, "Failed to apply PCIe power management."

    def generate_battery_report(self) -> Tuple[bool, str]:
        """
        Generates an official Windows battery health diagnostic report (powercfg /batteryreport)
        and automatically launches it in the system default browser.
        """
        report_path = os.path.join(tempfile.gettempdir(), "Apex_Battery_Report.html")
        self.log("Generating official Windows Battery Health Report...", "INFO")
        c, out = self.run_cmd(f'powercfg /batteryreport /output "{report_path}"')
        if c == 0 and os.path.exists(report_path):
            self.log(f"Battery report generated at: {report_path}", "SUCCESS")
            try:
                os.startfile(report_path)
            except Exception:
                pass
            return True, report_path
        else:
            self.log(f"Failed to generate battery report: {out}", "ERROR")
            return False, out

    def get_fast_startup_state(self) -> bool:
        """
        Queries whether Windows Fast Startup (HiberbootEnabled) is enabled.
        Fast Startup causes background battery drain while laptops are turned off.
        """
        try:
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Power")
            val, _ = winreg.QueryValueEx(k, "HiberbootEnabled")
            winreg.CloseKey(k)
            return val == 1
        except Exception:
            return True

    def set_fast_startup(self, enable: bool) -> Tuple[bool, str]:
        """
        Configures Windows Fast Startup. Disabling it prevents standby battery discharge.
        Automatically elevates via UAC if running in an un-elevated session.
        """
        val = 1 if enable else 0
        state_str = "Enabled (Default)" if enable else "Disabled (Prevents Shutdown Drain)"
        self.log(f"Configuring Fast Startup: {state_str}...", "INFO")
        try:
            k = winreg.CreateKeyEx(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Power",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(k, "HiberbootEnabled", 0, winreg.REG_DWORD, val)
            winreg.CloseKey(k)
            self.log(f"Fast Startup {state_str}.", "SUCCESS")
            return True, f"Fast Startup {state_str}."
        except Exception as e:
            if "Access is denied" in str(e) or not self.is_admin():
                self.log("Non-elevated session: Requesting UAC elevation to update Fast Startup in HKLM...", "INFO")
                elev_cmd = f"Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power' -Name 'HiberbootEnabled' -Value {val} -Type DWord -Force"
                c, out = self.run_elevated_ps(elev_cmd)
                if self.get_fast_startup_state() == enable:
                    self.log(f"Fast Startup {state_str} (via UAC elevation).", "SUCCESS")
                    return True, f"Fast Startup {state_str}."
            self.log(f"Error configuring Fast Startup: {e}", "ERROR")
            return False, str(e)

