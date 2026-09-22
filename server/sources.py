"""Upstream data sources shared by the app and the server.

This file must stay byte-identical in src/services/sources.py and server/sources.py
(enforced by tests/test_sources.py).
"""

import html
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import requests

logger = logging.getLogger("bitpulse.sources")

NEWS_FEEDS = (
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
)
ARTICLE_HOSTS = ("coindesk.com", "cointelegraph.com")
MAX_ARTICLES = 50

PERIOD_CONFIG = {
    "1H": {"interval": "2m", "range": "1d", "slice": -30, "coingecko_days": "1"},
    "1D": {"interval": "15m", "range": "1d", "slice": None, "coingecko_days": "1"},
    "1W": {"interval": "1h", "range": "1mo", "slice": -168, "coingecko_days": "7"},
    "1M": {"interval": "1d", "range": "1mo", "slice": None, "coingecko_days": "30"},
    "1Y": {"interval": "1d", "range": "1y", "slice": None, "coingecko_days": "365"},
    "5Y": {"interval": "1wk", "range": "5y", "slice": None, "coingecko_days": "1825"},
}

_TAG_RE = re.compile(r"<[^<]+>")
_NS_DC = "{http://purl.org/dc/elements/1.1/}"
_NS_MEDIA = "{http://search.yahoo.com/mrss/}"
_NS_CONTENT = "{http://purl.org/rss/1.0/modules/content/}"


# ================= NEWS =================

def parse_rss_date(raw_date: str | None) -> float | None:
    if not raw_date:
        return None
    try:
        return parsedate_to_datetime(raw_date).astimezone(timezone.utc).timestamp()
    except (TypeError, ValueError, IndexError):
        return None


def format_relative_time(timestamp: float | None, now: float | None = None) -> str:
    if timestamp is None:
        return "Latest"
    if now is None:
        now = datetime.now(timezone.utc).timestamp()
    seconds = max(0, int(now - timestamp))
    if seconds < 3600:
        return f"{max(1, seconds // 60)}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def _text(node) -> str:
    return (node.text or "").strip() if node is not None else ""


def parse_rss(content: bytes, fallback_publisher: str) -> list[dict]:
    root = ET.fromstring(content)
    articles = []
    for item in root.iter("item"):
        media = item.find(f"{_NS_MEDIA}content")
        img_url = media.attrib.get("url", "") if media is not None else ""

        description = _text(item.find(f"{_NS_CONTENT}encoded")) or _text(item.find("description"))
        if description:
            description = _TAG_RE.sub("", html.unescape(description)).strip()

        published_ts = parse_rss_date(_text(item.find("pubDate")))
        articles.append({
            "title": _text(item.find("title")) or "Crypto News",
            "link": _text(item.find("link")),
            "publisher": _text(item.find(f"{_NS_DC}creator")) or fallback_publisher,
            "published_ts": published_ts,
            "published_at": format_relative_time(published_ts),
            "description": description,
            "thumbnail": {"resolutions": [{"url": img_url}]} if img_url else {},
            "categories": [c.text.strip() for c in item.findall("category") if c.text],
        })
    return articles


def fetch_rss_feed(session: requests.Session, url: str, publisher: str) -> list[dict]:
    try:
        resp = session.get(url, timeout=7)
        resp.raise_for_status()
        return parse_rss(resp.content, publisher)
    except (requests.RequestException, ET.ParseError) as exc:
        logger.warning("RSS fetch failed (%s): %s", url, exc)
        return []


def dedupe_articles(articles: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique = []
    for article in articles:
        link = article.get("link")
        if link and link not in seen:
            seen.add(link)
            unique.append(article)
    unique.sort(key=lambda a: a.get("published_ts") or 0, reverse=True)
    return unique[:MAX_ARTICLES]


def fetch_all_news(session: requests.Session) -> list[dict]:
    articles = []
    for publisher, url in NEWS_FEEDS:
        articles.extend(fetch_rss_feed(session, url, publisher))
    return dedupe_articles(articles)


def is_allowed_article_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return (
        parsed.scheme == "https"
        and port in (None, 443)
        and not parsed.username
        and any(host == h or host.endswith("." + h) for h in ARTICLE_HOSTS)
    )


# ================= MARKET =================

def fetch_yahoo_prices(session: requests.Session, period: str) -> dict | None:
    cfg = PERIOD_CONFIG[period]
    try:
        r = session.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD",
            params={"interval": cfg["interval"], "range": cfg["range"]},
            timeout=10,
        )
        r.raise_for_status()
        result = r.json().get("chart", {}).get("result") or []
        if not result:
            return None
        timestamps = result[0].get("timestamp") or []
        closes = (result[0].get("indicators", {}).get("quote") or [{}])[0].get("close") or []
        valid = [(t, p) for t, p in zip(timestamps, closes, strict=False) if p is not None]
        if cfg["slice"]:
            valid = valid[cfg["slice"]:]
        if not valid:
            return None
        return {"timestamps": [t for t, _ in valid], "prices": [p for _, p in valid]}
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        logger.warning("Yahoo fetch failed: %s", exc)
        return None


def fetch_coingecko_prices(session: requests.Session, period: str) -> dict | None:
    try:
        r = session.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            params={"vs_currency": "usd", "days": PERIOD_CONFIG[period]["coingecko_days"]},
            timeout=10,
        )
        r.raise_for_status()
        raw = r.json().get("prices") or []
        if period == "1H":
            raw = raw[-30:]
        if not raw:
            return None
        return {"timestamps": [int(p[0] / 1000) for p in raw], "prices": [p[1] for p in raw]}
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        logger.warning("CoinGecko fetch failed: %s", exc)
        return None


def fetch_fng(session: requests.Session) -> dict | None:
    try:
        r = session.get("https://api.alternative.me/fng/", timeout=5)
        r.raise_for_status()
        return r.json()["data"][0]
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Fear & Greed fetch failed: %s", exc)
        return None


BLOCK_HEIGHT_URLS = (
    "https://blockstream.info/api/blocks/tip/height",
    "https://mempool.space/api/blocks/tip/height",
)


def fetch_block_height(session: requests.Session) -> int | None:
    for url in BLOCK_HEIGHT_URLS:
        try:
            r = session.get(url, timeout=4)
            r.raise_for_status()
            return int(r.text.strip())
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Block height fetch failed (%s): %s", url, exc)
    return None


def build_market_payload(price_data: dict, fng: dict | None, block_height: int | None, period: str) -> dict:
    prices = price_data["prices"]
    return {
        "prices": prices,
        "timestamps": price_data["timestamps"],
        "current_price": prices[-1],
        "high": max(prices),
        "low": min(prices),
        "change_pct": ((prices[-1] - prices[0]) / prices[0]) * 100 if len(prices) >= 2 and prices[0] else 0.0,
        "fng": fng,
        "block_height": block_height,
        "period": period,
    }


def fetch_market(session: requests.Session, period: str) -> dict | None:
    price_data = fetch_yahoo_prices(session, period) or fetch_coingecko_prices(session, period)
    if not price_data:
        return None
    return build_market_payload(price_data, fetch_fng(session), fetch_block_height(session), period)
