import pytest
from fastapi.testclient import TestClient

import app as server


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    server._gemini_client.cache_clear()
    yield TestClient(server.app)
    server._gemini_client.cache_clear()


def test_health_reports_missing_ai_key(client):
    assert client.get("/health").json() == {"status": "ok", "ai_configured": False}


def test_chat_returns_503_without_key(client):
    assert client.post("/v1/chat", json={"message": "hi"}).status_code == 503


def test_chat_accepts_long_assistant_history():
    payload = server.ChatRequest(message="hi", history=[{"role": "assistant", "text": "x" * 3000}])
    assert "x" * 3000 in server.build_prompt(payload)


@pytest.mark.parametrize("url", ["http://169.254.169.254/", "https://example.com/", "http://localhost/"])
def test_article_endpoint_rejects_foreign_urls(client, url, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("must not fetch")

    monkeypatch.setattr(server._session, "get", fail)
    assert client.get("/v1/news/article", params={"url": url}).status_code == 400


def test_article_redirect_to_foreign_host_is_blocked(monkeypatch):
    class Redirect:
        is_redirect = True
        headers = {"location": "http://169.254.169.254/"}

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return Redirect()

    monkeypatch.setattr(server._session, "get", fake_get)
    with pytest.raises(server.ArticleFetchError):
        server._download_article("https://www.coindesk.com/a")
    assert calls == ["https://www.coindesk.com/a"]


def test_market_rejects_unknown_period(client):
    assert client.get("/v1/market", params={"period": "2D"}).status_code == 400


def test_extract_article_text_skips_boilerplate():
    html = b"""<html><nav><p>Navigation link text that is quite long indeed, really</p></nav>
    <p>short</p><p>This is a real paragraph of the article body with enough length.</p>
    <p>We use cookies to improve your experience on this website, accept them.</p></html>"""
    assert server.extract_article_text(html) == "This is a real paragraph of the article body with enough length."


def test_rate_limiter_blocks_and_recovers():
    limiter = server.RateLimiter(limit=2, window_seconds=10)
    assert limiter.allow("a", now=0)
    assert limiter.allow("a", now=1)
    assert not limiter.allow("a", now=2)
    assert limiter.allow("b", now=2)
    assert limiter.allow("a", now=11.5)


def test_rate_limiter_sweeps_idle_clients():
    limiter = server.RateLimiter(limit=5, window_seconds=10)
    for i in range(499):
        limiter.allow(f"ip{i}", now=0)
    limiter.allow("late", now=100)
    assert list(limiter._hits) == ["late"]


class FakeRequest:
    def __init__(self, forwarded=None, host="10.0.0.1"):
        self.headers = {"x-forwarded-for": forwarded} if forwarded else {}
        self.client = type("C", (), {"host": host})()


def test_client_ip_uses_proxy_appended_address(monkeypatch):
    monkeypatch.setattr(server, "TRUSTED_PROXY_HOPS", 1)
    assert server.client_ip(FakeRequest("6.6.6.6, 1.2.3.4")) == "1.2.3.4"
    assert server.client_ip(FakeRequest()) == "10.0.0.1"


def test_client_ip_ignores_header_without_proxy(monkeypatch):
    monkeypatch.setattr(server, "TRUSTED_PROXY_HOPS", 0)
    assert server.client_ip(FakeRequest("6.6.6.6")) == "10.0.0.1"
