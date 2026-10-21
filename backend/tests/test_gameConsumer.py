"""
WebSocket-Consumer-Tests: Nachrichten im JSON-Vertrag (event + payload).
Deckt alle Branches im GameConsumer ab (Ziel: 100% Zeilenabdeckung).
"""
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis
import pytest
from channels.testing import WebsocketCommunicator

from backend.GameConsumer import GameConsumer
from backend.gameLoop import games, GameLoop
from backend.playableObject import AlarmTask, ROLE_M, ROLE_P1, ROLE_P2
from backend.redis_handler import DEFAULT_TIME, ROLES, RedisHandler


# ---------------------------------------------------------------- Fixtures
@pytest.fixture(autouse=True)
def clean_games():
    games.clear()
    yield
    games.clear()


@pytest.fixture
def env():
    fake = fakeredis.FakeStrictRedis()
    fake.flushall()
    with patch("backend.redis_handler.redis.Redis", return_value=fake):
        yield fake


# ---------------------------------------------------------------- Helfer
async def verbinden(game_id="test_game"):
    # Wie im echten Ablauf: der Host hat die Sitzung vorher per create-game angelegt
    handler = RedisHandler()
    if not handler.r.exists(handler._k_state(game_id)):
        handler.create_game(game_id)
    return await verbinden_roh(game_id)


async def verbinden_roh(game_id):
    """Verbinden, ohne die Sitzung vorher anzulegen."""
    comm = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/game/{game_id}/")
    comm.scope["url_route"] = {"kwargs": {"game_id": game_id}}
    akzeptiert, _ = await comm.connect()
    return comm, akzeptiert


async def verbinden_ohne_initial(game_id):
    comm, akzeptiert = await verbinden(game_id)
    assert akzeptiert is True
    await comm.receive_json_from()
    return comm


async def registrieren(comm, name):
    await comm.send_json_to({"event": "player_register", "payload": {"player_name": name}})


async def waehle_rolle(comm, role):
    await comm.send_json_to({"event": "choose_role", "payload": {"role": role}})


async def recv_until(comm, event, pred=lambda p: True, timeout=3):
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise asyncio.TimeoutError(f"{event} nicht empfangen")
        msg = await comm.receive_json_from(timeout=remaining)
        if msg["event"] == event and pred(msg["payload"]):
            return msg


async def spieler(game_id, *namen_rollen):
    """Spieler registrieren und Rollen wählen. Rückgabe: Liste von comm."""
    out = []
    for name, role in namen_rollen:
        comm = await verbinden_ohne_initial(game_id)
        await registrieren(comm, name)
        await waehle_rolle(comm, role)
        await recv_until(comm, "role_assigned", lambda p: p["role"] == role)
        out.append(comm)
    return out


async def beenden(*comms, game_ids=()):
    for gid in game_ids:
        if gid in games:
            await games[gid].stop_game()
    for c in comms:
        await c.disconnect()


def state_key(game_id):
    return f"game:{game_id}:state"


def set_button_task(env, game_id, task_id="task-btn"):
    env.hset(state_key(game_id), "task", json.dumps({
        "task_id": task_id,
        "kind": "button",
        "instruction": "Test",
        "assigned_to_player": None,
        "state": {"target": "reactor_vent", "value": "open"},
    }))


# ---------------------------------------------------------------- Connect / Ping
@pytest.mark.asyncio
async def test_connect_sends_lobby_update(env):
    comm, ok = await verbinden("cov_connect")
    assert ok is True
    msg = await comm.receive_json_from()
    assert msg["event"] == "lobby_update"
    assert msg["payload"]["status"] == "waiting"
    await comm.disconnect()


@pytest.mark.asyncio
async def test_connect_unknown_game_is_rejected(env):
    """Vertippte Sitzungs-ID: Fehler mit code, Verbindung zu, keine Geister-Lobby."""
    comm, ok = await verbinden_roh("gibtsnicht")
    assert ok is True  # erst annehmen, damit der Browser die Fehlermeldung lesen kann
    msg = await comm.receive_json_from()
    assert msg["event"] == "error"
    assert msg["payload"]["code"] == "unknown_game"
    assert (await comm.receive_output())["code"] == 4404
    assert not env.exists(state_key("gibtsnicht"))


@pytest.mark.asyncio
async def test_unknown_game_register_creates_nothing(env):
    """Auch ein player_register, das sich mit dem Schließen kreuzt, legt keine Sitzung an."""
    comm, _ = await verbinden_roh("gibtsnicht2")
    await comm.receive_json_from()   # error
    await comm.receive_output()      # close
    await registrieren(comm, "A")
    await comm.receive_nothing(timeout=0.2)
    assert not env.exists(state_key("gibtsnicht2"))
    await comm.disconnect()


