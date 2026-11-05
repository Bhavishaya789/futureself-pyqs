#!/usr/bin/env python3
"""
PYQ Smart Scraper - Alternative Sources
========================================
Scrapes PYQs from open-access education portals that publicly host
previous year question papers. Uses structured scraping with rate limiting.

Sources:
  1. myCBSEguide.com - CBSE papers
  2. aglasem.com - Multi-exam PYQs
  3. cbseacademic.nic.in - CBSE official
  4. jeemain.nta.nic.in - JEE Main official
  5. nta.ac.in - NTA exams
  6. upsc.gov.in - UPSC official
  7. icai.org - CA exam papers
  8. ssc.nic.in - SSC official

Usage:
    python pyq_scraper.py --source cbse_official
    python pyq_scraper.py --source nta_official
    python pyq_scraper.py --source upsc_official
    python pyq_scraper.py --source icai_official
    python pyq_scraper.py --all
"""

import os
import re
import sys
import json
import time
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote

BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "_Downloads_Log"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
})

DOWNLOAD_MANIFEST = {}


def safe_get(url, timeout=30, retries=3):
    """Safe HTTP GET with retries."""
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt+1}/{retries} failed for {url}: {e}")
            time.sleep(2 ** attempt)
    return None


def download_pdf(url, dest_path, label=""):
    """Download a PDF file."""
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists():
        logger.info(f"  SKIP (exists): {dest_path.name}")
        return True

    logger.info(f"  Downloading: {label or dest_path.name}")
    resp = safe_get(url)
    if resp is None:
        return False

    # Verify it's a PDF
    if not (resp.content[:4] == b"%PDF" or "pdf" in resp.headers.get("Content-Type", "").lower()):
        logger.warning(f"  Not a valid PDF: {url}")
        return False

    with open(dest_path, "wb") as f:
        f.write(resp.content)

    size = len(resp.content) // 1024
    logger.info(f"  ✅ {dest_path.name} ({size} KB)")
    DOWNLOAD_MANIFEST[str(dest_path)] = {
        "source_url": url,
        "size_kb": size,
        "label": label,
        "timestamp": datetime.now().isoformat(),
    }
    return True


# ── CBSE Official Scraper ─────────────────────────────────────────────────────
def scrape_cbse_official():
    """
    Scrape CBSE official website for question papers.
    URL: https://cbseacademic.nic.in/question-paper.html
    """
    logger.info("Scraping CBSE Official (cbseacademic.nic.in)...")

    base_url = "https://cbseacademic.nic.in"
    qp_page = f"{base_url}/question-paper.html"

    resp = safe_get(qp_page)
    if not resp:
        logger.error("Could not reach CBSE academic portal")
        return

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find all PDF links
    pdf_links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.lower().endswith(".pdf"):
            full_url = urljoin(base_url, href)
            pdf_links.append((full_url, a_tag.get_text(strip=True)))

    logger.info(f"Found {len(pdf_links)} PDF links on CBSE page")

    for url, label in pdf_links:
        # Try to determine class and subject from URL/label
        cls = None
        if "10th" in url.lower() or "class10" in url.lower():
            cls = 10
        elif "12th" in url.lower() or "class12" in url.lower():
            cls = 12

        if cls:
            # Extract year
            year_match = re.search(r"20\d{2}", url)
            year = year_match.group() if year_match else "unknown"

            subject = "General"
            for subj in ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Hindi", "Science", "Economics"]:
                if subj.lower() in url.lower() or subj.lower() in label.lower():
                    subject = subj
                    break

            dest = BASE_DIR / f"CBSE_Class_{cls}" / subject / f"CBSE_{cls}_{subject}_{year}.pdf"
            download_pdf(url, dest, label)
            time.sleep(0.5)


