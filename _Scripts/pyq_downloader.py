#!/usr/bin/env python3
"""
PYQ Collection Master Downloader
=================================
Downloads Previous Year Question Papers from 2000 to 2026 from multiple
public sources for all major Indian competitive and board exams.

Sources:
  - CBSE Official (cbseacademic.nic.in, cbse.gov.in)
  - ICAI Official (icai.org) for CA exams
  - Mrunal.org / UPSC resources
  - Various open-access repositories

Usage:
    python pyq_downloader.py --exam ALL
    python pyq_downloader.py --exam JEE --years 2015-2024
    python pyq_downloader.py --exam NEET
    python pyq_downloader.py --exam UPSC
    python pyq_downloader.py --exam CA
    python pyq_downloader.py --exam CBSE --class 10
    python pyq_downloader.py --exam CBSE --class 12
    python pyq_downloader.py --list-exams
"""

import os
import sys
import time
import json
import argparse
import logging
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Setup ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / "_Scripts"
LOG_DIR = BASE_DIR / "_Downloads_Log"
INDEX_DIR = BASE_DIR / "_Index"

LOG_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/pdf,application/xhtml+xml,*/*",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

DOWNLOAD_INDEX = {}  # Track all downloads


# ── Helpers ──────────────────────────────────────────────────────────────────
def download_file(url: str, dest_path: Path, retries: int = 3) -> bool:
    """Download a file from URL to dest_path with retry logic."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists():
        logger.info(f"  SKIP (exists): {dest_path.name}")
        return True

    for attempt in range(1, retries + 1):
        try:
            resp = SESSION.get(url, timeout=60, stream=True)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower() and "octet-stream" not in content_type.lower():
                # Check if it's actually a PDF by looking at magic bytes
                first_bytes = b""
                chunk_gen = resp.iter_content(chunk_size=1024)
                first_chunk = next(chunk_gen, b"")
                if not first_chunk.startswith(b"%PDF"):
                    logger.warning(f"  NOT PDF: {url}")
                    return False
                first_bytes = first_chunk

            with open(dest_path, "wb") as f:
                if first_bytes:
                    f.write(first_bytes)
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            size_kb = dest_path.stat().st_size // 1024
            logger.info(f"  ✅ Downloaded ({size_kb} KB): {dest_path.name}")
            DOWNLOAD_INDEX[str(dest_path)] = {
                "url": url,
                "size_kb": size_kb,
                "downloaded_at": datetime.now().isoformat(),
            }
            return True

        except requests.exceptions.RequestException as e:
            logger.warning(f"  Attempt {attempt}/{retries} failed for {url}: {e}")
            time.sleep(2 ** attempt)

    logger.error(f"  ❌ Failed after {retries} attempts: {url}")
    return False


def save_index():
    """Save the download index to JSON."""
    index_file = INDEX_DIR / "download_index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(DOWNLOAD_INDEX, f, indent=2, ensure_ascii=False)
    logger.info(f"Index saved: {index_file}")


# ── CBSE Class 10 & 12 ───────────────────────────────────────────────────────
def download_cbse(class_level: int = None):
    """Download CBSE PYQs from official and open sources."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING CBSE PYQs")
    logger.info("=" * 60)

    # CBSE official question paper URLs follow predictable patterns
    # Source: cbseacademic.nic.in
    cbse_sources = {
        10: {
            "Mathematics": [
                ("2024", "https://cbseacademic.nic.in/web_material/QP/2024/10th/MATHEMATICS_STD_Outside_Delhi_2024.pdf"),
                ("2023", "https://cbseacademic.nic.in/web_material/QP/2023/10th/Mathematics-Standard.pdf"),
                ("2022", "https://cbseacademic.nic.in/web_material/QP/2022/10th/Mathematics-Standard.pdf"),
            ],
            "Science": [
                ("2024", "https://cbseacademic.nic.in/web_material/QP/2024/10th/SCIENCE_Outside_Delhi_2024.pdf"),
                ("2023", "https://cbseacademic.nic.in/web_material/QP/2023/10th/Science.pdf"),
            ],
        },
        12: {
            "Mathematics": [
                ("2024", "https://cbseacademic.nic.in/web_material/QP/2024/12th/MATHEMATICS_Outside_Delhi_2024.pdf"),
                ("2023", "https://cbseacademic.nic.in/web_material/QP/2023/12th/Mathematics.pdf"),
            ],
            "Physics": [
                ("2024", "https://cbseacademic.nic.in/web_material/QP/2024/12th/PHYSICS_Outside_Delhi_2024.pdf"),
                ("2023", "https://cbseacademic.nic.in/web_material/QP/2023/12th/Physics.pdf"),
            ],
            "Chemistry": [
                ("2024", "https://cbseacademic.nic.in/web_material/QP/2024/12th/CHEMISTRY_Outside_Delhi_2024.pdf"),
                ("2023", "https://cbseacademic.nic.in/web_material/QP/2023/12th/Chemistry.pdf"),
            ],
            "Biology": [
                ("2024", "https://cbseacademic.nic.in/web_material/QP/2024/12th/BIOLOGY_Outside_Delhi_2024.pdf"),
                ("2023", "https://cbseacademic.nic.in/web_material/QP/2023/12th/Biology.pdf"),
            ],
        },
    }

    classes = [10, 12] if class_level is None else [class_level]
    for cls in classes:
        if cls not in cbse_sources:
            continue
        for subject, papers in cbse_sources[cls].items():
            folder = BASE_DIR / f"CBSE_Class_{cls}" / subject
            folder.mkdir(parents=True, exist_ok=True)
            for year, url in papers:
                filename = f"CBSE_Class{cls}_{subject}_{year}.pdf"
                download_file(url, folder / filename)
                time.sleep(0.5)


# ── JEE Mains & Advanced ─────────────────────────────────────────────────────
def download_jee():
    """Download JEE Main and Advanced PYQs."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING JEE PYQs")
    logger.info("=" * 60)

    # JEE Advanced official PDFs (iitb.ac.in, jeeadv.ac.in)
    jee_advanced_papers = []
    for year in range(2013, 2025):
        for paper in [1, 2]:
            jee_advanced_papers.append({
                "year": year,
                "paper": paper,
                "url": f"https://jeeadv.ac.in/past_qps/jee_adv_{year}_paper_{paper}.pdf",
                "folder": BASE_DIR / "JEE" / "JEE_Advanced" / f"Paper_{paper}",
                "filename": f"JEE_Advanced_{year}_Paper_{paper}.pdf",
            })

    # JEE Main (NTA official)
    jee_main_papers = []
    for year in range(2014, 2025):
        jee_main_papers.append({
            "year": year,
            "url": f"https://cdn3.digialm.com/EForms/configuredHtml/1258/68964/Exam/{year}_JEE_Main_Paper.pdf",
            "folder": BASE_DIR / "JEE" / "JEE_Mains",
            "filename": f"JEE_Main_{year}.pdf",
        })

    all_papers = jee_advanced_papers + jee_main_papers
    for paper_info in all_papers:
        paper_info["folder"].mkdir(parents=True, exist_ok=True)
        download_file(paper_info["url"], paper_info["folder"] / paper_info["filename"])
        time.sleep(0.3)


# ── NEET ─────────────────────────────────────────────────────────────────────
def download_neet():
    """Download NEET PYQs."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING NEET PYQs")
    logger.info("=" * 60)

    neet_folder = BASE_DIR / "NEET"
    neet_folder.mkdir(parents=True, exist_ok=True)

    # NEET papers from NTA official (nta.ac.in / ntaresults.nic.in)
    neet_years = list(range(2013, 2025))  # NEET started 2013 (earlier AIPMT)
    aipmt_years = list(range(2000, 2013))  # AIPMT before NEET

    for year in neet_years:
        url = f"https://nta.ac.in/Download/ExamArticles/NEET_{year}_Question_Paper.pdf"
        filename = f"NEET_{year}_QP.pdf"
        download_file(url, neet_folder / filename)
        time.sleep(0.3)

    for year in aipmt_years:
        url = f"https://cbse.gov.in/cbsenew/documents/AIPMT_{year}.pdf"
        filename = f"AIPMT_{year}_QP.pdf"
        download_file(url, neet_folder / filename)
        time.sleep(0.3)


# ── NDA ───────────────────────────────────────────────────────────────────────
def download_nda():
    """Download NDA PYQs from UPSC official."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING NDA PYQs")
    logger.info("=" * 60)

    nda_folder = BASE_DIR / "NDA"
    upsc_nda_folder = BASE_DIR / "UPSC" / "NDA_NA"

    for folder in [nda_folder, upsc_nda_folder]:
        folder.mkdir(parents=True, exist_ok=True)

    for year in range(2000, 2025):
        for exam_num in [1, 2]:
            url = f"https://upsc.gov.in/sites/default/files/QP-NDA-{year}-{exam_num:02d}.pdf"
            filename = f"NDA_{year}_{exam_num}.pdf"
            download_file(url, nda_folder / filename)
            time.sleep(0.3)


# ── CA Exams (ICAI) ───────────────────────────────────────────────────────────
def download_ca():
    """Download CA Foundation, Intermediate, and Final PYQs from ICAI."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING CA PYQs (ICAI)")
    logger.info("=" * 60)

    # ICAI official question paper portal: icai.org
    # Papers are categorized as May/November attempts
    ca_levels = {
        "CA_Foundation": {
            "folder": BASE_DIR / "CA" / "CA_Foundation",
            "subjects": {
                "Paper_1_Accounting": "P1",
                "Paper_2_Business_Laws": "P2",
                "Paper_3_Mathematics_Statistics": "P3",
                "Paper_4_Business_Economics": "P4",
            },
            "start_year": 2004,  # CPT introduced 2004, Foundation from 2018
        },
        "CA_Intermediate": {
            "folder": BASE_DIR / "CA" / "CA_Intermediate",
            "subjects": {
                "Paper_1_Advanced_Accounting": "P1",
                "Paper_2_Corporate_Laws": "P2",
                "Paper_3_Cost_Accounting": "P3",
                "Paper_4_Taxation": "P4",
                "Paper_5_Advanced_Accounting": "P5",
                "Paper_6_Auditing": "P6",
                "Paper_7_Financial_Management": "P7",
            },
            "start_year": 2002,
        },
        "CA_Final": {
            "folder": BASE_DIR / "CA" / "CA_Final",
            "subjects": {
                "Paper_1_Financial_Reporting": "P1",
                "Paper_2_Strategic_FM": "P2",
                "Paper_3_Advanced_Auditing": "P3",
                "Paper_4_Corporate_Laws": "P4",
                "Paper_5_Strategic_Management": "P5",
                "Paper_6_ISCA": "P6",
                "Paper_7_Direct_Tax": "P7",
                "Paper_8_Indirect_Tax": "P8",
            },
            "start_year": 2000,
        },
    }

    for level_name, level_info in ca_levels.items():
        level_folder = level_info["folder"]
        level_folder.mkdir(parents=True, exist_ok=True)

        for year in range(level_info["start_year"], 2025):
            for attempt in ["May", "November"]:
                for subject, code in level_info["subjects"].items():
                    subject_folder = level_folder / subject
                    subject_folder.mkdir(exist_ok=True)

                    # ICAI official URL pattern
                    url = (
                        f"https://www.icai.org/post/question-papers/"
                        f"{level_name.lower().replace('_', '-')}/{year}/{attempt.lower()}/{code}.pdf"
                    )
                    filename = f"CA_{level_name}_{subject}_{year}_{attempt}.pdf"
                    download_file(url, subject_folder / filename)
                    time.sleep(0.2)


# ── UPSC ─────────────────────────────────────────────────────────────────────
def download_upsc():
    """Download UPSC Civil Services and other UPSC exam PYQs."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING UPSC PYQs")
    logger.info("=" * 60)

    upsc_base = BASE_DIR / "UPSC"

    # Civil Services Prelims
    for year in range(2000, 2025):
        # GS Paper 1
        url = f"https://upsc.gov.in/sites/default/files/QP-CSP-GS-{year}.pdf"
        dest = upsc_base / "Civil_Services" / "Prelims" / "General_Studies_Paper_1" / f"UPSC_CSE_Prelims_GS1_{year}.pdf"
        download_file(url, dest)
        time.sleep(0.3)

        # CSAT (from 2011)
        if year >= 2011:
            url = f"https://upsc.gov.in/sites/default/files/QP-CSP-CSAT-{year}.pdf"
            dest = upsc_base / "Civil_Services" / "Prelims" / "CSAT_Paper_2" / f"UPSC_CSE_Prelims_CSAT_{year}.pdf"
            download_file(url, dest)
            time.sleep(0.3)

    # Civil Services Mains
    for year in range(2000, 2025):
        for paper_num in range(1, 5):
            url = f"https://upsc.gov.in/sites/default/files/QP-CSM-GS{paper_num}-{year}.pdf"
            dest = upsc_base / "Civil_Services" / "Mains" / f"General_Studies_{paper_num}" / f"UPSC_CSE_Mains_GS{paper_num}_{year}.pdf"
            download_file(url, dest)
            time.sleep(0.2)

        # Essay
        url = f"https://upsc.gov.in/sites/default/files/QP-CSM-Essay-{year}.pdf"
        dest = upsc_base / "Civil_Services" / "Mains" / "Essay" / f"UPSC_CSE_Mains_Essay_{year}.pdf"
        download_file(url, dest)
        time.sleep(0.2)

    # CDS (Combined Defence Services)
    for year in range(2000, 2025):
        for exam_num in [1, 2]:
            for subject in ["Mathematics", "English", "GK"]:
                url = f"https://upsc.gov.in/sites/default/files/QP-CDS-{subject[:3].upper()}-{year}-{exam_num}.pdf"
                dest = upsc_base / "CDS" / subject / f"CDS_{year}_{exam_num}_{subject}.pdf"
                download_file(url, dest)
                time.sleep(0.2)

    # ESE (Engineering Services)
    for year in range(2000, 2025):
        for stream in ["Civil", "Mechanical", "Electrical", "Electronics"]:
            stream_folder = upsc_base / "Engineering_Services_ESE" / f"{stream}_Engineering"
            stream_folder.mkdir(parents=True, exist_ok=True)
            url = f"https://upsc.gov.in/sites/default/files/QP-ESE-{stream[:3].upper()}-{year}.pdf"
            dest = stream_folder / f"ESE_{year}_{stream}.pdf"
            download_file(url, dest)
            time.sleep(0.2)

    # CAPF
    for year in range(2003, 2025):
        url = f"https://upsc.gov.in/sites/default/files/QP-CAPF-GS-{year}.pdf"
        dest = upsc_base / "CAPF" / "General_Ability_Intelligence" / f"CAPF_{year}_Paper1.pdf"
        download_file(url, dest)
        time.sleep(0.3)


# ── SSC ───────────────────────────────────────────────────────────────────────
def download_ssc():
    """Download SSC exam PYQs."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING SSC PYQs")
    logger.info("=" * 60)

    ssc_base = BASE_DIR / "SSC"

    # SSC CGL
    for year in range(2000, 2025):
        for tier in [1, 2]:
            url = f"https://ssc.nic.in/SSCFileServer/PortalManagement/UploadedFiles/QP_CGL_T{tier}_{year}.pdf"
            dest = ssc_base / "CGL" / f"Tier_{tier}" / f"SSC_CGL_Tier{tier}_{year}.pdf"
            download_file(url, dest)
            time.sleep(0.2)

    # SSC CHSL
    for year in range(2003, 2025):
        for tier in [1, 2]:
            url = f"https://ssc.nic.in/SSCFileServer/PortalManagement/UploadedFiles/QP_CHSL_T{tier}_{year}.pdf"
            dest = ssc_base / "CHSL" / f"Tier_{tier}" / f"SSC_CHSL_Tier{tier}_{year}.pdf"
            download_file(url, dest)
            time.sleep(0.2)


# ── Banking ───────────────────────────────────────────────────────────────────
def download_banking():
    """Download Banking exam PYQs (IBPS, SBI, RBI)."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING BANKING PYQs")
    logger.info("=" * 60)

    banking_base = BASE_DIR / "Banking"

    # Note: IBPS and SBI official sites don't host question papers publicly
    # We document the structure and use alternative open sources
    banking_exams = {
        "IBPS_PO": {"start": 2011, "phases": ["Prelims", "Mains"]},
        "IBPS_Clerk": {"start": 2011, "phases": ["Prelims", "Mains"]},
        "SBI_PO": {"start": 2000, "phases": ["Prelims", "Mains"]},
        "SBI_Clerk": {"start": 2000, "phases": ["Prelims", "Mains"]},
        "RBI_Grade_B": {"start": 2005, "phases": ["Phase_1", "Phase_2"]},
    }

    for exam, info in banking_exams.items():
        for year in range(info["start"], 2025):
            for phase in info["phases"]:
                dest_folder = banking_base / exam / phase
                dest_folder.mkdir(parents=True, exist_ok=True)
                # Placeholder file indicating where papers should go
                placeholder = dest_folder / f"{exam}_{year}_{phase}_TO_BE_DOWNLOADED.txt"
                if not placeholder.exists():
                    with open(placeholder, "w") as f:
                        f.write(f"Source: {exam} {phase} {year}\n")
                        f.write("Download from: https://www.ibps.in/question-papers/ or bank official sites\n")


# ── Railways ──────────────────────────────────────────────────────────────────
def download_railways():
    """Download Railways (RRB) exam PYQs."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING RAILWAYS PYQs")
    logger.info("=" * 60)

    railways_base = BASE_DIR / "Railways"

    rrb_exams = {
        "RRB_NTPC": ["CBT_1", "CBT_2"],
        "RRB_JE": ["CBT_1", "CBT_2"],
        "RRB_Group_D": [""],
        "RRB_ALP": [""],
    }

    for exam, phases in rrb_exams.items():
        for phase in phases:
            if phase:
                folder = railways_base / exam / phase
            else:
                folder = railways_base / exam
            folder.mkdir(parents=True, exist_ok=True)

            # RRB official (indianrailways.gov.in / rrbcdg.gov.in)
            for year in range(2000, 2025):
                url = f"https://www.rrbcdg.gov.in/uploads/QP_{exam}_{phase}_{year}.pdf"
                filename = f"{exam}_{phase}_{year}.pdf" if phase else f"{exam}_{year}.pdf"
                download_file(url, folder / filename)
                time.sleep(0.2)


# ── CAT / Management ─────────────────────────────────────────────────────────
def download_management():
    """Download Management entrance PYQs (CAT, XAT, SNAP etc)."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING MANAGEMENT ENTRANCE PYQs")
    logger.info("=" * 60)

    mgmt_base = BASE_DIR / "Management_Entrance"

    # CAT (IIM official)
    for year in range(2000, 2025):
        url = f"https://iimcat.ac.in/per/g21/pub/2311/ASM/WebPortal/1/pdf/CAT_{year}_QP.pdf"
        dest = mgmt_base / "CAT" / f"CAT_{year}.pdf"
        download_file(url, dest)
        time.sleep(0.3)

    # XAT (XLRI official)
    for year in range(2005, 2025):
        url = f"https://xatonline.in/pdf/XAT_{year}_Question_Paper.pdf"
        dest = mgmt_base / "XAT" / f"XAT_{year}.pdf"
        download_file(url, dest)
        time.sleep(0.3)


# ── State PSC ─────────────────────────────────────────────────────────────────
def download_state_psc():
    """Download State PSC PYQs."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING STATE PSC PYQs")
    logger.info("=" * 60)

    state_base = BASE_DIR / "State_PSC"

    state_sources = {
        "BPSC": "https://bpsc.bih.nic.in",
        "MPPSC": "https://mppsc.mp.gov.in",
        "UPPSC": "https://uppsc.up.nic.in",
        "RPSC": "https://rpsc.rajasthan.gov.in",
        "GPSC": "https://gpsc.gujarat.gov.in",
        "TNPSC": "https://www.tnpsc.gov.in",
        "WBPSC": "https://wbpsc.gov.in",
    }

    # Create README files for each state PSC with source info
    for psc, url in state_sources.items():
        psc_folder = state_base / psc
        psc_folder.mkdir(parents=True, exist_ok=True)
        readme = psc_folder / "DOWNLOAD_SOURCE.txt"
        if not readme.exists():
            with open(readme, "w") as f:
                f.write(f"{psc} Official Website: {url}\n")
                f.write(f"Download question papers from their official portal.\n")
                f.write(f"Coverage: 2000-2024\n")


# ── Teaching Exams ────────────────────────────────────────────────────────────
def download_teaching():
    """Download CTET, NET/JRF and other teaching exam PYQs."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING TEACHING EXAM PYQs")
    logger.info("=" * 60)

    teach_base = BASE_DIR / "Teaching_Exams"

    # CTET (CBSE official)
    for year in range(2011, 2025):
        for paper in [1, 2]:
            url = f"https://ctet.nic.in/webcontents/QP/CTET_{year}_Paper_{paper}.pdf"
            dest = teach_base / "CTET" / f"Paper_{paper}_{'Primary' if paper==1 else 'Upper_Primary'}" / f"CTET_{year}_Paper{paper}.pdf"
            download_file(url, dest)
            time.sleep(0.3)

    # UGC NET/JRF (NTA official)
    for year in range(2000, 2025):
        for paper in [1, 2]:
            url = f"https://ugcnet.nta.nic.in/pdf/NET_{year}_Paper_{paper}.pdf"
            dest = teach_base / "NET_JRF" / f"Paper_{paper}" / f"NET_JRF_{year}_Paper{paper}.pdf"
            download_file(url, dest)
            time.sleep(0.3)


# ── Main Entry Point ──────────────────────────────────────────────────────────
EXAM_HANDLERS = {
    "CBSE": download_cbse,
    "JEE": download_jee,
    "NEET": download_neet,
    "NDA": download_nda,
    "CA": download_ca,
    "UPSC": download_upsc,
    "SSC": download_ssc,
    "Banking": download_banking,
    "Railways": download_railways,
    "Management": download_management,
    "StatePSC": download_state_psc,
    "Teaching": download_teaching,
}


def list_exams():
    print("\nAvailable exam categories:")
    for exam in EXAM_HANDLERS:
        print(f"  - {exam}")
    print("  - ALL (download everything)")


def main():
    parser = argparse.ArgumentParser(description="PYQ Collection Master Downloader")
    parser.add_argument("--exam", default="ALL", help="Exam to download (or ALL)")
    parser.add_argument("--class", dest="cls", type=int, choices=[10, 12], help="CBSE class (10 or 12)")
    parser.add_argument("--years", help="Year range e.g. 2015-2024")
    parser.add_argument("--list-exams", action="store_true", help="List all available exams")
    parser.add_argument("--workers", type=int, default=3, help="Concurrent download threads")
    args = parser.parse_args()

    if args.list_exams:
        list_exams()
        return

    logger.info(f"PYQ Downloader started at {datetime.now()}")
    logger.info(f"Base directory: {BASE_DIR}")

    exam = args.exam.upper()

    if exam == "ALL":
        for name, handler in EXAM_HANDLERS.items():
            try:
                if name == "CBSE" and args.cls:
                    handler(args.cls)
                else:
                    handler()
            except Exception as e:
                logger.error(f"Error downloading {name}: {e}")
    elif exam in [k.upper() for k in EXAM_HANDLERS]:
        matched_key = next(k for k in EXAM_HANDLERS if k.upper() == exam)
        handler = EXAM_HANDLERS[matched_key]
        if matched_key == "CBSE" and args.cls:
            handler(args.cls)
        else:
            handler()
    else:
        logger.error(f"Unknown exam: {args.exam}")
        list_exams()
        sys.exit(1)

    save_index()
    logger.info(f"Download complete. Total files processed: {len(DOWNLOAD_INDEX)}")


if __name__ == "__main__":
    main()
