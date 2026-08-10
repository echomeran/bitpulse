param(
    [string]$BundleId = "com.bitpulse.app",
    [string]$Version = "1.0.0",
    [int]$BuildNumber = 1,
    [string]$KeystorePath = ""
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$flet = Join-Path $projectRoot "venv\Scripts\flet.exe"
$appPath = Join-Path $projectRoot "src"
$outputPath = Join-Path $projectRoot "build\apk"

if (-not (Test-Path $flet)) {
    throw "Flet was not found at $flet. Activate/install the project virtual environment first."
}

$arguments = @(
    "build", "apk", $appPath,
    "--output", $outputPath,
    "--project", "bitpulse",
    "--product", "BitPulse",
    "--org", "com.bitpulse",
    "--bundle-id", $BundleId,
    "--description", "Bitcoin news, market data and AI education.",
    "--build-version", $Version,
    "--build-number", $BuildNumber,
    "--arch", "arm64-v8a",
    "--android-permissions", "android.permission.INTERNET=True", "android.permission.ACCESS_NETWORK_STATE=True"
)

if ($KeystorePath) {
    $arguments += "--android-signing-key-store", $KeystorePath
}

& $flet @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Android build failed."
}
