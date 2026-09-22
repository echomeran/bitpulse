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

For production, deploy `server` to a TLS-enabled service such as Render or Cloud Run. Put the public HTTPS URL in `src/assets/app_config.json` as `ai_api_url`, then rebuild the APK. The URL is public; the Gemini key stays only on the server.

Server settings (see `server/.env.example`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | — | Required for `/v1/chat`; without it chat returns 503 and `/health` reports `ai_configured: false`. |
| `RATE_LIMIT_PER_HOUR` | 30 | Chat requests per client IP per hour. |
| `ARTICLE_RATE_LIMIT_PER_HOUR` | 120 | Uncached article fetches per client IP per hour. |
| `TRUSTED_PROXY_HOPS` | 1 | Reverse proxies in front of the server. Keep `1` on Render/Cloud Run; use `0` when the server is exposed directly, otherwise clients can spoof `X-Forwarded-For`. |

`server/sources.py` and `src/services/sources.py` are the same module shared by the server and the app's offline fallback. Edit one and copy it to the other; a test fails if they differ.

## Development

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\venv\Scripts\ruff.exe check .
.\venv\Scripts\python.exe -m pytest
```

CI runs the same lint and tests on every push and pull request.

## Android build

Before a release build, choose a bundle ID you own and retain the Android signing key securely. A personal ARM64 test APK can be built with:

```powershell
.\scripts\build-android.ps1 -BundleId "com.yourname.bitpulse" -Version "1.0.0" -BuildNumber 1
```

Releases are built by GitHub Actions when a `v*` tag is pushed (`git tag v1.1.0 && git push origin v1.1.0`); the version comes from the tag. To sign release APKs, add these repository secrets: `ANDROID_KEYSTORE_BASE64` (the `.jks` file, base64-encoded), `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_PASSWORD` and `ANDROID_KEY_ALIAS`. Without them the APK is debug-signed.

Test a fresh install on a physical Android device: first launch, no network, refresh, all market periods, article open/back, AI error handling, and system Back from the detail screen.

## Data sources

- CoinDesk RSS and Cointelegraph RSS: headline, publisher, timestamp, RSS summary and original link. When the backend is configured, the article screen also shows the article text extracted from the publisher page (only coindesk.com and cointelegraph.com URLs are fetched).
- Yahoo Finance chart endpoint, with CoinGecko as fallback: BTC/USD historical series.
- Alternative.me: Crypto Fear & Greed Index.
- Blockstream Esplora, with mempool.space as fallback: current block height for the halving estimate.

The app stores the most recently fetched news and market data in platform app storage so it can show saved data after a network failure. News are attributed and the original publisher article opens in the device browser.

## Scope disclaimer

Market information is educational and is not financial advice. Data can be delayed, unavailable, or incorrect; users should verify information with the original source.
