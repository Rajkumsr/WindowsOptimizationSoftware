"""
Apex Windows Optimizer - Standalone Executable (.exe) Builder
Compiles the application into a single portable binary with:
- Zero Python runtime dependencies required on target systems
- Native High-DPI awareness and dark obsidian UI
- Automated UAC administrator privilege elevation manifest
- Embedded 256x256 high-resolution application icon
- Official Windows PE version and developer metadata (Rajkumar Patil)
"""

import os
import sys
import shutil
import subprocess
import time

# Ensure UTF-8 output across all Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def print_banner():
    banner = r"""
========================================================================
     >> APEX WINDOWS OPTIMIZER PRO - STANDALONE EXE COMPILER <<
                 Created by Rajkumar Patil
========================================================================
    """
    print(banner)

def ensure_dependencies():
    """Ensure PyInstaller is installed."""
    print("[1/5] Checking build dependencies...")
    try:
        import PyInstaller
        print(f"      [OK] PyInstaller {PyInstaller.__version__} is ready.")
    except ImportError:
        print("      [*] PyInstaller not detected. Installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("      [OK] PyInstaller installed successfully.")

def ensure_icon(project_root):
    """Ensure the application icon exists."""
    print("[2/5] Checking application icon...")
    icon_path = os.path.join(project_root, "assets", "app_icon.ico")
    if not os.path.exists(icon_path):
        print("      [*] assets/app_icon.ico not found. Generating high-res icon...")
        ps_script = os.path.join(project_root, "generate_icon.ps1")
        if os.path.exists(ps_script):
            subprocess.check_call(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script])
        else:
            raise FileNotFoundError("Neither assets/app_icon.ico nor generate_icon.ps1 was found.")
    print(f"      [OK] Application icon verified ({os.path.getsize(icon_path):,} bytes).")
    return icon_path

def clean_previous_builds(project_root):
    """Clean leftover build artifacts."""
    print("[3/5] Cleaning prior build cache...")
    build_dir = os.path.join(project_root, "build")

    if os.path.exists(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)
    print("      [OK] Clean workspace ready.")

def build_executable(project_root, icon_path):
    """Invoke PyInstaller to generate the standalone single-file binary."""
    print("[4/5] Compiling standalone binary with PyInstaller...")
    version_file = os.path.join(project_root, "file_version_info.txt")
    main_script = os.path.join(project_root, "main.py")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--uac-admin",
        "--name", "ApexWindowsOptimizer",
        "--specpath", os.path.join(project_root, "build"),
        "--workpath", os.path.join(project_root, "build", "pyinstaller"),
        "--distpath", os.path.join(project_root, "dist"),
        "--icon", icon_path,
        "--paths", project_root,
        "--add-data", f"{os.path.join(project_root, 'assets')};assets",
        "--hidden-import", "pystray._win32",
        "--hidden-import", "PIL",
        "--hidden-import", "psutil",
        "--collect-submodules", "ui",
        "--clean",
        main_script
    ]

    if os.path.exists(version_file):
        cmd.extend(["--version-file", version_file])

    start_time = time.time()
    result = subprocess.run(cmd, cwd=project_root)
    elapsed = time.time() - start_time

    if result.returncode != 0:
        print(f"\n[ERROR] PyInstaller compilation failed with return code {result.returncode}")
        sys.exit(result.returncode)

    print(f"      [OK] Compilation finished in {elapsed:.1f} seconds.")

def verify_output(project_root):
    """Verify and report on the compiled output binary."""
    print("[5/5] Verifying binary integrity...")
    exe_path = os.path.join(project_root, "dist", "ApexWindowsOptimizer.exe")
    if not os.path.exists(exe_path):
        print(f"[ERROR] Expected output file not found at: {exe_path}")
        sys.exit(1)

    size_bytes = os.path.getsize(exe_path)
    size_mb = size_bytes / (1024 * 1024)

    print("\n" + "=" * 72)
    print("  [SUCCESS] STANDALONE EXECUTABLE BUILT WITH SUCCESS!")
    print("=" * 72)
    print(f"  * Binary Name     : ApexWindowsOptimizer.exe")
    print(f"  * Output Location : {exe_path}")
    print(f"  * File Size       : {size_mb:.2f} MB ({size_bytes:,} bytes)")
    print(f"  * Architecture    : 64-bit Windows Standalone Binary")
    print(f"  * Elevation       : Auto UAC Admin Elevation Configured")
    print(f"  * Developer       : Rajkumar Patil")
    print("=" * 72)
    print("  You can now distribute this single .exe file to any Windows PC.")
    print("  It runs completely independently without requiring Python installed!\n")

def main():
    print_banner()
    project_root = os.path.dirname(os.path.abspath(__file__))
    ensure_dependencies()
    icon_path = ensure_icon(project_root)
    clean_previous_builds(project_root)
    build_executable(project_root, icon_path)
    verify_output(project_root)

if __name__ == "__main__":
    main()
