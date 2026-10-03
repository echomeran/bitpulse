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
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["ai_configured"] is False
    assert body["model"] == server.CHAT_MODELS[0]


def test_chat_returns_503_without_key(client):
    assert client.post("/v1/chat", json={"message": "hi"}).status_code == 503
    assert client.post("/v1/chat/stream", json={"message": "hi"}).status_code == 503
    assert client.get("/v1/news/summary", params={"url": "https://coindesk.com/a"}).status_code == 503


def test_prompt_carries_news_details_and_date():
    payload = server.ChatRequest(
        message="what happened?",
        news=[{
            "title": "ETF outflows",
            "publisher": "CoinDesk",
            "published_at": "2h ago",
            "summary": "Funds lost $200M in a day.",
            "categories": ["ETFs", "Markets"],
        }],
        market_summary="BTC $84,800",
    )
    prompt = server.build_prompt(payload)
    assert "ETF outflows (CoinDesk, 2h ago) [ETFs, Markets]" in prompt
    assert "Funds lost $200M in a day." in prompt
    assert "BTC $84,800" in prompt
    assert str(server.datetime.now(server.timezone.utc).year) in prompt


class _Busy(server.genai_errors.ServerError):
    def __init__(self):
        super().__init__(503, {"error": {"message": "busy"}})


def test_generate_reply_falls_back_to_the_next_model(monkeypatch):
    monkeypatch.setattr(server, "CHAT_MODELS", ["busy-model", "spare-model"])
    used = []

    class FakeModels:
        def generate_content(self, model, contents, config):
            used.append(model)
            if model == "busy-model":
                raise _Busy()
            return type("R", (), {"text": "answer", "candidates": []})()

    reply = server._generate_reply(type("C", (), {"models": FakeModels()})(), "prompt")
    assert reply == "answer"
    assert used == ["busy-model", "spare-model"]


def test_generate_reply_reraises_non_overload_errors(monkeypatch):
    monkeypatch.setattr(server, "CHAT_MODELS", ["a", "b"])

    class FakeModels:
        def generate_content(self, model, contents, config):
            raise ValueError("bad request")

    with pytest.raises(ValueError):
        server._generate_reply(type("C", (), {"models": FakeModels()})(), "prompt")


def test_summary_endpoint_rejects_foreign_urls(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    server._gemini_client.cache_clear()
    assert client.get("/v1/news/summary", params={"url": "https://example.com/a"}).status_code == 400


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
