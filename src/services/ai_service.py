"""AI chat client for the BitPulse backend."""

import json
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path

import requests

from services import news_service
from services.net import session

logger = logging.getLogger("bitpulse.ai")

MAX_HISTORY_TURNS = 6
MAX_TURN_CHARS = 4000
MAX_NEWS_ITEMS = 12
MAX_NEWS_SUMMARY_CHARS = 400
STREAM_ERROR_MARKER = "\u0000error"

ERR_UNREACHABLE = "Could not reach the AI service. Check your connection and try again."
ERR_TIMEOUT = "The AI service took too long to respond. Please try again."
ERR_BUSY = "The AI service is busy. Please try again in a minute."
ERR_UNAVAILABLE = "The AI service is temporarily unavailable. Please try again."
ERR_EMPTY = "The AI service returned an empty response."


def get_api_url() -> str:
    configured = os.getenv("BITPULSE_AI_URL", "").strip()
    if configured:
        return configured.rstrip("/")

    assets_dir = Path(os.getenv("FLET_ASSETS_DIR", str(Path(__file__).resolve().parents[1] / "assets")))
    try:
        data = json.loads((assets_dir / "app_config.json").read_text(encoding="utf-8"))
        return str(data.get("ai_api_url", "")).rstrip("/")
    except (OSError, ValueError, TypeError, AttributeError):
        return ""


def build_payload(
    message: str,
    history: list[dict],
    btc_price: str,
    news_items: list[dict] | None,
    market_summary: str,
) -> dict:
    return {
        "message": message,
        "history": [
            {"role": turn["role"], "text": turn["text"][:MAX_TURN_CHARS]}
            for turn in history[-MAX_HISTORY_TURNS:]
        ],
        "btc_price": btc_price,
        "market_summary": market_summary[:1000],
        "news": [
            {
                "title": item.get("title", "")[:280],
                "publisher": item.get("publisher", "Unknown")[:100],
                "published_at": news_service.published_label(item)[:40],
                "summary": (item.get("description") or "")[:MAX_NEWS_SUMMARY_CHARS],
                "categories": [c[:40] for c in (item.get("categories") or [])[:6]],
            }
            for item in (news_items or [])[:MAX_NEWS_ITEMS]
        ],
    }


def send_chat_message(
    api_url: str,
    message: str,
    history: list[dict],
    btc_price: str = "$ --",
    news_items: list[dict] | None = None,
    market_summary: str = "",
) -> tuple[str | None, str | None]:
    """Return (reply, None) on success or (None, user-facing error).

    Retries once to ride out cold starts of the free-tier backend.
    """
    payload = build_payload(message, history, btc_price, news_items, market_summary)

    response = None
    for attempt in range(2):
        try:
            response = session.post(f"{api_url}/v1/chat", json=payload, timeout=45)
        except requests.ConnectionError:
            if attempt == 0:
                time.sleep(2)
                continue
            return None, ERR_UNREACHABLE
        except requests.Timeout:
            if attempt == 0:
                continue
            return None, ERR_TIMEOUT
        except requests.RequestException:
            return None, ERR_UNREACHABLE
        if response.status_code in (502, 503) and attempt == 0:
            time.sleep(3)
            continue
        break

    if response is None:
        return None, ERR_UNREACHABLE
    if response.status_code == 429:
        return None, ERR_BUSY
    if response.status_code >= 400:
        logger.warning("AI backend returned HTTP %s", response.status_code)
        return None, ERR_UNAVAILABLE

    try:
        reply = (response.json().get("reply") or "").strip()
    except (ValueError, AttributeError):
        reply = ""
    return (reply, None) if reply else (None, ERR_EMPTY)


def stream_chat_message(
    api_url: str,
    message: str,
    history: list[dict],
    btc_price: str = "$ --",
    news_items: list[dict] | None = None,
    market_summary: str = "",
    on_chunk: Callable[[str], None] = lambda _: None,
) -> tuple[str | None, str | None]:
    """Stream the reply, handing each piece to *on_chunk*, and return (reply, error).

    Falls back to the non-streaming endpoint when the backend does not serve one.
    """
    payload = build_payload(message, history, btc_price, news_items, market_summary)
    args = (api_url, message, history, btc_price, news_items, market_summary)
    parts: list[str] = []
    failed = False

    try:
        with session.post(f"{api_url}/v1/chat/stream", json=payload, timeout=(5, 45), stream=True) as response:
            if response.status_code == 404:
                return send_chat_message(*args)
            if response.status_code == 429:
                return None, ERR_BUSY
            if response.status_code >= 400:
                logger.warning("AI backend returned HTTP %s", response.status_code)
                return None, ERR_UNAVAILABLE

            response.encoding = response.encoding or "utf-8"
            for piece in response.iter_content(chunk_size=None, decode_unicode=True):
                if not piece:
                    continue
                if STREAM_ERROR_MARKER in piece:
                    failed = True
                    piece = piece.replace(STREAM_ERROR_MARKER, "")
                if piece:
                    parts.append(piece)
                    on_chunk(piece)
                if failed:
                    break
    except requests.RequestException as exc:
        logger.warning("Streaming chat failed: %s", exc)
        return (None, ERR_UNREACHABLE) if not parts else ("".join(parts), None)

    reply = "".join(parts).strip()
    if reply:
        return reply, None
    return None, ERR_UNAVAILABLE if failed else ERR_EMPTY
