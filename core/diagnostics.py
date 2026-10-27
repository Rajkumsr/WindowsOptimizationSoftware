"""
Apex Windows Optimizer - Hardware Telemetry & Diagnostics Mixin
Provides system hardware identification, CPU load monitoring, RAM working set flushing,
health score calculation, and 1-click quick boost diagnostics.
"""

import os
import sys
import subprocess
import shutil
import winreg
import ctypes
import time
from typing import Dict, List, Optional, Tuple, Any
from .base import CREATE_NO_WINDOW


class DiagnosticsMixin:
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
        """Returns instantaneous system CPU load percentage with rate-limiting cache & Win32 fallback."""
        now = time.time()
        # Cooldown guard: if queried within 0.8 seconds, return cached value to prevent psutil delta zeroing
        if (now - self._last_cpu_time) < 0.8 and self._cached_cpu_pct > 0.0:
            return self._cached_cpu_pct

        # 1. Primary method: psutil
        try:
            import psutil
            val = float(psutil.cpu_percent(interval=None))
            if val > 0.0 or self._cached_cpu_pct == 0.0:
                self._cached_cpu_pct = val
                self._last_cpu_time = now
                if val > 0.0:
                    return self._cached_cpu_pct
        except Exception:
            pass

        # 2. Native Win32 Fallback via GetSystemTimes (zero external dependencies)
        try:
            class FILETIME(ctypes.Structure):
                _fields_ = [("dwLowDateTime", ctypes.c_uint32), ("dwHighDateTime", ctypes.c_uint32)]

            def _ft(ft):
                return (ft.dwHighDateTime << 32) | ft.dwLowDateTime

            idle, kern, user = FILETIME(), FILETIME(), FILETIME()
            if ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user)):
                idle_i = _ft(idle)
                kern_i = _ft(kern)
                user_i = _ft(user)
                if self._prev_kernel_time > 0:
                    d_idle = idle_i - self._prev_idle_time
                    d_kern = kern_i - self._prev_kernel_time
                    d_user = user_i - self._prev_user_time
                    total = d_kern + d_user
                    if total > 0:
                        load = max(0.0, min(100.0, (1.0 - (d_idle / total)) * 100.0))
                        self._cached_cpu_pct = round(load, 1)
                        self._last_cpu_time = now
                self._prev_idle_time = idle_i
                self._prev_kernel_time = kern_i
                self._prev_user_time = user_i
        except Exception:
            pass

        return self._cached_cpu_pct

    def flush_ram_working_sets(self) -> Tuple[bool, int, float]:
        """
        Requests Windows to trim accessible process working sets using EmptyWorkingSet.
        The amount of memory made available varies and applications may fault pages back in.
        Returns: (success, process_count, freed_mb)
        """
        self.log("Requesting a trim of accessible process working sets...", "INFO")
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
            "enable_hags", "mmcss_priority", "disable_power_throttling"
        ]
        med_impact = [
            "irp_stack_size", "long_paths", "disable_p2p_update",
            "disable_lockscreen_ads", "disable_office_telemetry",
            "reset_hpet", "windowed_optimizations"
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
        1. Requests a trim of accessible process working sets
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
