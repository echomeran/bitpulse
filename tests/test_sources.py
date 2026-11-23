from pathlib import Path

import pytest

from services import sources

ROOT = Path(__file__).resolve().parents[1]

RSS = b"""<?xml version="1.0"?>
<rss xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:media="http://search.yahoo.com/mrss/"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <item>
    <title>Bitcoin ETF inflows</title>
    <link>https://www.coindesk.com/a</link>
    <pubDate>Mon, 21 Sep 2026 10:00:00 +0000</pubDate>
    <dc:creator>Jane</dc:creator>
    <media:content url="https://img/x.jpg"/>
    <content:encoded><![CDATA[<p>Full &amp; rich <b>body</b></p>]]></content:encoded>
    <category>ETFs</category>
  </item>
  <item>
    <title>Older</title>
    <link>https://www.coindesk.com/b</link>
    <pubDate>Sun, 20 Sep 2026 10:00:00 +0000</pubDate>
    <description>plain</description>
  </item>
  <item><title>No link</title></item>
</channel>
</rss>"""


def test_sources_module_is_identical_in_app_and_server():
    assert (ROOT / "src/services/sources.py").read_bytes() == (ROOT / "server/sources.py").read_bytes()


def test_parse_rss_extracts_fields():
    items = sources.parse_rss(RSS, "CoinDesk")
    first = items[0]
    assert first["title"] == "Bitcoin ETF inflows"
    assert first["publisher"] == "CoinDesk"
    assert first["author"] == "Jane"
    assert first["description"] == "Full & rich body"
    assert first["thumbnail"] == {"resolutions": [{"url": "https://img/x.jpg"}]}
    assert first["categories"] == ["ETFs"]
    assert first["published_ts"] == 1789984800.0
    assert items[1]["publisher"] == "CoinDesk"
    assert items[1]["author"] == ""
    assert items[1]["description"] == "plain"


def test_dedupe_sorts_newest_first_and_drops_missing_links():
    items = sources.parse_rss(RSS, "CoinDesk")
    result = sources.dedupe_articles(list(reversed(items)) + items)
    assert [a["link"] for a in result] == ["https://www.coindesk.com/a", "https://www.coindesk.com/b"]


@pytest.mark.parametrize(
    ("seconds_ago", "expected"),
    [(0, "1m ago"), (600, "10m ago"), (7200, "2h ago"), (3 * 86400, "3d ago")],
)
def test_format_relative_time(seconds_ago, expected):
    assert sources.format_relative_time(1_000_000 - seconds_ago, now=1_000_000) == expected


def test_format_relative_time_without_timestamp():
    assert sources.format_relative_time(None) == "Latest"


@pytest.mark.parametrize(
    "url",
    [
        "https://www.coindesk.com/markets/2026/09/21/x",
        "https://coindesk.com/x",
        "https://cointelegraph.com/news/x",
    ],
)
def test_allowed_article_urls(url):
    assert sources.is_allowed_article_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.coindesk.com/x",
        "https://evilcoindesk.com/x",
        "https://coindesk.com.evil.io/x",
        "https://user@coindesk.com/x",
        "https://coindesk.com:8443/x",
        "https://169.254.169.254/latest/meta-data",
        "http://localhost:8080/health",
        "file:///etc/passwd",
        "https://coindesk.com:abc/x",
        "",
    ],
)
def test_blocked_article_urls(url):
    assert not sources.is_allowed_article_url(url)


def test_build_market_payload():
    payload = sources.build_market_payload({"prices": [100.0, 90.0, 110.0], "timestamps": [1, 2, 3]}, None, 900_000, "1D")
    assert payload["current_price"] == 110.0
    assert payload["high"] == 110.0
    assert payload["low"] == 90.0
    assert payload["change_pct"] == pytest.approx(10.0)
    assert payload["block_height"] == 900_000


def test_short_periods_keep_a_trailing_window_not_the_utc_day():
    from sources import PERIOD_CONFIG, trim_to_window

    hour = 3600
    # Two days of 15-minute points ending at 14:00 UTC.
    points = [(t, float(t)) for t in range(0, 2 * 24 * hour, 15 * 60)]
    day = trim_to_window(points, PERIOD_CONFIG["1D"]["window"])
    assert day[-1][0] - day[0][0] == 24 * hour
    last_hour = trim_to_window(points, PERIOD_CONFIG["1H"]["window"])
    assert last_hour[-1][0] - last_hour[0][0] == hour
    assert trim_to_window(points, None) == points
    assert trim_to_window([], 3600) == []
    assert all(PERIOD_CONFIG[p]["range"] != "1d" for p in ("1H", "1D"))


def test_regulator_items_are_kept_only_when_about_crypto():
    from sources import allows_full_text, is_crypto_item

    assert is_crypto_item({"title": "SEC Charges Fake Crypto Asset Trading Platforms"})
    assert is_crypto_item({"title": "Roundtable", "description": "tokenization of securities"})
    assert not is_crypto_item({"title": "SEC Proposes Executive Compensation Reforms"})
    assert not is_crypto_item({"title": "Ethernet outage at exchange"})
    assert allows_full_text("https://www.cftc.gov/PressRoom/PressReleases/9327-26")
    assert allows_full_text("https://bitcoinops.org/en/newsletters/2026/11/20/")
    assert not allows_full_text("https://cointelegraph.com/news/x")
    assert not allows_full_text("https://evil.example/sec.gov")


def test_recent_regulator_items_survive_the_headline_cap():
    from sources import REGULATOR_MAX_ITEMS, merge_regulator_items

    now = 1_000_000_000
    news = [{"link": f"n{i}", "published_ts": now - i} for i in range(50)]
    old = {"link": "sec-old", "published_ts": now - 40 * 86400}
    regs = [{"link": f"r{i}", "published_ts": now - 4 * 86400 - i} for i in range(8)] + [old]
    merged = merge_regulator_items(news, regs, now=now)
    kept = [a["link"] for a in merged if a["link"].startswith("r")]
    assert len(kept) == REGULATOR_MAX_ITEMS and "sec-old" not in [a["link"] for a in merged]
    assert merged[0]["link"] == "n0"  # still newest first


def test_sec_requests_carry_a_contact_address():
    from sources import CONTACT_EMAIL, request_headers

    assert CONTACT_EMAIL in request_headers("https://www.sec.gov/newsroom/press-releases/x")["User-Agent"]
    assert request_headers("https://cointelegraph.com/news/x") == {}
