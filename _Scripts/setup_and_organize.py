#!/usr/bin/env python3
"""
Quick setup script - installs dependencies and runs organizer on existing files.
Run this first before the main downloader.
"""
import subprocess
import sys
from pathlib import Path

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

print("Installing dependencies...")
for pkg in ["requests", "beautifulsoup4", "lxml"]:
    try:
        install(pkg)
        print(f"  ✅ {pkg}")
    except Exception as e:
        print(f"  ❌ {pkg}: {e}")

print("\nRunning organizer on existing archive...")
organizer = Path(__file__).parent / "pyq_organizer.py"
subprocess.run([sys.executable, str(organizer), "--organize", "--index", "--report"])

print("\nSetup complete! Now run RUN_DOWNLOADER.bat to start downloading.")
