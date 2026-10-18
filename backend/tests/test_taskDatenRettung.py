"""
Task 3 – Datenrettung (kind="data_rescue").

Vertrag (playableObject.DataRescueTask):
  MASTER  sieht Status (GESPERRT / FREIGESCHALTET)
  FI-SI   bekommt ASCII-Codes, tippt das Wort (target=ascii_answer)
  FI-AE   bekommt Binär-Codes, tippt Dezimalzahlen (target=binary_answer)
  Beide freigeschaltet → sync_button innerhalb SYNC_WINDOW → gelöst
"""
import json
import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter, TASK_MULTIPLIER
from backend.playableObject import ROLE_M, ROLE_P1, ROLE_P2

GAME = "t3_session"
MASTER_NAME = "Anna"
P1_NAME = "Ben"
P2_NAME = "Celim"


@pytest.fixture
def dc():
    fake = fakeredis.FakeStrictRedis()
    fake.flushall()
    with patch("backend.redis_handler.redis.Redis", return_value=fake):
        center = DataCenter(game_id=GAME)
        for name, role in (
            (MASTER_NAME, ROLE_M),
            (P1_NAME, ROLE_P1),
            (P2_NAME, ROLE_P2),
        ):
            center.redis.r.hset(
                center.redis._k_players(GAME),
                name,
                json.dumps({"name": name, "role": role}),
            )
        center.start()
        center.new_task("data_rescue")
        yield center


def _press(dc, name, target, value):
    return dc.process_input(name, {
        "action_type": "button_press",
        "target": target,
        "value": value,
    })


def _state(dc):
    return dc.current_task()["state"]


def _view(dc, role):
    return dc.snapshot()["tasks"][0]["views"][role]


def test_new_task_is_data_rescue_with_views(dc):
    task = dc.current_task()
    assert task["kind"] == "data_rescue"
    views = dc.snapshot()["tasks"][0]["views"]
    assert set(views) >= {ROLE_M, ROLE_P1, ROLE_P2}


def test_master_sees_status_not_solutions(dc):
    master = _view(dc, ROLE_M)
    assert "p1_status" in master
    assert "p2_status" in master
    assert master["p1_status"] == "GESPERRT"
    st = _state(dc)
    assert st["p1_word"] not in json.dumps(master)


def test_p1_sees_ascii_codes_not_binary(dc):
    st = _state(dc)
    p1 = _view(dc, ROLE_P1)
    assert p1["ascii_codes"] == st["p1_codes"]
    assert "binary_codes" not in p1
    assert p1["button_unlocked"] is False


def test_p2_sees_binary_codes_not_ascii(dc):
    st = _state(dc)
    p2 = _view(dc, ROLE_P2)
    assert p2["binary_codes"] == st["p2_binary"]
    assert "ascii_codes" not in p2
    assert p2["button_unlocked"] is False


def test_nobody_sees_solutions_in_views(dc):
    st = _state(dc)
    for role in (ROLE_M, ROLE_P1, ROLE_P2):
        blob = json.dumps(_view(dc, role))
        assert st["p1_word"] not in blob


def test_correct_ascii_unlocks_button_and_keeps_task(dc):
    st = _state(dc)
    task_id = dc.current_task()["task_id"]

    res = _press(dc, P1_NAME, "ascii_answer", st["p1_word"])

    assert res["result"] == "correct"
    assert dc.current_task()["task_id"] == task_id
    assert dc.health == 300
    assert _state(dc)["p1_unlocked"] is True
    assert _view(dc, ROLE_P1)["button_unlocked"] is True
    assert _view(dc, ROLE_M)["p1_status"] == "FREIGESCHALTET"


def test_correct_binary_unlocks_button_and_keeps_task(dc):
    st = _state(dc)
    task_id = dc.current_task()["task_id"]
    ziel = " ".join(str(v) for v in st["p2_values"])

    res = _press(dc, P2_NAME, "binary_answer", ziel)

    assert res["result"] == "correct"
    assert dc.current_task()["task_id"] == task_id
    assert _state(dc)["p2_unlocked"] is True
    assert _view(dc, ROLE_P2)["button_unlocked"] is True


