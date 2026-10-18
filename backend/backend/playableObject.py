from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import random

ROLE_M = "MASTER"
ROLE_P1 = "FI-SI"
ROLE_P2 = "FI-AE"

FIRE_SEQUENCE_LEN = 3


class Outcome(str, Enum):
    IGNORED = "ignored"
    PROGRESS = "progress"
    SOLVED = "solved"
    WRONG = "wrong"


@dataclass
class StepResult:
    outcome: Outcome
    state: dict


class PlayableObject(ABC):
    kind: str
    instruction: str

    @classmethod
    @abstractmethod
    def create(cls, players: dict) -> dict:
        pass

    @classmethod
    @abstractmethod
    def views(cls, state: dict) -> dict:
        pass

    @classmethod
    @abstractmethod
    def handle_input(cls, state: dict, player_name: str, role: str | None,
                     data, now: float) -> StepResult:
        pass


# --------------------------------------------------------------------------- Button
class ButtonTask(PlayableObject):
    kind = "button"
    instruction = "Drücke den richtigen Knopf!"

    BUTTONS = [
        {"target": "reactor_vent", "value": "open", "instruction": "Öffne das Reaktor-Ventil!"},
        {"target": "main_cooling", "value": "on",   "instruction": "Aktiviere die Hauptkühlung!"},
        {"target": "backup_power", "value": "off",  "instruction": "Schalte die Notstromversorgung aus!"},
    ]

    @classmethod
    def create(cls, players):
        button = random.choice(cls.BUTTONS)
        names = list(players.keys())
        return {
            **button,
            "assigned_to_player": random.choice(names) if names else None,
        }

    @classmethod
    def views(cls, state):
        return {}

    @classmethod
    def handle_input(cls, state, player_name, role, data, now):
        if data.target == state["target"] and str(data.value) == state["value"]:
            return StepResult(Outcome.SOLVED, state)
        return StepResult(Outcome.WRONG, state)


# --------------------------------------------------------------------------- Alarm
class AlarmTask(PlayableObject):
    kind = "alarm"
    instruction = "Alarm verifizieren!"

    COMPONENTS = [
        {"id": "K1", "label": "NETZWERK-SWITCH 2", "symbol": "raute"},
        {"id": "K2", "label": "HAUPT-STROM B-04", "symbol": "dreieck"},
        {"id": "K3", "label": "LÜFTUNG SYSTEM A", "symbol": "quadrat"},
        {"id": "K4", "label": "FIREWALL-MODUL", "symbol": "kreis"},
    ]

    # Pool für den Shutdown-Code. Wird bei jedem Task neu gemischt.
    CODE_POOL = ['dreieck-runter', 'kreuz', 'dreieck-runter-voll', 'stern']
    # Aufkleber-Farben. Ihre Reihenfolge (nur der Leitstand kennt sie) ordnet den Code.
    STICKER_COLORS = ["ROT", "GELB", "GRÜN", "BLAU"]

    # Escape-Room-Verteilung (GAME_DESIGN.md, Aufgabe 1):
    #   Leitstand  sieht, WELCHER Steckplatz brennt, und die Farb-Reihenfolge -> tippt den Code
    #   Vorderseite sieht die Schalter (Symbole in Steckplatz-Reihenfolge)    -> drückt den Schalter
    #   Rückseite  sieht die Code-Symbole auf farbigen Aufklebern, gemischt   -> keine Eingabe
    @classmethod
    def create(cls, players):
        slot = random.randrange(len(cls.COMPONENTS))
        broken = cls.COMPONENTS[slot]

        code = list(cls.CODE_POOL)
        random.shuffle(code)
        color_order = list(cls.STICKER_COLORS)
        random.shuffle(color_order)
        # Das i-te Code-Symbol bekommt die i-te Farbe der Farb-Reihenfolge ...
        stickers = [{"symbol": s, "color": c} for s, c in zip(code, color_order)]
        # ... die Rückseite sieht die Aufkleber aber gemischt.
        random.shuffle(stickers)

        return {
            "burning_slot": slot + 1,
            "broken_id": broken["id"],
            "broken_symbol": broken["symbol"],
            "code": code,
            "color_order": color_order,
            "stickers": stickers,
            "switch_ok": False,
            "cmd_ok": False,
        }

    @classmethod
    def views(cls, state):
        return {
            ROLE_M: {
                "type": "alarm_leds",
                "slots": len(cls.COMPONENTS),
                "burning_slot": state["burning_slot"],
                "color_order": state["color_order"],
                "p_done": state["cmd_ok"],
            },
            ROLE_P1: {
                "type": "main_switches",
                "switches": [c["symbol"] for c in cls.COMPONENTS],
                "p_done": state["switch_ok"],
            },
            ROLE_P2: {
                "type": "code_stickers",
                "stickers": state["stickers"],
            },
        }

    @classmethod
    def handle_input(cls, state, player_name, role, data, now):
        value = str(data.value).strip().lower()

        if data.target == "main_switch" and role == ROLE_P1:
            if value not in (state["broken_symbol"].lower(), state["broken_id"].lower()):
                return StepResult(Outcome.WRONG, state)
            state["switch_ok"] = True

        elif data.target == "shutdown_cmd" and role == ROLE_M:
            expected = ",".join(state["code"]).lower()
            if value.replace(" ", "") != expected:
                return StepResult(Outcome.WRONG, state)
            state["cmd_ok"] = True
        else:
            return StepResult(Outcome.IGNORED, state)

        if state["switch_ok"] and state["cmd_ok"]:
            return StepResult(Outcome.SOLVED, state)
        return StepResult(Outcome.PROGRESS, state)


