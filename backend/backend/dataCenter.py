import json
import random
import time
from pydantic import ValidationError
from .redis_handler import RedisHandler, _s, DEFAULT_TIME
from .schemas import PlayerInput
from .playableObject import TASK_TYPES, Outcome

HEALTH_BONUS = 15
MISTAKE_DAMAGE = 60
TOTAL_TASKS = 4

# Drei Rätsel, dann das Finale (GAME_DESIGN.md).
ROTATION = ["alarm", "fire_protocol", "data_rescue", "reboot"]

# Welche Ziffer des Neustart-Codes eine gelöste Aufgabe aufdeckt.
REWARD_SLOT = {"alarm": 0, "fire_protocol": 1, "data_rescue": 2}
REBOOT_CODE_LEN = 3

# Score-Multiplikator je nach Aufgabe.
# Score pro gelöster Aufgabe = Restzeit in Sekunden × Multiplikator
TASK_MULTIPLIER = {
    "alarm": 1,
    "fire_protocol": 2,
    "data_rescue": 3,
    "reboot": 4,
}


class DataCenter:
    def __init__(self, game_id: str = "test_game"):
        self.game_id = game_id
        self.redis = RedisHandler()
        self.max_health = 300

        state_key = self.redis._k_state(self.game_id)
        if not self.redis.r.exists(state_key):
            self.redis.r.hset(state_key, mapping={
                "health": self.max_health,
                "time_left": DEFAULT_TIME,
                "status": "waiting",
            })

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
    def score(self) -> int:
        val = self.redis.r.hget(self._key, "score")
        return int(val) if val else 0

    @property
    def reboot_code(self) -> list[int]:
        raw = self.redis.r.hget(self._key, "reboot_code")
        return json.loads(raw) if raw else []

    def _reboot_digits(self, state: dict) -> list[int | None]:
        """Neustart-Code für den Beamer: nur die bereits aufgedeckten Ziffern."""
        code = json.loads(state["reboot_code"]) if state.get("reboot_code") else []
        revealed = json.loads(state["reboot_revealed"]) if state.get("reboot_revealed") else []
        return [
            code[i] if i in revealed and i < len(code) else None
            for i in range(REBOOT_CODE_LEN)
        ]

    def _reveal_digit(self, kind: str) -> None:
        slot = REWARD_SLOT.get(kind)
        if slot is None:
            return
        raw = self.redis.r.hget(self._key, "reboot_revealed")
        revealed = json.loads(raw) if raw else []
        if slot not in revealed:
            self.redis.r.hset(self._key, "reboot_revealed", json.dumps(sorted(revealed + [slot])))

    @property
    def time_left(self) -> int:
        val = self.redis.r.hget(self._key, "time_left")
        return int(val) if val else 0

    def snapshot(self) -> dict:
        state = {_s(k): _s(v) for k, v in (self.redis.r.hgetall(self._key) or {}).items()}
        started = int(state.get("started_at") or time.time())
        task = json.loads(state["task"]) if state.get("task") else None
        return {
            "health": max(0, int(state.get("health", 0))),
            "time_left": max(0, int(state.get("time_left", 0))),
            "survived_seconds": int(time.time()) - started,
            "tasks": [self._public(task)] if task else [],
            "score": int(state.get("score", 0)),
            "reboot_digits": self._reboot_digits(state),
        }

    def start(self):
        self.redis.r.hset(self._key, mapping={
            "status": "running",
            "health": self.max_health,
            "time_left": DEFAULT_TIME,
            "started_at": int(time.time()),
            "score": 0,
            "solved_count": 0,
            "reboot_code": json.dumps([random.randint(0, 9) for _ in range(REBOOT_CODE_LEN)]),
            "reboot_revealed": json.dumps([]),
        })
        self.redis.r.hdel(self._key, "task", "over_announced")
        self.new_task(kind="alarm")
        self.redis.refresh_ttl(self.game_id)

    def apply_tick(self, amount: int = 1) -> int:
        new_hp = self.redis.r.hincrby(self._key, "health", -amount)
        if new_hp <= 0:
            self.redis.r.hset(self._key, mapping={"health": 0, "status": "game_over"})
            return 0
        return new_hp

    def tick(self) -> dict:
        self.apply_tick(1)
        self.redis.r.hincrby(self._key, "time_left", -1)
        return self.snapshot()

    def finish(self):
        self.redis.r.hset(self._key, "status", "game_over")

    def claim_game_over(self) -> bool:
        """True nur beim ersten Aufruf pro Runde: wer True bekommt, meldet das Spielende."""
        return bool(self.redis.r.hsetnx(self._key, "over_announced", 1))

    def register_mistake(self) -> int:
        if self.health <= 0:
            return 0
        return self.apply_tick(MISTAKE_DAMAGE)

    @staticmethod
    def _public(task: dict) -> dict:
        out = {
            "task_id": task.get("task_id"),
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

    def new_task(self, kind: str | None = None) -> dict:
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
        if kind == "reboot":
            state = task_cls.create(players_data, digits=self.reboot_code)
        else:
            state = task_cls.create(players_data)
        task = {
            "task_id": f"task-{counter:03d}",
            "kind": kind,
            "instruction": state.get("instruction", task_cls.instruction),
            "assigned_to_player": state.get("assigned_to_player"),
            "state": state,
        }
        r.hset(self._key, mapping={"task": json.dumps(task), "last_task_idx": kind})
        return task

    def _score_for_solve(self, kind: str) -> int:
        """Score = Restzeit × Multiplikator (T1=1, T2=2, T3=3)."""
        multiplier = TASK_MULTIPLIER.get(kind, 1)
        return max(0, self.time_left) * multiplier

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

        task = self.current_task()
        if task:
            task_cls = TASK_TYPES.get(task.get("kind"))
            if task_cls is None:
                return {"result": "error", "message": "unknown task kind"}

            players = self.redis._load_players(self.game_id)
            role = (players.get(player_name) or {}).get("role")

            res = task_cls.handle_input(task["state"], player_name, role, data, time.time())

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

                # Score = Restzeit × Multiplikator der gerade gelösten Aufgabe
                gain = self._score_for_solve(task.get("kind", ""))
                self.redis.r.hincrby(self._key, "score", gain)
                self._reveal_digit(task.get("kind", ""))

                solved = self.redis.r.hincrby(self._key, "solved_count", 1)
                if solved >= TOTAL_TASKS:
                    self.redis.r.hset(self._key, "status", "won")
                    return {"result": "correct", "won": True, "score_gain": gain}

                self.new_task()
                return {"result": "correct", "score_gain": gain}

        self.register_mistake()
        return {"result": "wrong"}