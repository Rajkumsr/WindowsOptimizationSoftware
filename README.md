# Apex Windows Optimizer (Pro Suite v2.0)

A modern, high-performance, dark-themed Windows optimization and debloating desktop application built with Python and Tkinter.

---

## 🌟 Highlights & Capabilities

### 1. 📊 Comprehensive Dashboard & Live Telemetry
* **Real-time Live Telemetry**: Live RAM monitoring loop (free, total, and percentage load) updated periodically, along with CPU, storage, and active chassis detection (`🖥️ Desktop PC` vs `💻 Laptop`).
* **One-Click Quick Optimization**: Applies recommended safety tweaks across performance, privacy, and shell settings with automated rollback snapshot creation.
* **Instant Utilities**: Flush DNS cache, restart Windows Explorer shell, export registry backups, and create System Restore points.

### 2. ⚡ Real State Detection & Bi-Directional Toggles
* **Live System State Inspection**: On launch, the software inspects the Windows Registry to determine what is already `[OPTIMIZED]` vs `[DEFAULT]`.
* **Bi-Directional Revert / Undo**: Turning any toggle switch `OFF` restores standard Windows default configurations cleanly.
* **Multi-User Profile Deployment**: Mounts `C:\Users\Default\NTUSER.DAT` into `HKU` so customizations automatically deploy to **all current and future user accounts**.

### 3. 🎯 High-DPI Display Scaling Awareness
* Fully declared DPI-aware process (`SetProcessDpiAwareness`) rendering crisp, clear text and cards on 1080p, 1440p, 4K, and 125%/150% scaled displays.
* Scoped, smooth mousewheel scrolling that eliminates cross-tab scroll bleeding.

### 4. ⚡ System & Kernel Performance
* **Disable Network Throttling**: Uncaps multimedia and gaming network traffic (`NetworkThrottlingIndex` = `0xFFFFFFFF`).
* **Foreground Responsiveness**: Sets 90% CPU priority for active applications and games (`SystemResponsiveness` = `10`).
* **Accelerated Shutdown**: Shortens service termination delay to 5 seconds (`WaitToKillServiceTimeout` = `5000`).
* **NTFS Long File Paths**: Eliminates the legacy MAX_PATH 260-character limitation.
* **Firmware WPBT & OEM Bloat Blocking**: Prevents motherboard BIOS/UEFI firmware from injecting promotional software into Windows at boot.
* **IRP Stack Size Tuning**: Optimizes server communication buffer size (`IRPStackSize` = `30`) for high-throughput LAN file sharing.
* **Disable P2P Update Seeding**: Prevents Delivery Optimization from using your upstream bandwidth to seed updates to external PCs.
* **F8 Legacy Boot Menu**: Restores classic boot options for instant recovery.
* **Desktop Hibernation Control**: Disables `hiberfil.sys` on desktop systems to reclaim disk space equivalent to total RAM size.

### 5. 🛡️ Privacy & Telemetry
* **Diagnostic Data & CEIP**: Disables DiagTrack, feedback notifications, error reporting telemetry, and Customer Experience Improvement tasks.
* **Lock Screen Spotlight Ads**: Removes rotating sponsored tips and recommendations.
* **Microsoft Recall AI**: Blocks automated background screenshot harvesting.
* **Edge Optimization**: Disables Edge background preloading, startup boost, shopping assistant, and telemetry.
* **Office Telemetry**: Disables telemetry logging and feedback for Microsoft Office 2013-365.

### 6. 🎨 Explorer & Shell Personalization
* **File Extensions Visibility**: Always displays `.exe`, `.zip`, `.pdf`, etc. to prevent spoofing.
* **Open to 'This PC'**: Sets File Explorer default view directly to drives instead of Quick Access.
* **Windows 11 Classic Context Menu**: Restores full right-click context menu instantly.
* **Start Menu Search Privacy**: Disables Bing web search integration to keep search purely local.
* **Taskbar 'End Task'**: Enables direct process termination from taskbar right-click.
* **Taskbar Cleanup**: Hides widgets and Copilot buttons.
* **Accelerated Menu Delays**: Reduces menu show delay to 10ms.
* **Sticky Keys Prompt**: Disables 5x Shift dialog.