# --------------------------------------------------------------------------- FireProtocol
class FireProtocolTask(PlayableObject):
    kind = "fire_protocol"
    instruction = "Löschprotokoll ausführen!"

    VALVES = ["V-31", "V-32", "V-33"]
    COLORS = ["ORANGE", "RED", "GREEN"]
    FRAGMENT_POOL = ["DRV", "AK26", "SYS", "BOX", "SEC", "FIRE"]

    # Escape-Room-Verteilung (GAME_DESIGN.md, Aufgabe 2):
    #   Jede Rolle kennt genau EINEN Schritt der Sequenz -> nur gemeinsam kann die
    #   Vorderseite fluten. Passwort-Fragmente tragen 1–3 Punkte, sortiert ergeben sie
    #   das Passwort. Fragment 0 = Leitstand, 1 = Rückseite, 2 = erst nach dem Fluten.
    @classmethod
    def create(cls, players):
        sequence = [
            {"valve": random.choice(cls.VALVES), "color": random.choice(cls.COLORS)}
            for _ in range(FIRE_SEQUENCE_LEN)
        ]

        steps = list(range(FIRE_SEQUENCE_LEN))
        random.shuffle(steps)
        clue_steps = {ROLE_M: steps[0], ROLE_P1: steps[1], ROLE_P2: steps[2]}

        dots = [1, 2, 3]
        random.shuffle(dots)
        texts = random.sample(cls.FRAGMENT_POOL, 3)
        fragments = [{"dots": d, "text": t} for d, t in zip(dots, texts)]

        return {
            "sequence": sequence,
            "step": 0,
            "clue_steps": clue_steps,
            "fragments": fragments,
            "p1_done": False,
            "p2_done": False,
        }

    @classmethod
    def _clue(cls, state, role):
        idx = state["clue_steps"][role]
        step = state["sequence"][idx]
        return {"step": idx + 1, "valve": step["valve"], "color": step["color"]}

    @classmethod
    def views(cls, state):
        frags = state["fragments"]
        last = frags[2] if state["p1_done"] else None

        return {
            ROLE_M: {
                "type": "fire_log",
                "clue": cls._clue(state, ROLE_M),
                "fragment": frags[0],
            },
            ROLE_P1: {
                "type": "valve_panel",
                "valves": cls.VALVES,
                "colors": cls.COLORS,
                "sequence_len": len(state["sequence"]),
                "step": state["step"],
                "clue": cls._clue(state, ROLE_P1),
                "last_fragment": last,
                "p_done": state["p1_done"],
            },
            ROLE_P2: {
                "type": "password_input",
                "clue": cls._clue(state, ROLE_P2),
                "fragment": frags[1],
                "last_fragment": last,
                "p_done": state["p2_done"],
            },
        }

    @classmethod
    def handle_input(cls, state, player_name, role, data, now):
        value = str(data.value).strip().upper()

        if data.target == "valve_action" and role == ROLE_P1:
            if state["p1_done"]:
                return StepResult(Outcome.IGNORED, state)
            step = state["step"]
            if step >= len(state["sequence"]):
                return StepResult(Outcome.IGNORED, state)

            if ":" not in value:
                return StepResult(Outcome.WRONG, state)
            valve_in, color_in = value.split(":", 1)
            valve_map = {"ALPHA": "V-31", "BETA": "V-32", "GAMMA": "V-33"}
            valve_norm = valve_map.get(valve_in, valve_in)

            current = state["sequence"][step]
            if valve_norm != current["valve"].upper() or color_in != current["color"].upper():
                return StepResult(Outcome.WRONG, state)

            state["step"] = step + 1
            if state["step"] >= len(state["sequence"]):
                state["p1_done"] = True
            return StepResult(Outcome.PROGRESS, state)

        if data.target == "release_pw" and role == ROLE_P2:
            if not state["p1_done"]:
                return StepResult(Outcome.IGNORED, state)

            ordered = sorted(state["fragments"], key=lambda f: f["dots"])
            expected = "".join(f["text"] for f in ordered).upper()

            clean_in = value.replace("-", "").replace(" ", "").upper()
            if clean_in != expected:
                return StepResult(Outcome.WRONG, state)

            state["p2_done"] = True
            return StepResult(Outcome.SOLVED, state)

        return StepResult(Outcome.IGNORED, state)


