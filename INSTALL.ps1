param([switch]$NoLaunch)
$ErrorActionPreference = 'Stop'
function Read-Sha256([string]$path) {
    $stream = [IO.File]::OpenRead($path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}
try {
    $manifest = Get-Content -LiteralPath "$PSScriptRoot\package.json" -Raw | ConvertFrom-Json
    if ($manifest.version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid version in package manifest.' }
    $libraryRoot = Join-Path $env:LOCALAPPDATA 'SkriviTTS'
    $versionRoot = Join-Path $libraryRoot ('versions\' + $manifest.version)
    $packageRoot = [IO.Path]::GetFullPath($PSScriptRoot) + [IO.Path]::DirectorySeparatorChar
    foreach ($item in $manifest.files.PSObject.Properties) {
        $sourceFile = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $item.Name))
        if (!$sourceFile.StartsWith($packageRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid path in package.' }
        if ((Read-Sha256 $sourceFile) -ne $item.Value) { throw "Package verification failed: $($item.Name)" }
    }
    foreach ($item in $manifest.files.PSObject.Properties) {
        if ($item.Name.StartsWith('app/')) {
            $destinationFile = Join-Path $versionRoot $item.Name.Substring(4)
        } elseif ($item.Name.StartsWith('runtimes/') -or $item.Name.StartsWith('models/')) {
            $destinationFile = Join-Path $libraryRoot $item.Name
        } else { continue }
        if ((Test-Path -LiteralPath $destinationFile) -and (Read-Sha256 $destinationFile) -eq $item.Value) { continue }
        if ($item.Name.StartsWith('models/') -and (Test-Path -LiteralPath $destinationFile)) { throw 'An existing model differs from this bundle. It has been preserved; verify it in the Model library before installing.' }
        if ($item.Name.StartsWith('runtimes/') -and (Test-Path -LiteralPath $destinationFile)) { throw 'An existing runtime differs from this immutable profile. It has been preserved; use a new runtime profile.' }
        New-Item -ItemType Directory -Force -Path (Split-Path $destinationFile) | Out-Null
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $item.Name) -Destination $destinationFile
    }
    $installedApp = Join-Path $versionRoot 'SkriviTTS.exe'
    $registration = Start-Process -FilePath $installedApp -ArgumentList '--register-bundled' -WindowStyle Hidden -PassThru -Wait
    if ($registration.ExitCode -ne 0) { throw 'Could not register the bundled models. Existing shortcuts are unchanged.' }
    # Preserve the startup choice while updating its versioned path.
    $startupKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    if ((Get-ItemProperty -LiteralPath $startupKey -Name SkriviTTS -ErrorAction SilentlyContinue)) {
        Set-ItemProperty -LiteralPath $startupKey -Name SkriviTTS -Value ('"' + $installedApp + '" --tray')
    }
    # Switch shortcuts only after the complete package is verified and copied.
    $shellLink = New-Object -ComObject WScript.Shell
    $menuPath = Join-Path ([Environment]::GetFolderPath('Programs')) 'Skrivi TTS.lnk'
    $shortcut = $shellLink.CreateShortcut($menuPath)
    $shortcut.TargetPath = Join-Path $versionRoot 'SkriviTTS.exe'
    $shortcut.IconLocation = $shortcut.TargetPath + ",0"
    $shortcut.WorkingDirectory = $versionRoot
    $shortcut.Save()
    $desktopLink = $shellLink.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Skrivi TTS.lnk'))
    $desktopLink.TargetPath = $shortcut.TargetPath
    $desktopLink.IconLocation = $shortcut.TargetPath + ",0"
    $desktopLink.WorkingDirectory = $versionRoot
    $desktopLink.Save()
    Write-Host "Installed Skrivi TTS $($manifest.version). Existing models, settings, presets and audio were preserved."
    if (!$NoLaunch) { Start-Process -FilePath $shortcut.TargetPath -WorkingDirectory $versionRoot -WindowStyle Hidden }
} catch {
    Write-Host "Installation did not complete: $_"
    exit 1
}
