#!/usr/bin/env python3
"""
NEET and JEE Mains Clean Collector
===================================
Downloads verified authentic Previous Year Question Papers for:
1. NEET (2022 to 2026) -> NEET/
2. JEE Mains (2022 to 2026 all shifts) -> JEE/JEE_Mains/
"""

import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote
import requests
import urllib3

urllib3.disable_warnings()

BASE_DIR = Path(r"c:\Users\DELL\Downloads\pyq_collection_2000_2026_starter")

NEET_URLS = [
    "https://ntaexampapers.com/wp-content/uploads/NEET-2022-Question-Paper.pdf",
    "https://ntaexampapers.com/wp-content/uploads/NEET-2023-Question-Paper.pdf",
    "https://ntaexampapers.com/wp-content/uploads/NEET-2024-Question-Paper.pdf",
    "https://ntaexampapers.com/wp-content/uploads/NEET-2025-Question-Paper.pdf",
    "https://ntaexampapers.com/wp-content/uploads/NEET-2026-Question-Paper-Code-11.pdf",
]

JEE_MAIN_URLS = [
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2022-Question-Paper.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2023-Question-Paper.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Answer-Key-Session-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Answer-Key-Session-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Arch-B.Planning-12-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Arch-12-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Planning-12-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Tech-4-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Tech-4-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Tech-5-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Tech-5-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Tech-6-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Tech-6-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Tech-8-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Tech-8-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Tech-9-Apr-Shift-1-Hindi.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2024-Question-Paper-B.Tech-9-Apr-Shift-2-Hindi.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Answer-Key-Session-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Answer-Key-Session-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Arch-B.Planing-9-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Arch-30-Jan-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Planing-9-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-02-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-2-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-22-Jan-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-23-Jan-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-28-Jan-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-28-Jan-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-29-Jan-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-3-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-3-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-4-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-4-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-7-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-7-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2025-Question-Paper-B.Tech-8-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2026-Answer-Key-Session-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2026-Question-Paper-B-Tech-2nd-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2026-Question-Paper-B-Tech-4th-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2026-Question-Paper-B-Tech-4th-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2026-Question-Paper-B-Tech-5th-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2026-Question-Paper-B-Tech-5th-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2026-Question-Paper-B-Tech-6th-Apr-Shift-1.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2026-Question-Paper-B-Tech-6th-Apr-Shift-2.pdf",
    "https://ntaexampapers.com/wp-content/uploads/JEE-Main-2026-Question-Paper-B-Tech-8th-Apr-Shift-2.pdf",
]

def download(url, dest):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 10000:
        print(f"  [EXISTS] {dest.name}")
        return True
    for attempt in range(1, 4):
        try:
            r = requests.get(url, verify=False, timeout=60)
            if r.status_code == 200 and r.content.startswith(b"%PDF"):
                with open(dest, "wb") as f:
                    f.write(r.content)
                kb = len(r.content) // 1024
                print(f"  [OK ({kb} KB)] {dest.name}")
                return True
            time.sleep(1)
        except Exception as e:
            time.sleep(2 ** attempt)
    print(f"  [FAILED] {dest.name}")
    return False

def main():
    print("=== DOWNLOADING NEET PAPERS ===")
    neet_dir = BASE_DIR / "NEET"
    for u in NEET_URLS:
        fname = unquote(u.split("/")[-1])
        download(u, neet_dir / fname)
        time.sleep(0.5)

    print("\n=== DOWNLOADING JEE MAINS PAPERS ===")
    jee_dir = BASE_DIR / "JEE" / "JEE_Mains"
    for u in JEE_MAIN_URLS:
        fname = unquote(u.split("/")[-1])
        download(u, jee_dir / fname)
        time.sleep(0.5)

    print("\nDone!")

if __name__ == "__main__":
    main()
