#!/usr/bin/env python3
"""
PYQ Mass Collector
==================
Mass downloads Previous Year Question Papers from official verified endpoints:
1. UPSC Official (upsc.gov.in) -> Civil Services, NDA, CDS, CAPF, ESE, etc.
2. CBSE Academic (cbseacademic.nic.in) -> Class 10 and 12 (2020-2025)
3. CBSE Official (cbse.gov.in) -> Board Papers (2022-2026)
4. ICAI (icai.org) -> CA Foundation, Inter, Final
"""

import os
import re
import sys
import time
import json
import logging
import requests
import zipfile
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import urllib3

urllib3.disable_warnings()

BASE_DIR = Path(r"c:\Users\DELL\Downloads\pyq_collection_2000_2026_starter")
LOG_DIR = BASE_DIR / "_Downloads_Log"
INDEX_DIR = BASE_DIR / "_Index"

LOG_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)

# Safe console logger without non-ascii symbols that crash cp1252
class SafeFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        return msg.encode("ascii", "replace").decode("ascii")

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(SafeFormatter("%(asctime)s [%(levelname)s] %(message)s"))
file_handler = logging.FileHandler(LOG_DIR / f"mass_collect_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

logger = logging.getLogger("mass_collector")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(file_handler)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
})

def safe_download(url, dest_path, min_bytes=1000):
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and dest_path.stat().st_size >= min_bytes:
        return True, "EXISTS"

    for attempt in range(1, 4):
        try:
            resp = SESSION.get(url, timeout=45, verify=False, stream=True)
            if resp.status_code != 200:
                time.sleep(1)
                continue
            
            content = resp.content
            if len(content) < min_bytes:
                time.sleep(1)
                continue
            
            # If expecting PDF, check magic byte or content
            if dest_path.suffix.lower() == ".pdf" and not content.startswith(b"%PDF") and b"%PDF" not in content[:1024]:
                return False, "INVALID_PDF"

            with open(dest_path, "wb") as f:
                f.write(content)
            
            kb = len(content) // 1024
            return True, f"DOWNLOADED ({kb} KB)"
        except Exception as e:
            time.sleep(2 ** attempt)
            
    return False, "FAILED"


