"""Shared services used by BitPulse views."""

from services.ai_service import get_api_url, send_chat_message
from services.cache import load_json, save_json
from services.market_service import (
    fetch_fng_data,
    fetch_price_from_api,
    live_price_ref,
    load_cached_market,
    save_market_cache,
)
from services.news_service import (
    all_news_cache,
    fetch_news_from_api,
    get_image_url,
    load_cached_news,
    save_news_cache,
)

__all__ = [
    "get_api_url",
    "send_chat_message",
    "load_json",
    "save_json",
    "fetch_fng_data",
    "fetch_price_from_api",
    "live_price_ref",
    "load_cached_market",
    "save_market_cache",
    "all_news_cache",
    "fetch_news_from_api",
    "get_image_url",
    "load_cached_news",
    "save_news_cache",
]
