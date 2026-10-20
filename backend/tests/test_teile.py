"""Fundorte und Teile (GAME_DESIGN.md, Abschnitt „Fundorte und Teilekiste“).

Nach jeder der drei Aufgaben öffnet sich ein Fundort und das Team bekommt ein
Hardware-Teil für das Finale:

  Aufgabe 1 (alarm)          → Ersatzteilschrank → Netzteil      (Etikett: 115 V oder 230 V)
  Aufgabe 2 (fire_protocol)  → Lager             → Lüfter        (Etikett: Pfeil = Luftstrom)
  Aufgabe 3 (data_rescue)    → Datentresor       → Backup-Platte (Etikett: RAID-Platz 1–4)

Die Etiketten werden pro Runde ausgelost. game_tick.parts listet die gefundenen Teile
(Beamer: Umrisse füllen sich; Leitstand: Teilekiste mit Etiketten).
"""
import json

import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter, tick_payload
from backend.playableObject import ROLE_M, ROLE_P1, ROLE_P2

GAME = "teile_session"


@pytest.fixture
def dc():
    fake = fakeredis.FakeStrictRedis()
    fake.flushall()
    with patch("backend.redis_handler.redis.Redis", return_value=fake):
        center = DataCenter(game_id=GAME)
        for name, role in (("Anna", ROLE_M), ("Ben", ROLE_P1), ("Celim", ROLE_P2)):
            center.redis.r.hset(center.redis._k_players(GAME), name, json.dumps({"name": name, "role": role}))
        center.redis.r.hset(center._key, "dev_mode", "1")   # Überspringen statt echter Rätsel
        center.start()
        yield center


def _ids(dc):
    return [t["id"] for t in dc.snapshot()["parts"]]


def test_no_parts_at_the_start(dc):
    assert dc.snapshot()["parts"] == []
    assert tick_payload(dc.snapshot())["parts"] == []


def test_each_task_opens_its_place_and_gives_its_part(dc):
    dc.skip_task()
    netzteil = dc.snapshot()["parts"][0]
    assert netzteil["id"] == "psu"
    assert netzteil["name"] == "Netzteil"
    assert netzteil["fundort"] == "schrank"
    assert netzteil["label"] in ("115 V", "230 V")

    dc.skip_task()
    luefter = dc.snapshot()["parts"][1]
    assert (luefter["id"], luefter["name"], luefter["fundort"]) == ("fan", "Lüfter", "lager")

    dc.skip_task()
    platte = dc.snapshot()["parts"][2]
    assert (platte["id"], platte["name"], platte["fundort"]) == ("disk", "Backup-Platte", "tresor")
    assert platte["label"] in {f"RAID-Platz {n}" for n in range(1, 5)}


def test_the_finale_gives_no_part(dc):
    for _ in range(3):
        dc.skip_task()
    assert dc.current_task()["kind"] == "repair"
    dc.skip_task()
    assert _ids(dc) == ["psu", "fan", "disk"]


def test_a_solved_task_gives_the_part_too(dc):
    """Echte Lösung (nicht nur DEV-Überspringen) läuft über denselben Weg."""
    task = dc.current_task()
    dc.redis.r.hdel(dc._key, "task")
    dc._advance(task)
    assert _ids(dc) == ["psu"]


def test_labels_are_drawn_per_round():
    gesehen_v, gesehen_raid = set(), set()
    fake = fakeredis.FakeStrictRedis()
    with patch("backend.redis_handler.redis.Redis", return_value=fake):
        center = DataCenter(game_id="teile_zufall")
        for _ in range(60):
            center.start()
            spec = center.parts_spec
            gesehen_v.add(spec["psu"]["label"])
            gesehen_raid.add(spec["disk"]["label"])
    assert gesehen_v == {"115 V", "230 V"}
    assert len(gesehen_raid) == 4


def test_new_round_starts_with_an_empty_box(dc):
    dc.skip_task()
    dc.start()
    assert dc.snapshot()["parts"] == []
