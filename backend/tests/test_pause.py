"""Pause während der Zwischenszene (feat/pause-zwischenszene).

Nach jeder gelösten Aufgabe zeigen Handys und Beamer die Zwischenszene (Fundort öffnet
sich, Titelkarte). So lange stehen Uhr und Feuer, und das ×2-Zeitfenster der nächsten
Aufgabe beginnt erst danach. Dauer: PAUSE_NACH (Datentresor etwas länger).
"""
import json

import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter, PAUSE_NACH, FIRE_EVERY
from backend.playableObject import ROLE_M, ROLE_P1, ROLE_P2

GAME = "pause_session"


@pytest.fixture
def dc():
    fake = fakeredis.FakeStrictRedis()
    fake.flushall()
    with patch("backend.redis_handler.redis.Redis", return_value=fake):
        center = DataCenter(game_id=GAME)
        for name, role in (("Anna", ROLE_M), ("Ben", ROLE_P1), ("Celim", ROLE_P2)):
            center.redis.r.hset(center.redis._k_players(GAME), name, json.dumps({"name": name, "role": role}))
        uhr = {"t": 1000.0}
        center._now = lambda: uhr["t"]
        center.uhr = uhr
        center.start()
        yield center


def _loesen(dc):
    """Aktuelle Aufgabe als gelöst weiterschalten (gleicher Weg wie eine echte Lösung)."""
    task = dc.current_task()
    dc.redis.r.hdel(dc._key, "task")
    dc._advance(task)


def test_pause_fits_the_cutscene():
    """Fundort ~5 s (Datentresor 6 s). Vor Aufgabe 2 kommt das Tutorial zur Löschanlage dazu
    (feat/tutorial-loeschanlage, 12 s), vor Aufgabe 3 das Binär-Tutorial (feat/tutorial-binaer, 14 s)
    – Zwischenszene.vue TUTORIAL_MS."""
    assert PAUSE_NACH == {"alarm": 5 + 12, "fire_protocol": 5 + 14, "data_rescue": 6}


def test_clock_and_fire_stand_still_during_the_cutscene(dc):
    _loesen(dc)                                   # Alarm gelöst → Ersatzteilschrank
    zeit, leben = dc.time_left, dc.health
    for _ in range(PAUSE_NACH["alarm"]):
        dc.tick()
    assert dc.time_left == zeit
    assert dc.health == leben

    dc.uhr["t"] += PAUSE_NACH["alarm"]            # Szene vorbei
    for _ in range(FIRE_EVERY):
        dc.tick()
    assert dc.time_left == zeit - FIRE_EVERY
    assert dc.health == leben - 1


def test_the_data_vault_pauses_a_little_longer(dc):
    for _ in range(3):
        _loesen(dc)
    zeit = dc.time_left
    dc.uhr["t"] += PAUSE_NACH["data_rescue"] - 0.5
    dc.tick()
    assert dc.time_left == zeit
    dc.uhr["t"] += 0.5
    dc.tick()
    assert dc.time_left == zeit - 1


def test_the_x2_window_of_the_next_task_starts_after_the_cutscene(dc):
    _loesen(dc)
    assert dc.current_task()["started_at"] == 1000.0 + PAUSE_NACH["alarm"]


def test_no_pause_at_the_start_and_after_a_new_round(dc):
    zeit = dc.time_left
    dc.tick()
    assert dc.time_left == zeit - 1

    _loesen(dc)
    dc.start()
    zeit = dc.time_left
    dc.tick()
    assert dc.time_left == zeit - 1
