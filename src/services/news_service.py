"""News data service — fetches articles from backend API or directly from RSS feeds."""

import html
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

from services.cache import load_json, save_json

logger = logging.getLogger("bitpulse.news")

NEWS_CACHE_FILE = "news_cache.json"
NEWS_CACHE_MAX_AGE = 6 * 60 * 60  # 6 hours

# Module-level cache shared with ai_view
all_news_cache: list[dict] = []

_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0 (BitPulse/1.0)"})


def format_published_at(raw_date: str | None) -> str:
    """Convert an RSS pubDate string into a human-friendly relative time."""
    if not raw_date:
        return "Latest"
    try:
        published = parsedate_to_datetime(raw_date).astimezone(timezone.utc)
        seconds = max(0, int((datetime.now(timezone.utc) - published).total_seconds()))
        if seconds < 3600:
            return f"{max(1, seconds // 60)}m ago"
        if seconds < 86400:
            return f"{seconds // 3600}h ago"
        return f"{seconds // 86400}d ago"
    except (TypeError, ValueError, IndexError):
        return "Latest"


def _fetch_rss_feed(url: str, fallback_publisher: str) -> list[dict]:
    """Parse a single RSS feed URL and return a list of article dicts."""
    try:
        resp = _session.get(url, timeout=7)
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        news_list = []
        for item in items:
            title_node = item.find("title")
            title = title_node.text if title_node is not None else "Crypto News"

            link_node = item.find("link")
            link = link_node.text if link_node is not None else ""

            pub_date_node = item.find("pubDate")
            published_at = format_published_at(
                pub_date_node.text if pub_date_node is not None else None
            )

            creator = item.find("{http://purl.org/dc/elements/1.1/}creator")
            publisher = creator.text if creator is not None else fallback_publisher

            media = item.find("{http://search.yahoo.com/mrss/}content")
            img_url = media.attrib.get("url", "") if media is not None else ""

            content_node = item.find(
                "{http://purl.org/rss/1.0/modules/content/}encoded"
            )
            if content_node is not None and content_node.text:
                description = content_node.text
            else:
                desc_node = item.find("description")
                description = desc_node.text if desc_node is not None else ""

            if description:
                description = html.unescape(description)
                description = re.sub("<[^<]+>", "", description)

            categories = [c.text.strip() for c in item.findall("category") if c.text]
            news_list.append(
                {
                    "title": title,
                    "link": link,
                    "publisher": publisher,
                    "published_at": published_at,
                    "description": description.strip(),
                    "thumbnail": (
                        {"resolutions": [{"url": img_url}]} if img_url else {}
                    ),
                    "categories": categories,
                }
            )
        return news_list
    except Exception as exc:
        logger.warning("RSS fetch error (%s): %s", url, exc)
        return []


def fetch_news_from_api(api_url: str = "") -> list[dict]:
    """Fetch news — prefer the backend proxy, fall back to direct RSS.

    When *api_url* is non-empty the function calls ``GET /v1/news`` on the
    BitPulse backend which has its own server-side cache and aggregation.
    If that fails (or no URL is configured), we fall back to fetching the
    RSS feeds directly so the app still works without a backend.
    """
    # Try backend proxy first
    if api_url:
        try:
            resp = _session.get(f"{api_url}/v1/news", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                articles = data.get("articles", [])
                if articles:
                    return articles
        except Exception as exc:
            logger.warning("Backend news proxy failed, falling back to RSS: %s", exc)

    # Direct RSS fallback
    feeds = [
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Cointelegraph", "https://cointelegraph.com/rss"),
    ]
    articles: list[dict] = []
    for publisher, url in feeds:
        articles.extend(_fetch_rss_feed(url, publisher))

    seen_links: set[str] = set()
    unique: list[dict] = []
    for article in articles:
        link = article.get("link")
        if link and link not in seen_links:
            seen_links.add(link)
            unique.append(article)
    return unique[:50]


def get_image_url(item: dict) -> str:
    """Extract thumbnail URL from a news item, with a safe fallback."""
    try:
        return item["thumbnail"]["resolutions"][0]["url"]
    except (KeyError, IndexError, TypeError):
        return "icon_clean.png"


def load_cached_news() -> list[dict]:
    """Load news from the local JSON cache."""
    data, _ = load_json(NEWS_CACHE_FILE, NEWS_CACHE_MAX_AGE)
    return data or []


def save_news_cache(articles: list[dict]) -> None:
    """Persist news articles to the local JSON cache."""
    save_json(NEWS_CACHE_FILE, articles)
