$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot)
$ocrPython = Join-Path (Get-Location) 'build/ocr-env/Scripts/python.exe'
$priorPath = $env:PATH
$env:PATH = "$env:WINDIR\System32;$env:WINDIR;$(Split-Path $ocrPython)"
try {
    & $ocrPython -m PyInstaller --clean --noconfirm --onedir --console --name OCRWorker --collect-all tesserocr ocr_host.py
    if ($LASTEXITCODE -ne 0) { throw 'OCR worker build failed' }
} finally { $env:PATH = $priorPath }
