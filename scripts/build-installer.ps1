param([string]$Compiler = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe")
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$root = Split-Path $PSScriptRoot -Parent
$build = Join-Path $root 'build\exe-installer'
New-Item -ItemType Directory -Force -Path $build | Out-Null
$archive = Join-Path $build 'Skrivi-TTS-0.2.1-Windows-x64.zip'
$expected = '076beea27234c6442c7f782948c2680422176eb8a172e1aef16b2f96c4e58050'
if (!(Test-Path -LiteralPath $archive)) {
    Write-Host 'Downloading the published full bundle...'
    & curl.exe --fail --location --retry 3 --output $archive 'https://github.com/workavoidance/Skrivi-TTS/releases/download/v0.2.1/Skrivi-TTS-0.2.1-Windows-x64.zip'
    if ($LASTEXITCODE -ne 0) { throw 'Bundle download failed.' }
}
Write-Host 'Verifying published archive...'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'Published source archive checksum mismatch.'
}
$payload = Join-Path $build 'payload'
Write-Host 'Extracting payload...'
if (!(Test-Path -LiteralPath $payload)) { Expand-Archive -LiteralPath $archive -DestinationPath $payload }
$manifest = Get-Content -LiteralPath (Join-Path $payload 'package.json') -Raw | ConvertFrom-Json
if ($manifest.version -ne '0.2.1') { throw 'Unexpected app version.' }
$prefix = [IO.Path]::GetFullPath($payload) + '\'
Write-Host 'Verifying all payload files...'
foreach ($item in $manifest.files.PSObject.Properties) {
    $file = [IO.Path]::GetFullPath((Join-Path $payload $item.Name))
    if (!$file.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid package path.' }
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Value) {
        throw "Package file checksum mismatch: $($item.Name)"
    }
}
# No app, model or engine is rebuilt: these are the exact published 0.2.1 bytes.
$output = Join-Path $root 'dist\installer'
New-Item -ItemType Directory -Force -Path $output | Out-Null
Write-Host 'Compiling Windows setup...'
& $Compiler "/DPackageDir=$payload" "/DOutputDir=$output" (Join-Path $root 'installer\SkriviTTS.iss')
if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed.' }
$exe = Join-Path $output 'Skrivi-TTS-0.2.1-windows-x64-setup.exe'
$hash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  $([IO.Path]::GetFileName($exe))" | Set-Content -LiteralPath (Join-Path $output 'INSTALLER-SHA256SUMS.txt') -Encoding ascii
$commit = & git -C $root rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'Cannot record installer source commit.' }
@{
    installer_source_commit = $commit.Trim()
    app_version = $manifest.version
    app_source_commit = $manifest.source_commit
    source_archive_sha256 = $expected
    installer_sha256 = $hash
    compiler = (Get-Item -LiteralPath $Compiler).VersionInfo.FileVersion
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'INSTALLER-PROVENANCE.json') -Encoding utf8
