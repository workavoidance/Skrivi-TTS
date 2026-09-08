$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot)
$pythonBuild = Join-Path (Get-Location) '.build-env\Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonBuild)) { throw 'Create .build-env and install requirements-build.lock first.' }
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /target:exe /platform:x64 /r:System.Net.Http.dll /r:System.Web.Extensions.dll /out:native\VoxHost.exe native\Host.cs native\Engine.cs native\VoiceSettings.cs native\OwnedJob.cs native\Contracts.cs
if ($LASTEXITCODE -ne 0) { throw 'Native build failed' }
& $pythonBuild -m PyInstaller --noconfirm --onedir --windowed --name SkriviTTS --paths app app/main.py
if ($LASTEXITCODE -ne 0) { throw 'Application build failed' }
& $pythonBuild -m PyInstaller --noconfirm --onedir --console --name SkriviWorker --collect-all piper --collect-all tokenizers --collect-all onnxruntime --collect-all soundfile worker_host.py
if ($LASTEXITCODE -ne 0) { throw 'Engine runtime build failed' }
Write-Host 'Compiled desktop app and reusable engine runtime. Run scripts/package.py with the existing CrispASR runtime directory.'
