# Build RigAlert MSI installer
# Run from the installer\ directory or from the repo root
# Requires: WiX v3 at C:\wix3 and a built dist\RigAlert.exe

$ErrorActionPreference = "Stop"
$repo    = Split-Path $PSScriptRoot -Parent
$wix     = "C:\wix3"
$distDir = Join-Path $repo "dist"
$installer = Join-Path $repo "installer"

# 1. Build EXE first
Write-Host "==> Building EXE with PyInstaller..." -ForegroundColor Cyan
Push-Location $repo
python -m PyInstaller RigAlert.spec --noconfirm
Pop-Location

# 2. Compile WXS -> WIXOBJ
Write-Host ""
Write-Host "==> Compiling WXS..." -ForegroundColor Cyan
& "$wix\candle.exe" -arch x64 "$installer\RigAlert.wxs" -out "$distDir\RigAlert.wixobj"

# 3. Link WIXOBJ -> MSI
Write-Host ""
Write-Host "==> Linking MSI..." -ForegroundColor Cyan
& "$wix\light.exe" `
    -ext "$wix\WixUIExtension.dll" `
    "$distDir\RigAlert.wixobj" `
    -out "$distDir\RigAlert.msi" `
    -cultures:en-us `
    -sw1076

# 4. Report
$msi = Join-Path $distDir "RigAlert.msi"
if (Test-Path $msi) {
    $size = [math]::Round((Get-Item $msi).Length / 1MB, 1)
    Write-Host ""
    Write-Host "SUCCESS: dist\RigAlert.msi ($size MB)" -ForegroundColor Green

    # Optional: copy to Desktop
    $desktop = [Environment]::GetFolderPath("Desktop")
    Copy-Item $msi "$desktop\RigAlert.msi" -Force
    Write-Host "Copied to Desktop." -ForegroundColor Green
} else {
    Write-Host "FAILED — MSI not created." -ForegroundColor Red
    exit 1
}
