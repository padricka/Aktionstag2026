"""Leaderboard: jede beendete Runde als Eintrag in einer JSON-Datei."""
import json

from backend import leaderboard


def _runde(score, *namen, result="meltdown", survived=60):
    return leaderboard.add_entry(list(namen) or ["A", "B", "C"], score, result, survived, game_id="g")


def test_empty_leaderboard(leaderboard_file):
    seite = leaderboard.page()
    assert seite == {"entries": [], "page": 1, "per_page": 20, "total": 0, "pages": 1}
    assert not leaderboard_file.exists()


def test_add_entry_is_saved_as_json(leaderboard_file):
    _runde(450, "Anna", "Ben", "Cem", result="victory", survived=200)
    data = json.loads(leaderboard_file.read_text(encoding="utf-8"))
    (eintrag,) = data["entries"]
    assert eintrag["players"] == ["Anna", "Ben", "Cem"]
    assert eintrag["score"] == 450
    assert eintrag["result"] == "victory"
    assert eintrag["survived_seconds"] == 200
    assert eintrag["created_at"]


def test_add_entry_returns_rank_top5_and_total():
    for punkte in (100, 900, 300, 700, 500, 200):
        _runde(punkte)
    neu = _runde(600)
    assert neu["entry"]["rank"] == 3
    assert neu["total"] == 7
    assert [e["score"] for e in neu["top"]] == [900, 700, 600, 500, 300]
    assert [e["rank"] for e in neu["top"]] == [1, 2, 3, 4, 5]


def test_equal_score_older_game_ranks_first():
    erster = _runde(500, "Erst", "X", "Y")
    zweiter = _runde(500, "Spaet", "X", "Y")
    assert erster["entry"]["rank"] == 1
    assert zweiter["entry"]["rank"] == 2


def test_pages_of_twenty_sorted_high_to_low():
    for punkte in range(1, 46):            # 45 Runden: 1..45 Punkte
        _runde(punkte)
    s1 = leaderboard.page(1)
    s3 = leaderboard.page(3)
    assert s1["total"] == 45 and s1["pages"] == 3
    assert [e["score"] for e in s1["entries"]][:3] == [45, 44, 43]
    assert [e["rank"] for e in s1["entries"]] == list(range(1, 21))
    assert [e["rank"] for e in leaderboard.page(2)["entries"]] == list(range(21, 41))
    assert [e["score"] for e in s3["entries"]] == [5, 4, 3, 2, 1]


def test_page_out_of_range_is_clamped():
    for punkte in range(25):
        _runde(punkte)
    assert leaderboard.page(99)["page"] == 2
    assert leaderboard.page(0)["page"] == 1
    assert leaderboard.page(1, per_page=1000)["per_page"] == 100


def test_top_without_adding():
    for punkte in (10, 20, 30):
        _runde(punkte)
    top = leaderboard.top()
    assert [e["score"] for e in top["top"]] == [30, 20, 10]
    assert top["total"] == 3


def test_broken_file_is_kept_as_backup_not_lost(leaderboard_file):
    leaderboard_file.write_text("{kaputt", encoding="utf-8")
    _runde(10)
    backups = list(leaderboard_file.parent.glob("leaderboard.json.kaputt-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "{kaputt"
    assert leaderboard.page()["total"] == 1
