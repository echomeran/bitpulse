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
    assert first["publisher"] == "Jane"
    assert first["description"] == "Full & rich body"
    assert first["thumbnail"] == {"resolutions": [{"url": "https://img/x.jpg"}]}
    assert first["categories"] == ["ETFs"]
    assert first["published_ts"] == 1789984800.0
    assert items[1]["publisher"] == "CoinDesk"
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
