from datetime import datetime, timezone

import pytest

from services import ai_service, market_service, news_service
from views.news_view import FILTERS, matches_filter


def test_chat_payload_truncates_to_server_limits():
    history = [{"role": "assistant", "text": "x" * 9000}] * 10
    news = [{"title": "t" * 500, "publisher": "p"}] * 20
    payload = ai_service.build_payload("hi", history, "$1", news, "s" * 2000)
    assert len(payload["history"]) == ai_service.MAX_HISTORY_TURNS
    assert all(len(t["text"]) == ai_service.MAX_TURN_CHARS for t in payload["history"])
    assert len(payload["news"]) == ai_service.MAX_NEWS_ITEMS
    assert len(payload["news"][0]["title"]) == 280
    assert len(payload["market_summary"]) == 1000


def test_http_session_verifies_tls():
    from services.net import session

    assert session.verify not in (False, None)


def test_published_label_prefers_timestamp():
    assert news_service.published_label({"published_ts": 0, "published_at": "5m ago"}).endswith("d ago")
    assert news_service.published_label({"published_at": "5m ago"}) == "5m ago"
    assert news_service.published_label({}) == "Latest"


def test_get_image_url_falls_back():
    assert news_service.get_image_url({}) == news_service.DEFAULT_IMAGE
    assert news_service.get_image_url({"thumbnail": {"resolutions": [{"url": ""}]}}) == news_service.DEFAULT_IMAGE


def test_fetch_full_article_skips_without_backend_or_foreign_url():
    assert news_service.fetch_full_article("", "https://www.coindesk.com/a") is None
    assert news_service.fetch_full_article("https://api", "https://example.com/a") is None


@pytest.mark.parametrize(
    ("height", "expected_days"),
    [(1_049_856, 1), (1_050_000, 1458), (900_000, 1041)],
)
def test_estimate_days_to_halving(height, expected_days):
    assert market_service.estimate_days_to_halving(height) == expected_days


def test_estimate_days_to_halving_without_height():
    now = datetime(2026, 9, 22, tzinfo=timezone.utc)
    assert 500 < market_service.estimate_days_to_halving(None, now=now) < 700


def test_market_summary_includes_snapshots():
    data = {
        "prices": [float(p) for p in range(100, 110)],
        "timestamps": [1_790_000_000 + i * 86400 for i in range(10)],
        "change_pct": 9.0,
        "fng": {"value": "55", "value_classification": "Greed"},
        "period": "1M",
    }
    summary = market_service.build_market_summary(data)
    assert "Current price : $109.00" in summary
    assert "Fear & Greed  : 55 / 100 (Greed)" in summary
    assert summary.count("  ") >= 5


def test_offline_market_cache_outlives_live_refresh(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    market_service.save_market_cache("1D", {"prices": [1.0]})
    assert market_service.load_cached_market("1D") == {"prices": [1.0]}
    assert market_service.OFFLINE_CACHE_MAX_AGE >= 3600


@pytest.mark.parametrize(
    ("item", "label"),
    [
        ({"title": "BTC hits new high"}, "Bitcoin"),
        ({"title": "x", "categories": ["Bitcoin News"]}, "Bitcoin"),
        ({"title": "SEC delays decision"}, "Policy"),
        ({"title": "x", "categories": ["Markets"]}, "Markets"),
        ({"title": "Spot ETF flows"}, "ETFs"),
    ],
)
def test_news_filters(item, label):
    assert matches_filter(item, label)
    assert matches_filter(item, "All News")


def test_filters_do_not_match_everything():
    assert not any(matches_filter({"title": "weather report"}, label) for label in FILTERS)
