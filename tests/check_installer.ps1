param([string]$Version='0.2.1',[string]$InstallerPath='',[string]$PayloadPath='',[switch]$RequireSigned)
# Deliberately CI-only: never install/uninstall or create test fixtures in a user's library.
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_ENVIRONMENT -ne 'github-hosted') {
    throw 'This integration test is restricted to a disposable GitHub-hosted runner.'
}
$root = Split-Path $PSScriptRoot -Parent
$library = Join-Path $env:LOCALAPPDATA 'SkriviTTS'
if (Test-Path -LiteralPath $library) { throw 'Test requires an empty disposable library.' }
$evidence = Join-Path $root 'build\installer-tests'
New-Item -ItemType Directory -Force -Path $evidence | Out-Null
$installer = if ($InstallerPath) { (Resolve-Path $InstallerPath).Path } else { Join-Path $root 'dist\installer\Skrivi-TTS-0.2.1-windows-x64-setup.exe' }
$manifestPath = if ($PayloadPath) { Join-Path (Resolve-Path $PayloadPath).Path 'package.json' } else { Join-Path $root 'build\exe-installer\payload\package.json' }
function Run-Setup([string]$name, [bool]$shouldPass) {
    $log = Join-Path $evidence ($name + '.log')
    $proc = Start-Process -FilePath $installer -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/LOG="' + $log + '"')) -WindowStyle Hidden -PassThru
    if (!$proc.WaitForExit(300000)) { Stop-Process -Id $proc.Id; throw "Timed out: $name" }
    if (($proc.ExitCode -eq 0) -ne $shouldPass) { if (Test-Path -LiteralPath $log) { Get-Content -LiteralPath $log -Tail 60 | Write-Host }; throw "$name returned $($proc.ExitCode)" }
}
# Check conflict handling before any app files or shortcuts are installed.
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$modelEntry = $manifest.files.PSObject.Properties | Where-Object { $_.Name.StartsWith('models/') } | Select-Object -First 1
$conflict = Join-Path $library $modelEntry.Name
New-Item -ItemType Directory -Force -Path (Split-Path $conflict) | Out-Null
Set-Content -LiteralPath $conflict -Value 'CI conflict fixture'
$before = (Get-FileHash -LiteralPath $conflict).Hash
Run-Setup 'conflict' $false
if ((Get-FileHash -LiteralPath $conflict).Hash -ne $before) { throw 'Conflicting model was overwritten.' }
if (Test-Path -LiteralPath (Join-Path $library "versions\$Version\SkriviTTS.exe")) { throw 'Conflict installed app anyway.' }
# Remove only this known disposable fixture, not a directory or model collection.
Remove-Item -LiteralPath $conflict
Run-Setup 'first-install' $true
$app = Join-Path $library "versions\$Version\SkriviTTS.exe"
$check = Start-Process -FilePath $app -ArgumentList '--check-startup' -WindowStyle Hidden -PassThru
if (!$check.WaitForExit(30000) -or $check.ExitCode -ne 0) { throw 'Installed startup failed.' }
$shortcut = Join-Path ([Environment]::GetFolderPath('Programs')) 'Skrivi TTS.lnk'
if (!(Test-Path -LiteralPath $shortcut)) { throw 'Start-menu shortcut missing.' }
$startup = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
if ((Get-ItemProperty -LiteralPath $startup -Name SkriviTTS -ErrorAction SilentlyContinue)) { throw 'Setup enabled startup without consent.' }
Set-Content -LiteralPath (Join-Path $library 'reader-settings.json') -Value '{"language":"en","speed":1.25}'
foreach ($name in @('presets','voices','outputs')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $library $name) | Out-Null
    Set-Content -LiteralPath (Join-Path $library ($name + '\ci-preservation.txt')) -Value 'preserve this user fixture'
}
function Snapshot {
    $rows = @{}
    Get-ChildItem -LiteralPath $library -Recurse -File | Where-Object {
        $_.FullName -notlike '*\versions\*' -and $_.FullName -notlike '*\uninstall\*'
    } | ForEach-Object {
        $rows[$_.FullName] = @{hash=(Get-FileHash -LiteralPath $_.FullName).Hash; ticks=$_.LastWriteTimeUtc.Ticks}
    }
    return $rows
}
$original = Snapshot
# Diagnose any package-integrity conflict directly before the second install.
& "$env:WINDIR/System32/WindowsPowerShell/v1.0/powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $root 'installer/preflight.ps1') -ManifestPath $manifestPath -LibraryRoot $library
if ($LASTEXITCODE -ne 0) { throw 'Installed data differs from the package manifest before reinstall.' }
Run-Setup 'reinstall' $true
foreach ($path in $original.Keys) {
    if (!(Test-Path -LiteralPath $path) -or (Get-FileHash -LiteralPath $path).Hash -ne $original[$path].hash) { throw "Reinstall changed $path" }
    # Registration may rewrite its index; weights, runtimes and user preferences must keep timestamps.
    if ([IO.Path]::GetFileName($path) -ne 'library.json' -and (Get-Item -LiteralPath $path).LastWriteTimeUtc.Ticks -ne $original[$path].ticks) { throw "Reinstall rewrote $path" }
}
& python (Join-Path $PSScriptRoot 'check_installed_voices.py') $Version
if ($LASTEXITCODE -ne 0) { throw 'Installed voice smoke tests failed.' }
$uninstaller = Join-Path $library 'uninstall\unins000.exe'
if ($RequireSigned -and (Get-AuthenticodeSignature -LiteralPath $uninstaller).Status -ne 'Valid') { throw 'Installed uninstaller must have a valid signature.' }
$uninstallLog = Join-Path $evidence 'uninstall.log'
$proc = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/LOG="' + $uninstallLog + '"')) -WindowStyle Hidden -PassThru
if (!$proc.WaitForExit(120000) -or $proc.ExitCode -ne 0) { throw 'Uninstall failed.' }
if (Test-Path -LiteralPath $app) { throw 'Uninstall retained executable.' }
if (Test-Path -LiteralPath $shortcut) { throw 'Uninstall retained shortcut.' }
foreach ($path in $original.Keys) {
    if (!(Test-Path -LiteralPath $path) -or (Get-FileHash -LiteralPath $path).Hash -ne $original[$path].hash) { throw "Uninstall changed user data: $path" }
}
@{conflict_preserved=$true; installed_startup=$true; reinstall_preserved=$original.Count; uninstall_preserved=$original.Count; voices='Bokmaal and English passed'} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence 'results.json') -Encoding utf8
