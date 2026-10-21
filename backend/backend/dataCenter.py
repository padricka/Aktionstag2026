import json
import random
import time
from pydantic import ValidationError
from . import leaderboard
from .redis_handler import RedisHandler, _s, DEFAULT_TIME, LOBBY_TTL, ROLES
from .schemas import PlayerInput
from .playableObject import TASK_TYPES, Outcome

MAX_HEALTH = 300
HEALTH_BONUS = 15
# Sekunden extra pro echt gelöster Aufgabe (nicht beim DEV-Überspringen)
TIME_BONUS = 60
# Der Server brennt: alle FIRE_EVERY Sekunden kostet das Feuer ein Leben (DEV: steht)
FIRE_EVERY = 3
# Sekunden Pause nach einer gelösten Aufgabe: so lange läuft die Zwischenszene
# (Zwischenszene.vue, DAUER/DAUER_TRESOR) – Uhr und Feuer stehen, das ×2-Fenster wartet
PAUSE_NACH = {"alarm": 5 + 12, "fire_protocol": 5 + 10, "data_rescue": 6}   # + Tutorials vor Aufgabe 2 und 3

# Antwort, wenn die Eingabe-Sperre nicht frei wird: lieber "nochmal" als Fortschritt verlieren
INPUT_BUSY = {"result": "error", "message": "Bitte erneut versuchen"}
MISTAKE_DAMAGE = 30
# Punkte, die jede geöffnete Hilfe-Notiz kostet (im DEV-Modus gratis)
HINT_COST = 50
TOTAL_TASKS = 4

# Drei Rätsel, dann das Finale: Server reparieren (GAME_DESIGN.md).
ROTATION = ["alarm", "fire_protocol", "data_rescue", "repair"]
FINALE = ROTATION[-1]

# Fundorte (GAME_DESIGN.md): nach jeder Aufgabe öffnet sich ein Ort mit einem Teil fürs Finale
FUNDORTE = {
    "alarm": {"id": "psu", "name": "Netzteil", "fundort": "schrank"},
    "fire_protocol": {"id": "fan", "name": "Lüfter", "fundort": "lager"},
    "data_rescue": {"id": "disk", "name": "Backup-Platte", "fundort": "tresor"},
}


def _neue_etiketten() -> dict:
    """Etiketten der Teile, pro Runde ausgelost – das Finale braucht sie."""
    return {
        "psu": {"label": random.choice(["115 V", "230 V"])},
        "fan": {"label": "Pfeil = Luftstrom"},
        "disk": {"label": f"RAID-Platz {random.choice([1, 2, 3, 4])}"},
    }

# Punkte (GAME_DESIGN.md, „Punkte“): Endpunkte = restliche Leben + Aufgabenpunkte
# (×2, wenn innerhalb FAST_LIMIT Sekunden ab Aufgabenstart gelöst) + Restzeit bei Sieg
# − HINT_COST je Hilfe-Notiz. Auch das Finale zählt (feat/finale-hilfen-punkte).
TASK_POINTS = {
    "alarm": 200,
    "fire_protocol": 250,
    "data_rescue": 300,
    "repair": 350,
}
FAST_LIMIT = {
    "alarm": 90,
    "fire_protocol": 150,
    "data_rescue": 210,
    "repair": 180,
}


def tick_payload(snap: dict) -> dict:
    """game_tick-Payload laut JSON_Vertrag – die einzige Stelle, die ihn zusammenbaut
    (Spielschleife und Consumer), damit kein Weg ein Feld vergisst."""
    return {
        "health": snap["health"],
        "max_health": snap.get("max_health", MAX_HEALTH),
        "time_left": snap["time_left"],
        "tasks": snap["tasks"],
        "hints": snap.get("hints") or {"total": 0, "opened": [], "cost": HINT_COST},
        "parts": snap.get("parts") or [],
    }


