"""News data: backend proxy first, direct RSS as fallback."""

import logging

import requests

from services import sources
from services.cache import load_json, save_json
from services.net import session

logger = logging.getLogger("bitpulse.news")

NEWS_CACHE_FILE = "news_cache.json"
NEWS_CACHE_MAX_AGE = 6 * 60 * 60
DEFAULT_IMAGE = "icon_clean.png"
# Short, because a sleeping free-tier backend answers in ~30s and fetching the
# feeds directly is faster than waiting for it to wake up.
BACKEND_TIMEOUT = (2, 5)  # (connect, read)

all_news_cache: list[dict] = []


def fetch_full_article(api_url: str, article_url: str) -> str | None:
    if not api_url or not sources.is_allowed_article_url(article_url):
        return None
    try:
        resp = session.get(f"{api_url}/v1/news/article", params={"url": article_url}, timeout=15)
        resp.raise_for_status()
        return resp.json().get("text")
    except (requests.RequestException, ValueError, AttributeError) as exc:
        logger.warning("Failed to fetch full article text: %s", exc)
        return None


def fetch_article_summary(api_url: str, article_url: str) -> tuple[str | None, str | None]:
    """Return (summary, None) or (None, user-facing error)."""
    if not api_url or not sources.is_allowed_article_url(article_url):
        return None, "Summaries are not available for this article."
    try:
        resp = session.get(
            f"{api_url}/v1/news/summary", params={"url": article_url}, timeout=(5, 40)
        )
        if resp.status_code == 429:
            return None, "The AI service is busy. Please try again in a minute."
        if resp.status_code >= 400:
            logger.warning("Summary request returned HTTP %s", resp.status_code)
            return None, "Could not summarize this article."
        summary = (resp.json().get("summary") or "").strip()
        return (summary, None) if summary else (None, "Could not summarize this article.")
    except (requests.RequestException, ValueError, AttributeError) as exc:
        logger.warning("Summary request failed: %s", exc)
        return None, "Could not reach the AI service."


def fetch_news_from_api(api_url: str = "") -> list[dict]:
    if api_url:
        try:
            resp = session.get(f"{api_url}/v1/news", timeout=BACKEND_TIMEOUT)
            resp.raise_for_status()
            articles = resp.json().get("articles") or []
            if articles:
                return articles
        except (requests.RequestException, ValueError, AttributeError) as exc:
            logger.warning("Backend news proxy failed, falling back to RSS: %s", exc)

    return sources.fetch_all_news(session)


def byline(item: dict) -> str:
    """Publisher, with the journalist appended when the feed names one."""
    publisher = item.get("publisher") or "CoinDesk"
    author = (item.get("author") or "").strip()
    return f"{publisher} · {author}" if author and author != publisher else publisher


def published_label(item: dict) -> str:
    timestamp = item.get("published_ts")
    if timestamp is not None:
        return sources.format_relative_time(timestamp)
    return item.get("published_at") or "Latest"


def get_image_url(item: dict) -> str:
    try:
        return item["thumbnail"]["resolutions"][0]["url"] or DEFAULT_IMAGE
    except (KeyError, IndexError, TypeError):
        return DEFAULT_IMAGE


def load_cached_news() -> list[dict]:
    data, _ = load_json(NEWS_CACHE_FILE, NEWS_CACHE_MAX_AGE)
    return data or []


def save_news_cache(articles: list[dict]) -> None:
    save_json(NEWS_CACHE_FILE, articles)
