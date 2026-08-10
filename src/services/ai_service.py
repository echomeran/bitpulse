"""AI chat service — communicates with the BitPulse backend API."""

import json
import logging
import os
from pathlib import Path

import requests

logger = logging.getLogger("bitpulse.ai")

_session = requests.Session()


def get_api_url() -> str:
    """Resolve the AI backend URL from env var or app_config.json."""
    configured = os.getenv("BITPULSE_AI_URL", "").strip()
    if configured:
        return configured.rstrip("/")

    assets_dir = Path(
        os.getenv(
            "FLET_ASSETS_DIR",
            str(Path(__file__).resolve().parents[1] / "assets"),
        )
    )
    config_path = assets_dir / "app_config.json"
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return str(data.get("ai_api_url", "")).rstrip("/")
    except (OSError, ValueError, TypeError):
        return ""


def send_chat_message(
    api_url: str,
    message: str,
    history: list[dict],
    btc_price: str = "$ --",
    news_items: list[dict] | None = None,
) -> tuple[str | None, str | None]:
    """Send a chat message to the backend and return (reply, error).

    Returns a tuple of (reply_text, None) on success or
    (None, error_message) on failure.
    """
    payload = {
        "message": message,
        "history": history[-6:],
        "btc_price": btc_price,
        "news": [
            {
                "title": item.get("title", ""),
                "publisher": item.get("publisher", "Unknown"),
            }
            for item in (news_items or [])[:12]
        ],
    }

    try:
        response = _session.post(f"{api_url}/v1/chat", json=payload, timeout=30)
    except requests.ConnectionError:
        return None, "Could not reach the AI service. Check your connection and try again."
    except requests.Timeout:
        return None, "The AI service took too long to respond. Please try again."
    except requests.RequestException:
        return None, "Could not reach the AI service. Check your connection and try again."

    if response.status_code == 429:
        return None, "The AI service is busy. Please try again in a minute."
    if response.status_code >= 400:
        return None, "The AI service is temporarily unavailable. Please try again."

    try:
        reply = response.json().get("reply", "").strip()
    except (ValueError, AttributeError):
        reply = ""

    if reply:
        return reply, None
    return None, "The AI service returned an empty response."
