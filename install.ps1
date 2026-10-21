# ==============================================================================
# Windows PowerShell Auto-Installer & Self-Healing Setup for fbacc
# Supported: Windows 10, Windows 11, Windows Server (PowerShell 5.1 & PowerShell 7+)
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "   ███████  ██    ██  ██████   ██   ██  ███    ███" -ForegroundColor Green
Write-Host "   ██        ██  ██   ██   ██  ██   ██  ████  ████" -ForegroundColor Green
Write-Host "   █████      ████    ██   ██  ███████  ██ ████ ██" -ForegroundColor Green
Write-Host "   ██          ██     ██   ██  ██   ██  ██  ██  ██" -ForegroundColor Green
Write-Host "   ███████     ██     ██████   ██   ██  ██      ██" -ForegroundColor Green
Write-Host "   EYDHM ENTERPRISE AUTOMATION & RECOVERY SUITE" -ForegroundColor Cyan
Write-Host "   Windows Automated Setup & Smart Doctor" -ForegroundColor DarkGray
Write-Host "   ─────────────────────────────────────────────────────────────────`n"

# 1. Python Detection & Bootstrapping
Write-Host "   [1/4] Checking Python Runtime Environment..." -ForegroundColor Cyan
$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
}

if (-not $PythonCmd) {
    Write-Host "   [!] Python not found in system PATH." -ForegroundColor Yellow
    Write-Host "   [*] Attempting auto-installation via Windows Package Manager (winget)..." -ForegroundColor Cyan
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $PythonCmd = "python"
    } else {
        Write-Host "   [x] Fatal: Python 3.8+ required. Please install Python from https://python.org" -ForegroundColor Red
        Exit 1
    }
}

$PyVer = & $PythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
Write-Host "   [✓] Python Runtime Detected: $PyVer ($PythonCmd)`n" -ForegroundColor Green

# 2. Workspace & Git Clone
Write-Host "   [2/4] Resolving Installation Workspace..." -ForegroundColor Cyan
$InstallDir = "$HOME\fbacc"
if (Test-Path "$PSScriptRoot\fbacc.py") {
    $TargetDir = $PSScriptRoot
    Write-Host "   [✓] Using current workspace: $TargetDir`n" -ForegroundColor Green
} else {
    $TargetDir = $InstallDir
    if (-not (Test-Path "$TargetDir\.git")) {
        Write-Host "   [*] Cloning repository to $TargetDir..." -ForegroundColor DarkGray
        git clone https://github.com/ficxuio-crypto/fbacc.git "$TargetDir"
    } else {
        Write-Host "   [*] Updating local repository at $TargetDir..." -ForegroundColor DarkGray
        git -C "$TargetDir" pull origin main
    }
    Write-Host "   [✓] Workspace prepared at $TargetDir`n" -ForegroundColor Green
}

Set-Location $TargetDir

# 3. Smart Doctor Dependency Diagnostic & Auto-Repair
Write-Host "   [3/4] Running Smart Doctor Dependency Diagnostic..." -ForegroundColor Cyan
& $PythonCmd doctor.py

# 4. Command Alias Registration
Write-Host "`n   [4/4] Registering Global Command Shortcut..." -ForegroundColor Cyan
$BatchLauncher = "$HOME\AppData\Local\Microsoft\WindowsApps\fbacc.cmd"
try {
    "@echo off`ncd /d `"$TargetDir`"`n$PythonCmd fbacc.py %*" | Out-File -FilePath $BatchLauncher -Encoding ascii -Force
    Write-Host "   [✓] Global CLI command registered: fbacc" -ForegroundColor Green
} catch {
    Write-Host "   [!] Note: You can launch anytime by navigating to $TargetDir and running '$PythonCmd fbacc.py'" -ForegroundColor DarkGray
}

Write-Host "`n   ═════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "   ✔ WINDOWS SETUP COMPLETE!" -ForegroundColor Green
Write-Host "   Launch interactive menu anytime with:" -ForegroundColor Cyan
Write-Host "      fbacc             (or: python fbacc.py)" -ForegroundColor Yellow
Write-Host "   ═════════════════════════════════════════════════════════════════`n" -ForegroundColor Green
