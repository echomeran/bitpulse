"""Interface languages.

English is the source language: every visible string is written in English in the code and
passed through ``t()``, which returns the translation for the chosen language or the English
text when there is none. Placeholders use ``str.format`` names, e.g. ``t("Low: {price}", price=p)``.

Flet 0.28 does not tell the app the phone's language, so the first launch reads Android's
``persist.sys.locale`` property (falling back to the environment), and the header has a menu
to change it. The choice is saved on the phone.
"""

import locale
import logging
import os
import subprocess
from datetime import datetime

from services.cache import load_json, save_json
from services.locales import es, pt, tr

logger = logging.getLogger("bitpulse.i18n")

SETTINGS_FILE = "settings.json"
DEFAULT_LANGUAGE = "en"
# Code -> name shown in the language menu, in that language.
LANGUAGES = {"en": "English", "es": "Español", "pt": "Português", "tr": "Türkçe"}
_LOCALES = {"es": es, "pt": pt, "tr": tr}

# Code -> translation table; English needs none.
STRINGS: dict[str, dict[str, str]] = {code: module.STRINGS for code, module in _LOCALES.items()}
MONTHS = {code: module.MONTHS for code, module in _LOCALES.items()}

_state = {"language": DEFAULT_LANGUAGE}


def t(text: str, **values) -> str:
    """*text* in the current language (English when there is no translation)."""
    translated = STRINGS.get(_state["language"], {}).get(text, text)
    return translated.format(**values) if values else translated


def language() -> str:
    return _state["language"]


def set_language(code: str, save: bool = True) -> None:
    if code not in LANGUAGES:
        code = DEFAULT_LANGUAGE
    _state["language"] = code
    if save:
        save_json(SETTINGS_FILE, {"language": code})


def _supported(tag: str | None) -> str | None:
    """'tr-TR', 'tr_TR.UTF-8' or 'tr' -> 'tr' when the app speaks it."""
    code = (tag or "").replace("_", "-").split("-")[0].split(".")[0].strip().lower()
    return code if code in LANGUAGES else None


def _android_locale() -> str:
    for prop in ("persist.sys.locale", "ro.product.locale"):
        try:
            out = subprocess.run(["getprop", prop], capture_output=True, text=True, timeout=2).stdout
        except (OSError, subprocess.SubprocessError):
            return ""
        if out.strip():
            return out.strip()
    return ""


def detect_language() -> str:
    """The phone's language when the app supports it, otherwise English."""
    candidates = [_android_locale(), os.getenv("LC_ALL"), os.getenv("LANG")]
    try:
        candidates.append(locale.getlocale()[0])
    except ValueError:
        pass
    for tag in candidates:
        code = _supported(tag)
        if code:
            return code
    return DEFAULT_LANGUAGE


def load_language() -> str:
    """Apply the saved choice, or on first launch the phone's language, and return it."""
    data, _ = load_json(SETTINGS_FILE)
    saved = _supported((data or {}).get("language")) if isinstance(data, dict) else None
    code = saved or detect_language()
    logger.info("Interface language: %s (%s)", code, "saved" if saved else "detected")
    set_language(code, save=False)
    return code


def relative_time(timestamp: float, now: float | None = None) -> str:
    if now is None:
        now = datetime.now().timestamp()
    seconds = max(0, int(now - timestamp))
    if seconds < 3600:
        return t("{n}m ago", n=max(1, seconds // 60))
    if seconds < 86400:
        return t("{n}h ago", n=seconds // 3600)
    return t("{n}d ago", n=seconds // 86400)


def short_date(dt: datetime, with_year: bool = False) -> str:
    """'25 Nov' / "Nov '26" with month names in the current language."""
    months = MONTHS.get(_state["language"])
    month = months[dt.month - 1] if months else dt.strftime("%b")
    return f"{month} '{dt:%y}" if with_year else f"{dt.day:02d} {month}"


def count_label(count: int, label: str) -> str:
    """'1 release', '2 releases', '1 code change'; 'news' has no singular form.

    A language with a separate singular gives it under "<label>|one" ('1 lanzamiento'); Turkish
    keeps the singular after a number ('2 sürüm'), so it needs no such keys.
    """
    code = _state["language"]
    if code == "en":
        if count == 1 and label.endswith("s") and label != "news":
            label = label[:-1]
        return f"{count} {label}"
    singular = STRINGS.get(code, {}).get(f"{label}|one") if count == 1 else None
    return f"{count} {singular or t(label)}"
