# Codex AccMgr - One-Click Installer for Windows PowerShell

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/lsjlovezz9-afk/Codex-AccMgr.git"
$InstallDir = Join-Path $env:USERPROFILE ".codex\codex-accmgr-app"
$AliasName = "codex-accmgr"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Codex AccMgr - Auto Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check requirements
if (-not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: git is not installed. Please install git for Windows first." -ForegroundColor Red
    exit
}

if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: python is not installed. Please install Python 3.6+ first." -ForegroundColor Red
    exit
}

# Clone or update repository
Write-Host "[1/3] Cloning/Updating repository..." -ForegroundColor Yellow
if (Test-Path $InstallDir) {
    Write-Host "Directory $InstallDir already exists. Updating..."
    Set-Location $InstallDir
    git pull origin main
} else {
    $CodexDir = Join-Path $env:USERPROFILE ".codex"
    if (-not (Test-Path $CodexDir)) {
        New-Item -ItemType Directory -Force -Path $CodexDir | Out-Null
    }
    git clone $RepoUrl $InstallDir
    Set-Location $InstallDir
}

# Install alias into PowerShell profile
Write-Host "[2/3] Configuring PowerShell profile..." -ForegroundColor Yellow
$ProfilePath = $PROFILE

if (-not (Test-Path (Split-Path $ProfilePath))) {
    New-Item -Type Directory -Path (Split-Path $ProfilePath) -Force | Out-Null
}
if (-not (Test-Path $ProfilePath)) {
    New-Item -Type File -Path $ProfilePath -Force | Out-Null
}

$RunPath = Join-Path $InstallDir "run.bat"
# We define a function instead of an alias so it can pass arguments properly if needed in the future
$AliasStr = "function ${AliasName} { & `"$RunPath`" @args }"

$ProfileContent = Get-Content $ProfilePath -ErrorAction SilentlyContinue
if ($ProfileContent -match "function ${AliasName} ") {
    Write-Host "Function '$AliasName' already exists in your PowerShell profile. Skipping."
} else {
    Add-Content -Path $ProfilePath -Value "`n# Codex AccMgr`n$AliasStr"
    Write-Host "Added '$AliasName' function to $ProfilePath"
}

Write-Host "[3/3] Installation Complete! 🎉" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start using Codex AccMgr, please restart your PowerShell or run:"
Write-Host "  . `"$ProfilePath`""
Write-Host ""
Write-Host "Then simply type: $AliasName"
Write-Host "========================================" -ForegroundColor Cyan
