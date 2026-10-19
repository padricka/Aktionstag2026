"""REST: GET /leaderboard/ für das Hauptmenü (seitenweise, höchste Punktzahl zuerst)."""
import json

from django.test import Client

from backend import leaderboard


def test_leaderboard_endpoint_pages():
    for punkte in range(1, 26):
        leaderboard.add_entry(["A", "B", "C"], punkte, "meltdown", 10)
    resp = Client().get("/leaderboard/", {"page": 2})
    assert resp.status_code == 200
    assert resp["Access-Control-Allow-Origin"] == "*"
    data = json.loads(resp.content)
    assert data["page"] == 2 and data["pages"] == 2 and data["total"] == 25
    assert [e["rank"] for e in data["entries"]] == [21, 22, 23, 24, 25]
    assert data["entries"][0]["score"] == 5


def test_leaderboard_endpoint_bad_page_falls_back_to_first():
    data = json.loads(Client().get("/leaderboard/", {"page": "abc", "per_page": "x"}).content)
    assert data["page"] == 1 and data["per_page"] == 20
