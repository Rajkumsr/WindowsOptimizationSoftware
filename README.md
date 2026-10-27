# Apex Windows Optimizer (Pro Suite v2.0)

A modern, high-performance, dark-themed Windows optimization and debloating desktop application built with Python and Tkinter.

---

## 🌟 Highlights & Capabilities

### 1. 📊 Comprehensive Dashboard & Live Health Diagnostics
* **Animated Donut Health Gauge**: Swept-arc circular health gauge rendered in your native Windows Accent color with dynamic score interpolation (0–100%) and hygiene ratings (`OPTIMAL`, `GOOD`, `FAIR`, `OPTIMIZING`).
* **🎛️ 1-Click Scenario Preset Profiles**: Instant one-click profiles tailored for common computer scenarios:
  * **🎮 Gaming & FPS Mode**: Hardware GPU Scheduling (HAGS), MMCSS audio/network scheduling, and Ultimate Performance power scheme.
  * **🔋 Battery Saver Mode**: Sets the maximum processor state to 85% on DC, enables PCIe ASPM, and disables Fast Startup. Battery-life effects vary by device and usage.
  * **🛡️ Maximum Privacy**: Shuts down telemetry, DiagTrack, CEIP, Microsoft Recall AI tracking, and Bing web search.
  * **🔄 Windows Defaults**: Reverts the system, gaming, and power settings covered by that preset. It does not undo app removals or all privacy, service, and shell changes.
* **Real-time Live Telemetry**: Instant CPU load percentage, physical RAM usage (free, total, and percentage load), system drive, active chassis detection (`🖥️ Desktop PC` vs `💻 Laptop`), and precise system uptime (`GetTickCount64`).
* **⚡ 1-Click Instant System Boost**: Requests Windows to trim process working sets, sweeps accessible temporary files, and refreshes DNS cache. The amount of memory or storage reclaimed depends on the system and running apps.
* **One-Click Quick Optimization**: Applies the selected performance, privacy, and shell settings after attempting to create a System Restore point or registry-export fallback. A registry export is a backup, not an automatic rollback.
* **Instant Utilities**: Request a process working-set trim, flush DNS cache, restart Windows Explorer shell, export registry backups, and create System Restore points.

### 2. 🎨 Native Windows Theme & Accent Palette Auto-Sync
* **100% Dynamic Windows Colorization**: Extracts colors directly from Windows via `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Accent\AccentPalette` (8 Fluent UI shades), DWM Colorization APIs, and Win32 `GetSysColor` metrics.
* **Dynamic Dark / Light Mode Adaptation**: Detects Windows `AppsUseLightTheme` and Personalization settings to blend buttons, gauge rings, active tabs, search outlines, and toast borders seamlessly with your OS theme.

### 3. 🔍 Global `Ctrl+F` Real-Time Search & Quick-Toggle Engine
* **Instantaneous Search**: Press `Ctrl+F` anywhere in the app to search across 33+ system, privacy, shell, gaming, and battery optimizations.
* **Live Inline ToggleSwitches**: Toggling any setting inside search results immediately writes to the engine and updates system states with a toast notification.

### 4. 🔔 Non-Blocking In-App Floating Toast Notifications (`ToastManager`)
* **Zero Disruption**: Replaced blocking modal dialogs with smooth floating toast notifications anchored to the bottom right of the window.
* **Contextual Visual Badges**: Toast cards feature status symbols (`✅`, `⚡`, `⚠️`, `ℹ️`, `❌`), Windows accent highlight borders, and auto-dismiss timers.

### 5. ⚡ Real State Detection & Bi-Directional Toggles
* **Live System State Inspection**: On launch, the software inspects the Windows Registry to determine what is already `[OPTIMIZED]` vs `[DEFAULT]`.
* **Bi-Directional Revert / Undo**: Turning a toggle switch `OFF` restores the tool's configured default for that setting; this may not recover a custom value that existed before Apex changed it.
* **Multi-User Profile Deployment**: Mounts `C:\Users\Default\NTUSER.DAT` into `HKU` so customizations automatically deploy to **all current and future user accounts**.

### 6. 🎯 High-DPI Display Scaling Awareness
* Fully declared DPI-aware process (`SetProcessDpiAwareness`) rendering crisp, clear text and cards on 1080p, 1440p, 4K, and 125%/150% scaled displays.
* Scoped, smooth mousewheel scrolling that eliminates cross-tab scroll bleeding.

