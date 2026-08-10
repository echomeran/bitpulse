import json
import os
from datetime import datetime, timezone
from pathlib import Path


def _cache_dir() -> Path:
    default_dir = Path(__file__).resolve().parents[2] / "storage"
    path = Path(os.getenv("FLET_APP_STORAGE_DATA", default_dir))
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(name: str, max_age_seconds: int | None = None):
    path = _cache_dir() / name
    if not path.exists():
        return None, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        saved_at = datetime.fromisoformat(payload["saved_at"])
        age = (datetime.now(timezone.utc) - saved_at).total_seconds()
        if max_age_seconds is not None and age > max_age_seconds:
            return None, saved_at
        return payload["data"], saved_at
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None, None


def save_json(name: str, data) -> None:
    path = _cache_dir() / name
    payload = {"saved_at": datetime.now(timezone.utc).isoformat(), "data": data}
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    temporary_path.replace(path)
