"""News data: backend proxy first, direct RSS as fallback."""

import logging

import requests

from services import sources
from services.cache import load_json, save_json
from services.net import session

logger = logging.getLogger("bitpulse.news")

NEWS_CACHE_FILE = "news_cache.json"
# Saved news is shown at launch while fresh news loads, so a week-old copy still beats a blank list.
NEWS_CACHE_MAX_AGE = 7 * 24 * 60 * 60
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


# Returned when the server has no summary for this source (publisher has not allowed AI use).
SUMMARY_UNAVAILABLE = "A summary is not available for this article."


def fetch_article_summary(
    api_url: str, article_url: str, style: str = "brief"
) -> tuple[str | None, str | None]:
    """Return (summary, None) or (None, user-facing error). *style* is "brief" or "simple"."""
    if not api_url or not sources.is_allowed_article_url(article_url):
        return None, "Summaries are not available for this article."
    try:
        resp = session.get(
            f"{api_url}/v1/news/summary",
            params={"url": article_url, "style": style},
            timeout=(5, 40),
        )
        if resp.status_code == 429:
            return None, "The AI service is busy. Please try again in a minute."
        if resp.status_code in (403, 502):
            return None, SUMMARY_UNAVAILABLE
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
    # Cointelegraph's feed writes "Cointelegraph by Ezra Reguerra"; the publisher is shown already.
    prefix = f"{publisher} by "
    if author.lower().startswith(prefix.lower()):
        author = author[len(prefix) :].strip()
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


# ---------------- Bitcoin Optech newsletter ----------------

NEWSLETTER_CACHE_FILE = "newsletters.json"
NEWSLETTER_STATE_FILE = "newsletter_state.json"
NEWSLETTER_TIMEOUT = (3, 25)  # the server may need to fetch Optech's feed first


def fetch_newsletters(api_url: str) -> list[dict]:
    """Newest-first list of Optech newsletters, falling back to the copy saved on the phone."""
    if api_url:
        try:
            resp = session.get(f"{api_url}/v1/newsletters", timeout=NEWSLETTER_TIMEOUT)
            resp.raise_for_status()
            items = resp.json().get("items") or []
            if items:
                save_json(NEWSLETTER_CACHE_FILE, items)
                return items
        except (requests.RequestException, ValueError, AttributeError) as exc:
            logger.warning("Newsletter list failed: %s", exc)
    return load_cached_newsletters()


def load_cached_newsletters() -> list[dict]:
    data, _ = load_json(NEWSLETTER_CACHE_FILE)
    return data if isinstance(data, list) else []


def fetch_newsletter(api_url: str, url: str) -> dict | None:
    """The issue as the server prepared it: markdown, sections of cards, counts and digest."""
    if not api_url:
        return None
    try:
        resp = session.get(
            f"{api_url}/v1/newsletters/content", params={"url": url}, timeout=NEWSLETTER_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) and data.get("markdown") else None
    except (requests.RequestException, ValueError, AttributeError) as exc:
        logger.warning("Newsletter content failed: %s", exc)
        return None


def fetch_newsletter_markdown(api_url: str, url: str) -> str | None:
    data = fetch_newsletter(api_url, url)
    return data.get("markdown") if data else None


def last_read_newsletter() -> int:
    data, _ = load_json(NEWSLETTER_STATE_FILE)
    try:
        return int((data or {}).get("last_read", 0))
    except (TypeError, ValueError, AttributeError):
        return 0


def mark_newsletter_read(number: int) -> None:
    if number > last_read_newsletter():
        save_json(NEWSLETTER_STATE_FILE, {"last_read": number})
