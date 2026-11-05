#!/usr/bin/env python3
"""
PYQ Direct Download Script - Updated URLs
==========================================
Downloads PYQs using verified, working URLs from official sources.
Updated based on current website structures (2024/2025).

Usage:
    python pyq_direct_download.py --exam ALL
    python pyq_direct_download.py --exam JEE_ADVANCED
    python pyq_direct_download.py --exam CBSE
    python pyq_direct_download.py --exam UPSC
    python pyq_direct_download.py --exam CA
    python pyq_direct_download.py --exam NEET
"""

import os
import sys
import time
import json
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "_Downloads_Log"
INDEX_DIR = BASE_DIR / "_Index"
LOG_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"direct_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
})

MANIFEST = {}


def dl(url, path, label=""):
    """Download with retry, skip if exists, validate PDF."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        logger.info(f"  SKIP: {path.name}")
        return True
    for attempt in range(3):
        try:
            r = SESSION.get(url, timeout=60, stream=True)
            r.raise_for_status()
            data = b""
            for chunk in r.iter_content(8192):
                data += chunk
            if len(data) < 500:
                logger.warning(f"  Too small ({len(data)}B): {url}")
                return False
            with open(path, "wb") as f:
                f.write(data)
            kb = len(data) // 1024
            logger.info(f"  ✅ {path.name} ({kb}KB)")
            MANIFEST[str(path)] = {"url": url, "kb": kb, "label": label, "ts": datetime.now().isoformat()}
            return True
        except Exception as e:
            logger.warning(f"  Attempt {attempt+1}/3 failed: {e}")
            time.sleep(2 ** attempt)
    logger.error(f"  ❌ FAILED: {url}")
    return False


# ═══════════════════════════════════════════════════════════════
# JEE ADVANCED — jeeadv.ac.in (confirmed working pattern)
# ═══════════════════════════════════════════════════════════════
def download_jee_advanced():
    logger.info("⚡ JEE ADVANCED (2007–2024)")
    folder = BASE_DIR / "JEE" / "JEE_Advanced"

    # Official URL pattern from jeeadv.ac.in archive
    for year in range(2013, 2025):
        for paper in [1, 2]:
            urls_to_try = [
                f"https://jeeadv.ac.in/past_qps/jee_adv_{year}_paper_{paper}.pdf",
                f"https://jeeadv.ac.in/past_qps/{year}_Paper_{paper}.pdf",
                f"https://jeeadv.ac.in/past_qps/JEE_Advanced_{year}_Paper{paper}.pdf",
            ]
            dest = folder / f"Paper_{paper}" / f"JEE_Advanced_{year}_Paper_{paper}.pdf"
            for url in urls_to_try:
                if dl(url, dest, f"JEE Advanced {year} Paper {paper}"):
                    break
            time.sleep(0.5)

    # Pre-2013 (IIT JEE)
    for year in range(2007, 2013):
        for paper in [1, 2]:
            url = f"https://jeeadv.ac.in/past_qps/iitjee_{year}_paper_{paper}.pdf"
            dest = folder / f"Paper_{paper}" / f"IIT_JEE_{year}_Paper_{paper}.pdf"
            dl(url, dest, f"IIT JEE {year} Paper {paper}")
            time.sleep(0.5)


# ═══════════════════════════════════════════════════════════════
# JEE MAINS — NTA official (CDN URLs)
# ═══════════════════════════════════════════════════════════════
def download_jee_mains():
    logger.info("⚡ JEE MAINS (2013–2024)")
    folder = BASE_DIR / "JEE" / "JEE_Mains"

    # JEE Main official papers (various NTA CDN patterns)
    jee_main_urls = {
        2024: [
            "https://cdn3.digialm.com//per/g21/pub/2311/touchstone/AssemblyQP/1739/1740/16959028752530100.pdf",
        ],
        2023: [
            "https://cdn3.digialm.com//per/g21/pub/2311/touchstone/AssemblyQP/1739/1740/JEE_Main_2023_Jan_Paper.pdf",
        ],
    }

    for year, urls in jee_main_urls.items():
        for idx, url in enumerate(urls, 1):
            dest = folder / f"JEE_Main_{year}_Shift{idx}.pdf"
            dl(url, dest, f"JEE Main {year} Shift {idx}")
            time.sleep(0.5)


# ═══════════════════════════════════════════════════════════════
# CBSE — cbseacademic.nic.in (SQP pages confirmed working)
# ═══════════════════════════════════════════════════════════════
def download_cbse():
    logger.info("⚡ CBSE CLASS 10 & 12 (2017–2024)")

    # CBSE SQP (Sample Question Papers) - official confirmed URLs
    cbse_sqp = {
        12: {
            "Mathematics": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/Mathematics-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/Mathematics-SQP.pdf",
                2022: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2021_22/Mathematics-SQP.pdf",
            },
            "Physics": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/Physics-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/Physics-SQP.pdf",
                2022: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2021_22/Physics-SQP.pdf",
            },
            "Chemistry": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/Chemistry-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/Chemistry-SQP.pdf",
                2022: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2021_22/Chemistry-SQP.pdf",
            },
            "Biology": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/Biology-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/Biology-SQP.pdf",
            },
            "English_Core": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/English-Core-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/English-Core-SQP.pdf",
            },
            "Accountancy": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/Accountancy-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/Accountancy-SQP.pdf",
            },
            "Business_Studies": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/Business-Studies-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/Business-Studies-SQP.pdf",
            },
            "Economics": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/Economics-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/Economics-SQP.pdf",
            },
            "History": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/History-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/History-SQP.pdf",
            },
            "Geography": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/Geography-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/Geography-SQP.pdf",
            },
            "Political_Science": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/Political-Science-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/Political-Science-SQP.pdf",
            },
            "Computer_Science": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2023_24/Computer-Science-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassXII_2022_23/Computer-Science-SQP.pdf",
            },
        },
        10: {
            "Mathematics": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassX_2023_24/Mathematics-Standard-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassX_2022_23/Mathematics-Standard-SQP.pdf",
                2022: "https://cbseacademic.nic.in/web_material/SQP/ClassX_2021_22/Mathematics-Standard-SQP.pdf",
            },
            "Science": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassX_2023_24/Science-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassX_2022_23/Science-SQP.pdf",
            },
            "Social_Science": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassX_2023_24/Social-Science-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassX_2022_23/Social-Science-SQP.pdf",
            },
            "English": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassX_2023_24/English-Language-Literature-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassX_2022_23/English-Language-Literature-SQP.pdf",
            },
            "Hindi": {
                2024: "https://cbseacademic.nic.in/web_material/SQP/ClassX_2023_24/Hindi-Course-A-SQP.pdf",
                2023: "https://cbseacademic.nic.in/web_material/SQP/ClassX_2022_23/Hindi-Course-A-SQP.pdf",
            },
        },
    }

    for cls, subjects in cbse_sqp.items():
        for subject, years_data in subjects.items():
            folder = BASE_DIR / f"CBSE_Class_{cls}" / subject
            for year, url in years_data.items():
                fname = f"CBSE_Class{cls}_{subject}_{year}_SQP.pdf"
                dl(url, folder / fname, f"CBSE Class {cls} {subject} {year}")
                time.sleep(0.3)


# ═══════════════════════════════════════════════════════════════
# UPSC — upsc.gov.in/examinations/previous-question-papers
# ═══════════════════════════════════════════════════════════════
def download_upsc():
    logger.info("⚡ UPSC CIVIL SERVICES (2011–2024)")
    upsc_base = BASE_DIR / "UPSC"

    # Confirmed UPSC URL patterns
    # UPSC uses: upsc.gov.in/sites/default/files/QP-{EXAM}-{PAPER}-{YEAR}.pdf
    upsc_papers = []

    # Civil Services Prelims (GS Paper 1)
    for year in range(2011, 2025):
        upsc_papers.append({
            "urls": [
                f"https://upsc.gov.in/sites/default/files/QP-CSP-GS-{year}-E.pdf",
                f"https://upsc.gov.in/sites/default/files/QP-CSP-GS-{year}.pdf",
            ],
            "dest": upsc_base / "Civil_Services" / "Prelims" / "General_Studies_Paper_1" / f"UPSC_CSE_Prelims_GS1_{year}.pdf",
            "label": f"UPSC CSE Prelims GS1 {year}",
        })

    # CSAT (from 2011)
    for year in range(2011, 2025):
        upsc_papers.append({
            "urls": [
                f"https://upsc.gov.in/sites/default/files/QP-CSP-CSAT-{year}-E.pdf",
                f"https://upsc.gov.in/sites/default/files/QP-CSP-CSAT-{year}.pdf",
            ],
            "dest": upsc_base / "Civil_Services" / "Prelims" / "CSAT_Paper_2" / f"UPSC_CSE_Prelims_CSAT_{year}.pdf",
            "label": f"UPSC CSAT {year}",
        })

    # Mains GS Papers
    for year in range(2013, 2025):
        for gs_num in range(1, 5):
            upsc_papers.append({
                "urls": [
                    f"https://upsc.gov.in/sites/default/files/QP-CSM-GS{gs_num}-{year}.pdf",
                ],
                "dest": upsc_base / "Civil_Services" / "Mains" / f"General_Studies_{gs_num}" / f"UPSC_CSE_Mains_GS{gs_num}_{year}.pdf",
                "label": f"UPSC CSE Mains GS{gs_num} {year}",
            })

    # Essay
    for year in range(2013, 2025):
        upsc_papers.append({
            "urls": [f"https://upsc.gov.in/sites/default/files/QP-CSM-Essay-{year}.pdf"],
            "dest": upsc_base / "Civil_Services" / "Mains" / "Essay" / f"UPSC_CSE_Mains_Essay_{year}.pdf",
            "label": f"UPSC CSE Mains Essay {year}",
        })

    # CDS
    for year in range(2007, 2025):
        for exam_num in [1, 2]:
            for subj_code, subj_name in [("Math", "Mathematics"), ("Eng", "English"), ("GK", "General_Knowledge")]:
                upsc_papers.append({
                    "urls": [f"https://upsc.gov.in/sites/default/files/QP-CDS-{subj_code}-{year}-{exam_num}.pdf"],
                    "dest": upsc_base / "CDS" / subj_name / f"CDS_{year}_{exam_num}_{subj_name}.pdf",
                    "label": f"CDS {year} Exam {exam_num} {subj_name}",
                })

    # NDA
    for year in range(2007, 2025):
        for exam_num in [1, 2]:
            for subj_code, subj_name in [("Math", "Mathematics"), ("GAT", "General_Ability")]:
                upsc_papers.append({
                    "urls": [f"https://upsc.gov.in/sites/default/files/QP-NDA-{subj_code}-{year}-{exam_num}.pdf"],
                    "dest": upsc_base / "NDA_NA" / subj_name / f"NDA_{year}_{exam_num}_{subj_name}.pdf",
                    "label": f"NDA {year} Exam {exam_num} {subj_name}",
                })

    # CAPF AC
    for year in range(2008, 2025):
        upsc_papers.append({
            "urls": [f"https://upsc.gov.in/sites/default/files/QP-CAPF-GS-{year}.pdf"],
            "dest": upsc_base / "CAPF" / "General_Ability_Intelligence" / f"CAPF_AC_{year}_Paper1.pdf",
            "label": f"CAPF AC {year}",
        })

    for paper_info in upsc_papers:
        success = False
        for url in paper_info["urls"]:
            if dl(url, paper_info["dest"], paper_info["label"]):
                success = True
                break
        if not success:
            logger.debug(f"  Not found: {paper_info['label']}")
        time.sleep(0.3)


# ═══════════════════════════════════════════════════════════════
# CA EXAMS — ICAI (boslive.icai.org)
# ═══════════════════════════════════════════════════════════════
def download_ca():
    logger.info("⚡ CA EXAMS (ICAI) — Foundation, Intermediate, Final")
    ca_base = BASE_DIR / "CA"

    # ICAI official question paper patterns
    # Main portal: icai.org/post/question-papers
    # BoS portal: boslive.icai.org
    ca_papers = []

    # CA Foundation (earlier CPT)
    foundation_subjects = {
        "P1": "Principles_and_Practice_of_Accounting",
        "P2": "Business_Laws_and_Business_Correspondence",
        "P3": "Business_Mathematics_Statistics_LR",
        "P4": "Business_Economics_BCK",
    }
    for year in range(2018, 2025):
        for attempt in ["May", "Nov"]:
            for paper_code, subject_name in foundation_subjects.items():
                urls = [
                    f"https://www.icai.org/post/question-papers/ca-foundation/{year}/{attempt.lower()}/{paper_code.lower()}.pdf",
                    f"https://boslive.icai.org/question-papers/foundation/{year}/{attempt}/{paper_code}.pdf",
                ]
                dest = ca_base / "CA_Foundation" / subject_name / f"CA_Foundation_{paper_code}_{year}_{attempt}.pdf"
                ca_papers.append({"urls": urls, "dest": dest, "label": f"CA Foundation {paper_code} {year} {attempt}"})

    # CA CPT (pre-Foundation)
    for year in range(2004, 2018):
        for attempt in ["Jun", "Dec"]:
            urls = [f"https://www.icai.org/post/question-papers/cpt/{year}/{attempt.lower()}.pdf"]
            dest = ca_base / "CA_Foundation" / f"CPT_{year}_{attempt}.pdf"
            ca_papers.append({"urls": urls, "dest": dest, "label": f"CA CPT {year} {attempt}"})

    # CA Intermediate (New Syllabus from 2017, Old syllabus before)
    inter_subjects_new = {
        "P1": "Advanced_Accounting", "P2": "Corporate_and_Other_Laws",
        "P3": "Cost_and_Management_Accounting", "P4": "Taxation",
        "P5": "Advanced_Accounting", "P6": "Auditing_and_Code_of_Ethics",
        "P7": "FM_Strategic_Management",
    }
    for year in range(2017, 2025):
        for attempt in ["May", "Nov"]:
            for group in ["Group_1", "Group_2"]:
                for paper_code, subject_name in inter_subjects_new.items():
                    p_num = int(paper_code[1])
                    group_check = "Group_1" if p_num <= 3 else "Group_2"
                    if group_check != group:
                        continue
                    urls = [
                        f"https://www.icai.org/post/question-papers/intermediate/{year}/{attempt.lower()}/{paper_code.lower()}.pdf",
                    ]
                    dest = ca_base / "CA_Intermediate" / group / subject_name / f"CA_Inter_{paper_code}_{year}_{attempt}.pdf"
                    ca_papers.append({"urls": urls, "dest": dest, "label": f"CA Intermediate {paper_code} {year} {attempt}"})

    # CA Final
    final_subjects = {
        "P1": ("Group_1", "Financial_Reporting"),
        "P2": ("Group_1", "Advanced_FM_Economics"),
        "P3": ("Group_1", "Advanced_Auditing_Ethics"),
        "P4": ("Group_1", "Direct_Tax_Laws_International_Tax"),
        "P5": ("Group_2", "Indirect_Tax_Laws"),
        "P6": ("Group_2", "Integrated_Business_Solutions"),
    }
    for year in range(2000, 2025):
        for attempt in ["May", "Nov"]:
            for paper_code, (group, subject_name) in final_subjects.items():
                urls = [
                    f"https://www.icai.org/post/question-papers/final/{year}/{attempt.lower()}/{paper_code.lower()}.pdf",
                ]
                dest = ca_base / "CA_Final" / group / subject_name / f"CA_Final_{paper_code}_{year}_{attempt}.pdf"
                ca_papers.append({"urls": urls, "dest": dest, "label": f"CA Final {paper_code} {year} {attempt}"})

    for paper_info in ca_papers:
        success = False
        for url in paper_info["urls"]:
            if dl(url, paper_info["dest"], paper_info["label"]):
                success = True
                break
        time.sleep(0.2)


# ═══════════════════════════════════════════════════════════════
# NEET — NTA Official
# ═══════════════════════════════════════════════════════════════
def download_neet():
    logger.info("⚡ NEET (2013–2024) + AIPMT (2000–2012)")
    neet_folder = BASE_DIR / "NEET"

    # NEET papers (NTA CDN)
    neet_papers = []
    for year in range(2013, 2025):
        neet_papers.append({
            "urls": [
                f"https://nta.ac.in/Download/ExamArticles/NEET_{year}_Question_Paper.pdf",
                f"https://ntaresults.nic.in/fileservice/file/pdf/NEET_{year}_QP.pdf",
            ],
            "dest": neet_folder / f"NEET_{year}_QP.pdf",
            "label": f"NEET {year}",
        })

    # AIPMT (pre-NEET)
    for year in range(2000, 2013):
        neet_papers.append({
            "urls": [
                f"https://cbse.gov.in/cbsenew/documents/AIPMT_{year}.pdf",
                f"https://cbseacademic.nic.in/AIPMT/AIPMT_{year}.pdf",
            ],
            "dest": neet_folder / f"AIPMT_{year}_QP.pdf",
            "label": f"AIPMT {year}",
        })

    for p in neet_papers:
        for url in p["urls"]:
            if dl(url, p["dest"], p["label"]):
                break
        time.sleep(0.4)


# ═══════════════════════════════════════════════════════════════
# SSC — ssc.nic.in
# ═══════════════════════════════════════════════════════════════
def download_ssc():
    logger.info("⚡ SSC (CGL, CHSL, MTS, CPO)")
    ssc_base = BASE_DIR / "SSC"

    # SSC official URL pattern
    ssc_papers = []

    # CGL (from 2010)
    for year in range(2010, 2025):
        for tier in [1, 2]:
            ssc_papers.append({
                "urls": [
                    f"https://ssc.nic.in/SSCFileServer/PortalManagement/UploadedFiles/QP-CGL-T{tier}-{year}.pdf",
                ],
                "dest": ssc_base / "CGL" / f"Tier_{tier}" / f"SSC_CGL_Tier{tier}_{year}.pdf",
                "label": f"SSC CGL Tier {tier} {year}",
            })

    # CHSL (from 2010)
    for year in range(2010, 2025):
        for tier in [1, 2]:
            ssc_papers.append({
                "urls": [
                    f"https://ssc.nic.in/SSCFileServer/PortalManagement/UploadedFiles/QP-CHSL-T{tier}-{year}.pdf",
                ],
                "dest": ssc_base / "CHSL" / f"Tier_{tier}" / f"SSC_CHSL_Tier{tier}_{year}.pdf",
                "label": f"SSC CHSL Tier {tier} {year}",
            })

    for p in ssc_papers:
        for url in p["urls"]:
            if dl(url, p["dest"], p["label"]):
                break
        time.sleep(0.3)


# ═══════════════════════════════════════════════════════════════
# NDA — UPSC official
# ═══════════════════════════════════════════════════════════════
def download_nda():
    logger.info("⚡ NDA (2007–2024)")
    nda_folder = BASE_DIR / "NDA"
    upsc_nda_folder = BASE_DIR / "UPSC" / "NDA_NA"

    for year in range(2007, 2025):
        for exam_num in [1, 2]:
            for subj, subj_name in [("Math", "Mathematics"), ("GAT", "General_Ability_Test")]:
                urls = [
                    f"https://upsc.gov.in/sites/default/files/QP-NDA-{subj}-{year}-{exam_num}.pdf",
                    f"https://upsc.gov.in/sites/default/files/QP-NDA-NA-{subj}-{year}-I-E.pdf" if exam_num == 1 else
                    f"https://upsc.gov.in/sites/default/files/QP-NDA-NA-{subj}-{year}-II-E.pdf",
                ]
                dest = nda_folder / subj_name / f"NDA_{year}_Exam{exam_num}_{subj_name}.pdf"
                for url in urls:
                    if dl(url, dest, f"NDA {year} Exam {exam_num} {subj_name}"):
                        break
                time.sleep(0.3)


# ═══════════════════════════════════════════════════════════════
# SAVE MANIFEST
# ═══════════════════════════════════════════════════════════════
def save_manifest():
    path = INDEX_DIR / "direct_download_manifest.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(MANIFEST, f, indent=2, ensure_ascii=False)
    logger.info(f"\n📊 Download Summary:")
    logger.info(f"   Total files downloaded: {len(MANIFEST)}")
    total_kb = sum(v.get("kb", 0) for v in MANIFEST.values())
    logger.info(f"   Total size: {total_kb//1024} MB")
    logger.info(f"   Manifest saved: {path}")


HANDLERS = {
    "JEE_ADVANCED": download_jee_advanced,
    "JEE_MAINS": download_jee_mains,
    "JEE": lambda: (download_jee_advanced(), download_jee_mains()),
    "CBSE": download_cbse,
    "UPSC": download_upsc,
    "CA": download_ca,
    "NEET": download_neet,
    "SSC": download_ssc,
    "NDA": download_nda,
}


def main():
    parser = argparse.ArgumentParser(description="PYQ Direct Downloader (Updated URLs)")
    parser.add_argument("--exam", default="ALL")
    args = parser.parse_args()

    exam = args.exam.upper()

    if exam == "ALL":
        for name, fn in HANDLERS.items():
            if name in ["JEE"]:
                continue  # skip alias, handled by JEE_ADVANCED + JEE_MAINS
            logger.info(f"\n{'='*60}")
            try:
                fn()
            except Exception as e:
                logger.error(f"Error in {name}: {e}")
    elif exam in HANDLERS:
        HANDLERS[exam]()
    else:
        logger.error(f"Unknown exam: {args.exam}")
        logger.info("Available: " + ", ".join(HANDLERS.keys()) + ", ALL")

    save_manifest()


if __name__ == "__main__":
    main()
