"""Market data service — BTC price history and Fear & Greed index."""

import logging

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from services.cache import load_json, save_json

logger = logging.getLogger("bitpulse.market")

MARKET_CACHE_FILE = "market_cache.json"
MARKET_CACHE_MAX_AGE = 120  # 2 minutes

# Module-level state shared with ai_view
live_price_ref: str = "$ --"

_session = requests.Session()
_session.verify = False
_session.headers.update({"User-Agent": "Mozilla/5.0 (BitPulse/1.0)"})

PERIOD_CONFIG = {
    "1H": {"interval": "2m", "range": "1d", "slice": -30},
    "1D": {"interval": "15m", "range": "1d", "slice": None},
    "1W": {"interval": "1h", "range": "1mo", "slice": -168},
    "1M": {"interval": "1d", "range": "1mo", "slice": None},
    "1Y": {"interval": "1d", "range": "1y", "slice": None},
    "5Y": {"interval": "1wk", "range": "5y", "slice": None},
}


def fetch_price_from_api(api_url: str = "", period: str = "1D") -> dict | None:
    """Fetch price data — prefer backend proxy, fall back to direct Yahoo/CoinGecko.

    Returns a dict with keys: prices, timestamps, current_price, high, low,
    change_pct, fng, period.  Returns None on total failure.
    """
    # Try backend proxy first
    if api_url:
        try:
            resp = _session.get(f"{api_url}/v1/market", params={"period": period}, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("prices"):
                    return data
        except Exception as exc:
            logger.warning("Backend market proxy failed, falling back: %s", exc)

    # Direct Yahoo fallback
    price_data = _fetch_yahoo_price(period)
    if not price_data:
        price_data = _fetch_coingecko_price(period)

    fng = fetch_fng_data()

    if not price_data:
        return None

    prices = price_data["prices"]
    return {
        "prices": prices,
        "timestamps": price_data["timestamps"],
        "current_price": prices[-1] if prices else None,
        "high": max(prices) if prices else None,
        "low": min(prices) if prices else None,
        "change_pct": (
            ((prices[-1] - prices[0]) / prices[0]) * 100
            if len(prices) >= 2 and prices[0] != 0
            else 0.0
        ),
        "fng": fng,
        "period": period,
    }


def _fetch_yahoo_price(period: str) -> dict | None:
    """Fetch BTC price history from Yahoo Finance."""
    cfg = PERIOD_CONFIG.get(period, PERIOD_CONFIG["1D"])
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD"
        f"?interval={cfg['interval']}&range={cfg['range']}"
    )
    try:
        r = _session.get(url, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return None

        timestamps = result[0].get("timestamp", [])
        indicators = result[0].get("indicators", {}).get("quote", [{}])[0]
        close_prices = indicators.get("close", [])

        valid = [(t, p) for t, p in zip(timestamps, close_prices) if p is not None]
        if cfg["slice"]:
            valid = valid[cfg["slice"]:]

        if not valid:
            return None

        return {
            "timestamps": [v[0] for v in valid],
            "prices": [v[1] for v in valid],
        }
    except Exception as exc:
        logger.warning("Yahoo fetch error: %s", exc)
        return None


def _fetch_coingecko_price(period: str) -> dict | None:
    """Fallback: fetch BTC price from CoinGecko public API."""
    days_map = {"1H": "1", "1D": "1", "1W": "7", "1M": "30", "1Y": "365", "5Y": "1825"}
    days = days_map.get(period, "1")
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
    try:
        r = _session.get(url, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        raw_prices = data.get("prices", [])
        if not raw_prices:
            return None

        timestamps = [int(p[0] / 1000) for p in raw_prices]
        prices = [p[1] for p in raw_prices]

        if period == "1H" and len(prices) > 30:
            timestamps = timestamps[-30:]
            prices = prices[-30:]

        return {"timestamps": timestamps, "prices": prices}
    except Exception as exc:
        logger.warning("CoinGecko fetch error: %s", exc)
        return None


def fetch_fng_data() -> dict | None:
    """Fetch the Fear & Greed index from alternative.me."""
    try:
        r = _session.get("https://api.alternative.me/fng/", timeout=5)
        return r.json()["data"][0] if r.status_code == 200 else None
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return None


def load_cached_market(period: str = "1D") -> dict | None:
    """Load market data from local JSON cache."""
    data, _ = load_json(f"market_{period}.json", MARKET_CACHE_MAX_AGE)
    return data


def save_market_cache(period: str, data: dict) -> None:
    """Persist market data to local JSON cache."""
    save_json(f"market_{period}.json", data)
