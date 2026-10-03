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

# Keep the key out of the console and out of shell history: it is passed as one argument.
$envVars = "GEMINI_API_KEY=$key,GEMINI_MODEL=gemini-2.5-flash,TRUSTED_PROXY_HOPS=1"

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
    --set-env-vars $envVars

if ($LASTEXITCODE -ne 0) { throw "Cloud Run deploy failed." }

& $gcloud run services describe $Service --project $Project --region $Region --format "value(status.url)"