class DataCenter:
    def __init__(self, game_id: str = "test_game"):
        self.game_id = game_id
        self.redis = RedisHandler()
        self.max_health = MAX_HEALTH
        # Uhr für Aufgabenstart und Lösezeit (×2-Limit); Tests setzen eine eigene
        self._now = time.time

        state_key = self.redis._k_state(self.game_id)
        if not self.redis.r.exists(state_key):
            self.redis.r.hset(state_key, mapping={
                "health": self.max_health,
                "time_left": DEFAULT_TIME,
                "status": "waiting",
            })
            # neu angelegt (Sitzung war abgelaufen): nicht für immer liegen lassen
            self.redis.r.expire(state_key, LOBBY_TTL)

    @property
    def _key(self) -> str:
        return self.redis._k_state(self.game_id)

    @property
    def health(self) -> int:
        val = self.redis.r.hget(self._key, "health")
        return int(val) if val else 0

    @property
    def status(self) -> str:
        return _s(self.redis.r.hget(self._key, "status")) or "waiting"

    @property
    def task_points(self) -> int:
        """Summe der Aufgabenpunkte (inkl. ×2) – in Redis unter „score“."""
        val = self.redis.r.hget(self._key, "score")
        return int(val) if val else 0

    @property
    def score(self) -> int:
        """Aktuelle Endpunkte nach der Formel (siehe snapshot)."""
        return self.snapshot()["score"]

    @property
    def parts_spec(self) -> dict:
        raw = self.redis.r.hget(self._key, "parts_spec")
        return json.loads(raw) if raw else {}

    def _parts(self, state: dict) -> list[dict]:
        """Gefundene Teile in Fundreihenfolge, mit Etikett (game_tick.parts)."""
        gefunden = json.loads(state["parts_found"]) if state.get("parts_found") else []
        spec = json.loads(state["parts_spec"]) if state.get("parts_spec") else {}
        alle = {f["id"]: f for f in FUNDORTE.values()}
        return [{**alle[i], "label": (spec.get(i) or {}).get("label", "")} for i in gefunden if i in alle]

    def _find_part(self, kind: str) -> None:
        teil = FUNDORTE.get(kind)
        if not teil:
            return
        raw = self.redis.r.hget(self._key, "parts_found")
        gefunden = json.loads(raw) if raw else []
        if teil["id"] not in gefunden:
            self.redis.r.hset(self._key, "parts_found", json.dumps(gefunden + [teil["id"]]))

    @property
    def time_left(self) -> int:
        val = self.redis.r.hget(self._key, "time_left")
        return int(val) if val else 0

    def snapshot(self) -> dict:
        state = {_s(k): _s(v) for k, v in (self.redis.r.hgetall(self._key) or {}).items()}
        started = int(state.get("started_at") or time.time())
        task = json.loads(state["task"]) if state.get("task") else None
        penalty = int(state.get("hint_penalty", 0))
        health = max(0, int(state.get("health", 0)))
        time_left = max(0, int(state.get("time_left", 0)))
        # Endpunkte: Leben + Aufgabenpunkte (+ Restzeit bei Sieg) − Hilfen, nie unter 0
        won_bonus = time_left if state.get("status") == "won" else 0
        score = health + int(state.get("score", 0)) + won_bonus - penalty
        return {
            "health": health,
            "time_left": time_left,
            "survived_seconds": int(time.time()) - started,
            "tasks": [self._public(task)] if task else [],
            "score": max(0, score),
            "hint_penalty": penalty,
            "hints": self._hints(task),
            "max_health": self.max_health,
            "parts": self._parts(state),
        }

    @staticmethod
    def _hints(task: dict | None) -> dict:
        """Für den Beamer: Themen, die noch auf dem Block stehen (nur id + label), und die
        schon abgerissenen Zettel mit Text. Ungeöffnete Texte gehen nie raus."""
        task_cls = TASK_TYPES.get((task or {}).get("kind"))
        if not task or not task_cls or not task_cls.HINTS:
            return {"total": 0, "available": [], "opened": [], "cost": HINT_COST}
        alle = task_cls.hints(task["state"])
        offen = task.get("hints_opened", [])
        nach_id = {h["id"]: h for h in alle}
        return {
            "task_id": task.get("task_id"),   # der Host schickt sie bei open_hint mit
            "total": task_cls.HINTS,
            "available": [{"id": h["id"], "label": h["label"]}
                          for h in alle if h["id"] not in offen and not h["done"]],
            "opened": [{"id": i, "label": nach_id[i]["label"], "text": nach_id[i]["text"]} for i in offen],
            "cost": HINT_COST,
        }

    def open_hint(self, hint_id: str | None, task_id: str | None = None) -> dict:
        """Host reißt den Zettel zum Thema hint_id ab (kostet HINT_COST, DEV gratis).
        Nur Themen, die noch auf dem Block stehen: nicht schon offen, Schritt nicht erledigt.
        task_id (falls mitgeschickt) muss die laufende Aufgabe sein – sonst hat das Team
        sie gerade gelöst und der Klick galt der alten Aufgabe."""
        if self.status != "running":
            return {"result": "error", "message": "Spiel läuft nicht"}
        # Gleiche Sperre wie bei Eingaben: sonst überschreibt ein gleichzeitiges
        # Lösen/Weiterschalten den Aufgabenstand
        with self.redis.lock(self._input_lock_name) as acquired:
            if not acquired:
                return dict(INPUT_BUSY)
            task = self.current_task()
            task_cls = TASK_TYPES.get((task or {}).get("kind"))
            if not task or not task_cls or not task_cls.HINTS:
                return {"result": "error", "message": "Für diese Aufgabe gibt es keine Hilfen"}
            if task_id is not None and task_id != task.get("task_id"):
                return {"result": "error", "message": "Die Aufgabe ist schon gelöst – Hilfe nicht geöffnet"}
            verfuegbar = {h["id"]: h for h in self._hints(task)["available"]}
            if hint_id not in verfuegbar:
                return {"result": "error", "message": "Diese Hilfe gibt es gerade nicht"}
            task["hints_opened"] = task.get("hints_opened", []) + [hint_id]
            self.redis.r.hset(self._key, "task", json.dumps(task))
            if not self.dev_mode:
                self.redis.r.hincrby(self._key, "hint_penalty", HINT_COST)
        return {"result": "opened", "id": hint_id}

    def start(self):
        self.redis.r.hset(self._key, mapping={
            "status": "running",
            "health": self.max_health,
            "time_left": int(_s(self.redis.r.hget(self._key, "start_time")) or DEFAULT_TIME),
            "started_at": int(time.time()),
            "score": 0,
            "hint_penalty": 0,
            "solved_count": 0,
            "fire_seconds": 0,
            "parts_found": json.dumps([]),
            "parts_spec": json.dumps(_neue_etiketten()),
        })
        self.redis.r.hdel(self._key, "task", "over_announced", "game_over", "pause_until")
        self.new_task(kind="alarm")
        self.redis.refresh_ttl(self.game_id)

    def apply_tick(self, amount: int = 1) -> int:
        new_hp = self.redis.r.hincrby(self._key, "health", -amount)
        if new_hp <= 0:
            self.redis.r.hset(self._key, mapping={"health": 0, "status": "game_over"})
            return 0
        return new_hp

    @property
    def dev_mode(self) -> bool:
        """DEV-Modus (vom Host in der Lobby gesetzt): Zeit steht, Fehler kosten nichts."""
        return _s(self.redis.r.hget(self._key, "dev_mode")) == "1"

    def tick(self) -> dict:
        """Eine Sekunde: die Zeit läuft, und alle FIRE_EVERY Sekunden frisst das Feuer ein
        Leben. Ist die Zeit abgelaufen oder sind die Leben weg, ist der Server verloren.

        Nur für eine laufende Runde und unter der Eingabe-Sperre: so überschreibt ein Tick
        weder einen Sieg in der letzten Sekunde noch eine zurückgesetzte Lobby, und ein
        abgelaufener Spielstand wird nicht als Geister-Runde neu angelegt."""
        if self.dev_mode:
            return self.snapshot()
        with self.redis.lock(self._input_lock_name) as acquired:
            if acquired and self.status == "running" and not self._pausiert():
                if self.redis.r.hincrby(self._key, "time_left", -1) <= 0:
                    self.redis.r.hset(self._key, mapping={"time_left": 0, "health": 0, "status": "game_over"})
                elif self.redis.r.hincrby(self._key, "fire_seconds", 1) % FIRE_EVERY == 0:
                    self.apply_tick(1)
        return self.snapshot()

    def finish(self):
        self.redis.r.hset(self._key, "status", "game_over")

    def remember_game_over(self, payload: dict):
        """Ergebnis merken, damit später Verbindende es bekommen (siehe GameConsumer.connect)."""
        self.redis.r.hset(self._key, "game_over", json.dumps(payload))

    def last_game_over(self) -> dict | None:
        raw = self.redis.r.hget(self._key, "game_over")
        return json.loads(raw) if raw else None

    def claim_game_over(self) -> bool:
        """True nur beim ersten Aufruf pro Runde: wer True bekommt, meldet das Spielende."""
        return bool(self.redis.r.hsetnx(self._key, "over_announced", 1))

    def record_result(self, result: str, snap: dict) -> dict:
        """Runde ins Leaderboard eintragen (nicht im DEV-Modus).

        Rückgabe für game_over: eigener Platz (None im DEV-Modus), Top 5, Anzahl Runden.
        """
        if self.dev_mode:
            return {**leaderboard.top(), "rank": None}
        players = self.redis._load_players(self.game_id)
        if not players:
            # z. B. verlassene DEV-Runde nach Ablauf: nie als Geister-Runde eintragen
            return {**leaderboard.top(), "rank": None}
        rolle = {r: i for i, r in enumerate(ROLES)}
        team = sorted(players, key=lambda n: rolle.get(players[n].get("role"), len(ROLES)))
        rec = leaderboard.add_entry(team, snap["score"], result, snap["survived_seconds"], self.game_id)
        return {"rank": rec["entry"]["rank"], "top": rec["top"], "total": rec["total"]}

    def register_mistake(self) -> int:
        if self.health <= 0:
            return 0
        if self.dev_mode:
            return self.health
        return self.apply_tick(MISTAKE_DAMAGE)

    def skip_task(self) -> dict:
        """DEV-Modus: aktuelle Aufgabe für alle überspringen (ohne Punkte und HP-Bonus)."""
        if not self.dev_mode:
            return {"result": "error", "message": "DEV-Modus ist aus"}
        if self.status != "running":
            return {"result": "error", "message": "game not running"}
        # Gleiche Sperre wie bei Eingaben: sonst schreibt eine gleichzeitige
        # Eingabe den alten Aufgabenstand über die neue Aufgabe
        with self.redis.lock(self._input_lock_name) as acquired:
            if not acquired:
                return dict(INPUT_BUSY)
            task = self.current_task()
            if not task or self.redis.r.hdel(self._key, "task") != 1:
                return {"result": "ignored"}
            won = self._advance(task)
        return {"result": "skipped", "won": won}

    def _advance(self, task: dict) -> bool:
        """Nach gelöster/übersprungener Aufgabe: Teil finden, Pause für die Zwischenszene,
        nächste Aufgabe. True = gewonnen."""
        self._find_part(task.get("kind", ""))
        solved = self.redis.r.hincrby(self._key, "solved_count", 1)
        if solved >= TOTAL_TASKS:
            self.redis.r.hset(self._key, "status", "won")
            return True
        pause = PAUSE_NACH.get(task.get("kind", ""), 0)
        self.redis.r.hset(self._key, "pause_until", self._now() + pause)
        self.new_task(start_delay=pause)
        return False

    def _pausiert(self) -> bool:
        """Läuft gerade die Zwischenszene? Dann stehen Uhr und Feuer."""
        bis = self.redis.r.hget(self._key, "pause_until")
        return bool(bis) and self._now() < float(bis)

    @staticmethod
    def _public(task: dict) -> dict:
        out = {
            "task_id": task.get("task_id"),
            "kind": task.get("kind"),
            "assigned_to_player": task.get("assigned_to_player"),
            "instruction": task.get("instruction"),
        }
        task_cls = TASK_TYPES.get(task.get("kind"))
        views = task_cls.views(task.get("state") or {}) if task_cls else {}
        if views:
            out["views"] = views
        return out

    def current_task(self):
        raw = self.redis.r.hget(self._key, "task")
        return json.loads(raw) if raw else None

    def new_task(self, kind: str | None = None, start_delay: float = 0) -> dict:
        r = self.redis.r
        players_data = self.redis._load_players(self.game_id)
        counter = r.hincrby(self._key, "task_counter", 1)

        if kind is None:
            last = _s(r.hget(self._key, "last_task_idx"))
            if last in ROTATION:
                next_idx = (ROTATION.index(last) + 1) % len(ROTATION)
                kind = ROTATION[next_idx]
            else:
                kind = ROTATION[0]

        task_cls = TASK_TYPES[kind]
        if kind == "repair":
            # das Finale baut die Teile ein – mit den Etiketten aus der Teilekiste
            state = task_cls.create(players_data, parts_spec=self.parts_spec)
        else:
            state = task_cls.create(players_data)
        task = {
            "task_id": f"task-{counter:03d}",
            "kind": kind,
            "instruction": state.get("instruction", task_cls.instruction),
            "assigned_to_player": state.get("assigned_to_player"),
            "state": state,
            # ab hier läuft das ×2-Limit (FAST_LIMIT) – erst nach der Zwischenszene
            "started_at": self._now() + start_delay,
        }
        r.hset(self._key, mapping={"task": json.dumps(task), "last_task_idx": kind})
        return task

    def _points_for(self, task: dict) -> int:
        """Aufgabenpunkte; ×2, wenn innerhalb von FAST_LIMIT Sekunden ab Aufgabenstart gelöst."""
        kind = task.get("kind", "")
        points = TASK_POINTS.get(kind, 0)
        limit = FAST_LIMIT.get(kind)
        started = task.get("started_at")
        if limit is not None and started is not None and self._now() - started <= limit:
            points *= 2
        return points

    def process_input(self, player_name: str, payload: dict) -> dict:
        if self.status != "running":
            return {"result": "error", "message": "game not running"}
        try:
            data = PlayerInput.model_validate(payload)
        except ValidationError:
            return {"result": "error", "message": "Payload not valid"}

        if data.target == "penalty":
            self.register_mistake()
            return {"result": "wrong", "health": self.health}

        # Eingaben einer Sitzung nacheinander: Lesen → Prüfen → Schreiben des
        # Aufgabenstands darf sich nicht überlappen, sonst überschreibt z. B. beim
        # gleichzeitigen Sync-Knopf der zweite Druck den ersten.
        with self.redis.lock(self._input_lock_name) as acquired:
            if not acquired:
                return dict(INPUT_BUSY)
            return self._apply_input(player_name, data)

    @property
    def _input_lock_name(self) -> str:
        return f"input:{self.game_id}"

    def _apply_input(self, player_name: str, data: PlayerInput) -> dict:
        """Eine Eingabe auf die aktuelle Aufgabe anwenden. Nur unter der Eingabe-Sperre aufrufen."""
        # Neu prüfen: Zwischen der Prüfung in process_input und der Sperre kann ein anderer
        # Spieler gewonnen haben – dann zählt diese Eingabe nicht (auch nicht als Fehler).
        if self.status != "running":
            return {"result": "ignored"}
        task = self.current_task()
        if task:
            task_cls = TASK_TYPES.get(task.get("kind"))
            if task_cls is None:
                return {"result": "error", "message": "unknown task kind"}

            players = self.redis._load_players(self.game_id)
            role = (players.get(player_name) or {}).get("role")

            res = task_cls.handle_input(task["state"], player_name, role, data, self._now())

            if res.outcome is Outcome.IGNORED:
                return {"result": "ignored"}

            if res.outcome is Outcome.PROGRESS:
                task["state"] = res.state
                self.redis.r.hset(self._key, "task", json.dumps(task))
                return {"result": "correct"}

            if res.outcome is Outcome.SOLVED:
                if self.redis.r.hdel(self._key, "task") != 1:
                    return {"result": "ignored"}

                if self.redis.r.hincrby(self._key, "health", HEALTH_BONUS) > self.max_health:
                    self.redis.r.hset(self._key, "health", self.max_health)

                # Aufgabenpunkte (×2 bei schneller Lösung) – bewusst nicht in der Antwort,
                # der Duplikator bleibt für die Spieler unsichtbar
                self.redis.r.hincrby(self._key, "score", self._points_for(task))
                if task.get("kind") != FINALE:
                    # Zeitbonus nur, wenn noch eine Aufgabe kommt (nach dem Finale zählt die Restzeit)
                    self.redis.r.hincrby(self._key, "time_left", TIME_BONUS)

                if self._advance(task):
                    return {"result": "correct", "won": True}
                return {"result": "correct"}

            # WRONG: Fehler kostet Leben; manche Aufgaben speichern dabei einen Rücksetzer
            if res.persist:
                task["state"] = res.state
                self.redis.r.hset(self._key, "task", json.dumps(task))
            self.register_mistake()
            out = {"result": "wrong"}
            if res.message:
                out["message"] = res.message
            return out

        self.register_mistake()
        return {"result": "wrong"}