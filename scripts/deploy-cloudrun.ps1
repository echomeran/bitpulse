param(
    [string]$Project = "project-a77b5649-8414-4a19-bd5",
    [string]$Service = "bitpulse-api",
    [string]$Region = "europe-west3"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot "server\.env"
$gcloud = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

if (-not (Test-Path $gcloud)) { throw "gcloud not found at $gcloud" }
if (-not (Test-Path $envFile)) { throw "server\.env not found; it must hold GEMINI_API_KEY." }

$match = Select-String -Path $envFile -Pattern '^GEMINI_API_KEY=(.+)$'
if (-not $match) { throw "GEMINI_API_KEY missing from server\.env" }
$key = $match.Matches[0].Groups[1].Value.Trim()

# Publishers whose terms forbid AI use of their articles without written consent (CoinDesk,
# Cointelegraph; permission asked 2026-11-25). Their pages are never fetched for summaries or chat.
# Remove a host once that publisher agrees in writing.
$summaryBlockedHosts = "coindesk.com,cointelegraph.com"

# The variables go through a temporary YAML file: it keeps the key off the command line, and the
# comma-separated host list survives (cmd.exe, which runs gcloud.cmd, would mangle "^" escapes).
$envFileYaml = Join-Path ([System.IO.Path]::GetTempPath()) ("bitpulse-env-" + [guid]::NewGuid() + ".yaml")
$yaml = @(
    "GEMINI_API_KEY: '$key'"
    "TRUSTED_PROXY_HOPS: '1'"
    "SUMMARY_BLOCKED_HOSTS: '$summaryBlockedHosts'"
) -join "`n"
[System.IO.File]::WriteAllText($envFileYaml, $yaml, (New-Object System.Text.UTF8Encoding $false))

try {
& $gcloud run deploy $Service `
    --project $Project `
    --source (Join-Path $projectRoot "server") `
    --region $Region `
    --allow-unauthenticated `
    --quiet `
    --memory 512Mi `
    --cpu 1 `
    --max-instances 3 `
    --timeout 60 `
    --env-vars-file $envFileYaml
} finally {
    Remove-Item -LiteralPath $envFileYaml -Force -ErrorAction SilentlyContinue
}

if ($LASTEXITCODE -ne 0) { throw "Cloud Run deploy failed." }

& $gcloud run services describe $Service --project $Project --region $Region --format "value(status.url)"