@pytest.mark.asyncio
async def test_connect_while_running_sends_tick(env):
    """Cover-Zeilen 24-27: späte Verbindung bei laufendem Spiel."""
    a = (await spieler("cov_late", ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE")))[0]
    try:
        # Spiel starten
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")

        late, ok = await verbinden("cov_late")
        assert ok is True
        lobby = await late.receive_json_from()
        assert lobby["event"] == "lobby_update"
        assert lobby["payload"]["status"] == "running"
        tick = await recv_until(late, "game_tick")
        assert {"health", "time_left", "tasks"} <= set(tick["payload"])
        await late.disconnect()
    finally:
        await beenden(a, game_ids=["cov_late"])


@pytest.mark.asyncio
async def test_ping_pong(env):
    comm = await verbinden_ohne_initial("cov_ping")
    await comm.send_json_to({"event": "ping", "payload": {}})
    assert (await comm.receive_json_from())["event"] == "pong"
    await comm.disconnect()


# ---------------------------------------------------------------- Fehlerhafte Payloads
@pytest.mark.asyncio
async def test_invalid_json(env):
    comm = await verbinden_ohne_initial("cov_ij")
    await comm.send_to(text_data="{kein json!")
    assert (await comm.receive_json_from())["event"] == "error"
    await comm.disconnect()


@pytest.mark.asyncio
async def test_json_not_object(env):
    comm = await verbinden_ohne_initial("cov_jno")
    await comm.send_to(text_data="[1,2,3]")
    assert (await comm.receive_json_from())["event"] == "error"
    await comm.disconnect()


@pytest.mark.asyncio
async def test_payload_not_object(env):
    """Cover-Zeile 65: payload kein dict."""
    comm = await verbinden_ohne_initial("cov_pno")
    await comm.send_json_to({"event": "ping", "payload": "kein-objekt"})
    msg = await comm.receive_json_from()
    assert msg["event"] == "error"
    assert "payload" in msg["payload"]["message"]
    await comm.disconnect()


@pytest.mark.asyncio
async def test_unknown_event(env):
    """Cover-Zeile 67: else-Zweig."""
    comm = await verbinden_ohne_initial("cov_unk")
    await comm.send_json_to({"event": "gibtsnicht", "payload": {}})
    assert (await comm.receive_json_from())["event"] == "error"
    await comm.disconnect()


# ---------------------------------------------------------------- host_register (Zeile 76-81)
@pytest.mark.asyncio
async def test_host_register(env):
    comm = await verbinden_ohne_initial("cov_host")
    await comm.send_json_to({"event": "host_register", "payload": {}})
    msg = await comm.receive_json_from()
    assert msg["event"] == "lobby_update"
    assert msg["payload"]["players"] == []
    await comm.disconnect()


# ---------------------------------------------------------------- player_register
@pytest.mark.asyncio
async def test_register_without_name(env):
    """Cover-Zeile 93-94: fehlender Name."""
    comm = await verbinden_ohne_initial("cov_noname")
    await comm.send_json_to({"event": "player_register", "payload": {}})
    msg = await comm.receive_json_from()
    assert msg["event"] == "error"
    await comm.disconnect()


@pytest.mark.asyncio
async def test_register_error_when_game_running(env):
    """Cover-Zeile 94: register_player liefert error."""
    (a,) = await spieler("cov_reg_err", ("A", "MASTER"))
    env.hset(state_key("cov_reg_err"), "status", "running")

    try:
        comm = await verbinden_ohne_initial("cov_reg_err")
        await registrieren(comm, "B")
        msg = await recv_until(comm, "error")
        assert "läuft" in msg["payload"]["message"]
        await comm.disconnect()
    finally:
        await beenden(a)


@pytest.mark.skip(reason="veraltet: role_assigned kommt erst nach choose_role (bzw. beim Reconnect), nicht beim Registrieren (TRIAGE.md)")
@pytest.mark.asyncio
async def test_register_assigns_role_and_broadcasts(env):
    """Cover-Zeile 101: role_assigned wird gesendet."""
    comm = await verbinden_ohne_initial("cov_reg_ok")
    await registrieren(comm, "A")
    msg = await recv_until(comm, "role_assigned")
    assert msg["payload"]["role"] is None
    await comm.disconnect()


@pytest.mark.asyncio
async def test_reconnect_with_role_sends_role_assigned(env):
    """Cover-Zeile 112-116: reconnect liefert direkt role_assigned."""
    a = await verbinden_ohne_initial("cov_reconnect")
    await registrieren(a, "A")
    await waehle_rolle(a, "MASTER")
    await recv_until(a, "role_assigned", lambda p: p["role"] == "MASTER")
    await a.disconnect()

    # Neue Verbindung, gleicher Name
    b = await verbinden_ohne_initial("cov_reconnect")
    await registrieren(b, "A")
    msg = await recv_until(b, "role_assigned", lambda p: p["role"] == "MASTER")
    assert msg["payload"]["role"] == "MASTER"
    await b.disconnect()


@pytest.mark.asyncio
async def test_disconnect_without_role_frees_slot(env):
    """Wer ohne Rolle geht, blockiert keinen der 3 Plätze."""
    gid = "cov_leave_free"
    a = await verbinden_ohne_initial(gid)
    b = await verbinden_ohne_initial(gid)
    c = await verbinden_ohne_initial(gid)
    for comm, name in ((a, "A"), (b, "B"), (c, "C")):
        await registrieren(comm, name)
        await recv_until(comm, "lobby_update", lambda p, n=name: any(x["name"] == n for x in p["players"]))

    await a.disconnect()
    msg = await recv_until(b, "lobby_update", lambda p: len(p["players"]) == 2)
    assert [p["name"] for p in msg["payload"]["players"]] == ["B", "C"]

    d = await verbinden_ohne_initial(gid)
    await registrieren(d, "D")
    await recv_until(d, "lobby_update", lambda p: any(x["name"] == "D" for x in p["players"]))
    await beenden(b, c, d)


@pytest.mark.asyncio
async def test_disconnect_with_role_keeps_slot(env):
    (a, b) = await spieler("cov_leave_role", ("A", "MASTER"), ("B", "FI-SI"))
    await a.disconnect()
    await b.send_json_to({"event": "host_register", "payload": {}})
    msg = await recv_until(b, "lobby_update")
    assert {"name": "A", "role": "MASTER", "ready": False} in msg["payload"]["players"]
    await b.disconnect()


@pytest.mark.asyncio
async def test_old_disconnect_does_not_remove_reloaded_player(env):
    """Reload: neue Verbindung meldet sich an, bevor die alte als getrennt gilt."""
    gid = "cov_leave_reload"
    alt = await verbinden_ohne_initial(gid)
    await registrieren(alt, "A")
    await recv_until(alt, "lobby_update", lambda p: len(p["players"]) == 1)

    neu = await verbinden_ohne_initial(gid)
    await registrieren(neu, "A")
    await recv_until(neu, "lobby_update", lambda p: len(p["players"]) == 1)
    await alt.disconnect()

    await waehle_rolle(neu, "MASTER")
    msg = await recv_until(neu, "role_assigned")
    assert msg["payload"]["role"] == "MASTER"
    await neu.disconnect()


# ---------------------------------------------------------------- choose_role (124-129)
@pytest.mark.asyncio
async def test_choose_role_without_register(env):
    """Cover-Zeile 124-125: player_name None."""
    comm = await verbinden_ohne_initial("cov_cr_noreg")
    await waehle_rolle(comm, "MASTER")
    msg = await recv_until(comm, "error")
    assert "registered" in msg["payload"]["message"]
    await comm.disconnect()


@pytest.mark.asyncio
async def test_choose_role_without_role_field(env):
    """Cover-Zeile 128-129: role fehlt."""
    comm = await verbinden_ohne_initial("cov_cr_norole")
    await registrieren(comm, "A")
    await comm.send_json_to({"event": "choose_role", "payload": {}})
    msg = await recv_until(comm, "error")
    assert "role" in msg["payload"]["message"]
    await comm.disconnect()


@pytest.mark.asyncio
async def test_choose_role_error_from_redis(env):
    """choose_role liefert error (z. B. gleiche Rolle doppelt)."""
    a = await verbinden_ohne_initial("cov_cr_dup")
    b = await verbinden_ohne_initial("cov_cr_dup")
    await registrieren(a, "A")
    await registrieren(b, "B")
    await waehle_rolle(a, "MASTER")
    await recv_until(a, "role_assigned")
    await waehle_rolle(b, "MASTER")
    msg = await recv_until(b, "error")
    assert "vergeben" in msg["payload"]["message"]
    await a.disconnect()
    await b.disconnect()


# ---------------------------------------------------------------- owner_settings
@pytest.mark.asyncio
async def test_owner_settings_valid(env):
    comm = await host_verbinden("cov_os_ok")          # nur der Host darf (fix/kleinkram)
    await comm.send_json_to({"event": "owner_settings", "payload": {"time": 60}})
    msg = await recv_until(comm, "lobby_update")
    assert msg["payload"]["status"] in ("waiting", "ready")
    await comm.disconnect()


@pytest.mark.asyncio
async def test_owner_settings_invalid(env):
    comm = await host_verbinden("cov_os_bad")
    await comm.send_json_to({"event": "owner_settings", "payload": {"time": "abc"}})
    msg = await recv_until(comm, "error")
    assert "Einstellungen" in msg["payload"]["message"]
    await comm.disconnect()


# ---------------------------------------------------------------- reset_game
@pytest.mark.asyncio
@pytest.mark.parametrize("event", ["reset_game", "new_lobby"])
async def test_reset_lobby_clears_players(env, event):
    """Cover-Zeile 76-81: reset_game/new_lobby."""
    (a,) = await spieler(f"cov_{event}", ("A", "MASTER"))
    await a.send_json_to({"event": event, "payload": {}})
    msg = await recv_until(a, "lobby_update", lambda p: p["players"] == [])
    assert msg["payload"]["status"] == "waiting"
    await a.disconnect()


# ---------------------------------------------------------------- start_game
@pytest.mark.asyncio
async def test_start_game_incomplete_lobby(env):
    """Cover-Zeile 209-216: nicht bereit."""
    (a,) = await spieler("cov_start_inc", ("A", "MASTER"))
    await a.send_json_to({"event": "start_game", "payload": {}})
    msg = await recv_until(a, "error")
    assert "3 Spieler" in msg["payload"]["message"]
    await a.disconnect()


@pytest.mark.asyncio
async def test_start_game_success_and_second_fails(env):
    (a, b, c) = await spieler("cov_start_ok",
                              ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")

        await a.send_json_to({"event": "start_game", "payload": {}})
        msg = await recv_until(a, "error")
        assert msg["payload"]["code"] == "start_failed"
        assert "läuft bereits" in msg["payload"]["message"]
    finally:
        await beenden(a, b, c, game_ids=["cov_start_ok"])


# ---------------------------------------------------------------- player_input
@pytest.mark.asyncio
async def test_player_input_without_registration(env):
    comm = await verbinden_ohne_initial("cov_pi_noreg")
    await comm.send_json_to({"event": "player_input", "payload": {
        "action_type": "button_press", "target": "x", "value": "y"
    }})
    msg = await recv_until(comm, "error")
    assert "Rolle" in msg["payload"]["message"] or "registered" in msg["payload"]["message"]
    await comm.disconnect()


@pytest.mark.asyncio
async def test_player_input_before_start(env):
    """input_result error bei game not running."""
    (a,) = await spieler("cov_pi_before", ("A", "MASTER"))
    await a.send_json_to({"event": "player_input", "payload": {
        "action_type": "button_press", "target": "x", "value": "y"
    }})
    res = await recv_until(a, "input_result")
    assert res["payload"]["result"] == "error"
    await recv_until(a, "error")
    await a.disconnect()


@pytest.mark.asyncio
async def test_player_input_wrong(env):
    (a, b, c) = await spieler("cov_pi_wrong",
                              ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
        set_button_task(env, "cov_pi_wrong")

        await b.send_json_to({"event": "player_input", "payload": {
            "action_type": "button_press", "target": "nope", "value": "nope"
        }})
        res = await recv_until(b, "input_result")
        assert res["payload"]["result"] == "wrong"
        await recv_until(b, "game_tick", lambda p: p["health"] <= 240)
    finally:
        await beenden(a, b, c, game_ids=["cov_pi_wrong"])


@pytest.mark.asyncio
async def test_player_input_correct(env):
    (a, b, c) = await spieler("cov_pi_correct",
                              ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
        set_button_task(env, "cov_pi_correct")
        env.hset(state_key("cov_pi_correct"), "health", 100)

        await b.send_json_to({"event": "player_input", "payload": {
            "action_type": "button_press", "target": "reactor_vent", "value": "open"
        }})
        res = await recv_until(b, "input_result")
        assert res["payload"]["result"] == "correct"
    finally:
        await beenden(a, b, c, game_ids=["cov_pi_correct"])


@pytest.mark.asyncio
async def test_player_input_ignored(env):
    """input_result 'ignored' wenn Rolle nicht passt."""
    (a, b, c) = await spieler("cov_pi_ignored",
                              ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")

        # AlarmTask: P2 versucht main_switch (nur P1 erlaubt)
        st = AlarmTask.create({})
        env.hset(state_key("cov_pi_ignored"), "task", json.dumps({
            "task_id": "t-x", "kind": "alarm", "instruction": "x",
            "assigned_to_player": None, "state": st,
        }))

        await c.send_json_to({"event": "player_input", "payload": {
            "action_type": "button_press", "target": "main_switch", "value": st["broken_symbol"]
        }})
        res = await recv_until(c, "input_result")
        assert res["payload"]["result"] == "ignored"
    finally:
        await beenden(a, b, c, game_ids=["cov_pi_ignored"])


@pytest.mark.asyncio
async def test_player_input_error_from_datacenter(env):
    """input_result error wenn Payload ungültig."""
    (a, b, c) = await spieler("cov_pi_derr",
                              ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")

        await b.send_json_to({"event": "player_input", "payload": {
            "action_type": "unknown_action", "target": "x", "value": "y"
        }})
        res = await recv_until(b, "input_result")
        assert res["payload"]["result"] == "error"
        await recv_until(b, "error")
    finally:
        await beenden(a, b, c, game_ids=["cov_pi_derr"])


# ---------------------------------------------------------------- _tasks_for_me (219-226)
@pytest.mark.asyncio
async def test_tasks_for_me_filters_views(env):
    """Cover-Zeile 219-226: tasks_for_me liefert 'view' je Rolle, kein 'views'."""
    (a, b, c) = await spieler("cov_tfm",
                              ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")

        st = AlarmTask.create({})
        env.hset(state_key("cov_tfm"), "task", json.dumps({
            "task_id": "t-alarm", "kind": "alarm", "instruction": "x",
            "assigned_to_player": None, "state": st,
        }))

        def ist(p):
            return p["tasks"] and p["tasks"][0]["task_id"] == "t-alarm"

        tick_a = await recv_until(a, "game_tick", ist)
        tick_b = await recv_until(b, "game_tick", ist)
        tick_c = await recv_until(c, "game_tick", ist)

        task_a = tick_a["payload"]["tasks"][0]
        task_b = tick_b["payload"]["tasks"][0]
        task_c = tick_c["payload"]["tasks"][0]

        assert "views" not in task_a and "state" not in task_a
        assert task_a["view"]["type"] == "alarm_leds"
        assert task_b["view"]["type"] == "main_switches"
        assert task_c["view"]["type"] == "code_stickers"
    finally:
        await beenden(a, b, c, game_ids=["cov_tfm"])


# ---------------------------------------------------------------- broadcast-Methoden (238-243)
@pytest.mark.asyncio
async def test_broadcast_lobby_update(env):
    """Cover-Zeile 238-240: lobby_update handler im Consumer."""
    a = await verbinden_ohne_initial("cov_bcast_lobby")
    b = await verbinden_ohne_initial("cov_bcast_lobby")

    # Wenn b joined, soll a das lobby_update bekommen (Broadcast)
    await registrieren(a, "A")
    await recv_until(a, "lobby_update")
    await registrieren(b, "B")
    await recv_until(a, "lobby_update", lambda p: len(p["players"]) == 2)

    await a.disconnect()
    await b.disconnect()


async def game_over_events(comm, dauer):
    """Alle game_over, die in `dauer` Sekunden ankommen."""
    gesehen = []
    deadline = time.monotonic() + dauer
    while time.monotonic() < deadline:
        # receive_nothing statt Timeout: ein Timeout in receive_json_from bricht die App ab
        if await comm.receive_nothing(timeout=0.1):
            continue
        msg = await comm.receive_json_from()
        if msg["event"] == "game_over":
            gesehen.append(msg["payload"]["result"])
    return gesehen


@pytest.mark.asyncio
@pytest.mark.parametrize("ausloeser, erwartet", [
    ("sieg", "victory"),
    ("strafe", "meltdown"),
])
async def test_game_over_by_input_is_sent_only_once(env, ausloeser, erwartet):
    """Spielende durch Eingabe: Consumer meldet es, die Spielschleife darf es nicht nochmal tun."""
    gid = f"cov_over_once_{ausloeser}"
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")

        if ausloeser == "sieg":
            set_button_task(env, gid)
            env.hset(state_key(gid), "solved_count", 3)   # letzte Aufgabe
            payload = {"action_type": "button_press", "target": "reactor_vent", "value": "open"}
        else:
            env.hset(state_key(gid), "health", 10)
            payload = {"action_type": "button_press", "target": "penalty", "value": "wrong"}

        await b.send_json_to({"event": "player_input", "payload": payload})
        # Die Spielschleife prüft jede Sekunde den Status → >2 s warten
        assert await game_over_events(c, 2.5) == [erwartet]
    finally:
        await beenden(a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_broadcast_game_over(env):
    """Cover-Zeile 243: game_over handler im Consumer."""
    (a, b, c) = await spieler("cov_bcast_over",
                              ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
        env.hset(state_key("cov_bcast_over"), "time_left", 1)   # Zeit läuft ab → Leben 0

        for comm in (a, b, c):
            over = await recv_until(comm, "game_over", timeout=5)
            assert over["payload"]["result"] == "meltdown"
            assert "score" in over["payload"]
    finally:
        await beenden(a, b, c, game_ids=["cov_bcast_over"])

# ---------------------------------------------------------------- DEV-Modus
async def host_verbinden(game_id):
    host = await verbinden_ohne_initial(game_id)
    await host.send_json_to({"event": "host_register", "payload": {}})
    await recv_until(host, "lobby_update")
    return host


async def dev_spiel(env, gid, dev=True):
    """Host + 3 Spieler, optional DEV-Modus, Spiel läuft (nach der Einsatzbesprechung)."""
    host = await host_verbinden(gid)
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    if dev:
        await host.send_json_to({"event": "dev_mode", "payload": {"enabled": True}})
        await recv_until(a, "lobby_update", lambda p: p["dev_mode"] is True)
    await a.send_json_to({"event": "start_game", "payload": {}})
    await recv_until(a, "lobby_update", lambda p: p["status"] == "briefing")
    if not dev:   # ohne DEV-Modus wartet der Beamer, bis alle „Bereit“ gedrückt haben
        for comm in (a, b, c):
            await comm.send_json_to({"event": "player_ready", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["all_ready"])
    await host.send_json_to({"event": "start_game", "payload": {}})   # Intro am Beamer fertig
    await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
    return host, a, b, c


@pytest.mark.asyncio
async def test_dev_mode_toggle_only_for_host(env):
    (a,) = await spieler("cov_dev_nohost", ("A", "MASTER"))
    await a.send_json_to({"event": "dev_mode", "payload": {"enabled": True}})
    msg = await recv_until(a, "error")
    assert msg["payload"]["code"] == "dev_denied"
    assert env.hget(state_key("cov_dev_nohost"), "dev_mode") in (None, b"0")
    await a.disconnect()


@pytest.mark.asyncio
async def test_host_toggles_dev_mode_for_everyone(env):
    gid = "cov_dev_toggle"
    host = await host_verbinden(gid)
    (a,) = await spieler(gid, ("A", "MASTER"))

    await host.send_json_to({"event": "dev_mode", "payload": {"enabled": True}})
    msg = await recv_until(a, "lobby_update", lambda p: p["dev_mode"] is True)
    assert msg["payload"]["dev_mode"] is True

    await host.send_json_to({"event": "dev_mode", "payload": {"enabled": False}})
    await recv_until(a, "lobby_update", lambda p: p["dev_mode"] is False)
    await beenden(host, a)


@pytest.mark.asyncio
async def test_dev_mode_needs_boolean(env):
    host = await host_verbinden("cov_dev_bool")
    await host.send_json_to({"event": "dev_mode", "payload": {"enabled": "ja"}})
    msg = await recv_until(host, "error")
    assert msg["payload"]["code"] == "dev_denied"
    await host.disconnect()


@pytest.mark.asyncio
async def test_dev_mode_toggle_rejected_while_running(env):
    gid = "cov_dev_running"
    host, a, b, c = await dev_spiel(env, gid, dev=False)
    try:
        await host.send_json_to({"event": "dev_mode", "payload": {"enabled": True}})
        msg = await recv_until(host, "error")
        assert msg["payload"]["code"] == "dev_denied"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_dev_skip_task_moves_everyone_on(env):
    gid = "cov_dev_skip"
    host, a, b, c = await dev_spiel(env, gid)
    try:
        await host.send_json_to({"event": "dev_skip_task", "payload": {}})
        tick = await recv_until(b, "game_tick", lambda p: p["reboot_digits"][0] is not None)
        assert tick["payload"]["tasks"][0]["view"]["type"] == "valve_panel"   # Aufgabe 2, Vorderseite
        task = json.loads(env.hget(state_key(gid), "task"))
        assert task["kind"] == "fire_protocol"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_dev_skip_task_only_for_host(env):
    gid = "cov_dev_skip_nohost"
    host, a, b, c = await dev_spiel(env, gid)
    try:
        await b.send_json_to({"event": "dev_skip_task", "payload": {}})
        msg = await recv_until(b, "error")
        assert msg["payload"]["code"] == "dev_denied"
        assert json.loads(env.hget(state_key(gid), "task"))["kind"] == "alarm"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_dev_skip_task_needs_dev_mode(env):
    gid = "cov_dev_skip_off"
    host, a, b, c = await dev_spiel(env, gid, dev=False)
    try:
        await host.send_json_to({"event": "dev_skip_task", "payload": {}})
        msg = await recv_until(host, "error")
        assert msg["payload"]["code"] == "dev_denied"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_dev_skip_last_task_wins_once(env):
    gid = "cov_dev_skip_win"
    host, a, b, c = await dev_spiel(env, gid)
    try:
        env.hset(state_key(gid), "solved_count", 3)   # Finale läuft
        await host.send_json_to({"event": "dev_skip_task", "payload": {}})
        assert await game_over_events(c, 2.5) == ["victory"]
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_dev_mode_time_stands_still(env):
    gid = "cov_dev_time"
    host, a, b, c = await dev_spiel(env, gid)
    try:
        t1 = await recv_until(a, "game_tick")
        t2 = await recv_until(a, "game_tick", timeout=3)
        assert t1["payload"]["time_left"] == t2["payload"]["time_left"] == DEFAULT_TIME
        assert t2["payload"]["health"] == 300
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_dev_skip_without_task_is_silent(env):
    """Doppelklick/keine Aufgabe: kein Fehler, nichts passiert."""
    gid = "cov_dev_skip_none"
    host, a, b, c = await dev_spiel(env, gid)
    try:
        env.hdel(state_key(gid), "task")
        await host.send_json_to({"event": "dev_skip_task", "payload": {}})
        await host.send_json_to({"event": "ping", "payload": {}})
        seen = []
        while (msg := await host.receive_json_from())["event"] != "pong":
            seen.append(msg["event"])
        assert "error" not in seen
        assert env.hget(state_key(gid), "solved_count") == b"0"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


# ---------------------------------------------------------------- Leaderboard am Spielende
@pytest.mark.asyncio
async def test_game_over_carries_leaderboard_with_own_rank(env, leaderboard_file):
    gid = "cov_lb"
    (a, b, c) = await spieler(gid, ("Anna", "MASTER"), ("Ben", "FI-SI"), ("Cem", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
        env.hset(state_key(gid), mapping={"health": 10, "score": 333})
        await b.send_json_to({"event": "player_input", "payload": {
            "action_type": "button_press", "target": "penalty", "value": "x"}})

        over = await recv_until(c, "game_over", timeout=5)
        lb = over["payload"]["leaderboard"]
        assert lb["rank"] == 1 and lb["total"] == 1
        assert lb["top"][0]["players"] == ["Anna", "Ben", "Cem"]
        assert lb["top"][0]["score"] == 333
        assert json.loads(leaderboard_file.read_text(encoding="utf-8"))["entries"][0]["score"] == 333
    finally:
        await beenden(a, b, c, game_ids=[gid])


# ---------------------------------------------------------------- Groß-/Kleinschreibung der ID
@pytest.mark.asyncio
async def test_game_id_is_case_insensitive(env):
    """Der Beamer zeigt die ID groß (XVK2), erzeugt wird sie klein: beides muss gehen."""
    RedisHandler().create_game("cov_case")
    comm, ok = await verbinden_roh("COV_CASE")
    assert ok is True
    msg = await comm.receive_json_from()
    assert msg["event"] == "lobby_update"
    await registrieren(comm, "A")
    await recv_until(comm, "lobby_update", lambda p: len(p["players"]) == 1)
    assert env.hexists("game:cov_case:players", "A")
    assert not env.exists("game:COV_CASE:state")
    await comm.disconnect()
# ---------------------------------------------------------------- game_tick vertragskonform
TICK_FELDER = {"health", "max_health", "time_left", "tasks", "reboot_digits", "hints", "parts"}


@pytest.mark.asyncio
async def test_tick_after_player_input_is_complete(env):
    """Auch der Tick direkt nach einer Eingabe hat alle Felder (vorher fehlte reboot_digits)."""
    gid = "cov_tick_input"
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
        set_button_task(env, gid)
        env.hset(state_key(gid), "time_left", 77)   # Loop-Ticks (300→…) davon unterscheiden
        await b.send_json_to({"event": "player_input", "payload": {
            "action_type": "button_press", "target": "reactor_vent", "value": "open"
        }})
        await recv_until(b, "input_result")
        # gelöst: +TIME_BONUS; so unterscheidet sich der Sofort-Tick von den Loop-Ticks (300→…)
        from backend.dataCenter import TIME_BONUS
        tick = await recv_until(b, "game_tick", lambda p: p["time_left"] in (76 + TIME_BONUS, 77 + TIME_BONUS))
        assert set(tick["payload"]) == TICK_FELDER
    finally:
        await beenden(a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_tick_on_late_connect_is_complete_and_has_kind(env):
    gid = "cov_tick_late"
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
        late = await verbinden_ohne_initial(gid)
        tick = await recv_until(late, "game_tick")
        assert set(tick["payload"]) == TICK_FELDER
        assert tick["payload"]["tasks"][0]["kind"] == "alarm"
        await late.disconnect()
    finally:
        await beenden(a, b, c, game_ids=[gid])


# ---------------------------------------------------------------- Hilfe-Notizen (Host)
@pytest.mark.asyncio
async def test_host_tears_off_a_hint_and_everyone_sees_it(env):
    gid = "cov_hint"
    host, a, b, c = await dev_spiel(env, gid, dev=False)
    try:
        await host.send_json_to({"event": "open_hint", "payload": {"id": "order"}})
        tick = await recv_until(b, "game_tick", lambda p: len(p["hints"]["opened"]) == 1)
        hints = tick["payload"]["hints"]
        assert hints["opened"][0]["id"] == "order" and hints["opened"][0]["text"]
        assert [h["id"] for h in hints["available"]] == ["cable", "symbols", "scratch"]
        assert hints["cost"] == 50
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_only_the_host_opens_hints(env):
    gid = "cov_hint_nohost"
    host, a, b, c = await dev_spiel(env, gid, dev=False)
    try:
        await b.send_json_to({"event": "open_hint", "payload": {"id": "order"}})
        msg = await recv_until(b, "error")
        assert msg["payload"]["code"] == "hint_denied"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_same_hint_twice_or_unknown_is_refused(env):
    gid = "cov_hint_twice"
    host, a, b, c = await dev_spiel(env, gid, dev=True)
    try:
        await host.send_json_to({"event": "open_hint", "payload": {"id": "cable"}})
        await recv_until(a, "game_tick", lambda p: len(p["hints"]["opened"]) == 1)
        await host.send_json_to({"event": "open_hint", "payload": {"id": "cable"}})
        assert (await recv_until(host, "error"))["payload"]["code"] == "hint_denied"
        await host.send_json_to({"event": "open_hint", "payload": {}})
        assert (await recv_until(host, "error"))["payload"]["code"] == "hint_denied"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


# ---------------------------------------------------------------- Einsatzbesprechung (Intro am Beamer)
@pytest.mark.asyncio
async def test_player_start_with_beamer_opens_the_briefing_first(env):
    gid = "cov_briefing"
    host = await host_verbinden(gid)
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        msg = await recv_until(host, "lobby_update", lambda p: p["status"] == "briefing")
        assert msg["payload"]["ready_to_start"] is True
        assert gid not in games                                   # Zeit läuft noch nicht
        assert env.hget(state_key(gid), "status").decode() == "briefing"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_host_starts_the_game_after_the_intro(env):
    gid = "cov_briefing_go"
    host = await host_verbinden(gid)
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(host, "lobby_update", lambda p: p["status"] == "briefing")
        for comm in (a, b, c):
            await comm.send_json_to({"event": "player_ready", "payload": {}})
        await recv_until(host, "lobby_update", lambda p: p["all_ready"])
        await host.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(b, "lobby_update", lambda p: p["status"] == "running")
        await recv_until(b, "game_tick")
        assert games[gid].is_active
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_players_cannot_skip_the_briefing(env):
    gid = "cov_briefing_noskip"
    host = await host_verbinden(gid)
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(host, "lobby_update", lambda p: p["status"] == "briefing")
        await b.send_json_to({"event": "start_game", "payload": {}})
        await c.send_json_to({"event": "choose_role", "payload": {"role": "MASTER"}})
        await recv_until(c, "error")
        assert gid not in games
        assert env.hget(state_key(gid), "status").decode() == "briefing"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_without_beamer_the_game_starts_directly(env):
    gid = "cov_briefing_nohost"
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
    finally:
        await beenden(a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_beamer_gone_during_briefing_players_can_start(env):
    gid = "cov_briefing_hostgone"
    host = await host_verbinden(gid)
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "briefing")
        await host.disconnect()
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
    finally:
        await beenden(a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_host_cannot_start_before_all_roles_are_taken(env):
    gid = "cov_briefing_notready"
    host = await host_verbinden(gid)
    (a,) = await spieler(gid, ("A", "MASTER"))
    try:
        await host.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(host, "error")
        assert gid not in games
    finally:
        await beenden(host, a, game_ids=[gid])


# ---------------------------------------------------------------- Fehlercodes für das Frontend (fix/verbindung)
@pytest.mark.asyncio
async def test_full_lobby_rejects_with_register_denied(env):
    gid = "cov_register_denied"
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    d = await verbinden_ohne_initial(gid)
    try:
        await registrieren(d, "D")
        msg = await recv_until(d, "error")
        assert msg["payload"]["code"] == "register_denied"
    finally:
        await beenden(a, b, c, d, game_ids=[gid])


@pytest.mark.asyncio
async def test_failed_start_reports_start_failed(env):
    gid = "cov_start_failed"
    host = await host_verbinden(gid)
    (a,) = await spieler(gid, ("A", "MASTER"))
    try:
        await host.send_json_to({"event": "start_game", "payload": {}})
        msg = await recv_until(host, "error")
        assert msg["payload"]["code"] == "start_failed"
    finally:
        await beenden(host, a, game_ids=[gid])


# ---------------------------------------------------------------- Beamer-Anwesenheit (fix/beamer-anwesenheit)
def host_keys(env, gid):
    return list(env.scan_iter(match=f"game:{gid}:host:*"))


@pytest.mark.asyncio
async def test_beamer_presence_is_a_short_lived_key(env):
    """Statt eines Zählers: ein Schlüssel je Beamer-Verbindung mit kurzer Lebensdauer –
    nach einem Server-Absturz verschwindet er von selbst."""
    from backend.redis_handler import HOST_TTL
    gid = "cov_presence"
    host = await host_verbinden(gid)
    try:
        keys = host_keys(env, gid)
        assert len(keys) == 1
        assert 0 < env.ttl(keys[0]) <= HOST_TTL
    finally:
        await beenden(host, game_ids=[gid])
    assert host_keys(env, gid) == []                       # sauber getrennt → sofort weg


@pytest.mark.asyncio
async def test_host_ping_keeps_the_beamer_present(env):
    gid = "cov_presence_ping"
    host = await host_verbinden(gid)
    try:
        key = host_keys(env, gid)[0]
        env.expire(key, 2)
        await host.send_json_to({"event": "host_ping", "payload": {}})
        await asyncio.sleep(0.1)
        assert env.ttl(key) > 2
    finally:
        await beenden(host, game_ids=[gid])


@pytest.mark.asyncio
async def test_stale_beamer_after_crash_does_not_block_the_start(env):
    """Server-Absturz: kein disconnect, aber der Anwesenheits-Schlüssel läuft ab →
    Spieler-Start geht ohne Einsatzbesprechung direkt los."""
    gid = "cov_presence_crash"
    host = await host_verbinden(gid)
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        for key in host_keys(env, gid):
            env.delete(key)                                 # = abgelaufen
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_beamer_presence_survives_new_round(env):
    gid = "cov_presence_reset"
    host = await host_verbinden(gid)
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await host.send_json_to({"event": "reset_game", "payload": {}})
        await recv_until(host, "lobby_update", lambda p: p["status"] == "waiting")
        assert len(host_keys(env, gid)) == 1
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_player_start_during_briefing_explains_the_beamer(env):
    gid = "cov_presence_explain"
    host = await host_verbinden(gid)
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "briefing")
        await b.send_json_to({"event": "start_game", "payload": {}})
        msg = await recv_until(b, "error")
        assert "Beamer" in msg["payload"]["message"]
        assert env.hget(state_key(gid), "status").decode() == "briefing"
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


# ---------------------------------------------------------------- Wiedereinstieg (fix/wiedereinstieg)
@pytest.mark.asyncio
async def test_running_game_resumes_when_someone_connects_after_a_restart(env):
    gid = "cov_resume"
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
        await games[gid].stop_game()                       # = Server neu gestartet, Schleife weg
        games.pop(gid, None)
        assert env.hget(state_key(gid), "status").decode() == "running"

        neu = await verbinden_ohne_initial(gid)            # jemand verbindet sich (neu)
        assert games[gid].is_active
        await recv_until(neu, "game_tick")                 # die Zeit läuft wieder
        await neu.disconnect()
    finally:
        await beenden(a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_late_joiner_after_victory_gets_the_real_result(env):
    gid = "cov_late_result"
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
        env.hset(state_key(gid), "status", "won")
        over = await recv_until(a, "game_over", timeout=5)
        assert over["payload"]["result"] == "victory"

        neu = await verbinden(gid)
        comm = neu[0]
        erstes = await comm.receive_json_from()
        assert erstes["event"] == "game_over"              # vor dem lobby_update: kein falsches Bild
        assert erstes["payload"]["result"] == "victory"
        assert erstes["payload"]["score"] == over["payload"]["score"]
        await comm.disconnect()
    finally:
        await beenden(a, b, c, game_ids=[gid])


# ---------------------------------------------------------------- Rechte und Namen (fix/kleinkram)
@pytest.mark.asyncio
async def test_owner_settings_only_from_the_host(env):
    (a,) = await spieler("cov_os_nohost", ("A", "MASTER"))
    try:
        await a.send_json_to({"event": "owner_settings", "payload": {"time": 1}})
        msg = await recv_until(a, "error")
        assert msg["payload"]["code"] == "settings_denied"
        assert int(env.hget(state_key("cov_os_nohost"), "time_left")) != 1
    finally:
        await beenden(a, game_ids=["cov_os_nohost"])


@pytest.mark.asyncio
async def test_players_cannot_reset_a_running_game(env):
    gid = "cov_reset_running"
    (a, b, c) = await spieler(gid, ("A", "MASTER"), ("B", "FI-SI"), ("C", "FI-AE"))
    try:
        await a.send_json_to({"event": "start_game", "payload": {}})
        await recv_until(a, "lobby_update", lambda p: p["status"] == "running")
        await b.send_json_to({"event": "reset_game", "payload": {}})
        msg = await recv_until(b, "error")
        assert msg["payload"]["code"] == "reset_denied"
        assert env.hget(state_key(gid), "status").decode() == "running"
    finally:
        await beenden(a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_host_can_reset_a_running_game(env):
    gid = "cov_reset_host"
    host, a, b, c = await dev_spiel(env, gid)
    try:
        await host.send_json_to({"event": "reset_game", "payload": {}})
        await recv_until(host, "lobby_update", lambda p: p["status"] == "waiting")
    finally:
        await beenden(host, a, b, c, game_ids=[gid])


@pytest.mark.asyncio
async def test_same_name_while_the_first_is_still_connected_is_refused(env):
    """Zwei Geräte (verschiedene client_id), gleicher Name, beide verbunden."""
    gid = "cov_same_name"
    erster = await verbinden_ohne_initial(gid)
    await erster.send_json_to({"event": "player_register", "payload": {"player_name": "Max", "client_id": "tab-1"}})
    await recv_until(erster, "lobby_update", lambda p: len(p["players"]) == 1)
    zweiter = await verbinden_ohne_initial(gid)
    try:
        await zweiter.send_json_to({"event": "player_register", "payload": {"player_name": "Max", "client_id": "tab-2"}})
        msg = await recv_until(zweiter, "error")
        assert msg["payload"]["code"] == "register_denied"
        assert "vergeben" in msg["payload"]["message"]
    finally:
        await beenden(erster, zweiter, game_ids=[gid])


@pytest.mark.asyncio
async def test_same_tab_reloading_keeps_its_name(env):
    """F5: dieselbe client_id meldet sich neu an, bevor die alte Verbindung weg ist."""
    gid = "cov_same_tab"
    alt = await verbinden_ohne_initial(gid)
    await alt.send_json_to({"event": "player_register", "payload": {"player_name": "Max", "client_id": "tab-1"}})
    await recv_until(alt, "lobby_update", lambda p: len(p["players"]) == 1)
    neu = await verbinden_ohne_initial(gid)
    try:
        await neu.send_json_to({"event": "player_register", "payload": {"player_name": "Max", "client_id": "tab-1"}})
        await waehle_rolle(neu, "MASTER")
        msg = await recv_until(neu, "role_assigned")
        assert msg["payload"]["role"] == "MASTER"
    finally:
        await beenden(alt, neu, game_ids=[gid])


@pytest.mark.asyncio
async def test_same_name_after_the_first_left_is_a_reconnect(env):
    gid = "cov_same_name_reconnect"
    (a,) = await spieler(gid, ("Max", "MASTER"))
    await a.disconnect()
    neu = await verbinden_ohne_initial(gid)
    try:
        await registrieren(neu, "Max")
        msg = await recv_until(neu, "role_assigned")
        assert msg["payload"]["role"] == "MASTER"
    finally:
        await beenden(neu, game_ids=[gid])
