"""
Apex Windows Optimizer - Power & Battery Management Mixin
Provides advanced battery telemetry, active power plan switching, processor eco mode,
PCIe ASPM link state power management, fast startup toggling, and HTML battery reporting.
"""

import os
import sys
import re
import time
import tempfile
import winreg
import ctypes
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any


class PowerMixin:
    # -------------------------------------------------------------
    # 10. Battery & Power Conservation Engine (Universal)
    # -------------------------------------------------------------
    def _get_battery_specs(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Retrieves hardware battery specifications: design capacity, full charge capacity,
        wear level, cycle count, manufacturer, serial number, and chemistry.
        Caches results for 60 seconds to avoid repeating XML generation.
        """
        now = time.time()
        if not force_refresh and self._cached_battery_specs and (now - self._last_battery_specs_time < 60):
            return self._cached_battery_specs

        specs = {
            "design_capacity": 0,
            "full_capacity": 0,
            "cycle_count": 0,
            "health_percent": 100.0,
            "wear_percent": 0.0,
            "chemistry": "Lithium-Ion",
            "manufacturer": "OEM",
            "serial_number": "N/A",
            "device_id": "Internal Battery"
        }

        xml_path = os.path.join(tempfile.gettempdir(), "apex_battery_specs.xml")
        try:
            # Generate official battery report XML quietly
            cmd = f'powercfg /batteryreport /xml /output "{xml_path}"'
            c, _ = self.run_cmd(cmd)
            if c == 0 and os.path.exists(xml_path):
                tree = ET.parse(xml_path)
                root = tree.getroot()
                bat = None
                for b in root.iter():
                    if b.tag.endswith("Battery") and not b.tag.endswith("Batteries"):
                        bat = b
                        break

                if bat is not None:
                    raw_data = {}
                    for child in bat:
                        tag = child.tag.split("}")[-1]
                        raw_data[tag] = (child.text or "").strip()

                    try:
                        des_cap = int(raw_data.get("DesignCapacity", "0"))
                    except ValueError:
                        des_cap = 0

                    try:
                        full_cap = int(raw_data.get("FullChargeCapacity", "0"))
                    except ValueError:
                        full_cap = 0

                    try:
                        cycles = int(raw_data.get("CycleCount", "0"))
                    except ValueError:
                        cycles = 0

                    specs["design_capacity"] = des_cap
                    specs["full_capacity"] = full_cap
                    specs["cycle_count"] = cycles
                    specs["manufacturer"] = raw_data.get("Manufacturer", "OEM").strip() or "OEM"
                    specs["serial_number"] = raw_data.get("SerialNumber", "N/A").strip() or "N/A"
                    specs["device_id"] = raw_data.get("Id", "Internal Battery").strip() or "Internal Battery"

                    chem = raw_data.get("Chemistry", "Li-I").strip()
                    if "li-i" in chem.lower() or "lion" in chem.lower():
                        specs["chemistry"] = "Lithium-Ion (Li-Ion)"
                    elif "poly" in chem.lower() or "lip" in chem.lower():
                        specs["chemistry"] = "Lithium-Polymer (Li-Po)"
                    elif chem:
                        specs["chemistry"] = chem
                    else:
                        specs["chemistry"] = "Lithium-Ion"

                    if des_cap > 0 and full_cap > 0:
                        health = min(100.0, round((full_cap / des_cap) * 100.0, 1))
                        specs["health_percent"] = health
                        specs["wear_percent"] = max(0.0, round(100.0 - health, 1))
        except Exception:
            pass

        self._cached_battery_specs = specs
        self._last_battery_specs_time = now
        return specs

    def _get_battery_dynamic_status(self) -> Dict[str, Any]:
        """
        Retrieves real-time voltage and charge/discharge rate via root/wmi:BatteryStatus.
        Caches for 5 seconds to preserve battery and CPU cycles.
        """
        now = time.time()
        if self._cached_battery_wmi_status and (now - self._last_battery_wmi_time < 5):
            return self._cached_battery_wmi_status

        dyn = {
            "voltage_v": 0.0,
            "rate_w": 0.0,
            "rate_text": "Direct AC"
        }
        try:
            ps_cmd = "Get-CimInstance -Namespace root/wmi -ClassName BatteryStatus | Select-Object ChargeRate, DischargeRate, Voltage, Charging, Discharging, PowerOnline | ConvertTo-Json -Compress"
            c, out = self.run_cmd(f'powershell -NoProfile -Command "{ps_cmd}"')
            if c == 0 and out.strip().startswith("{"):
                import json
                data = json.loads(out.strip())
                volt_mv = data.get("Voltage", 0) or 0
                dyn["voltage_v"] = round(volt_mv / 1000.0, 2)
                chg_rate = data.get("ChargeRate", 0) or 0
                dis_rate = data.get("DischargeRate", 0) or 0
                if chg_rate > 0:
                    w = round(chg_rate / 1000.0, 2)
                    dyn["rate_w"] = w
                    dyn["rate_text"] = f"+{w} W (Charging)"
                elif dis_rate > 0:
                    w = round(dis_rate / 1000.0, 2)
                    dyn["rate_w"] = w
                    dyn["rate_text"] = f"-{w} W (Discharging)"
                else:
                    dyn["rate_w"] = 0.0
                    dyn["rate_text"] = "Idle / Full"
        except Exception:
            pass

        self._cached_battery_wmi_status = dyn
        self._last_battery_wmi_time = now
        return dyn

    def get_battery_telemetry(self, refresh_specs: bool = False) -> Dict[str, Any]:
        """
        Retrieves real-time hardware battery telemetry via native kernel32 API,
        WMI metrics, and Windows battery diagnostics report with zero process lag.
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
            "battery_saver_active": False,
            "remaining_time_str": "Direct AC Power",
            "design_capacity": 0,
            "full_capacity": 0,
            "current_capacity": 0,
            "health_percent": 100.0,
            "wear_percent": 0.0,
            "cycle_count": 0,
            "chemistry": "Lithium-Ion",
            "manufacturer": "OEM",
            "serial_number": "N/A",
            "device_id": "Internal Battery",
            "voltage_v": 0.0,
            "rate_w": 0.0,
            "rate_text": "Direct AC",
            "fast_startup_enabled": True,
            "processor_eco_active": False,
            "pcie_aspm_active": False,
            "power_scheme": {}
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
                    status["battery_saver_active"] = (sps.SystemStatusFlag == 1)

                    if status["ac_online"]:
                        if status["is_charging"]:
                            status["status_text"] = f"⚡ Charging ({status['percent']}%) [AC Connected]"
                            status["remaining_time_str"] = "Charging on AC Power"
                        else:
                            status["status_text"] = f"🔌 Plugged In, Fully Charged ({status['percent']}%)"
                            status["remaining_time_str"] = "Fully Charged / Wall Current"
                    else:
                        status["status_text"] = f"🔋 On Battery Power ({status['percent']}%)"
                        if sps.BatteryLifeTime != 0xFFFFFFFF and sps.BatteryLifeTime > 0:
                            hrs = sps.BatteryLifeTime // 3600
                            mins = (sps.BatteryLifeTime % 3600) // 60
                            status["remaining_time_str"] = f"{hrs}h {mins:02d}m remaining"
                        else:
                            status["remaining_time_str"] = "Calculating runtime..."
        except Exception:
            pass

        # If system has a battery, enrich with hardware specs and WMI dynamic values
        if status["has_battery"]:
            specs = self._get_battery_specs(force_refresh=refresh_specs)
            status.update(specs)
            if status["full_capacity"] > 0:
                status["current_capacity"] = int(round(status["full_capacity"] * (status["percent"] / 100.0)))
            dyn = self._get_battery_dynamic_status()
            status["voltage_v"] = dyn["voltage_v"]
            status["rate_w"] = dyn["rate_w"]
            status["rate_text"] = dyn["rate_text"]

        # Query Fast Startup state
        status["fast_startup_enabled"] = self.get_fast_startup_state()

        # Query Processor Eco & PCIe ASPM states
        status["processor_eco_active"] = self.get_processor_eco_state()
        status["pcie_aspm_active"] = self.get_pcie_aspm_state()

        # Query active and installed Windows Power Schemes
        status["power_scheme"] = self.get_power_schemes()

        return status

    def get_power_schemes(self) -> Dict[str, Any]:
        """
        Retrieves all registered Windows power schemes and the currently active plan.
        Detects custom vendor plans like AMD Ryzen Balanced or Intel Dynamic Tuning.
        """
        schemes = []
        active_guid = "381b4222-f694-41f0-9685-ff5bb260df2e"
        active_name = "Balanced"
        is_ryzen = False

        try:
            c, out = self.run_cmd("powercfg /list")
            for line in out.splitlines():
                line = line.strip()
                m = re.search(r"Power Scheme GUID:\s*([a-f0-9\-]+)\s*\((.*?)\)(\s*\*?)", line, re.IGNORECASE)
                if m:
                    guid = m.group(1).strip()
                    name = m.group(2).strip()
                    is_active = ("*" in m.group(3)) or ("*" in line)
                    name = name.replace("AMD Ryzen? Balanced", "AMD Ryzen™ Balanced")
                    name = name.replace("AMD Ryzen? High Performance", "AMD Ryzen™ High Performance")
                    if is_active and "ryzen" in name.lower():
                        is_ryzen = True
                    schemes.append({
                        "guid": guid,
                        "name": name,
                        "is_active": is_active
                    })
                    if is_active:
                        active_guid = guid
                        active_name = name
        except Exception:
            pass

        return {
            "active_guid": active_guid,
            "active_name": active_name,
            "is_ryzen": is_ryzen,
            "all_schemes": schemes
        }

    def set_active_power_scheme(self, scheme_guid: str) -> Tuple[bool, str]:
        """Activates a specified Windows Power Scheme GUID."""
        try:
            c, out = self.run_cmd(f"powercfg /setactive {scheme_guid}")
            if c == 0:
                self.log(f"Activated Windows Power Scheme: {scheme_guid}", "SUCCESS")
                return True, "Power Scheme activated successfully."
            return False, f"Failed to activate power scheme: {out}"
        except Exception as e:
            return False, str(e)

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
        Configures the maximum processor state and energy preference on battery (DC).
        Effects on performance, temperature, fan noise, and runtime depend on the device.
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

