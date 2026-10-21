"""Hilfe-Notizen (GAME_DESIGN.md, Abschnitt „Hilfe-Notizen“).

Zu jeder Aufgabe gibt es Hilfe-Themen (Aufgabe 1: 4, Aufgabe 2: 5, Aufgabe 3: 6,
Finale: keine). Jedes Thema gehört zu einem Schritt der Aufgabe. Am Beamer liegt ein
Abreißblock: Der Host reißt den Zettel zu dem Thema ab, an dem das Team gerade hängt –
in beliebiger Reihenfolge. Themen, deren Schritt laut Spielstand schon erledigt ist,
stehen nicht mehr auf dem Block. Jeder abgerissene Zettel kostet HINT_COST Punkte
(DEV-Modus: gratis). Die Texte passen zur laufenden Runde.
"""
import json

import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter, HINT_COST, tick_payload
from backend.playableObject import (
    AlarmTask, FireProtocolTask, DataRescueTask, RepairTask, ROLE_M, ROLE_P1, ROLE_P2,
)

GAME = "hilfe_session"
M, V, R = "Anna", "Ben", "Celim"


@pytest.fixture
def dc():
    fake = fakeredis.FakeStrictRedis()
    fake.flushall()
    with patch("backend.redis_handler.redis.Redis", return_value=fake):
        center = DataCenter(game_id=GAME)
        for name, role in ((M, ROLE_M), (V, ROLE_P1), (R, ROLE_P2)):
            center.redis.r.hset(center.redis._k_players(GAME), name, json.dumps({"name": name, "role": role}))
        center.start()
        yield center


def _hints(dc):
    return dc.snapshot()["hints"]


def _ids(liste):
    return [h["id"] for h in liste]


def _eingabe(dc, name, target, value):
    return dc.process_input(name, {"action_type": "button_press", "target": target, "value": value})


def _nach_id(cls, st):
    return {h["id"]: h for h in cls.hints(st)}


# ------------------------------------------------------------------ Themen je Aufgabe
@pytest.mark.parametrize("cls, ids", [
    (AlarmTask, ["cable", "order", "symbols", "scratch"]),
    (FireProtocolTask, ["probe", "order", "power", "agents", "release"]),
    (DataRescueTask, ["disk", "login", "convert", "ascii", "key", "decrypt"]),
    (RepairTask, ["give", "maintenance", "disk", "fan", "psu", "keys"]),
])
def test_each_task_has_its_topics(cls, ids):
    for _ in range(30):
        hilfen = cls.hints(cls.create({}))
        assert _ids(hilfen) == ids
        assert cls.HINTS == len(ids)
        for h in hilfen:
            assert h["label"] and len(h["label"]) <= 24
            assert isinstance(h["text"], str) and len(h["text"]) > 20
            assert isinstance(h["done"], bool)


def test_finale_hints_fit_the_round_and_know_what_is_done():
    """feat/finale-hilfen-punkte: auch das Finale hat Hilfe-Notizen, passend zur Runde."""
    st = RepairTask.create({}, {"disk": {"label": "RAID-Platz 3"}, "psu": {"label": "230 V"}})
    h = _nach_id(RepairTask, st)
    assert "Vorderseite" in h["give"]["text"] and "Rückseite" in h["give"]["text"]
    assert "BAY 2" in h["maintenance"]["text"] and f"FAN {st['fan_slot'] - 1}" in h["maintenance"]["text"]
    assert "Schacht 3" in h["disk"]["text"]
    assert st["gang"] in h["fan"]["text"] and st["fan_dir"] in h["fan"]["text"]
    assert f"Schacht {st['psu_bay']}" in h["psu"]["text"] and "230 V" in h["psu"]["text"]
    assert "Strom" in h["keys"]["text"]
    assert not any(x["done"] for x in h.values())

    st["orte"] = {"disk": "eingebaut", "fan": "FI-SI", "psu": "FI-AE"}
    h = _nach_id(RepairTask, st)
    assert h["give"]["done"] and h["disk"]["done"]
    assert not h["fan"]["done"] and not h["maintenance"]["done"]


def test_alarm_hints_fit_the_round_and_know_what_is_done():
    for _ in range(50):
        st = AlarmTask.create({})
        h = _nach_id(AlarmTask, st)
        cut_slot = AlarmTask._cut_index(st["burning_slot"] - 1) + 1
        assert f"Stelle {cut_slot}" in h["cable"]["text"]
        order = list(reversed(st["color_order"])) if st["led"] == "blinkt" else st["color_order"]
        assert " → ".join(order) in h["order"]["text"]
        assert AlarmTask.SYMBOL_NAMES[st["solution"][0]] in h["symbols"]["text"]
        if st["scratched"]:
            assert AlarmTask.SYMBOL_NAMES[st["broken_symbol"]] in h["scratch"]["text"]
        else:
            assert "kein" in h["scratch"]["text"].lower()
        assert not any(x["done"] for x in h.values())

        st["switch_ok"] = True
        h = _nach_id(AlarmTask, st)
        assert h["cable"]["done"] and not h["order"]["done"]
        st["cmd_ok"] = True
        assert all(x["done"] for x in AlarmTask.hints(st))