# ── NTA Official Scraper ──────────────────────────────────────────────────────
def scrape_nta_official():
    """
    Scrape NTA (National Testing Agency) official pages.
    Covers: JEE Main, NEET, CTET, NET/JRF
    URL: https://nta.ac.in
    """
    logger.info("Scraping NTA Official (nta.ac.in)...")

    nta_pages = [
        ("https://jeemain.nta.nic.in/webinfo2024/Page/Page?PageId=2&LangId=P", "JEE_Mains"),
        ("https://neet.nta.nic.in/webinfo2024/Page/Page?PageId=2&LangId=P", "NEET"),
        ("https://ugcnet.nta.nic.in/WebInfo/Page/Page?PageId=1&LangId=P", "NET_JRF"),
        ("https://ctet.nic.in/webcontents/", "CTET"),
    ]

    for page_url, exam_type in nta_pages:
        logger.info(f"Checking {exam_type} at {page_url}")
        resp = safe_get(page_url)
        if not resp:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.lower().endswith(".pdf"):
                full_url = urljoin(page_url, href)
                label = a_tag.get_text(strip=True)
                year_match = re.search(r"20\d{2}", href + label)
                year = year_match.group() if year_match else "unknown"

                if exam_type == "JEE_Mains":
                    dest = BASE_DIR / "JEE" / "JEE_Mains" / f"JEE_Main_{year}_{label[:30]}.pdf"
                elif exam_type == "NEET":
                    dest = BASE_DIR / "NEET" / f"NEET_{year}_{label[:30]}.pdf"
                elif exam_type == "NET_JRF":
                    paper = "Paper_1" if "paper 1" in label.lower() else "Paper_2"
                    dest = BASE_DIR / "Teaching_Exams" / "NET_JRF" / paper / f"NET_{year}_{label[:30]}.pdf"
                elif exam_type == "CTET":
                    paper = "Paper_1_Primary" if "paper-i" in label.lower() or "paper 1" in label.lower() else "Paper_2_Upper_Primary"
                    dest = BASE_DIR / "Teaching_Exams" / "CTET" / paper / f"CTET_{year}_{label[:30]}.pdf"
                else:
                    continue

                download_pdf(full_url, dest, label)
                time.sleep(0.5)


# ── UPSC Official Scraper ─────────────────────────────────────────────────────
def scrape_upsc_official():
    """
    Scrape UPSC official question papers page.
    URL: https://upsc.gov.in/question-papers
    """
    logger.info("Scraping UPSC Official (upsc.gov.in)...")

    upsc_qp_url = "https://upsc.gov.in/question-papers"
    resp = safe_get(upsc_qp_url)
    if not resp:
        logger.error("Could not reach UPSC question papers page")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    upsc_base = BASE_DIR / "UPSC"

    exam_mapping = {
        "civil services": "Civil_Services",
        "cse": "Civil_Services",
        "ias": "Civil_Services",
        "cds": "CDS",
        "nda": "NDA_NA",
        "ese": "Engineering_Services_ESE",
        "ies": "Engineering_Services_ESE",
        "capf": "CAPF",
        "ifs": "IFS",
        "scra": "SCRA",
        "geo": "Geologist_Exam",
    }

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if not href.lower().endswith(".pdf"):
            continue

        full_url = urljoin("https://upsc.gov.in", href)
        label = a_tag.get_text(strip=True).lower()
        year_match = re.search(r"20\d{2}|19\d{2}", href + label)
        year = year_match.group() if year_match else "unknown"

        dest_folder = upsc_base / "Civil_Services" / "Prelims" / "General_Studies_Paper_1"  # default
        for key, folder_name in exam_mapping.items():
            if key in label or key in href.lower():
                if "prelim" in label or "pre" in href.lower():
                    dest_folder = upsc_base / folder_name / "Prelims"
                elif "main" in label or "mains" in href.lower():
                    dest_folder = upsc_base / folder_name / "Mains"
                else:
                    dest_folder = upsc_base / folder_name
                break

        filename = f"UPSC_{year}_{Path(href).name}"
        download_pdf(full_url, dest_folder / filename, label)
        time.sleep(0.5)


# ── ICAI Official Scraper ─────────────────────────────────────────────────────
def scrape_icai_official():
    """
    Scrape ICAI (Institute of Chartered Accountants of India) for CA exam PYQs.
    URL: https://www.icai.org/post/question-papers
    """
    logger.info("Scraping ICAI Official (icai.org)...")

    icai_pages = [
        ("https://www.icai.org/post/question-papers/ca-foundation", "CA_Foundation"),
        ("https://www.icai.org/post/question-papers/intermediate", "CA_Intermediate"),
        ("https://www.icai.org/post/question-papers/final", "CA_Final"),
    ]

    ca_base = BASE_DIR / "CA"

    for page_url, level in icai_pages:
        logger.info(f"Scraping {level}...")
        resp = safe_get(page_url)
        if not resp:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        level_folder = ca_base / level

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if not href.lower().endswith(".pdf"):
                continue

            full_url = urljoin("https://www.icai.org", href)
            label = a_tag.get_text(strip=True)
            year_match = re.search(r"20\d{2}", href + label)
            year = year_match.group() if year_match else "unknown"

            # Determine attempt (May/November)
            attempt = "May" if "may" in label.lower() else "November" if "nov" in label.lower() else "Unknown"

            # Determine subject/paper
            paper_match = re.search(r"paper[\s\-_]*(\d)", label.lower())
            paper_num = paper_match.group(1) if paper_match else "X"

            dest_folder = level_folder / f"Paper_{paper_num}"
            dest_folder.mkdir(parents=True, exist_ok=True)
            filename = f"{level}_Paper{paper_num}_{year}_{attempt}.pdf"

            download_pdf(full_url, dest_folder / filename, label)
            time.sleep(0.3)


