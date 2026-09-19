param([switch]$NoLaunch)
$ErrorActionPreference = 'Stop'
try {
    $manifest = Get-Content -LiteralPath "$PSScriptRoot\package.json" -Raw | ConvertFrom-Json
    $libraryRoot = Join-Path $env:LOCALAPPDATA 'SkriviTTS'
    foreach ($item in $manifest.required_runtimes.PSObject.Properties) {
        $target = [IO.Path]::GetFullPath((Join-Path $libraryRoot $item.Name))
        $runtimeRoot = [IO.Path]::GetFullPath((Join-Path $libraryRoot 'runtimes')) + [IO.Path]::DirectorySeparatorChar
        if (!$target.StartsWith($runtimeRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid runtime path in update.' }
        if (!(Test-Path -LiteralPath $target)) { throw 'This update needs the full 0.2.1 installation first. Download the full Windows package; existing models will be reused.' }
        if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Value) { throw 'This update needs a different engine runtime. Use the full Windows package; existing models will be reused.' }
    }
    & "$PSScriptRoot\INSTALL-core.ps1" -NoLaunch:$NoLaunch
    exit $LASTEXITCODE
} catch {
    Write-Host "Update did not complete: $_"
    exit 1
}
