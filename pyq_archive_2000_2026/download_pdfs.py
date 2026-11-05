"""Download PDF URLs listed in pdf_urls.csv. Python 3 standard library only.
Run: python download_pdfs.py
This script does not scrape websites or bypass login/captcha/access restrictions.
"""
import csv, pathlib, urllib.request, urllib.parse, time
ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'papers'
OUT.mkdir(exist_ok=True)
with (ROOT / 'pdf_urls.csv').open(newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
for row in rows:
    url = row['pdf_url'].strip()
    if not url or not url.lower().startswith('https://'):
        continue
    category = ''.join(c if c.isalnum() or c in '-_' else '_' for c in row['category'])
    exam = ''.join(c if c.isalnum() or c in '-_' else '_' for c in row['exam'])
    year = row['year'].strip()
    filename = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in row['filename'])
    target = OUT / category / exam / year / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        print('SKIP', target)
        continue
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 PYQ personal archival downloader'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read(100_000_000)
        if not data.startswith(b'%PDF'):
            print('NOT PDF', url)
            continue
        target.write_bytes(data)
        print('OK', target)
    except Exception as e:
        print('FAILED', url, str(e))
    time.sleep(1)
