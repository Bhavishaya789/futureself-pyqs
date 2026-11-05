import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import sys
import os
import time
from pathlib import Path

BASE_DIR = Path(r"c:\Users\DELL\Downloads\pyq_collection_2000_2026_starter")

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})

def dl(url, dest):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"  SKIP: {dest.name}")
        return True
    for attempt in range(3):
        try:
            r = session.get(url, timeout=60, stream=True)
            r.raise_for_status()
            data = r.content
            if len(data) < 500:
                print(f"  Too small: {url}")
                return False
            with open(dest, "wb") as f:
                f.write(data)
            print(f"  OK ({len(data)//1024}KB): {dest.name}")
            return True
        except Exception as e:
            print(f"  Attempt {attempt+1}/3 failed: {e}")
            time.sleep(2**attempt)
    print(f"  FAILED: {url}")
    return False

# ============================================================
# 1. JEE ADVANCED - confirmed working pattern
# ============================================================
print("\n=== JEE ADVANCED ===")
r = session.get("https://jeeadv.ac.in/archive.html", timeout=20)
soup = BeautifulSoup(r.text, "html.parser")
jee_folder = BASE_DIR / "JEE" / "JEE_Advanced"

for a in soup.find_all("a", href=True):
    href = a["href"]
    if ".pdf" not in href.lower():
        continue
    full_url = urljoin("https://jeeadv.ac.in/", href)
    label = a.get_text(strip=True)
    
    # Determine paper and year from URL/text
    fname = href.split("/")[-1]
    
    # Pattern: past_qps/YYYY_1.pdf or past_qps/YYYY_2.pdf
    import re
    year_match = re.search(r"(20\d\d|19\d\d)", fname + label)
    year = year_match.group() if year_match else "unknown"
    
    paper = "1" if "_1" in fname or "paper1" in fname.lower() or "p1" in fname.lower() else \
            "2" if "_2" in fname or "paper2" in fname.lower() or "p2" in fname.lower() else "X"
    
    lang = "hindi" if "hindi" in fname.lower() or "hindi" in label.lower() else "english"
    
    dest = jee_folder / f"Paper_{paper}" / f"JEE_Advanced_{year}_Paper{paper}_{lang}.pdf"
    dl(full_url, dest)
    time.sleep(0.3)

# ============================================================
# 2. UPSC - scrape the full question papers page
# ============================================================
print("\n=== UPSC ===")
upsc_base = BASE_DIR / "UPSC"
r = session.get("https://upsc.gov.in/examinations/previous-question-papers", timeout=20)
soup = BeautifulSoup(r.text, "html.parser")

for a in soup.find_all("a", href=True):
    href = a["href"]
    if ".pdf" not in href.lower():
        continue
    full_url = urljoin("https://upsc.gov.in", href)
    label = a.get_text(strip=True).lower()
    fname = href.split("/")[-1]
    
    year_match = re.search(r"(20\d\d|19\d\d)", fname + label)
    year = year_match.group() if year_match else "unknown"
    
    # Categorize
    if "cse" in fname.lower() or "civil" in label or "ias" in fname.lower():
        if "pre" in fname.lower() or "prelim" in label:
            if "csat" in fname.lower():
                dest_folder = upsc_base / "Civil_Services" / "Prelims" / "CSAT_Paper_2"
            else:
                dest_folder = upsc_base / "Civil_Services" / "Prelims" / "General_Studies_Paper_1"
        elif "main" in fname.lower() or "mains" in label:
            gs_match = re.search(r"gs(\d)", fname.lower())
            gs_num = gs_match.group(1) if gs_match else "1"
            dest_folder = upsc_base / "Civil_Services" / "Mains" / f"General_Studies_{gs_num}"
        else:
            dest_folder = upsc_base / "Civil_Services"
    elif "cds" in fname.lower():
        dest_folder = upsc_base / "CDS" / "General_Knowledge"
    elif "nda" in fname.lower():
        dest_folder = upsc_base / "NDA_NA" / "Mathematics"
    elif "capf" in fname.lower():
        dest_folder = upsc_base / "CAPF" / "General_Ability_Intelligence"
    elif "ese" in fname.lower() or "ies" in fname.lower():
        dest_folder = upsc_base / "Engineering_Services_ESE" / "Civil_Engineering"
    else:
        dest_folder = upsc_base / "Civil_Services" / "Prelims" / "General_Studies_Paper_1"
    
    dest_folder.mkdir(parents=True, exist_ok=True)
    dest = dest_folder / f"UPSC_{year}_{fname}"
    dl(full_url, dest)
    time.sleep(0.3)

# ============================================================  
# 3. CBSE - scrape main page for SQP
# ============================================================
print("\n=== CBSE ===")
r = session.get("https://cbseacademic.nic.in/", timeout=20)
soup = BeautifulSoup(r.text, "html.parser")

for a in soup.find_all("a", href=True):
    href = a["href"]
    label = a.get_text(strip=True).lower()
    if ".pdf" not in href.lower():
        continue
    full_url = urljoin("https://cbseacademic.nic.in/", href)
    fname = href.split("/")[-1]
    
    year_match = re.search(r"(20\d\d|19\d\d)", fname + label)
    year = year_match.group() if year_match else "unknown"
    
    if "sqp" in fname.lower() or "sample" in label:
        if "xii" in href.lower() or "class12" in href.lower() or "12" in fname:
            cls_folder = BASE_DIR / "CBSE_Class_12"
        elif "x" in href.lower() or "class10" in href.lower() or "10" in fname:
            cls_folder = BASE_DIR / "CBSE_Class_10"
        else:
            cls_folder = BASE_DIR / "CBSE_Class_12"
        
        subject = "General"
        for subj in ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Hindi", "Science", "Economics", "History", "Geography", "Accountancy"]:
            if subj.lower() in fname.lower() or subj.lower() in label:
                subject = subj
                break
        
        dest = cls_folder / subject / f"CBSE_{year}_{fname}"
        dl(full_url, dest)
        time.sleep(0.3)

print("\nDone!")
