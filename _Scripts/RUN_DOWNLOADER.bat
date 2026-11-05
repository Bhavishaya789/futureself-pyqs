@echo off
REM ============================================================
REM PYQ Collection Master Runner
REM Run this script to start downloading all PYQ papers
REM ============================================================

echo.
echo ============================================================
echo   PYQ COLLECTION - MASTER DOWNLOADER
echo   Coverage: 2000-2026 | All Major Indian Exams
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Install dependencies
echo Installing required packages...
pip install requests beautifulsoup4 lxml --quiet
if errorlevel 1 (
    echo ERROR: Failed to install packages
    pause
    exit /b 1
)

echo.
echo Select what to download:
echo   1. ALL exams (recommended - full collection)
echo   2. CBSE Class 10 only
echo   3. CBSE Class 12 only
echo   4. JEE (Mains + Advanced)
echo   5. NEET
echo   6. NDA
echo   7. CA (Foundation + Intermediate + Final)
echo   8. UPSC (all exams)
echo   9. SSC (all exams)
echo   10. Banking exams
echo   11. Railways exams
echo   12. Scrape from official websites
echo   13. Organize existing files + Build index
echo.
set /p choice="Enter choice (1-13): "

cd /d "%~dp0"

if "%choice%"=="1" (
    echo Starting FULL collection...
    python pyq_downloader.py --exam ALL
    python pyq_scraper.py --all
    python pyq_organizer.py --all
)
if "%choice%"=="2" (
    python pyq_downloader.py --exam CBSE --class 10
    python pyq_scraper.py --source cbse_official
)
if "%choice%"=="3" (
    python pyq_downloader.py --exam CBSE --class 12
    python pyq_scraper.py --source cbse_official
)
if "%choice%"=="4" (
    python pyq_downloader.py --exam JEE
    python pyq_scraper.py --source nta_official
)
if "%choice%"=="5" (
    python pyq_downloader.py --exam NEET
    python pyq_scraper.py --source nta_official
)
if "%choice%"=="6" (
    python pyq_downloader.py --exam NDA
)
if "%choice%"=="7" (
    python pyq_downloader.py --exam CA
    python pyq_scraper.py --source icai_official
)
if "%choice%"=="8" (
    python pyq_downloader.py --exam UPSC
    python pyq_scraper.py --source upsc_official
)
if "%choice%"=="9" (
    python pyq_downloader.py --exam SSC
    python pyq_scraper.py --source ssc_official
)
if "%choice%"=="10" (
    python pyq_downloader.py --exam Banking
)
if "%choice%"=="11" (
    python pyq_downloader.py --exam Railways
)
if "%choice%"=="12" (
    python pyq_scraper.py --all
)
if "%choice%"=="13" (
    python pyq_organizer.py --all
)

echo.
echo ============================================================
echo   DONE! Check _Index\COLLECTION_REPORT.txt for summary
echo   Check _Downloads_Log\ for detailed logs
echo ============================================================
pause
