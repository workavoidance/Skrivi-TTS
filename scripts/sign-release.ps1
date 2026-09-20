param([Parameter(Mandatory=$true)][string]$Root,[Parameter(Mandatory=$true)][string]$Thumbprint,[switch]$VerifyOnly)
$ErrorActionPreference='Stop'
$signTool=Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe" | Sort-Object FullName -Descending | Select-Object -First 1
if (!$signTool) { throw 'Windows SDK SignTool is required.' }
if ($Thumbprint -notmatch '^[0-9a-fA-F]{40}$') { throw 'Invalid signing certificate thumbprint.' }
$files=Get-ChildItem -LiteralPath $Root -Recurse -File | Where-Object { $_.Extension -in '.exe','.dll','.pyd','.ps1' }
$records=@()
foreach ($file in $files) {
    $sig=Get-AuthenticodeSignature -LiteralPath $file.FullName
    if (!$VerifyOnly -and $sig.Status -ne 'Valid') {
        if ($sig.Status -ne 'NotSigned') { throw "Existing invalid signature: $($file.Name)" }
        & $signTool.FullName sign /sha1 $Thumbprint /fd SHA256 /tr http://time.certum.pl /td SHA256 $file.FullName
        if ($LASTEXITCODE -ne 0) { throw "Signing failed: $($file.Name)" }
        $sig=Get-AuthenticodeSignature -LiteralPath $file.FullName
        if ($sig.SignerCertificate.Thumbprint -ne $Thumbprint) { throw 'Unexpected signing certificate.' }
        if (!$sig.TimeStamperCertificate) { throw 'Timestamp missing.' }
    }
    if ($sig.Status -ne 'Valid') { throw "Signature verification failed: $($file.Name)" }
    & $signTool.FullName verify /pa /all $file.FullName
    if ($LASTEXITCODE -ne 0) { throw "Trust validation failed: $($file.Name)" }
    $records += @{ file=$file.FullName.Substring((Resolve-Path $Root).Path.Length).TrimStart('\'); signer=$sig.SignerCertificate.Subject; thumbprint=$sig.SignerCertificate.Thumbprint }
}
$records | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Root 'SIGNATURES.json') -Encoding utf8
Write-Host "Verified $($files.Count) executable/script signatures."