# ── SSC Official Scraper ──────────────────────────────────────────────────────
def scrape_ssc_official():
    """
    Scrape SSC official website for question papers.
    URL: https://ssc.nic.in
    """
    logger.info("Scraping SSC Official (ssc.nic.in)...")

    ssc_pages = [
        "https://ssc.nic.in/Portal/QuestionPapers",
    ]

    ssc_base = BASE_DIR / "SSC"

    for page_url in ssc_pages:
        resp = safe_get(page_url)
        if not resp:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        exam_patterns = {
            "CGL": ["CGL", "Combined Graduate Level"],
            "CHSL": ["CHSL", "Combined Higher Secondary"],
            "MTS": ["MTS", "Multi Tasking"],
            "CPO": ["CPO", "Central Police"],
            "GD": ["GD", "General Duty"],
            "Steno": ["Stenographer"],
            "JE": ["Junior Engineer", "JE"],
        }

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if not href.lower().endswith(".pdf"):
                continue

            full_url = urljoin("https://ssc.nic.in", href)
            label = a_tag.get_text(strip=True)
            year_match = re.search(r"20\d{2}", href + label)
            year = year_match.group() if year_match else "unknown"

            matched_exam = "General"
            for exam, patterns in exam_patterns.items():
                for p in patterns:
                    if p.lower() in label.lower() or p.lower() in href.lower():
                        matched_exam = exam
                        break

            tier = "Tier_1"
            if "tier 2" in label.lower() or "tier-2" in label.lower() or "t2" in href.lower():
                tier = "Tier_2"
            elif "tier 3" in label.lower() or "tier-3" in label.lower():
                tier = "Tier_3"

            if matched_exam in ["CGL", "CHSL"]:
                dest_folder = ssc_base / matched_exam / tier
            else:
                dest_folder = ssc_base / matched_exam

            dest_folder.mkdir(parents=True, exist_ok=True)
            filename = f"SSC_{matched_exam}_{year}_{tier}.pdf"
            download_pdf(full_url, dest_folder / filename, label)
            time.sleep(0.3)


# ── Save manifest ─────────────────────────────────────────────────────────────
def save_manifest():
    manifest_path = BASE_DIR / "_Index" / "scrape_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(DOWNLOAD_MANIFEST, f, indent=2, ensure_ascii=False)
    logger.info(f"Scrape manifest saved: {manifest_path}")
    logger.info(f"Total files downloaded: {len(DOWNLOAD_MANIFEST)}")


# ── Main ──────────────────────────────────────────────────────────────────────
SCRAPERS = {
    "cbse_official": scrape_cbse_official,
    "nta_official": scrape_nta_official,
    "upsc_official": scrape_upsc_official,
    "icai_official": scrape_icai_official,
    "ssc_official": scrape_ssc_official,
}


def main():
    parser = argparse.ArgumentParser(description="PYQ Smart Scraper")
    parser.add_argument("--source", help="Source to scrape")
    parser.add_argument("--all", action="store_true", help="Scrape all sources")
    parser.add_argument("--list", action="store_true", help="List available sources")
    args = parser.parse_args()

    if args.list:
        print("Available sources:")
        for src in SCRAPERS:
            print(f"  - {src}")
        return

    if args.all:
        for name, scraper in SCRAPERS.items():
            logger.info(f"\n{'='*60}\nRunning scraper: {name}\n{'='*60}")
            try:
                scraper()
            except Exception as e:
                logger.error(f"Scraper {name} failed: {e}")
    elif args.source:
        if args.source in SCRAPERS:
            SCRAPERS[args.source]()
        else:
            logger.error(f"Unknown source: {args.source}")
            return
    else:
        parser.print_help()
        return

    save_manifest()


if __name__ == "__main__":
    main()
