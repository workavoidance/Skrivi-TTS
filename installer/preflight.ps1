param(
    [Parameter(Mandatory=$true)][string]$ManifestPath,
    [Parameter(Mandatory=$true)][string]$LibraryRoot
)
$ErrorActionPreference = 'Stop'
try {
    $manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    $base = [IO.Path]::GetFullPath($LibraryRoot).TrimEnd('\') + '\'
    foreach ($item in $manifest.files.PSObject.Properties) {
        if (!$item.Name.StartsWith('models/') -and !$item.Name.StartsWith('runtimes/')) { continue }
        $destination = [IO.Path]::GetFullPath((Join-Path $base $item.Name))
        if (!$destination.StartsWith($base, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Invalid path in package manifest.'
        }
        if (Test-Path -LiteralPath $destination) {
            if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Value) {
                throw "Existing file differs and has been preserved: $($item.Name)"
            }
        }
    }
    exit 0
} catch {
    Write-Error $_
    exit 1
}
