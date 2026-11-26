import asyncio

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


def test_prompt_includes_article_text_when_reading_one():
    payload = server.ChatRequest(message="what does this mean?", article_url="https://coindesk.com/a")
    prompt = server.build_prompt(payload, "The ETF lost $200M in a day.")
    assert "ARTICLE THE USER IS READING" in prompt
    assert "The ETF lost $200M in a day." in prompt
    assert "ARTICLE THE USER IS READING" not in server.build_prompt(payload)


@pytest.mark.parametrize("url", ["", "https://example.com/a", "http://169.254.169.254/"])
def test_article_context_skips_urls_outside_the_allowlist(url, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("must not fetch")

    monkeypatch.setattr(server._session, "get", fail)
    payload = server.ChatRequest(message="hi", article_url=url)
    assert asyncio.run(server._article_context(payload)) == ""


def test_article_context_skips_hosts_blocked_for_ai_use(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("must not fetch")

    monkeypatch.setattr(server._session, "get", fail)
    monkeypatch.setenv("SUMMARY_BLOCKED_HOSTS", "coindesk.com, cointelegraph.com")
    payload = server.ChatRequest(message="hi", article_url="https://www.coindesk.com/markets/x")
    assert asyncio.run(server._article_context(payload)) == ""


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


def _chunk(text, finish=None):
    candidate = type("Cand", (), {"finish_reason": finish})()
    return type("Chunk", (), {"text": text, "candidates": [candidate]})()


def test_stream_marks_a_reply_cut_by_the_token_cap(monkeypatch):
    monkeypatch.setattr(server, "CHAT_MODELS", ["m"])

    class FakeModels:
        def generate_content_stream(self, model, contents, config):
            yield _chunk("Half an ans")
            yield _chunk("wer", server.types.FinishReason.MAX_TOKENS)

    pieces = list(server._stream_reply(type("C", (), {"models": FakeModels()})(), "prompt"))
    assert "".join(pieces) == "Half an answer" + server.TRUNCATED_NOTE


def test_stream_leaves_a_finished_reply_alone(monkeypatch):
    monkeypatch.setattr(server, "CHAT_MODELS", ["m"])

    class FakeModels:
        def generate_content_stream(self, model, contents, config):
            yield _chunk("Done.", server.types.FinishReason.STOP)

    assert list(server._stream_reply(type("C", (), {"models": FakeModels()})(), "prompt")) == ["Done."]


def test_thinking_limit_matches_each_model_family():
    assert server._thinking_config("gemini-2.5-flash").thinking_budget == server.THINKING_BUDGET
    assert server._thinking_config("gemini-2.5-flash", budget=0).thinking_budget == 0
    gemini3 = server._thinking_config("gemini-3.5-flash")
    assert gemini3.thinking_budget is None and gemini3.thinking_level is not None


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


def test_report_records_the_reply_in_the_log(client, caplog):
    server.report_limiter._hits.clear()
    body = {"question": "is BTC safe?", "answer": "Yes, guaranteed.", "article_url": ""}
    with caplog.at_level("WARNING", logger="bitpulse-api"):
        response = client.post("/v1/report", json=body)
    assert response.status_code == 200
    line = next(r.getMessage() for r in caplog.records if "AI_REPLY_REPORT" in r.getMessage())
    assert '"answer": "Yes, guaranteed."' in line


def test_report_rejects_an_empty_answer_and_floods(client, monkeypatch):
    server.report_limiter._hits.clear()
    assert client.post("/v1/report", json={"answer": ""}).status_code == 422
    monkeypatch.setattr(server.report_limiter, "allow", lambda key, now=None: False)
    assert client.post("/v1/report", json={"answer": "x"}).status_code == 429


OPTECH_SAMPLE = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title type="html">Bitcoin Optech Newsletter #432</title>
    <link href="https://bitcoinops.org/en/newsletters/2026/11/20/" rel="alternate"/>
    <published>2026-11-20T00:00:00+00:00</published>
    <content type="html">&lt;p&gt;This week's newsletter
summarizes a &lt;a href="/en/topics/pooled-mining/"&gt;mining&lt;/a&gt; analysis.&lt;/p&gt;
&lt;h2 id="news"&gt;News&lt;/h2&gt;&lt;ul&gt;&lt;li class="anchor-list"&gt;&lt;a href="#x"&gt;&#9679;&lt;/a&gt; &lt;strong&gt;Topic:&lt;/strong&gt; text&lt;/li&gt;&lt;/ul&gt;</content>
  </entry>
  <entry>
    <title type="html">Bitcoin Optech Newsletter #431 Recap Podcast</title>
    <link href="https://bitcoinops.org/en/podcast/2026/11/17/" rel="alternate"/>
    <published>2026-11-17T00:00:00+00:00</published>
    <content type="html">&lt;p&gt;podcast&lt;/p&gt;</content>
  </entry>
</feed>"""


def test_optech_feed_keeps_newsletters_as_clean_markdown():
    items, bodies = server.parse_optech_feed(OPTECH_SAMPLE)
    assert [i["number"] for i in items] == [432]  # the podcast recap is left out
    body = bodies[items[0]["url"]]
    assert "https://bitcoinops.org/en/topics/pooled-mining/" in body  # relative link made absolute
    assert "newsletter summarizes" in body  # wrapped source lines joined
    assert "●" not in body and "](#" not in body  # anchor bullets removed
    assert "## News" in body and items[0]["license"] == "MIT"


def test_article_text_keeps_words_apart_across_links():
    html = b"<p>The CFTC released the <a href='#'>agenda</a> for a roundtable (<b>24/7</b> trading) today.</p>"
    assert server.extract_article_text(html) == "The CFTC released the agenda for a roundtable (24/7 trading) today."


def test_full_text_is_only_served_for_sources_that_allow_it(client):
    response = client.get("/v1/news/article", params={"url": "https://cointelegraph.com/news/x"})
    assert response.status_code == 403


def test_summaries_can_be_switched_off_per_host(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("SUMMARY_BLOCKED_HOSTS", "cointelegraph.com")
    server._gemini_client.cache_clear()
    blocked = client.get("/v1/news/summary", params={"url": "https://cointelegraph.com/news/x"})
    assert blocked.status_code == 403
    assert client.get("/v1/news/summary", params={"url": "https://cointelegraph.com/x", "style": "long"}).status_code == 422


def test_summary_keeps_only_the_bullet_lines():
    raw = "Here's a quick rundown:\n\n- First fact.\n* Second fact.\n\nHope this helps!"
    assert server.bullet_lines_only(raw) == "- First fact.\n- Second fact."
    assert server.bullet_lines_only("Just one sentence.") == "Just one sentence."


def test_newsletter_splits_into_titled_cards():
    items, _ = server.parse_optech_feed(OPTECH_SAMPLE)
    sections = server._newsletter_cache["sections"][items[0]["url"]]
    assert [s["title"] for s in sections] == ["News"]
    card = sections[0]["items"][0]
    assert card["title"] == "Topic" and card["preview"] == "text"
    assert items[0]["counts"] == {"News": 1} and items[0]["reading_minutes"] >= 1


def test_release_items_take_their_title_from_the_project_link():
    html = (
        '<h2>Releases</h2><ul><li class="anchor-list"><p><a href="#x">●</a> '
        '<a href="https://github.com/bitcoin/bitcoin/pull/1">Bitcoin Core #1</a> fixes a leak. More text.</p></li></ul>'
    )
    card = server.newsletter_sections(html)[0]["items"][0]
    assert card["title"] == "Bitcoin Core #1" and card["preview"] == "Fixes a leak."


def test_article_text_prefers_the_marked_story_area():
    banner = "<p>" + "An official website of the United States government. " * 2 + "</p>"
    story = "<p>" + "The Commission today announced charges against a crypto platform. " * 6 + "</p>"
    page = f"<html><body>{banner}<main>{story}</main></body></html>".encode()
    assert "official website" not in server.extract_article_text(page)
    teaser = f"<html><body><article><p>Short teaser text that is long enough to count.</p></article>{story}</body></html>"
    assert "announced charges" in server.extract_article_text(teaser.encode())


def test_chat_prompt_names_the_app_language():
    turkish = server.build_prompt(server.ChatRequest(message="merhaba", lang="tr"))
    assert "APP LANGUAGE" in turkish and "Turkish" in turkish
    english = server.build_prompt(server.ChatRequest(message="hi"))
    assert "APP LANGUAGE" not in english
    assert server.language_note("xx") == ""


def test_chat_rejects_a_malformed_language(client):
    assert client.post("/v1/chat", json={"message": "hi", "lang": "turkish"}).status_code == 422


def test_summaries_are_cached_per_language():
    url = "https://example.com/a"
    # English keeps the key the pre-written newsletter digest is stored under.
    assert server.summary_cache_key("simple", url) == f"simple|{url}"
    assert server.summary_cache_key("simple", url, "tr") == f"simple|tr|{url}"
    assert "Turkish" in server.summary_instruction("brief", "tr")
    assert server.summary_instruction("brief") == server.SUMMARY_INSTRUCTION


def test_summary_language_is_validated(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    server._gemini_client.cache_clear()
    response = client.get("/v1/news/summary", params={"url": "https://coindesk.com/a", "lang": "TR-tr"})
    assert response.status_code == 422


def test_a_summary_cut_off_at_the_token_cap_keeps_only_whole_lines():
    from types import SimpleNamespace

    from google.genai import types

    cut = SimpleNamespace(
        text="- First whole point.\n- Second whole point.\n- Third one stops mid-wo",
        candidates=[SimpleNamespace(finish_reason=types.FinishReason.MAX_TOKENS)],
    )
    client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **_: cut))
    assert server._summarize(client, "text") == "- First whole point.\n- Second whole point."
    assert server.drop_unfinished_line("- only line, cut") == ""


def test_every_app_language_has_a_name_for_the_model():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from services import i18n

    assert set(i18n.LANGUAGES) <= set(server.LANGUAGE_NAMES)
