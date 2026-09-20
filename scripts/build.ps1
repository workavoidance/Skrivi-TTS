$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot)
$pythonBuild = Join-Path (Get-Location) '.build-env\Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonBuild)) { throw 'Create .build-env and install requirements-build.lock first.' }
& $pythonBuild scripts/prepare-build.py
if ($LASTEXITCODE -ne 0) { throw 'Preparing pinned runtime failed' }
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /target:exe /platform:x64 /r:System.Net.Http.dll /r:System.Web.Extensions.dll /out:native\VoxHost.exe native\Host.cs native\Engine.cs native\VoiceSettings.cs native\OwnedJob.cs native\Contracts.cs
if ($LASTEXITCODE -ne 0) { throw 'Native build failed' }
$framework = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319"
& "$framework\csc.exe" /nologo /target:exe /platform:x64 "/r:$framework\WPF\UIAutomationClient.dll" "/r:$framework\WPF\UIAutomationTypes.dll" "/r:$framework\WPF\WindowsBase.dll" /out:native\Selection.exe native\Selection.cs
if ($LASTEXITCODE -ne 0) { throw 'Selection helper build failed' }
# Resolve Windows SDK/system DLLs, never unrelated tools from an ambient PATH.
$originalBuildPath = $env:PATH
$env:PATH = "$env:WINDIR\System32;$env:WINDIR;$env:WINDIR\System32\Wbem;$(Split-Path $pythonBuild)"
try {
& $pythonBuild -m PyInstaller --clean --noconfirm --onedir --windowed --name SkriviTTS --icon assets/skrivi-tts.ico --collect-all langdetect --paths app app/main.py
if ($LASTEXITCODE -ne 0) { throw 'Application build failed' }
} finally { $env:PATH = $originalBuildPath }
$check = Start-Process -FilePath 'dist/SkriviTTS/SkriviTTS.exe' -ArgumentList '--check-startup' -WindowStyle Hidden -PassThru
if (!$check.WaitForExit(30000)) { Stop-Process -Id $check.Id; throw 'Packaged reader startup check timed out' }
if ($check.ExitCode -ne 0) { throw 'Packaged reader startup check failed' }
Write-Host 'Compiled desktop app and reusable engine runtime. Run scripts/package.py with the existing CrispASR runtime directory.'
