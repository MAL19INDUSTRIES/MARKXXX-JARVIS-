import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
STATUS_PATH = ROOT / "tmp" / "jarvis_status.json"


def _ensure_dir():
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)


def write_status(data: dict) -> None:
    try:
        _ensure_dir()
        payload = {**data}
        payload.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
        STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def read_status() -> dict:
    try:
        if STATUS_PATH.exists():
            return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {}


def clear_status() -> None:
    try:
        if STATUS_PATH.exists():
            STATUS_PATH.unlink()
    except Exception:
        pass
