"""Task 2 – Löschprotokoll (kind='fire_protocol')."""
import json
import pytest
import fakeredis
from unittest.mock import patch

from backend.dataCenter import DataCenter
from backend.playableObject import *  # noqa
from backend.playableObject import ROLE_M, ROLE_P1, ROLE_P2

GAME = "t2_session"
MASTER_NAME = "Anna"
P1_NAME = "Ben"
P2_NAME = "Celim"


@pytest.fixture
def dc():
    fake = fakeredis.FakeStrictRedis()
    fake.flushall()
    with patch("backend.redis_handler.redis.Redis", return_value=fake):
        center = DataCenter(game_id=GAME)
        for name, role in ((MASTER_NAME, ROLE_M), (P1_NAME, ROLE_P1), (P2_NAME, ROLE_P2)):
            center.redis.r.hset(
                center.redis._k_players(GAME),
                name,
                json.dumps({"name": name, "role": role}),
            )
        center.start()
        center.new_task("fire_protocol")
        yield center


def _press(dc, name, target, value):
    return dc.process_input(name, {"action_type": "button_press", "target": target, "value": value})


def _text(dc, name, target, value):
    return dc.process_input(name, {"action_type": "text_input", "target": target, "value": value})


def _state(dc):
    return dc.current_task()["state"]


def _view(dc, role):
    return dc.snapshot()["tasks"][0]["views"][role]


def _erwartetes_pw(st):
    alle = st["fragments"] + [st["last_fragment"]]
    return "".join(alle[i] for i in st["order"])


def test_new_task_is_fire_protocol_with_views(dc):
    task = dc.current_task()
    assert task["kind"] == "fire_protocol"
    views = dc.snapshot()["tasks"][0]["views"]
    assert set(views) >= {ROLE_M, ROLE_P1, ROLE_P2}


def test_master_sees_sequence_and_order(dc):
    st = _state(dc)
    master = _view(dc, ROLE_M)
    assert master["sequence"] == st["sequence"]
    assert master["order"] == st["order"]


def test_p1_sees_options_but_not_solution(dc):
    p1 = _view(dc, ROLE_P1)
    assert "valves" in p1 and "colors" in p1
    assert "sequence" not in p1
    assert p1["step"] == 0
    assert p1["last_fragment"] is None


def test_p2_sees_fragments_but_not_last_one(dc):
    p2 = _view(dc, ROLE_P2)
    assert p2["fragments"] == _state(dc)["fragments"]
    assert p2["last_fragment"] is None


def test_p1_must_submit_all_three_steps(dc):
    st = _state(dc)
    task_id = dc.current_task()["task_id"]

    for step in st["sequence"]:
        res = _press(dc, P1_NAME, "valve_action", f"{step['valve']}:{step['color']}")
        assert res["result"] == "correct"

    assert dc.current_task()["task_id"] == task_id
    assert _state(dc)["p1_done"] is True
    assert _view(dc, ROLE_P1)["last_fragment"] == st["last_fragment"]


def test_p1_wrong_step_costs_health(dc):
    res = _press(dc, P1_NAME, "valve_action", "V-99:lila")
    assert res["result"] == "wrong"
    assert dc.health == 240


def test_full_flow_solves_and_heals(dc):
    st = _state(dc)
    task_id = dc.current_task()["task_id"]
    dc.redis.r.hset(dc.redis._k_state(GAME), "health", 100)
    dc.redis.r.hset(dc.redis._k_state(GAME), "time_left", 100)

    for step in st["sequence"]:
        _press(dc, P1_NAME, "valve_action", f"{step['valve']}:{step['color']}")

    res = _text(dc, P2_NAME, "release_pw", _erwartetes_pw(st))

    assert res["result"] == "correct"
    assert dc.health == 115
    assert dc.current_task()["task_id"] != task_id
    assert dc.score >= 100


def test_p2_cannot_submit_before_p1_done(dc):
    st = _state(dc)
    res = _text(dc, P2_NAME, "release_pw", _erwartetes_pw(st))
    assert res["result"] == "ignored"


def test_wrong_pw_costs_health(dc):
    st = _state(dc)
    for step in st["sequence"]:
        _press(dc, P1_NAME, "valve_action", f"{step['valve']}:{step['color']}")
    res = _text(dc, P2_NAME, "release_pw", "FALSCH")
    assert res["result"] == "wrong"
    assert dc.health == 240


def test_master_cannot_operate(dc):
    st = _state(dc)
    step = st["sequence"][0]
    assert _press(dc, MASTER_NAME, "valve_action", f"{step['valve']}:{step['color']}")["result"] == "ignored"
    assert _text(dc, MASTER_NAME, "release_pw", "x")["result"] == "ignored"


def test_wrong_role_cannot_operate(dc):
    st = _state(dc)
    step = st["sequence"][0]
    assert _press(dc, P2_NAME, "valve_action", f"{step['valve']}:{step['color']}")["result"] == "ignored"
    assert _text(dc, P1_NAME, "release_pw", "x")["result"] == "ignored"