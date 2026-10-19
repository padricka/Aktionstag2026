"""Leaderboard: jede beendete Runde als Eintrag in einer JSON-Datei.

Datei: LEADERBOARD_FILE (Umgebungsvariable), sonst backend/data/leaderboard.json.
Im Docker-Container liegt backend/data auf einem eigenen Volume, damit die
Einträge einen Neubau überstehen.
"""
import json
import math
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "data" / "leaderboard.json"
TOP_N = 5
PER_PAGE = 20
MAX_PER_PAGE = 100

# Consumer und Spielschleife schreiben aus Threads (asyncio.to_thread)
_lock = threading.Lock()


def _file() -> Path:
    return Path(os.environ.get("LEADERBOARD_FILE", DEFAULT_FILE))


def _load() -> list[dict]:
    path = _file()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("entries", []))
    except FileNotFoundError:
        return []
    except (ValueError, AttributeError):
        # Kaputte Datei nicht still überschreiben: zur Seite legen, neu anfangen
        backup = path.with_name(f"{path.name}.kaputt-{int(time.time())}")
        path.replace(backup)
        print(f"[LEADERBOARD] Datei unlesbar, gesichert als {backup.name}")
        return []


def _save(entries: list[dict]) -> None:
    path = _file()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps({"entries": entries}, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)   # atomar: nie eine halb geschriebene Datei


def _ranked(entries: list[dict]) -> list[dict]:
    """Höchste Punktzahl zuerst; bei Gleichstand die ältere Runde vorn."""
    ordered = sorted(entries, key=lambda e: (-e["score"], e["created_at"]))
    return [{**e, "rank": i} for i, e in enumerate(ordered, 1)]


def add_entry(players: list[str], score: int, result: str, survived_seconds: int,
              game_id: str | None = None) -> dict:
    """Runde eintragen. Rückgabe: eigener Eintrag (mit Platz), Top 5, Anzahl Runden."""
    entry = {
        "id": uuid.uuid4().hex[:12],
        "players": list(players),
        "score": int(score),
        "result": result,
        "survived_seconds": int(survived_seconds),
        "game_id": game_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
    }
    with _lock:
        entries = _load()
        entries.append(entry)
        _save(entries)
    ranked = _ranked(entries)
    own = next(e for e in ranked if e["id"] == entry["id"])
    return {"entry": own, "top": ranked[:TOP_N], "total": len(ranked)}


def top(n: int = TOP_N) -> dict:
    with _lock:
        ranked = _ranked(_load())
    return {"top": ranked[:n], "total": len(ranked)}


def page(page: int = 1, per_page: int = PER_PAGE) -> dict:
    per_page = max(1, min(int(per_page), MAX_PER_PAGE))
    with _lock:
        ranked = _ranked(_load())
    pages = max(1, math.ceil(len(ranked) / per_page))
    page = max(1, min(int(page), pages))
    start = (page - 1) * per_page
    return {
        "entries": ranked[start:start + per_page],
        "page": page,
        "per_page": per_page,
        "total": len(ranked),
        "pages": pages,
    }