def test_fire_hints_fit_the_round_and_know_what_is_done():
    for _ in range(50):
        st = FireProtocolTask.create({})
        h = _nach_id(FireProtocolTask, st)
        probe = next(e for e in st["log"] if e["test"])
        assert probe["time"] in h["probe"]["text"] and probe["rack"] in h["probe"]["text"]
        assert " → ".join(s["rack"] for s in st["sequence"]) in h["order"]["text"]
        assert "CO2" in h["power"]["text"]
        for s in st["sequence"]:
            assert f"{s['rack']}: {s['agent']}" in h["agents"]["text"]
        assert "3" in h["release"]["text"]

        st["p1_done"] = True
        st["step"] = len(st["sequence"])
        done = {i for i, x in _nach_id(FireProtocolTask, st).items() if x["done"]}
        assert done == {"probe", "order", "power", "agents"}       # nur die Freigabe bleibt


def test_fire_power_hint_is_done_once_that_rack_is_extinguished():
    for _ in range(50):
        st = FireProtocolTask.create({})
        racks = {r["rack"]: r for r in st["racks"]}
        idx = next(i for i, s in enumerate(st["sequence"])
                   if racks[s["rack"]]["power"] and racks[s["rack"]]["material"] in ("PAPIER", "KABEL"))
        st["step"] = idx
        assert not _nach_id(FireProtocolTask, st)["power"]["done"]
        st["step"] = idx + 1
        assert _nach_id(FireProtocolTask, st)["power"]["done"]


def test_rescue_hints_fit_the_round_and_know_what_is_done():
    """feat/leichter-datenrettung: Themen Platte, Login, Umrechnen, Buchstabe, Schlüssel, Entschlüsseln."""
    for _ in range(50):
        st = DataRescueTask.create({})
        h = _nach_id(DataRescueTask, st)
        assert list(h) == ["disk", "login", "convert", "ascii", "key", "decrypt"]
        assert st["serial"] in h["disk"]["text"]
        assert f"0x{ord(st['login'][0]):02X}" in h["login"]["text"] and f"= {st['login'][0]}" in h["login"]["text"]
        assert "64" in h["convert"]["text"] and str(ord(st["cipher"][0])) in h["convert"]["text"]
        assert f"{ord(st['cipher'][0])} = {st['cipher'][0]}" in h["ascii"]["text"]
        assert f"k = {st['k']}" in h["key"]["text"] and f"Nr. {st['key_nr']}" in h["key"]["text"]
        assert st["cipher"][0] in h["decrypt"]["text"] and st["word"][0] in h["decrypt"]["text"]

        st["mounted"] = True
        st["logged_in"] = True
        st["key_set"] = True
        done = {i for i, x in _nach_id(DataRescueTask, st).items() if x["done"]}
        assert done == {"disk", "login", "key"}


# ------------------------------------------------------------------ Abreißen über das DataCenter
def test_snapshot_lists_topics_but_no_texts_before_opening(dc):
    hints = _hints(dc)
    assert hints["total"] == 4 and hints["cost"] == HINT_COST and hints["opened"] == []
    assert _ids(hints["available"]) == ["cable", "order", "symbols", "scratch"]
    assert all(set(h) == {"id", "label"} for h in hints["available"])


def test_host_tears_off_any_topic_and_pays_for_it(dc):
    texte = _nach_id(AlarmTask, dc.current_task()["state"])
    assert dc.open_hint("symbols")["result"] == "opened"
    hints = _hints(dc)
    assert hints["opened"] == [{"id": "symbols", "label": texte["symbols"]["label"], "text": texte["symbols"]["text"]}]
    assert "symbols" not in _ids(hints["available"])
    assert dc.snapshot()["hint_penalty"] == HINT_COST


def test_topics_already_solved_disappear_from_the_pad(dc):
    st = dc.current_task()["state"]
    assert _eingabe(dc, V, "main_switch", st["target_symbol"])["result"] == "correct"
    assert "cable" not in _ids(_hints(dc)["available"])
    assert dc.open_hint("cable")["result"] == "error"
    assert dc.snapshot()["hint_penalty"] == 0


def test_opened_hint_stays_visible_when_its_step_is_done(dc):
    dc.open_hint("cable")
    st = dc.current_task()["state"]
    _eingabe(dc, V, "main_switch", st["target_symbol"])
    assert _ids(_hints(dc)["opened"]) == ["cable"]