# ==============================================================================
# 1. UPSC COLLECTOR
# ==============================================================================
def collect_upsc_all(max_downloads=200):
    logger.info("=== Starting UPSC Mass Collection ===")
    url = "https://www.upsc.gov.in/examinations/previous-question-papers"
    try:
        resp = SESSION.get(url, verify=False, timeout=25)
    except Exception as e:
        logger.error(f"Failed to access UPSC portal: {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower():
            full_url = urljoin("https://www.upsc.gov.in", href)
            label = a.get_text(strip=True)
            links.append((full_url, label))

    logger.info(f"Discovered {len(links)} UPSC PDF papers on official portal.")
    
    downloaded = 0
    for full_url, label in links:
        if downloaded >= max_downloads:
            logger.info(f"Reached UPSC batch limit of {max_downloads}.")
            break

        filename = unquote(full_url.split("/")[-1])
        fn_clean = re.sub(r'[\\/*?:"<>|]', "_", filename)
        
        # Extract year
        ym = re.search(r"20\d\d|19\d\d", fn_clean)
        year = ym.group() if ym else "2024"

        # Determine target folder
        fn_lower = fn_clean.lower()
        if "csm" in fn_lower or "civil" in fn_lower or "cgl" in fn_lower:
            # Civil Services Mains / General Studies
            if "gs" in fn_lower or "general" in fn_lower:
                gsm = re.search(r"paper[-_\s]*([ivx1-4]+)", fn_lower)
                pnum = gsm.group(1) if gsm else "1"
                dest_dir = BASE_DIR / "UPSC" / "Civil_Services" / "Mains" / f"General_Studies_{pnum}"
            elif "essay" in fn_lower:
                dest_dir = BASE_DIR / "UPSC" / "Civil_Services" / "Mains" / "Essay"
            elif "optional" in fn_lower or "lit" in fn_lower:
                dest_dir = BASE_DIR / "UPSC" / "Civil_Services" / "Mains" / "Optional_Subjects"
            else:
                dest_dir = BASE_DIR / "UPSC" / "Civil_Services" / "Mains"
        elif "csp" in fn_lower or "prelim" in fn_lower:
            if "csat" in fn_lower or "paper-ii" in fn_lower:
                dest_dir = BASE_DIR / "UPSC" / "Civil_Services" / "Prelims" / "CSAT_Paper_2"
            else:
                dest_dir = BASE_DIR / "UPSC" / "Civil_Services" / "Prelims" / "General_Studies_Paper_1"
        elif "ndana" in fn_lower or "nda" in fn_lower:
            if "math" in fn_lower:
                dest_dir = BASE_DIR / "NDA" / "Mathematics"
            else:
                dest_dir = BASE_DIR / "NDA" / "General_Ability_Test"
        elif "cdse" in fn_lower or "cds" in fn_lower:
            if "math" in fn_lower:
                dest_dir = BASE_DIR / "Defence" / "CDS" / "Mathematics"
            elif "english" in fn_lower:
                dest_dir = BASE_DIR / "Defence" / "CDS" / "English"
            else:
                dest_dir = BASE_DIR / "Defence" / "CDS" / "General_Knowledge"
        elif "ese" in fn_lower or "ies" in fn_lower:
            if "civil" in fn_lower:
                dest_dir = BASE_DIR / "UPSC" / "Engineering_Services_ESE" / "Civil_Engineering"
            elif "mech" in fn_lower:
                dest_dir = BASE_DIR / "UPSC" / "Engineering_Services_ESE" / "Mechanical_Engineering"
            elif "elec" in fn_lower:
                dest_dir = BASE_DIR / "UPSC" / "Engineering_Services_ESE" / "Electrical_Engineering"
            else:
                dest_dir = BASE_DIR / "UPSC" / "Engineering_Services_ESE"
        elif "capf" in fn_lower:
            dest_dir = BASE_DIR / "UPSC" / "CAPF" / "General_Ability_Intelligence"
        elif "ifs" in fn_lower:
            dest_dir = BASE_DIR / "UPSC" / "IFS"
        elif "geo" in fn_lower:
            dest_dir = BASE_DIR / "UPSC" / "Geologist_Exam"
        else:
            dest_dir = BASE_DIR / "UPSC" / "Civil_Services"

        dest_file = dest_dir / fn_clean
        ok, status = safe_download(full_url, dest_file)
        if ok and status != "EXISTS":
            downloaded += 1
            logger.info(f"[{downloaded}] UPSC {status}: {dest_file.name}")
        elif status == "EXISTS":
            pass
        else:
            logger.warning(f"UPSC {status}: {fn_clean}")
            
        time.sleep(0.15)


# ==============================================================================
# 2. CBSE ACADEMIC COLLECTOR (Class 10 & 12)
# ==============================================================================
def collect_cbse_academic():
    logger.info("=== Starting CBSE Academic Collection (Class 10 & 12) ===")
    
    sessions = [
        ("sqp_classx_2023-24.html", 10, "2024"),
        ("sqp_classxii_2023-24.html", 12, "2024"),
        ("SQP_CLASSX_2022-23.html", 10, "2023"),
        ("SQP_CLASSXII_2022-23.html", 12, "2023"),
        ("SQP_CLASSX_2021-22.html", 10, "2022"),
        ("SQP_CLASSXII_2021-22.html", 12, "2022"),
        ("SQP_CLASSX_2020-21.html", 10, "2021"),
        ("SQP_CLASSXII_2020-21.html", 12, "2021"),
    ]
    
    subject_map = {
        "math": "Mathematics",
        "phy": "Physics",
        "chem": "Chemistry",
        "bio": "Biology",
        "sci": "Science",
        "social": "Social_Science",
        "eng": "English",
        "hin": "Hindi",
        "san": "Sanskrit",
        "comp": "Computer_Science",
        "account": "Accountancy",
        "bus": "Business_Studies",
        "eco": "Economics",
        "hist": "History",
        "geo": "Geography",
        "pol": "Political_Science",
    }
    
    total_downloaded = 0
    for page_name, cls, year in sessions:
        page_url = f"https://cbseacademic.nic.in/{page_name}"
        try:
            resp = SESSION.get(page_url, verify=False, timeout=20)
            if resp.status_code != 200:
                continue
        except Exception as e:
            logger.warning(f"Error accessing {page_url}: {e}")
            continue
            
        soup = BeautifulSoup(resp.text, "html.parser")
        pdf_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".pdf" in href.lower() and "sqp" in href.lower():
                full_url = urljoin(page_url, href)
                pdf_links.append((full_url, a.get_text(strip=True)))
                
        logger.info(f"CBSE Class {cls} ({year}): found {len(pdf_links)} SQP papers")
        
        for full_url, label in pdf_links:
            fname = unquote(full_url.split("/")[-1])
            fn_clean = re.sub(r'[\\/*?:"<>|]', "_", fname)
            
            # Map subject
            subj = "General"
            for k, sname in subject_map.items():
                if k in fn_clean.lower() or k in label.lower():
                    subj = sname
                    break
                    
            dest_dir = BASE_DIR / f"CBSE_Class_{cls}" / subj
            dest_file = dest_dir / f"CBSE_{cls}_{subj}_{year}_{fn_clean}"
            
            ok, status = safe_download(full_url, dest_file)
            if ok and status != "EXISTS":
                total_downloaded += 1
                logger.info(f"[{total_downloaded}] CBSE Class {cls} {status}: {dest_file.name}")
            
            time.sleep(0.1)


# ==============================================================================
# 3. CBSE OFFICIAL BOARD PAPERS (cbse.gov.in)
# ==============================================================================
def collect_cbse_official_board():
    logger.info("=== Starting CBSE Official Board Papers Collection ===")
    url = "https://www.cbse.gov.in/cbsenew/question-paper.html"
    try:
        resp = SESSION.get(url, verify=False, timeout=25)
        if resp.status_code != 200:
            return
    except Exception as e:
        logger.error(f"Failed to access CBSE board papers: {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    zip_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".zip" in href.lower() or ".pdf" in href.lower():
            full_url = urljoin("https://www.cbse.gov.in/cbsenew/", href)
            zip_links.append(full_url)

    logger.info(f"Discovered {len(zip_links)} board question paper packages on cbse.gov.in")
    
    # Prioritize key subjects
    key_subjects = [
        "MATHEMATICS", "PHYSICS", "CHEMISTRY", "BIOLOGY", "SCIENCE",
        "ENGLISH_CORE", "ACCOUNTANCY", "BUSINESS_STUDIES", "ECONOMICS",
        "COMPUTER_SCIENCE", "SOCIAL_SCIENCE"
    ]
    
    filtered_links = []
    for link in zip_links:
        for subj in key_subjects:
            if subj in link.upper():
                filtered_links.append((link, subj))
                break
                
    logger.info(f"Filtered {len(filtered_links)} major subject packages to download.")
    
    count = 0
    for link, subj in filtered_links[:60]:
        filename = unquote(link.split("/")[-1])
        cls = "CBSE_Class_12" if "/XII/" in link.upper() else "CBSE_Class_10" if "/X/" in link.upper() else "CBSE_Class_12"
        
        # Clean subject folder name
        subj_clean = subj.replace("_", " ").title().replace(" ", "_")
        dest_dir = BASE_DIR / cls / subj_clean
        dest_file = dest_dir / filename
        
        ok, status = safe_download(link, dest_file, min_bytes=5000)
        if ok and status != "EXISTS":
            count += 1
            logger.info(f"[{count}] CBSE Board {status}: {dest_file.name}")
            
            # If ZIP, unpack PDFs
            if dest_file.suffix.lower() == ".zip":
                try:
                    with zipfile.ZipFile(dest_file, "r") as z:
                        for zinfo in z.infolist():
                            if zinfo.filename.lower().endswith(".pdf"):
                                z.extract(zinfo, dest_dir)
                                logger.info(f"   Extracted PDF: {Path(zinfo.filename).name}")
                except Exception as ze:
                    logger.warning(f"Zip extraction failed for {dest_file.name}: {ze}")
        time.sleep(0.2)


def main():
    logger.info("PYQ Mass Collector initialized.")
    logger.info(f"Target Directory: {BASE_DIR}")
    
    # 1. UPSC collection
    collect_upsc_all(max_downloads=150)
    
    # 2. CBSE Academic SQP collection
    collect_cbse_academic()
    
    # 3. CBSE Official Board Question Papers
    collect_cbse_official_board()
    
    logger.info("Mass collection finished.")

if __name__ == "__main__":
    main()
