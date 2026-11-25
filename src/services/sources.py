"""Upstream data sources shared by the app and the server.

This file must stay byte-identical in src/services/sources.py and server/sources.py
(enforced by tests/test_sources.py).
"""

import html
import logging
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import requests

logger = logging.getLogger("bitpulse.sources")

NEWS_FEEDS = (
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
)
# US regulators publish everything, so only their crypto items are kept. Works of the US federal
# government are not under copyright (17 U.S.C. 105), so their full text may be shown.
REGULATOR_FEEDS = (
    ("SEC", "https://www.sec.gov/news/pressreleases.rss"),
    ("CFTC", "https://www.cftc.gov/RSS/RSSGP/rssgp.xml"),
)
CRYPTO_TOPIC = re.compile(
    r"\b(crypto\w*|digital[- ]asset\w*|bitcoin|blockchain|stablecoin\w*|tokeni[sz]\w*|"
    r"ether(eum)?|defi|virtual currenc\w*|web3)\b",
    re.IGNORECASE,
)
# Regulators post a crypto item every few days, so the 50 newest headlines would always push
# them out. They get their own slots instead.
REGULATOR_MAX_ITEMS = 5
REGULATOR_MAX_AGE = 30 * 24 * 3600
ARTICLE_HOSTS = ("coindesk.com", "cointelegraph.com", "sec.gov", "cftc.gov", "bitcoinops.org")
# The SEC's fair-access policy asks automated clients to name themselves and give a contact
# address in the User-Agent; without it sec.gov answers 403.
CONTACT_EMAIL = "bitpulseapp.support@gmail.com"
SEC_USER_AGENT = f"BitPulse/1.1 {CONTACT_EMAIL}"


def request_headers(url: str) -> dict:
    """Per-site headers for outgoing requests (only sec.gov needs any)."""
    return {"User-Agent": SEC_USER_AGENT} if _host_in(url, ("sec.gov",)) else {}


# Sources whose text the app may show in full. Everything else gets a short summary and a link.
FULL_TEXT_HOSTS = ("sec.gov", "cftc.gov", "bitcoinops.org")
MAX_ARTICLES = 50

# "window" trims to a trailing span in seconds. Yahoo's "1d" range means "since 00:00 UTC", so
# 1H and 1D fetch two days and keep the last hour / 24 hours; otherwise 1D showed only the
# hours since midnight UTC and 1H was nearly empty just after it.
PERIOD_CONFIG = {
    "1H": {"interval": "2m", "range": "2d", "window": 3600, "coingecko_days": "1"},
    "1D": {"interval": "15m", "range": "2d", "window": 86400, "coingecko_days": "1"},
    "1W": {"interval": "1h", "range": "1mo", "window": 7 * 86400, "coingecko_days": "7"},
    "1M": {"interval": "90m", "range": "1mo", "window": 30 * 86400, "coingecko_days": "30"},
    "1Y": {"interval": "1d", "range": "1y", "window": None, "coingecko_days": "365"},
    "5Y": {"interval": "1wk", "range": "5y", "window": None, "coingecko_days": "1825"},
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
            # dc:creator is the journalist, not the outlet the article must be attributed to.
            "publisher": fallback_publisher,
            "author": _text(item.find(f"{_NS_DC}creator")),
            "published_ts": published_ts,
            "published_at": format_relative_time(published_ts),
            "description": description,
            "thumbnail": {"resolutions": [{"url": img_url}]} if img_url else {},
            "categories": [c.text.strip() for c in item.findall("category") if c.text],
        })
    return articles


def fetch_rss_feed(session: requests.Session, url: str, publisher: str) -> list[dict]:
    try:
        resp = session.get(url, timeout=7, headers=request_headers(url))
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


def is_crypto_item(article: dict) -> bool:
    return bool(CRYPTO_TOPIC.search(f"{article.get('title', '')} {article.get('description', '')}"))


def fetch_all_news(session: requests.Session) -> list[dict]:
    """Fetch every feed at once so one slow or blocked publisher does not delay the rest."""
    feeds = [(p, u, False) for p, u in NEWS_FEEDS] + [(p, u, True) for p, u in REGULATOR_FEEDS]
    with ThreadPoolExecutor(max_workers=len(feeds)) as pool:
        results = pool.map(lambda f: (f[2], fetch_rss_feed(session, f[1], f[0])), feeds)
    news, regulators = [], []
    for crypto_only, items in results:
        if crypto_only:
            regulators.extend(a for a in items if is_crypto_item(a))
        else:
            news.extend(items)
    return merge_regulator_items(dedupe_articles(news), regulators)


def merge_regulator_items(news: list[dict], regulators: list[dict], now: float | None = None) -> list[dict]:
    """Add the newest recent regulator items on top of the capped headline list, newest first."""
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    recent = [a for a in regulators if (a.get("published_ts") or 0) >= now - REGULATOR_MAX_AGE]
    recent = dedupe_articles(recent)[:REGULATOR_MAX_ITEMS]
    links = {a.get("link") for a in news}
    merged = news + [a for a in recent if a.get("link") not in links]
    merged.sort(key=lambda a: a.get("published_ts") or 0, reverse=True)
    return merged


def _host_in(url: str, hosts: tuple[str, ...]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in hosts)


def allows_full_text(url: str) -> bool:
    """True for sources whose licence lets the app show the whole article (see FULL_TEXT_HOSTS)."""
    return is_allowed_article_url(url) and _host_in(url, FULL_TEXT_HOSTS)


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

def trim_to_window(points: list[tuple[int, float]], window: int | None) -> list[tuple[int, float]]:
    """Keep the (timestamp, price) points within *window* seconds of the newest one."""
    if not window or not points:
        return points
    cutoff = points[-1][0] - window
    return [(t, p) for t, p in points if t >= cutoff]


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
        valid = trim_to_window(valid, cfg["window"])
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
        valid = trim_to_window([(int(t / 1000), p) for t, p in raw], PERIOD_CONFIG[period]["window"])
        if not valid:
            return None
        return {"timestamps": [t for t, _ in valid], "prices": [p for _, p in valid]}
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
    """Fetch price, sentiment and block height concurrently; they are independent."""
    with ThreadPoolExecutor(max_workers=3) as pool:
        prices = pool.submit(fetch_yahoo_prices, session, period)
        fng = pool.submit(fetch_fng, session)
        height = pool.submit(fetch_block_height, session)
        price_data = prices.result() or fetch_coingecko_prices(session, period)
        if not price_data:
            return None
        return build_market_payload(price_data, fng.result(), height.result(), period)
