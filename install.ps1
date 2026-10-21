# ==============================================================================
# Windows PowerShell Auto-Installer for fbacc
# ==============================================================================

Write-Host "=== Facebook Automation Engine Windows Installer ===" -ForegroundColor Green

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Python was not detected in PATH. Please install Python 3.10+ from python.org or Microsoft Store." -ForegroundColor Red
    Exit 1
}

Write-Host "[+] Installing required Python packages..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "[+] Running QA self-verification..." -ForegroundColor Cyan
python fbacc.py --test

Write-Host "`n[+] Installation successful! Launch interactive menu with:" -ForegroundColor Green
Write-Host "    python fbacc.py" -ForegroundColor Yellow