### 7. ⚡ System & Kernel Performance
* **Disable Network Throttling**: Uncaps multimedia and gaming network traffic (`NetworkThrottlingIndex` = `0xFFFFFFFF`).
* **Foreground Responsiveness**: Sets 90% CPU priority for active applications and games (`SystemResponsiveness` = `10`).
* **Accelerated Shutdown**: Shortens service termination delay to 5 seconds (`WaitToKillServiceTimeout` = `5000`).
* **NTFS Long File Paths**: Eliminates the legacy MAX_PATH 260-character limitation.
* **Device Metadata Policy**: Prevents Windows from downloading device metadata from Microsoft; this setting does not block firmware WPBT software.
* **IRP Stack Size Configuration**: Sets the server `IRPStackSize` registry value to `30`; performance impact depends on system configuration.
* **Disable P2P Update Seeding**: Prevents Delivery Optimization from using your upstream bandwidth to seed updates to external PCs.
* **F8 Legacy Boot Menu**: Restores classic boot options for instant recovery.
* **Desktop Hibernation Control**: Can disable hibernation on desktop systems and remove `hiberfil.sys`; the disk space recovered varies by configuration.

### 8. 🛡️ Privacy & Telemetry
* **Diagnostic Data & CEIP**: Disables DiagTrack, feedback notifications, error reporting telemetry, and Customer Experience Improvement tasks.
* **Lock Screen Spotlight Ads**: Removes rotating sponsored tips and recommendations.
* **Microsoft Recall AI**: Blocks automated background screenshot harvesting.
* **Edge Optimization**: Disables Edge background preloading, startup boost, shopping assistant, and telemetry.
* **Office Telemetry**: Disables telemetry logging and feedback for Microsoft Office 2013-365.

### 9. 🎨 Explorer & Shell Personalization
* **File Extensions Visibility**: Always displays `.exe`, `.zip`, `.pdf`, etc. to prevent spoofing.
* **Open to 'This PC'**: Sets File Explorer default view directly to drives instead of Quick Access.
* **Windows 11 Classic Context Menu**: Restores full right-click context menu instantly.
* **Start Menu Search Privacy**: Disables Bing web search integration to keep search purely local.
* **Taskbar 'End Task'**: Enables direct process termination from taskbar right-click.
* **Taskbar Cleanup**: Hides widgets and Copilot buttons.
* **Accelerated Menu Delays**: Reduces menu show delay to 10ms.
* **Sticky Keys Prompt**: Disables 5x Shift dialog.

### 10. ⚙️ Services Optimizer
* **Granular Startup Control**: Presets for *Recommended (Safe)*, *Maximum Gaming*, and *Reset to Demand*.
* Configures telemetry, Xbox background services, diagnostic hubs, and error reporting services without breaking core Windows functionality.

### 11. 🗑️ App Debloater
* Uninstalls and unprovisions bloatware for current and future user accounts:
  * Microsoft Copilot
  * Bing Search Experience
  * Windows Widgets Runtime & Client Web Experience
  * MSN News & Weather
  * Solitaire Collection
  * Microsoft People & Feedback Hub
  * Phone Link (Your Phone)
  * Tips / Get Started

### 12. 🎮 Gaming & GPU Boost
* **Hardware-Accelerated GPU Scheduling (HAGS)**: Transfers frame scheduling directly to GPU VRAM.
* **Windowed Games Optimizations**: Modern flip presentation model for DirectX 10/11 games.
* **MMCSS Scheduling**: Configures maximum priority (`GPU Priority` = 8, `Priority` = 6, `SFIO Priority` = High).
* **Power Throttling Disable**: Prevents CPU frequency degradation during intense workloads.
* **Ultimate Performance Power Scheme**: Activates Windows' hidden latency-free power plan.
* **HPET Reset**: Removes explicit timer overrides to prevent micro-stuttering.

### 13. 🧹 Deep Disk & Cache Cleaner (Real BeardSweeper)
* Estimates file sizes before cleaning (actual reclaimable space may differ; locked files can be skipped). WinSxS cleanup is performed through DISM and is not assigned a fixed size estimate:
  * Windows System Temp & User Profile Temp
  * Windows Update Download Cache (`SoftwareDistribution\Download`)
  * DirectX Shader Cache (`D3DSCache`)
  * Delivery Optimization Cache
  * Crash Dumps & Windows Error Reports
  * Explorer Thumbnail Cache

### 14. 🔋 Universal Battery & Power Conservation Suite (Laptops)
* **Active Windows Power Plan & Vendor Scheme Detection**: Live display of your currently active Windows power scheme (e.g., `AMD Ryzen™ Balanced`, `Balanced`, `High Performance`), displaying full GUIDs, custom vendor badges (`🔥 AMD RYZEN™ CPPC TUNED`), and 1-click plan switcher buttons.
* **Real-Time Battery & Power Telemetry**: Instant battery percentage, AC adapter status, charging state, and automatic chassis classification (`🖥️ Desktop PC` vs `💻 Laptop`).
* **Processor Eco Boost Capping on DC**: Limits the configured maximum processor state on battery and adjusts Energy-Performance Preference (`PERFEPP`). Effects on temperature, fan noise, and battery runtime depend on the hardware and workload.
* **PCIe Link State Power Management (ASPM)**: Activates aggressive Active State Power Management (`powercfg /setdcvalueindex SCHEME_CURRENT SUB_PCIEXPRESS ASPM 2`) to power down idle PCIe bus lanes and NVMe storage on DC.
* **Fast Startup Configuration**: Can disable hybrid startup (`HiberbootEnabled = 0`). This changes startup behavior; any effect on overnight battery drain depends on the device.
* **Smart 80% / 20% Battery Health Audio & Toast Guard**: Live background monitoring guard that chimes and notifies you when charging hits 80% (to unplug and preserve lithium-ion cell longevity) or drops below 20% (to avoid deep discharge wear).
* **Official Windows Battery Health & Wear Diagnostics**: One-click generation of the detailed Microsoft Battery Lifecycle & Capacity Degradation report (`powercfg /batteryreport`) launched automatically in your browser.

