#!/usr/bin/env python3
"""
PYQ Organizer & Index Builder
==============================
Organizes downloaded PYQ PDFs, renames them consistently,
builds a searchable JSON index, and generates a summary report.

Usage:
    python pyq_organizer.py --organize
    python pyq_organizer.py --index
    python pyq_organizer.py --report
    python pyq_organizer.py --all
    python pyq_organizer.py --verify-pdfs
"""

import os
import re
import sys
import json
import shutil
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
INDEX_DIR = BASE_DIR / "_Index"
LOG_DIR = BASE_DIR / "_Downloads_Log"

INDEX_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"organize_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Exam metadata for structured indexing
EXAM_META = {
    "CBSE_Class_10": {
        "full_name": "CBSE Class 10 Board Examination",
        "board": "CBSE",
        "category": "Board Exams",
        "subjects": ["Mathematics", "Science", "Social_Science", "English", "Hindi", "Sanskrit"],
    },
    "CBSE_Class_12": {
        "full_name": "CBSE Class 12 Board Examination",
        "board": "CBSE",
        "category": "Board Exams",
        "subjects": ["Mathematics", "Physics", "Chemistry", "Biology", "English_Core", "Hindi_Core",
                     "Accountancy", "Business_Studies", "Economics", "History", "Geography",
                     "Political_Science", "Computer_Science"],
    },
    "JEE": {
        "full_name": "Joint Entrance Examination",
        "conducting_body": "NTA / IITs",
        "category": "Engineering Entrance",
        "sub_exams": ["JEE_Mains", "JEE_Advanced"],
    },
    "NEET": {
        "full_name": "National Eligibility cum Entrance Test",
        "conducting_body": "NTA",
        "category": "Medical Entrance",
        "subjects": ["Physics", "Chemistry", "Biology_Botany", "Biology_Zoology"],
    },
    "NDA": {
        "full_name": "National Defence Academy Examination",
        "conducting_body": "UPSC",
        "category": "Defence",
        "papers": ["Paper_1 (Mathematics)", "Paper_2 (General Ability Test)"],
    },
    "CA": {
        "full_name": "Chartered Accountancy Examinations",
        "conducting_body": "ICAI",
        "category": "Professional",
        "levels": ["CA_Foundation", "CA_Intermediate", "CA_Final"],
    },
    "UPSC": {
        "full_name": "Union Public Service Commission Examinations",
        "conducting_body": "UPSC",
        "category": "Government Services",
        "sub_exams": ["Civil_Services", "Engineering_Services_ESE", "CDS", "CAPF", "NDA_NA", "IFS"],
    },
    "SSC": {
        "full_name": "Staff Selection Commission Examinations",
        "conducting_body": "SSC",
        "category": "Government Services",
        "sub_exams": ["CGL", "CHSL", "MTS", "CPO", "GD_Constable", "JE", "Stenographer"],
    },
    "Banking": {
        "full_name": "Banking Sector Examinations",
        "conducting_body": "IBPS / RBI / SBI",
        "category": "Banking",
        "sub_exams": ["IBPS_PO", "IBPS_Clerk", "SBI_PO", "SBI_Clerk", "RBI_Grade_B"],
    },
    "Railways": {
        "full_name": "Railway Recruitment Board Examinations",
        "conducting_body": "RRB / RRC",
        "category": "Government Services",
        "sub_exams": ["RRB_NTPC", "RRB_JE", "RRB_Group_D", "RRB_ALP"],
    },
    "State_PSC": {
        "full_name": "State Public Service Commission Examinations",
        "conducting_body": "Various State PSCs",
        "category": "State Government Services",
        "sub_exams": ["BPSC", "MPPSC", "UPPSC", "RPSC", "GPSC", "TNPSC", "WBPSC"],
    },
    "Teaching_Exams": {
        "full_name": "Teaching Eligibility and Recruitment Examinations",
        "conducting_body": "CBSE / NTA / State Govts",
        "category": "Education",
        "sub_exams": ["CTET", "NET_JRF", "DSSSB", "KVS", "NVS"],
    },
    "Management_Entrance": {
        "full_name": "Management Entrance Examinations",
        "category": "Management",
        "sub_exams": ["CAT", "XAT", "MAT", "SNAP", "IIFT", "CMAT", "NMAT"],
    },
}


def compute_md5(filepath: Path) -> str:
    """Compute MD5 hash of a file."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_valid_pdf(filepath: Path) -> bool:
    """Check if file is a valid PDF."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(4)
            return header == b"%PDF"
    except Exception:
        return False


def extract_year_from_filename(filename: str) -> str:
    """Extract year from filename."""
    match = re.search(r"(20\d{2}|19\d{2})", filename)
    return match.group() if match else "unknown"


