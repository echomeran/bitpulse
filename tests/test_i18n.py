import ast
import string
from datetime import datetime
from pathlib import Path

import pytest

from services import ai_service, i18n, news_service
from views import ai_view, chat_panel, news_detail_view, news_view, newsletter_view

SRC = Path(__file__).resolve().parents[1] / "src"


@pytest.fixture(autouse=True)
def english_afterwards():
    yield
    i18n.set_language("en", save=False)


def literal_t_calls() -> set[str]:
    """Every string literal passed straight to t(...) in the app's source."""
    found = set()
    for path in SRC.rglob("*.py"):
        if "build" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and (
                    (isinstance(node.func, ast.Name) and node.func.id == "t")
                    or (isinstance(node.func, ast.Attribute) and node.func.attr == "t")
                )
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                found.add(node.args[0].value)
    return found


# Strings that reach t() through a variable rather than as a literal.
INDIRECT = {
    ai_view.GREETING,
    ai_view.DISCLAIMER,
    chat_panel.NO_BACKEND_MESSAGE,
    ai_service.ERR_UNREACHABLE,
    ai_service.ERR_TIMEOUT,
    ai_service.ERR_BUSY,
    ai_service.ERR_UNAVAILABLE,
    ai_service.ERR_EMPTY,
    ai_service.INTERRUPTED_NOTE,
    news_service.SUMMARY_UNAVAILABLE,
    "Summaries are not available for this article.",
    "Could not summarize this article.",
    "Could not reach the AI service.",
    "Ask BitPulse something…",
    "e.g. why does this matter?",
    "e.g. what does this mean for my wallet?",
    newsletter_view.CREDIT,
    news_view.ALL_NEWS,
    *(label for label in news_view.FILTERS if label not in {"Bitcoin", "DeFi"}),
    *(label for _, _, _, label in newsletter_view.SECTION_STYLES),
    newsletter_view.DEFAULT_SECTION_STYLE[2],
    "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed",
    "1H", "1D", "1W", "1M", "1Y", "5Y",
}


def placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


@pytest.mark.parametrize("code", [c for c in i18n.LANGUAGES if c != "en"])
def test_every_visible_string_has_a_translation(code):
    table = i18n.STRINGS[code]
    missing = sorted((literal_t_calls() | INDIRECT) - table.keys())
    assert not missing, f"untranslated for {code}: {missing}"


@pytest.mark.parametrize("code", [c for c in i18n.LANGUAGES if c != "en"])
def test_translations_keep_the_placeholders(code):
    wrong = [k for k, v in i18n.STRINGS[code].items() if placeholders(k) != placeholders(v)]
    assert not wrong


@pytest.mark.parametrize("code", [c for c in i18n.LANGUAGES if c != "en"])
def test_no_translation_key_is_left_unused(code):
    used = literal_t_calls() | INDIRECT | {"{n}m ago", "{n}h ago", "{n}d ago"}
    labels = {label for _, _, _, label in newsletter_view.SECTION_STYLES} | {newsletter_view.DEFAULT_SECTION_STYLE[2]}
    used |= {f"{label}|one" for label in labels}
    assert not sorted(set(i18n.STRINGS[code]) - used)


def test_every_language_names_twelve_months():
    assert all(len(months) == 12 for months in i18n.MONTHS.values())
    assert set(i18n.MONTHS) == set(i18n.STRINGS) == set(i18n.LANGUAGES) - {"en"}


def test_spanish_and_portuguese_counts_use_the_singular_for_one():
    i18n.set_language("es", save=False)
    assert i18n.count_label(1, "releases") == "1 lanzamiento"
    assert i18n.count_label(3, "releases") == "3 lanzamientos"
    i18n.set_language("pt", save=False)
    assert i18n.count_label(1, "code changes") == "1 mudança de código"
    assert i18n.relative_time(0, now=7200) == "há 2 h"
    assert i18n.short_date(datetime(2026, 9, 5)) == "05 set"


def test_t_falls_back_to_english_and_fills_placeholders():
    i18n.set_language("tr", save=False)
    assert i18n.t("Retry") == "Tekrar dene"
    assert i18n.t("Not translated yet") == "Not translated yet"
    assert i18n.t("Low: {price}", price="$1") == "En düşük: $1"
    i18n.set_language("en", save=False)
    assert i18n.t("Low: {price}", price="$1") == "Low: $1"


def test_unknown_language_falls_back_to_english():
    i18n.set_language("xx", save=False)
    assert i18n.language() == "en"


def test_language_tags_are_read_loosely():
    assert i18n._supported("tr-TR") == "tr"
    assert i18n._supported("tr_TR.UTF-8") == "tr"
    assert i18n._supported("en") == "en"
    assert i18n._supported("de-DE") is None
    assert i18n._supported("") is None and i18n._supported(None) is None


def test_saved_choice_wins_over_the_phone_language(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    monkeypatch.setattr(i18n, "detect_language", lambda: "en")
    assert i18n.load_language() == "en"
    i18n.set_language("tr")
    i18n.set_language("en", save=False)
    assert i18n.load_language() == "tr"


def test_first_launch_uses_the_phone_language(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    monkeypatch.setattr(i18n, "_android_locale", lambda: "tr-TR")
    assert i18n.load_language() == "tr"


def test_turkish_times_dates_and_counts():
    i18n.set_language("tr", save=False)
    assert i18n.relative_time(1000, now=1000 + 5 * 60) == "5 dk önce"
    assert i18n.relative_time(0, now=3 * 86400) == "3 gün önce"
    assert i18n.short_date(datetime(2026, 11, 5)) == "05 Kas"
    assert i18n.short_date(datetime(2026, 8, 5), with_year=True) == "Ağu '26"
    assert i18n.count_label(2, "releases") == "2 sürüm"
    assert i18n.count_label(1, "news") == "1 haber"


def test_english_dates_are_unchanged():
    assert i18n.short_date(datetime(2026, 11, 5)) == "05 Nov"
    assert i18n.short_date(datetime(2026, 11, 5), with_year=True) == "Nov '26"


def test_ai_context_stays_in_english_while_the_screen_is_turkish():
    i18n.set_language("tr", save=False)
    item = {"published_ts": 0}
    assert news_service.published_label(item).endswith("d ago")
    assert news_service.display_time(item).endswith("gün önce")
    assert ai_service.build_payload("merhaba", [], "$1", [], "")["lang"] == "tr"


def test_article_screen_builds_in_turkish():
    i18n.set_language("tr", save=False)

    class FakePage:
        def launch_url(self, _):
            pass

        def update(self):
            pass

    item = {"title": "T", "link": "https://example.com/a", "publisher": "CoinDesk"}
    assert news_detail_view.news_detail_view_component(item, lambda *_: None, FakePage()) is not None
