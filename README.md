# BitPulse

BitPulse is a Flet-based Bitcoin news, market, and AI education app. It shows attributed RSS headlines, a BTC/USD chart, the Fear & Greed Index, and an optional AI advisor.

## App setup

Use Python 3.10+ and install the mobile-app dependencies:

```powershell
cd src
..\venv\Scripts\python.exe -m pip install -r requirements.txt
..\venv\Scripts\flet.exe run main.py
```

The app works without the AI service; the AI tab displays a short unavailable message until an API URL is configured.

## AI service

The Gemini key must never be stored in the APK. The `server` directory contains a small FastAPI proxy with input validation, an in-memory rate limit, a timeout, and safe error responses.

```powershell
cd server
Copy-Item .env.example .env
# Set GEMINI_API_KEY in server\.env
..\venv\Scripts\python.exe -m pip install -r requirements.txt
..\venv\Scripts\uvicorn.exe app:app --host 0.0.0.0 --port 8080
```

For production, deploy `server` to a TLS-enabled service such as Cloud Run. Put the public HTTPS URL in `src/assets/app_config.json` as `ai_api_url`, then rebuild the APK. The URL is public; the Gemini key stays only on the server.

## Android build

Before a release build, choose a bundle ID you own and retain the Android signing key securely. A personal ARM64 test APK can be built with:

```powershell
.\scripts\build-android.ps1 -BundleId "com.yourname.bitpulse" -Version "1.0.0" -BuildNumber 1
```

Test a fresh install on a physical Android device: first launch, no network, refresh, all market periods, article open/back, AI error handling, and system Back from the detail screen.

## Data sources

- CoinDesk RSS and Cointelegraph RSS: headline, publisher, timestamp, RSS summary and original link.
- Yahoo Finance chart endpoint: BTC/USD historical series.
- Alternative.me: Crypto Fear & Greed Index.

The app stores the most recently fetched news in platform app storage so it can show saved headlines after a temporary network failure. News are attributed and the original publisher article opens in the device browser.

## Scope disclaimer

Market information is educational and is not financial advice. Data can be delayed, unavailable, or incorrect; users should verify information with the original source.