# --------------------------------------------------------------------------- DataRescue
class DataRescueTask(PlayableObject):
    kind = "data_rescue"
    instruction = "Daten retten!"

    WORDS = ["SERVER", "BACKUP", "DATEN", "RETTEN", "SICHERN", "CLOUD"]
    # Binärwerte-Pool: Buchstaben A-Z (65..90)
    LETTER_CODES = list(range(65, 91))

    # Beide Knöpfe müssen innerhalb dieses Fensters gedrückt werden (GAME_DESIGN.md, Aufgabe 3).
    SYNC_WINDOW = 3.0
    # Feste Punkte für die Rettung: der Test schreibt 50 vor, unabhängig von der Restzeit.
    fixed_score = 50

    @classmethod
    def create(cls, players):
        word = random.choice(cls.WORDS)
        p1_codes = [ord(c) for c in word]

        # Zwei unterschiedliche Buchstaben-Codes (A-Z) zufällig ziehen
        p2_values = random.sample(cls.LETTER_CODES, 2)
        p2_binary = [format(v, "08b") for v in p2_values]

        return {
            "p1_word": word,
            "p1_codes": p1_codes,
            "p2_values": p2_values,
            "p2_binary": p2_binary,
            "p1_unlocked": False,
            "p2_unlocked": False,
            # Zeitstempel der Sync-Drücke. Beide None = noch niemand gedrückt.
            "sync_at": {ROLE_P1: None, ROLE_P2: None},
        }

    @classmethod
    def views(cls, state):
        return {
            ROLE_M: {
                "type": "task3_master",
                "p1_status": "FREIGESCHALTET" if state["p1_unlocked"] else "GESPERRT",
                "p2_status": "FREIGESCHALTET" if state["p2_unlocked"] else "GESPERRT",
            },
            ROLE_P1: {
                "type": "task3_p1",
                "ascii_codes": state["p1_codes"],
                "button_unlocked": state["p1_unlocked"],
            },
            ROLE_P2: {
                "type": "task3_p2",
                "binary_codes": state["p2_binary"],
                "button_unlocked": state["p2_unlocked"],
            },
        }

    @classmethod
    def handle_input(cls, state, player_name, role, data, now):
        value = str(data.value).strip().upper()

        if data.target == "ascii_answer" and role == ROLE_P1:
            if value != state["p1_word"]:
                return StepResult(Outcome.WRONG, state)
            state["p1_unlocked"] = True
            return StepResult(Outcome.PROGRESS, state)

        if data.target == "binary_answer" and role == ROLE_P2:
            versuch = " ".join(value.split())
            ziel = " ".join(str(v) for v in state["p2_values"])
            if versuch != ziel:
                return StepResult(Outcome.WRONG, state)
            state["p2_unlocked"] = True
            return StepResult(Outcome.PROGRESS, state)

        if data.target == "sync_button":
            return cls._sync(state, role, now)

        return StepResult(Outcome.IGNORED, state)

    @classmethod
    def _sync(cls, state, role, now):
        """Zwei Drücke im selben Zeitfenster lösen die Rettung aus.

        Der erste Druck wartet (PROGRESS). Drückt derselbe Spieler erneut, passiert
        nichts. Kommt der zweite Druck zu spät, ist der Versuch daneben (WRONG,
        -60 HP über den DataCenter) und beide müssen neu drücken.
        """
        if role not in (ROLE_P1, ROLE_P2):
            return StepResult(Outcome.IGNORED, state)
        if not (state["p1_unlocked"] and state["p2_unlocked"]):
            return StepResult(Outcome.IGNORED, state)

        sync_at = state.setdefault("sync_at", {ROLE_P1: None, ROLE_P2: None})
        if sync_at.get(role) is not None:
            return StepResult(Outcome.IGNORED, state)

        partner = ROLE_P2 if role == ROLE_P1 else ROLE_P1
        partner_at = sync_at.get(partner)
        if partner_at is not None and now - partner_at > cls.SYNC_WINDOW:
            sync_at[ROLE_P1] = None
            sync_at[ROLE_P2] = None
            return StepResult(Outcome.WRONG, state)

        sync_at[role] = now
        if partner_at is None:
            return StepResult(Outcome.PROGRESS, state)
        return StepResult(Outcome.SOLVED, state)


TASK_TYPES = {
    cls.kind: cls
    for cls in (ButtonTask, AlarmTask, FireProtocolTask, DataRescueTask)
}