def test_wrong_ascii_costs_health(dc):
    res = _press(dc, P1_NAME, "ascii_answer", "FALSCH")
    assert res["result"] == "wrong"
    assert dc.health == 240


def test_wrong_binary_costs_health(dc):
    res = _press(dc, P2_NAME, "binary_answer", "0 0")
    assert res["result"] == "wrong"
    assert dc.health == 240


def test_button_locked_until_riddle_solved(dc):
    res = _press(dc, P1_NAME, "sync_button", "press")
    assert res["result"] == "ignored"
    assert dc.health == 300


def test_one_button_alone_does_not_solve(dc):
    st = _state(dc)
    task_id = dc.current_task()["task_id"]
    _press(dc, P1_NAME, "ascii_answer", st["p1_word"])
    _press(dc, P2_NAME, "binary_answer", " ".join(str(v) for v in st["p2_values"]))

    res = _press(dc, P1_NAME, "sync_button", "press")
    assert res["result"] == "correct"
    assert dc.current_task()["task_id"] == task_id


def test_both_buttons_within_window_solve(dc):
    st = _state(dc)
    task_id = dc.current_task()["task_id"]
    dc.redis.r.hset(dc.redis._k_state(GAME), "health", 100)
    dc.redis.r.hset(dc.redis._k_state(GAME), "time_left", 100)

    _press(dc, P1_NAME, "ascii_answer", st["p1_word"])
    _press(dc, P2_NAME, "binary_answer", " ".join(str(v) for v in st["p2_values"]))

    _press(dc, P1_NAME, "sync_button", "press")
    res = _press(dc, P2_NAME, "sync_button", "press")

    assert res["result"] == "correct"
    assert dc.health == 115
    assert dc.current_task()["task_id"] != task_id
    assert dc.score == 100 * TASK_MULTIPLIER["data_rescue"]


def test_same_player_pressing_twice_does_not_solve(dc):
    st = _state(dc)
    task_id = dc.current_task()["task_id"]
    _press(dc, P1_NAME, "ascii_answer", st["p1_word"])
    _press(dc, P2_NAME, "binary_answer", " ".join(str(v) for v in st["p2_values"]))

    _press(dc, P1_NAME, "sync_button", "press")
    _press(dc, P1_NAME, "sync_button", "press")

    assert dc.current_task()["task_id"] == task_id


def test_wrong_role_cannot_answer_ascii(dc):
    st = _state(dc)
    assert _press(dc, P2_NAME, "ascii_answer", st["p1_word"])["result"] == "ignored"
    assert _press(dc, MASTER_NAME, "ascii_answer", st["p1_word"])["result"] == "ignored"
    assert dc.health == 300


def test_wrong_role_cannot_answer_binary(dc):
    st = _state(dc)
    ziel = " ".join(str(v) for v in st["p2_values"])
    assert _press(dc, P1_NAME, "binary_answer", ziel)["result"] == "ignored"
    assert _press(dc, MASTER_NAME, "binary_answer", ziel)["result"] == "ignored"
    assert dc.health == 300


def test_master_cannot_press_sync(dc):
    st = _state(dc)
    _press(dc, P1_NAME, "ascii_answer", st["p1_word"])
    _press(dc, P2_NAME, "binary_answer", " ".join(str(v) for v in st["p2_values"]))
    assert _press(dc, MASTER_NAME, "sync_button", "press")["result"] == "ignored"


def test_wrong_attempts_do_not_block_rescue(dc):
    st = _state(dc)
    task_id = dc.current_task()["task_id"]

    _press(dc, P1_NAME, "ascii_answer", "FALSCH")
    _press(dc, P2_NAME, "binary_answer", "0 0")
    _press(dc, P1_NAME, "ascii_answer", st["p1_word"])
    _press(dc, P2_NAME, "binary_answer", " ".join(str(v) for v in st["p2_values"]))
    _press(dc, P1_NAME, "sync_button", "press")
    res = _press(dc, P2_NAME, "sync_button", "press")

    assert res["result"] == "correct"
    assert dc.current_task()["task_id"] != task_id