### 15. 📦 Software Updater (WinGet)
* Integrates directly with Windows Package Manager to inspect and update all installed applications silently.

### 16. 📝 Live Activity Console
* Color-coded real-time execution log with copy-to-clipboard and export capabilities.

### 17. 📌 System Tray Mini-Mode & Background Monitoring
* **Background Notification Area Integration**: Minimizes seamlessly to the Windows System Tray with a high-resolution dark icon (`pystray`).
* **Quick Action Tray Menu**: Right-click the tray icon to run quick maintenance, open the *Battery & Power Saver* suite, or reopen the application.
* **Smart Background Guard**: Keeps battery health alerts (80% / 20% lithium cell guard) active without keeping the main GUI window on your screen.
* **Dedicated Tray Controls**: Header "📌 Minimize to Tray" button and automatic minimize-on-close protection to avoid accidental process termination.

---

## 🚀 How to Run

### Method 1: Double-Click Launcher (Recommended)
Double-click `Run_ApexOptimizer.bat` in the project root. It will automatically detect administrative rights and prompt for UAC elevation if required.

### Method 2: Python Command Line
```powershell
# Standard Launch
python main.py

# Or run directly via package module
python -m ui.app
```
*(Uses Python's standard library `tkinter`, `winreg`, and `ctypes`)*

### Headless Automation
Run one or more operations without opening the GUI:
```powershell
python main.py --optimize --gaming
python main.py --cleanup
python main.py --winget --restart
```
The cleanup option runs every listed cleanup target, including DISM component-store cleanup. The process returns a non-zero exit code for reported operation errors; `--restart` is skipped if an operation reports an error.

### Run Tests
Run the Windows-compatible regression tests with:
```powershell
python -m unittest discover -s tests -v
```

### 📁 Project Architecture
```text
WindowsOptimizationSoftware/
├── assets/                  # 256x256 high-resolution application icons
│   └── app_icon.ico
├── core/                    # Backend Optimization & OS Telemetry Engine
│   ├── base.py               # Registry, command, logging, and profile-hive helpers
│   ├── cleanup.py            # Disk cleanup and WinGet operations
│   ├── debloat.py            # AppX package and scheduled-task operations
│   ├── diagnostics.py        # Hardware telemetry, health score, and quick boost
│   ├── gaming.py             # Gaming and GPU settings
│   ├── optimizer.py          # Combined engine built from feature mixins
│   ├── power.py              # Battery and power-plan operations
│   ├── services.py           # Windows service configuration
│   └── tweaks.py             # System, privacy, and Explorer settings
├── ui/                      # Modern Tkinter Presentation Layer
│   ├── __init__.py
│   ├── app.py               # Main window controller, telemetry loop & tabs
│   ├── theme.py             # Windows Personalization accent & DWM color sync
│   ├── components.py        # DonutGauge, ToastManager, ModernCard, ToggleSwitch
│   ├── tray.py              # System Tray background menu & notification manager
│   └── search_data.py       # Live Ctrl+F search index registry
├── tests/                   # Standard-library unittest regression tests
├── main.py                  # Application entry point & automated UAC elevation
├── build_exe.py             # Standalone binary compiler (PyInstaller)
├── file_version_info.txt    # Windows PE version and developer metadata
├── Run_ApexOptimizer.bat    # 1-Click launcher script
├── Build_Executable.bat     # 1-Click build script
└── README.md                # Documentation & Architecture
```

### Method 3: Compile Standalone Single-File Executable (.exe)
Compile the entire suite into a single portable binary that runs on any Windows PC with zero Python installation required:
```powershell
# Double-click Build_Executable.bat, or run:
python build_exe.py
```
The compiled binary with embedded high-resolution icon and auto-UAC elevation manifest is saved to:
`dist\ApexWindowsOptimizer.exe`

---

## 👨‍💻 Developer & Author

**Rajkumar Patil**  
*Creator & Lead Developer of Apex Windows Optimizer*

* **GitHub**: [github.com/Rajkumsr](https://github.com/Rajkumsr)
* **LinkedIn**: [linkedin.com/in/rajkumar-patil-2b13a5180](https://www.linkedin.com/in/rajkumar-patil-2b13a5180)
