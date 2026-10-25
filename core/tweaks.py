"""
Apex Windows Optimizer - System, Privacy & UI Tweaks Mixin
Provides real-time tweak state auditing, system performance optimization,
privacy/telemetry shielding, Windows Explorer shell customization, and restore point safety.
"""

import os
import winreg
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple, Any


class TweaksMixin:
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

        # Power & Hardware Efficiency Tweaks
        states["processor_eco"] = self.get_processor_eco_state()
        states["pcie_aspm"] = self.get_pcie_aspm_state()
        states["fast_startup"] = not self.get_fast_startup_state()

        # SvcHost process consolidation based on physical RAM
        svchost_val = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control", "SvcHostSplitThresholdInKB")
        states["svchost_split_threshold"] = (svchost_val is not None and svchost_val > 0)

        # Windows Defender background scan CPU load cap (25%)
        def_cpu = self.get_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender\Scan", "ScanAvgCPULoadFactor")
        states["defender_cpu_cap"] = (def_cpu == 25)

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

        # GameDVR background recording
        gdvr = self.get_reg(winreg.HKEY_CURRENT_USER, r"System\GameConfigStore", "GameDVR_Enabled")
        states["disable_gamedvr"] = (gdvr == 0)

        # Windows Native Game Mode
        gmode = self.get_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", "AutoGameModeEnabled")
        states["enable_game_mode"] = (gmode == 1)

        # Mouse Acceleration (1:1 Raw input)
        mspeed = self.get_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseSpeed")
        states["disable_mouse_acceleration"] = (str(mspeed) == "0")

        # Nagle's Algorithm (Network Gaming Latency)
        states["network_gaming_latency"] = self.get_nagle_algorithm_state()

        return states


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

        # Processor Eco Boost Capping on Battery (DC)
        if "processor_eco" in options:
            ok, _ = self.toggle_processor_eco(options["processor_eco"])
            if ok:
                success_count += 1

        # PCIe Link State Power Management (ASPM)
        if "pcie_aspm" in options:
            ok, _ = self.toggle_pcie_aspm(options["pcie_aspm"])
            if ok:
                success_count += 1

        # Disable Fast Startup (Stop phantom shutdown drain)
        if "fast_startup" in options:
            ok, _ = self.set_fast_startup(not options["fast_startup"])
            if ok:
                success_count += 1

        # SvcHost Split Threshold (Group SvcHost processes on <16GB RAM)
        if "svchost_split_threshold" in options:
            if options["svchost_split_threshold"]:
                self.log("Optimizing SvcHost process splitting threshold for physical RAM...", "INFO")
                s1 = self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control", "SvcHostSplitThresholdInKB", 380000, winreg.REG_DWORD)
                s2 = self.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\Control", "SvcHostSplitThresholdInKB", 380000, winreg.REG_DWORD)
                if s1 or s2:
                    self.log("SvcHost split threshold optimized (consolidates processes to conserve 300MB+ RAM).", "SUCCESS")
                    success_count += 1
            else:
                self.log("Reverting SvcHost process splitting threshold to Windows default...", "INFO")
                self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control", "SvcHostSplitThresholdInKB")
                self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\ControlSet001\Control", "SvcHostSplitThresholdInKB")
                self.log("SvcHost split threshold restored to default.", "SUCCESS")
                success_count += 1

        # Windows Defender Scan CPU Load Cap (Max 25% CPU)
        if "defender_cpu_cap" in options:
            def_scan_key = r"SOFTWARE\Policies\Microsoft\Windows Defender\Scan"
            if options["defender_cpu_cap"]:
                self.log("Capping Windows Defender background scan CPU usage to 25%...", "INFO")
                if self.set_reg(winreg.HKEY_LOCAL_MACHINE, def_scan_key, "ScanAvgCPULoadFactor", 25, winreg.REG_DWORD):
                    self.log("Defender background scan CPU capped at 25% (prevents 100% CPU lockups).", "SUCCESS")
                    success_count += 1
            else:
                self.log("Reverting Windows Defender CPU scan limit to default...", "INFO")
                self.delete_reg_value(winreg.HKEY_LOCAL_MACHINE, def_scan_key, "ScanAvgCPULoadFactor")
                self.log("Defender scan CPU limit restored to default.", "SUCCESS")
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


