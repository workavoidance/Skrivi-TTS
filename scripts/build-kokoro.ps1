$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot)
$kokoroPython = Join-Path (Get-Location) 'build/english-env/Scripts/python.exe'
& $kokoroPython -m PyInstaller --noconfirm --onedir --console --name KokoroWorker --exclude-module torch --exclude-module spacy_curated_transformers --exclude-module curated_transformers --collect-all kokoro_onnx --collect-all misaki --collect-all en_core_web_sm --collect-all espeakng_loader --collect-all language_tags --collect-all segments --collect-all csvw --collect-all phonemizer --collect-all spacy --collect-all soundfile --collect-all onnxruntime --copy-metadata en_core_web_sm --copy-metadata misaki --copy-metadata kokoro-onnx kokoro_host.py
if ($LASTEXITCODE -ne 0) { throw 'Kokoro runtime build failed' }
