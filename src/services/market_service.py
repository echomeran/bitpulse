"""Market data: BTC price history, Fear & Greed index and block height."""

import logging
from datetime import datetime, timedelta, timezone

import requests

from services import sources
from services.cache import load_json, save_json
from services.net import session

logger = logging.getLogger("bitpulse.market")

# Only read when a live fetch fails, so it may be much older than the live refresh interval.
OFFLINE_CACHE_MAX_AGE = 24 * 60 * 60

HALVING_INTERVAL = 210_000
AVG_BLOCK_MINUTES = 10
# Fallback anchor when block height is unavailable: block 840,000 was mined 2024-04-20 00:09 UTC.
_ANCHOR_BLOCK = 840_000
_ANCHOR_TIME = datetime(2024, 4, 20, 0, 9, tzinfo=timezone.utc)

live_price_ref: str = "$ --"
market_summary_ref: str = ""


def fetch_price_from_api(api_url: str = "", period: str = "1D") -> dict | None:
    if period not in sources.PERIOD_CONFIG:
        raise ValueError(f"Unknown period: {period}")

    if api_url:
        try:
            resp = session.get(f"{api_url}/v1/market", params={"period": period}, timeout=12)
            resp.raise_for_status()
            data = resp.json()
            if data.get("prices"):
                return data
        except (requests.RequestException, ValueError, AttributeError) as exc:
            logger.warning("Backend market proxy failed, falling back: %s", exc)

    return sources.fetch_market(session, period)


def load_cached_market(period: str) -> dict | None:
    data, _ = load_json(f"market_{period}.json", OFFLINE_CACHE_MAX_AGE)
    return data


def save_market_cache(period: str, data: dict) -> None:
    save_json(f"market_{period}.json", data)


def estimate_days_to_halving(block_height: int | None, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    if block_height is None:
        elapsed_blocks = (now - _ANCHOR_TIME).total_seconds() / 60 / AVG_BLOCK_MINUTES
        block_height = _ANCHOR_BLOCK + int(elapsed_blocks)
    next_halving = (block_height // HALVING_INTERVAL + 1) * HALVING_INTERVAL
    remaining = timedelta(minutes=(next_halving - block_height) * AVG_BLOCK_MINUTES)
    return remaining.days


def build_market_summary(data: dict) -> str:
    """Compact, LLM-readable summary: price stats, sentiment and 5 evenly spaced snapshots."""
    prices = data.get("prices") or []
    timestamps = data.get("timestamps") or []
    if not prices:
        return ""

    current = data.get("current_price") or prices[-1]
    high = data.get("high") or max(prices)
    low = data.get("low") or min(prices)
    change_pct = data.get("change_pct") or 0.0
    sign = "+" if change_pct >= 0 else ""
    lines = [
        f"BTC/USD market data — period: {data.get('period', '1M')}",
        f"Current price : ${current:,.2f}",
        f"Period high   : ${high:,.2f}",
        f"Period low    : ${low:,.2f}",
        f"Period change : {sign}{change_pct:.2f}%",
    ]

    fng = data.get("fng")
    if isinstance(fng, dict) and "value" in fng and "value_classification" in fng:
        lines.append(f"Fear & Greed  : {fng['value']} / 100 ({fng['value_classification']})")

    if len(timestamps) == len(prices) and len(prices) >= 7:
        lines.append("\nPrice snapshots (oldest → newest):")
        n = len(prices)
        for idx in (round(i * (n - 1) / 4) for i in range(5)):
            day = datetime.fromtimestamp(timestamps[idx], tz=timezone.utc).strftime("%d %b %Y")
            lines.append(f"  {day}: ${prices[idx]:,.2f}")

    return "\n".join(lines)