def build_master_index():
    """
    Walk the entire PYQ directory and build a comprehensive JSON index.
    """
    logger.info("Building master index...")

    index = {
        "generated_at": datetime.now().isoformat(),
        "base_dir": str(BASE_DIR),
        "total_files": 0,
        "total_size_mb": 0,
        "exams": {},
        "files": [],
    }

    total_size = 0
    file_count = 0

    # Directories to skip
    skip_dirs = {"_Scripts", "_Index", "_Downloads_Log", "pyq_archive_2000_2026"}

    for exam_dir in sorted(BASE_DIR.iterdir()):
        if not exam_dir.is_dir():
            continue
        if exam_dir.name.startswith(".") or exam_dir.name in skip_dirs:
            continue

        exam_name = exam_dir.name
        if exam_name not in index["exams"]:
            index["exams"][exam_name] = {
                "meta": EXAM_META.get(exam_name, {"full_name": exam_name, "category": "Other"}),
                "file_count": 0,
                "subjects": {},
                "years_covered": [],
            }

        years = set()
        for pdf_file in exam_dir.rglob("*.pdf"):
            if pdf_file.stat().st_size < 1000:  # Skip tiny files
                continue

            year = extract_year_from_filename(pdf_file.name)
            years.add(year)

            # Build relative path parts
            rel_parts = pdf_file.relative_to(BASE_DIR).parts
            subject_path = "/".join(rel_parts[1:-1]) if len(rel_parts) > 2 else ""

            size_kb = pdf_file.stat().st_size // 1024
            total_size += size_kb
            file_count += 1

            file_entry = {
                "exam": exam_name,
                "subject_path": subject_path,
                "filename": pdf_file.name,
                "full_path": str(pdf_file),
                "year": year,
                "size_kb": size_kb,
                "is_valid_pdf": is_valid_pdf(pdf_file),
            }
            index["files"].append(file_entry)
            index["exams"][exam_name]["file_count"] += 1

        if years:
            index["exams"][exam_name]["years_covered"] = sorted(list(years - {"unknown"}))

    index["total_files"] = file_count
    index["total_size_mb"] = round(total_size / 1024, 2)

    # Save index
    index_path = INDEX_DIR / "master_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    logger.info(f"[OK] Master index built: {file_count} files, {total_size//1024} MB")
    logger.info(f"Index saved: {index_path}")
    return index


def generate_report(index=None):
    """Generate a human-readable summary report."""
    if index is None:
        index_path = INDEX_DIR / "master_index.json"
        if not index_path.exists():
            index = build_master_index()
        else:
            with open(index_path) as f:
                index = json.load(f)

    report_lines = [
        "=" * 70,
        "PYQ COLLECTION - SUMMARY REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        f"\nTotal Files: {index['total_files']}",
        f"Total Size:  {index['total_size_mb']} MB",
        f"Base Dir:    {index['base_dir']}",
        "\n" + "─" * 70,
        "EXAM-WISE BREAKDOWN",
        "─" * 70,
    ]

    for exam_name, exam_data in sorted(index["exams"].items()):
        meta = exam_data.get("meta", {})
        full_name = meta.get("full_name", exam_name)
        file_count = exam_data.get("file_count", 0)
        years = exam_data.get("years_covered", [])
        year_range = f"{years[0]}-{years[-1]}" if len(years) >= 2 else (years[0] if years else "N/A")

        report_lines.append(f"\n📁 {exam_name}")
        report_lines.append(f"   Full Name: {full_name}")
        report_lines.append(f"   Files: {file_count} | Years: {year_range}")

    report_lines += [
        "\n" + "─" * 70,
        "SOURCES USED",
        "─" * 70,
        "• CBSE: cbseacademic.nic.in, cbse.gov.in",
        "• JEE: jeemain.nta.nic.in, jeeadv.ac.in",
        "• NEET: nta.ac.in, neet.nta.nic.in",
        "• UPSC: upsc.gov.in",
        "• CA: icai.org",
        "• SSC: ssc.nic.in",
        "• NDA: upsc.gov.in",
        "• Railways: rrbcdg.gov.in, indianrailways.gov.in",
        "\n" + "=" * 70,
    ]

    report_text = "\n".join(report_lines)
    report_path = INDEX_DIR / "COLLECTION_REPORT.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    try:
        print(report_text.encode("ascii", "replace").decode("ascii"))
    except Exception:
        pass
    logger.info(f"Report saved: {report_path}")


def verify_pdfs():
    """Check all PDFs for validity and report corrupted files."""
    logger.info("Verifying PDF integrity...")
    valid = 0
    invalid = 0
    invalid_files = []

    for pdf_file in BASE_DIR.rglob("*.pdf"):
        if is_valid_pdf(pdf_file):
            valid += 1
        else:
            invalid += 1
            invalid_files.append(str(pdf_file))
            logger.warning(f"Invalid/corrupted PDF: {pdf_file}")

    logger.info(f"✅ Valid PDFs: {valid}")
    logger.info(f"❌ Invalid PDFs: {invalid}")

    if invalid_files:
        invalid_log = INDEX_DIR / "invalid_pdfs.txt"
        with open(invalid_log, "w") as f:
            f.write("\n".join(invalid_files))
        logger.info(f"Invalid PDF list saved: {invalid_log}")


def organize_files():
    """
    Organize any loose PDFs in pyq_archive_2000_2026 into the proper structure.
    """
    archive_dir = BASE_DIR / "pyq_archive_2000_2026"
    if not archive_dir.exists():
        logger.info("No archive directory found, skipping organization.")
        return

    logger.info(f"Organizing files from {archive_dir}...")
    moved = 0

    for pdf_file in archive_dir.rglob("*.pdf"):
        filename_lower = pdf_file.name.lower()
        dest_dir = None

        # Match to appropriate folder
        if "jee" in filename_lower:
            if "advanced" in filename_lower or "adv" in filename_lower:
                dest_dir = BASE_DIR / "JEE" / "JEE_Advanced"
            else:
                dest_dir = BASE_DIR / "JEE" / "JEE_Mains"
        elif "neet" in filename_lower or "aipmt" in filename_lower:
            dest_dir = BASE_DIR / "NEET"
        elif "nda" in filename_lower:
            dest_dir = BASE_DIR / "NDA"
        elif "upsc" in filename_lower or "ias" in filename_lower or "cse" in filename_lower:
            dest_dir = BASE_DIR / "UPSC" / "Civil_Services" / "Prelims" / "General_Studies_Paper_1"
        elif "ssc" in filename_lower:
            if "cgl" in filename_lower:
                dest_dir = BASE_DIR / "SSC" / "CGL" / "Tier_1"
            elif "chsl" in filename_lower:
                dest_dir = BASE_DIR / "SSC" / "CHSL" / "Tier_1"
            else:
                dest_dir = BASE_DIR / "SSC"
        elif "cbse" in filename_lower:
            if "class_10" in filename_lower or "class10" in filename_lower or "_10_" in filename_lower:
                dest_dir = BASE_DIR / "CBSE_Class_10"
            elif "class_12" in filename_lower or "class12" in filename_lower or "_12_" in filename_lower:
                dest_dir = BASE_DIR / "CBSE_Class_12"
            else:
                dest_dir = BASE_DIR / "CBSE_Class_12"
        elif "cat" in filename_lower and "cata" not in filename_lower:
            dest_dir = BASE_DIR / "Management_Entrance" / "CAT"
        elif "ca_" in filename_lower or "icai" in filename_lower:
            if "foundation" in filename_lower:
                dest_dir = BASE_DIR / "CA" / "CA_Foundation"
            elif "inter" in filename_lower:
                dest_dir = BASE_DIR / "CA" / "CA_Intermediate"
            elif "final" in filename_lower:
                dest_dir = BASE_DIR / "CA" / "CA_Final"
            else:
                dest_dir = BASE_DIR / "CA"
        elif "ctet" in filename_lower:
            dest_dir = BASE_DIR / "Teaching_Exams" / "CTET"
        elif "net" in filename_lower and "jrf" in filename_lower:
            dest_dir = BASE_DIR / "Teaching_Exams" / "NET_JRF"
        elif "ibps" in filename_lower or "sbi" in filename_lower or "rbi" in filename_lower:
            dest_dir = BASE_DIR / "Banking"

        if dest_dir:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / pdf_file.name
            if not dest_file.exists():
                try:
                    shutil.copy2(pdf_file, dest_file)
                    moved += 1
                    logger.info(f"Moved: {pdf_file.name} → {dest_dir.name}/")
                except Exception as e:
                    logger.error(f"Could not copy {pdf_file.name}: {e}")
        else:
            logger.warning(f"Could not categorize: {pdf_file.name}")

    logger.info(f"Organization complete. Moved {moved} files.")


def main():
    parser = argparse.ArgumentParser(description="PYQ Organizer & Index Builder")
    parser.add_argument("--organize", action="store_true", help="Organize files from archive")
    parser.add_argument("--index", action="store_true", help="Build master index")
    parser.add_argument("--report", action="store_true", help="Generate summary report")
    parser.add_argument("--verify-pdfs", action="store_true", help="Verify PDF integrity")
    parser.add_argument("--all", action="store_true", help="Run all operations")
    args = parser.parse_args()

    if args.all or args.organize:
        organize_files()
    if args.all or args.index:
        build_master_index()
    if args.all or args.report:
        generate_report()
    if args.all or args.verify_pdfs:
        verify_pdfs()

    if not any([args.all, args.organize, args.index, args.report, args.verify_pdfs]):
        parser.print_help()


if __name__ == "__main__":
    main()