def test_user_scenario_key_without_the_earlier_hints(dc):
    """Aufgabe 3: Platte drin, angemeldet, Team hängt am Schlüssel → direkt diese Hilfe."""
    dc.redis.r.hset(dc._key, "dev_mode", "1")
    dc.skip_task()
    dc.skip_task()
    dc.redis.r.hset(dc._key, "dev_mode", "0")
    st = dc.current_task()["state"]
    _eingabe(dc, R, "mount_disk", st["serial"])
    dc.process_input(V, {"action_type": "text_input", "target": "terminal_login", "value": st["login"]})

    assert _ids(_hints(dc)["available"]) == ["convert", "ascii", "key", "decrypt"]
    assert dc.open_hint("key")["result"] == "opened"
    assert f"k = {st['k']}" in _hints(dc)["opened"][0]["text"]
    assert dc.snapshot()["hint_penalty"] == HINT_COST


def test_unknown_twice_or_missing_topic_is_refused(dc):
    assert dc.open_hint("gibtsnicht")["result"] == "error"
    assert dc.open_hint(None)["result"] == "error"
    assert dc.open_hint("order")["result"] == "opened"
    assert dc.open_hint("order")["result"] == "error"
    assert dc.snapshot()["hint_penalty"] == HINT_COST


def test_score_shown_is_reduced_by_the_hints(dc):
    vorher = dc.snapshot()["score"]
    dc.open_hint("order")
    assert dc.snapshot()["score"] == vorher - HINT_COST


def test_score_never_shows_negative(dc):
    dc.redis.r.hset(dc._key, "health", 0)
    dc.open_hint("order")
    assert dc.snapshot()["score"] == 0


def test_hints_are_free_in_dev_mode(dc):
    dc.redis.r.hset(dc._key, "dev_mode", "1")
    assert dc.open_hint("cable")["result"] == "opened"
    assert len(_hints(dc)["opened"]) == 1
    assert dc.snapshot()["hint_penalty"] == 0


def test_next_task_has_its_own_topics_but_keeps_the_penalty(dc):
    dc.open_hint("cable")
    dc.redis.r.hset(dc._key, "dev_mode", "1")
    dc.skip_task()
    hints = _hints(dc)
    assert hints["total"] == 5 and hints["opened"] == []
    assert _ids(hints["available"]) == ["probe", "order", "power", "agents", "release"]
    assert dc.snapshot()["hint_penalty"] == HINT_COST


def test_finale_offers_its_hints(dc):
    dc.redis.r.hset(dc._key, "dev_mode", "1")
    for _ in range(3):
        dc.skip_task()
    dc.redis.r.hset(dc._key, "dev_mode", "0")
    assert dc.current_task()["kind"] == "repair"
    assert _hints(dc)["total"] == 6
    assert dc.open_hint("cable")["result"] == "error"            # Thema einer anderen Aufgabe
    assert dc.open_hint("maintenance")["result"] == "opened"
    assert dc.snapshot()["hint_penalty"] == HINT_COST


def test_no_hints_when_game_is_not_running(dc):
    dc.finish()
    assert dc.open_hint("cable")["result"] == "error"


def test_new_game_resets_the_penalty(dc):
    dc.open_hint("cable")
    dc.start()
    assert dc.snapshot()["hint_penalty"] == 0


def test_tick_payload_carries_the_hints(dc):
    dc.open_hint("order")
    payload = tick_payload(dc.snapshot())
    assert payload["hints"]["total"] == 4
    assert _ids(payload["hints"]["opened"]) == ["order"]
    assert len(payload["hints"]["available"]) == 3


# ------------------------------------------------------------------ nur für die gemeinte Aufgabe (fix/kleinkram)
def test_hints_carry_the_task_id(dc):
    assert _hints(dc)["task_id"] == dc.current_task()["task_id"]


def test_hint_for_an_old_task_is_refused(dc):
    """Host klickt bei Aufgabe 1, genau als das Team sie löst: der Zettel darf nicht
    bei Aufgabe 2 abgerissen werden (dort gibt es auch ein Thema „order“)."""
    alt = dc.current_task()["task_id"]
    dc.redis.r.hset(dc._key, "dev_mode", "1")
    dc.skip_task()
    dc.redis.r.hset(dc._key, "dev_mode", "0")
    res = dc.open_hint("order", task_id=alt)
    assert res["result"] == "error"
    assert _hints(dc)["opened"] == []
    assert dc.snapshot()["hint_penalty"] == 0


def test_hint_with_the_current_task_id_works(dc):
    assert dc.open_hint("order", task_id=dc.current_task()["task_id"])["result"] == "opened"