### 7. ⚙️ Services Optimizer
* **Granular Startup Control**: Presets for *Recommended (Safe)*, *Maximum Gaming*, and *Reset to Demand*.
* Configures telemetry, Xbox background services, diagnostic hubs, and error reporting services without breaking core Windows functionality.

### 8. 🗑️ App Debloater
* Uninstalls and unprovisions bloatware for current and future user accounts:
  * Microsoft Copilot
  * Bing Search Experience
  * Windows Widgets Runtime & Client Web Experience
  * MSN News & Weather
  * Solitaire Collection
  * Microsoft People & Feedback Hub
  * Phone Link (Your Phone)
  * Tips / Get Started

### 9. 🎮 Gaming & GPU Boost
* **Hardware-Accelerated GPU Scheduling (HAGS)**: Transfers frame scheduling directly to GPU VRAM.
* **Windowed Games Optimizations**: Modern flip presentation model for DirectX 10/11 games.
* **MMCSS Scheduling**: Configures maximum priority (`GPU Priority` = 8, `Priority` = 6, `SFIO Priority` = High).
* **Power Throttling Disable**: Prevents CPU frequency degradation during intense workloads.
* **Ultimate Performance Power Scheme**: Activates Windows' hidden latency-free power plan.
* **HPET Reset**: Removes explicit timer overrides to prevent micro-stuttering.

### 10. 🔋 Battery Health & AC Power Bypass (Laptop & Acer Hardware)
* **Real-time Live Battery Telemetry**: Zero-overhead native kernel gauge showing exact percentage, charging status, and AC connection state.
* **Acer 80% Battery Charge Limit (AC Direct Bypass)**:
  * Locks maximum charge level to 80% and routes charger power directly to the motherboard/components (bypassing battery cells).
  * Prevents high-voltage saturation, thermal degradation, and battery swelling during prolonged gaming or desktop charging.
  * Dual-layer actuation: directly invokes `root\wmi:BatteryControl.SetBatteryHealthControl` and synchronizes with Acer's background service (`ACCSvc`).
* **Official Windows Battery Health Report**: 1-click diagnostic generator (`powercfg /batteryreport`) showing design capacity, full charge capacity, wear level %, and cycle history.
* **Prevent Standby & Shutdown Battery Drain**: One-click toggle to disable Windows Fast Startup (`HiberbootEnabled`), eliminating phantom 3-5% overnight battery discharge.

### 11. 🧹 Deep Disk & Cache Cleaner (Real BeardSweeper)
* Calculates exact reclaimable storage space before cleaning:
  * Windows System Temp & User Profile Temp
  * Windows Update Download Cache (`SoftwareDistribution\Download`)
  * DirectX Shader Cache (`D3DSCache`)
  * Delivery Optimization Cache
  * Crash Dumps & Windows Error Reports
  * Explorer Thumbnail Cache

### 12. 📦 Software Updater (WinGet)
* Integrates directly with Windows Package Manager to inspect and update all installed applications silently.

### 13. 📝 Live Activity Console
* Color-coded real-time execution log with copy-to-clipboard and export capabilities.

---

## 🚀 How to Run

### Method 1: Double-Click Launcher (Recommended)
Double-click `Run_ApexOptimizer.bat` in the project root. It will automatically detect administrative rights and prompt for UAC elevation if required.

### Method 2: Python Command Line
```powershell
# Standard Launch
python main.py

# Or run directly with GUI script
python gui_app.py
```
*(No external pip dependencies required — uses Python's standard library `tkinter`, `winreg`, and `ctypes`)*

---

## 👨‍💻 Developer & Author

**Rajkumar Patil**  
*Creator & Lead Developer of Apex Windows Optimizer*

* **GitHub**: [github.com/Rajkumsr](https://github.com/Rajkumsr)
* **LinkedIn**: [linkedin.com/in/rajkumar-patil-2b13a5180](https://www.linkedin.com/in/rajkumar-patil-2b13a5180)

