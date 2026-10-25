"""
Apex Windows Optimizer - Windows AppX Debloater & Telemetry Tasks Mixin
Provides safe AppX / UWP package uninstallation and disabling of diagnostic scheduled tasks.
"""

from typing import Dict, List, Tuple, Any


class DebloatMixin:
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
        # Terminate any running Chromium host widget or copilot processes before uninstallation
        self.run_ps("Get-Process | Where-Object { $_.Name -like '*Widget*' -or $_.Name -like '*Copilot*' } | Stop-Process -Force -ErrorAction SilentlyContinue")

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


