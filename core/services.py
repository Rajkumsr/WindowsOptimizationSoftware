"""
Apex Windows Optimizer - Windows Services Optimizer Mixin
Provides Windows services catalog discovery and safe optimization for unnecessary background services.
"""

import re
from typing import Dict, List, Tuple


class ServicesMixin:
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
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", svc) or mode not in {"disabled", "demand", "auto"}:
                self.log(f"Rejected invalid service configuration: {svc!r} / {mode!r}", "ERROR")
                continue

            startup_type = "Disabled" if mode == "disabled" else ("Manual" if mode == "demand" else "Automatic")
            ps_commands.append(f"""
            try {{
                $s = Get-Service -Name '{svc}' -ErrorAction Stop
                Set-Service -Name '{svc}' -StartupType {startup_type} -ErrorAction Stop
                if ('{mode}' -eq 'disabled' -and $s.Status -eq 'Running') {{
                    Stop-Service -Name '{svc}' -Force -ErrorAction Stop
                    }}
                Write-Output "OK:{svc}"
            }} catch {{
                Write-Output "ERR:{svc}:$($_.Exception.Message)"
            }}
            """)

        if not ps_commands:
            return 0

        full_ps = "\n".join(ps_commands)
        code, out = self.run_ps(full_ps)
        success = out.count("OK:")
        for line in out.splitlines():
            if line.startswith("ERR:"):
                self.log(f"Service configuration failed: {line[4:]}", "ERROR")
        if code != 0:
            self.log(f"Service configuration command failed with exit code {code}.", "ERROR")
        self.log(f"Configured {success} of {len(ps_commands)} services successfully.", "SUCCESS" if success == len(ps_commands) and code == 0 else "WARNING")
        return success

