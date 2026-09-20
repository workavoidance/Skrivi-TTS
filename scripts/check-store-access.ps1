$ErrorActionPreference = 'Stop'

foreach ($name in @('AZURE_AD_APPLICATION_CLIENT_ID', 'AZURE_AD_APPLICATION_SECRET', 'AZURE_AD_TENANT_ID', 'SELLER_ID')) {
    if (-not [Environment]::GetEnvironmentVariable($name)) { throw "Missing GitHub secret: $name" }
}
$tenant = [guid]::Parse($env:AZURE_AD_TENANT_ID).ToString()
$client = [guid]::Parse($env:AZURE_AD_APPLICATION_CLIENT_ID).ToString()
try {
    $token = Invoke-RestMethod -Method Post -Uri "https://login.microsoftonline.com/$tenant/oauth2/token" -Body @{
        grant_type = 'client_credentials'
        client_id = $client
        client_secret = $env:AZURE_AD_APPLICATION_SECRET
        resource = 'https://manage.devcenter.microsoft.com'
    }
} catch {
    throw 'Microsoft authentication failed. Check the tenant, client ID, and unexpired client secret.'
}
if (-not $token.access_token) { throw 'Microsoft returned no access token.' }
Write-Output "::add-mask::$($token.access_token)"
try {
    $apps = @()
    $relative = 'applications?top=100'
    do {
        if ($relative -notmatch '^applications(?:\?[A-Za-z0-9=&]+)?$') { throw 'Unexpected pagination link.' }
        $page = Invoke-RestMethod -Uri "https://manage.devcenter.microsoft.com/v1.0/my/$relative" -Headers @{
            Authorization = "Bearer $($token.access_token)"
        }
        $apps += @($page.value)
        $relative = $page.'@nextLink'
    } while ($relative)
} catch {
    throw 'Authentication succeeded, but Store app discovery failed. Check Partner Center permissions and API eligibility.'
}
$matches = @($apps | Where-Object { $_.packageIdentityName -eq 'Skrivi.SkriviLytt' -and $_.publisherName -eq 'CN=EF3D997F-87B2-4AD0-B65B-877EE1632E65' })
if ($matches.Count -ne 1) { throw 'Expected exactly one Skrivi Lytt Store listing with the reserved package identity.' }
$app = $matches[0]
$productId = [string]$app.id
if ($productId -notmatch '^[A-Z0-9]{12}$') { throw 'Unexpected Store product ID.' }
if ($env:STORE_PRODUCT_ID -and $env:STORE_PRODUCT_ID -ne $productId) { throw 'Store product ID changed between checks.' }
if ($env:GITHUB_OUTPUT) { "product_id=$productId" | Add-Content $env:GITHUB_OUTPUT }
Write-Output "Skrivi Lytt Store product: $productId"
$published = [bool]$app.lastPublishedApplicationSubmission.id
$pending = [bool]$app.pendingApplicationSubmission.id
$summary = @(
    'Microsoft authentication and Skrivi Lytt app access succeeded.',
    "Previously published submission: $published",
    "Pending submission or draft: $pending"
)
$summary | Write-Output
if ($env:GITHUB_STEP_SUMMARY) { $summary | Add-Content $env:GITHUB_STEP_SUMMARY }
if ($env:STORE_SUBMIT -eq 'true') {
    if (-not $published) { throw 'Complete the first Store submission in Partner Center before automating updates.' }
    if ($pending) { throw 'A Store draft or submission already exists. Resolve it in Partner Center; automation will not replace it.' }
}

if ($pending -and $env:STORE_SUBMIT -ne 'true') {
    $submissionId = [string]$app.pendingApplicationSubmission.id
    if ($submissionId -notmatch '^[0-9]+$') { throw 'Unexpected submission identifier.' }
    try {
        $state = Invoke-RestMethod -Uri "https://manage.devcenter.microsoft.com/v1.0/my/applications/$productId/submissions/$submissionId/status" -Headers @{
            Authorization = "Bearer $($token.access_token)"
        }
    } catch {
        throw 'Could not retrieve the pending submission status.'
    }
    $message = "Pending submission ${submissionId}: $($state.status)"
    Write-Output $message
    if ($env:GITHUB_STEP_SUMMARY) { $message | Add-Content $env:GITHUB_STEP_SUMMARY }
}
