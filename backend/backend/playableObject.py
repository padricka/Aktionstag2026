from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import random

from . import notes

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
    # Ablenker auf der Tastatur des Leitstands. Die Tastatur wird pro Aufgabe gemischt,
    # sonst stünden die echten Code-Symbole immer vorne. Die Kabel-Symbole gehören
    # dazu, weil Regel ③ eins davon in den Code setzen kann.
    KEYBOARD_DECOYS = ['dreieck-voll', 'herz', 'sechseck', 'blitz']
    # Aufkleber-Farben. Ihre Reihenfolge (nur der Leitstand kennt sie) ordnet den Code.
    STICKER_COLORS = ["ROT", "GELB", "GRÜN", "BLAU"]
    # Wie oft die LED blinkt bzw. ein Aufkleber zerkratzt ist (jede Runde neu gewürfelt)
    BLINK_CHANCE = 0.5
    SCRATCH_CHANCE = 0.6

    # Escape-Room-Verteilung (GAME_DESIGN.md, Aufgabe 1) + zerrissene Wartungsnotiz:
    #   Leitstand  sieht WELCHER Steckplatz brennt, ob die LED blinkt, die Farbfolge -> Code
    #   Vorderseite sieht die Kabel (Symbole in Steckplatz-Reihenfolge)           -> kappt eins
    #   Rückseite  sieht die Code-Symbole auf farbigen Aufklebern, evtl. zerkratzt
    # Regeln auf der Notiz (notes.ALARM_NOTE):
    #   ① nie das Kabel am Brandplatz: gerade Nummer → links daneben, ungerade → rechts
    #   ② Code = Farbfolge; blinkt die LED → rückwärts
    #   ③ zerkratzter Aufkleber → dort gilt das Symbol vom Kabel am Brandplatz
    @classmethod
    def create(cls, players):
        slot = random.randrange(len(cls.COMPONENTS))
        broken = cls.COMPONENTS[slot]
        target = cls.COMPONENTS[cls._cut_index(slot)]

        code = list(cls.CODE_POOL)
        random.shuffle(code)
        color_order = list(cls.STICKER_COLORS)
        random.shuffle(color_order)
        # Das i-te Code-Symbol bekommt die i-te Farbe der Farb-Reihenfolge ...
        stickers = [{"symbol": s, "color": c} for s, c in zip(code, color_order)]
        # ... die Rückseite sieht die Aufkleber aber gemischt.
        random.shuffle(stickers)
        keyboard = cls.CODE_POOL + [c["symbol"] for c in cls.COMPONENTS] + cls.KEYBOARD_DECOYS
        random.shuffle(keyboard)

        led = "blinkt" if random.random() < cls.BLINK_CHANCE else "leuchtet"
        scratched = random.choice(color_order) if random.random() < cls.SCRATCH_CHANCE else None

        # Lösung nach den Regeln der Notiz
        order = list(reversed(color_order)) if led == "blinkt" else list(color_order)
        by_color = {s["color"]: s["symbol"] for s in stickers}
        solution = [broken["symbol"] if c == scratched else by_color[c] for c in order]

        return {
            "keyboard": keyboard,
            "burning_slot": slot + 1,
            "broken_id": broken["id"],
            "broken_symbol": broken["symbol"],
            "target_id": target["id"],
            "target_symbol": target["symbol"],
            "led": led,
            "scratched": scratched,
            "code": code,
            "solution": solution,
            "color_order": color_order,
            "stickers": stickers,
            "switch_ok": False,
            "cmd_ok": False,
        }

    @staticmethod
    def _cut_index(slot):
        """Regel ①: Steckplatz-Nummer = slot + 1; gerade → links daneben, ungerade → rechts."""
        nummer = slot + 1
        return nummer - 2 if nummer % 2 == 0 else nummer

    @classmethod
    def views(cls, state):
        return {
            ROLE_M: {
                "type": "alarm_leds",
                "slots": len(cls.COMPONENTS),
                "burning_slot": state["burning_slot"],
                "color_order": state["color_order"],
                "led": state["led"],
                "keyboard": state["keyboard"],
                "p_done": state["cmd_ok"],
                "note": notes.piece(notes.ALARM_NOTE, ROLE_M),
            },
            ROLE_P1: {
                "type": "main_switches",
                "switches": [c["symbol"] for c in cls.COMPONENTS],
                "p_done": state["switch_ok"],
                "note": notes.piece(notes.ALARM_NOTE, ROLE_P1),
            },
            ROLE_P2: {
                "type": "code_stickers",
                # zerkratzt: Farbe noch erkennbar, das Symbol nicht mehr
                "stickers": [
                    {"symbol": None, "color": s["color"], "scratched": True}
                    if s["color"] == state["scratched"] else s
                    for s in state["stickers"]
                ],
                "note": notes.piece(notes.ALARM_NOTE, ROLE_P2),
            },
        }

    @classmethod
    def handle_input(cls, state, player_name, role, data, now):
        value = str(data.value).strip().lower()

        if data.target == "main_switch" and role == ROLE_P1:
            if value not in (state["target_symbol"].lower(), state["target_id"].lower()):
                return StepResult(Outcome.WRONG, state)
            state["switch_ok"] = True

        elif data.target == "shutdown_cmd" and role == ROLE_M:
            expected = ",".join(state["solution"]).lower()
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

    RACKS = ["A-01", "A-02", "B-01", "B-02"]
    AGENTS = ["WASSER", "SCHAUM", "CO2", "INERTGAS", "ABSCHOTTEN"]
    # Brandgut → Anzeige auf der Rückseite und Löschmittel laut Löschplan ①
    MATERIALS = {
        "PAPIER": {"label": "Papierarchiv", "agent": "WASSER"},
        "KABEL": {"label": "Kabelbaum", "agent": "SCHAUM"},
        "SERVER": {"label": "Server", "agent": "INERTGAS"},
        "AKKU": {"label": "USV-Akku (Lithium)", "agent": "ABSCHOTTEN"},
    }
    AKKU_CHANCE = 0.5
    RM_OFFSET = 120          # Rauchmelder zeigen Ortszeit = UTC + 2 h (Löschplan ③)
    RELEASE_WINDOW = 3       # Sekunden für die Vier-Augen-Freigabe (Löschplan ④)

    # Escape-Room-Verteilung (GAME_DESIGN.md, Aufgabe 2): Log nur am Leitstand,
    # Strom nur vorne, Brandgut nur hinten; die Regeln stehen auf dem Löschplan
    # jeweils bei dem, der die Fakten dazu NICHT sieht.
    @classmethod
    def create(cls, players):
        fires = random.sample(cls.RACKS, FIRE_SEQUENCE_LEN)      # in Reihenfolge der Meldung
        spare = next(r for r in cls.RACKS if r not in fires)

        power = {r: random.random() < 0.5 for r in cls.RACKS}
        material = {spare: random.choice(list(cls.MATERIALS))}
        # Strom-Regel kommt immer vor: ein Brand mit Papier/Kabel unter Strom
        akku, override, *rest = random.sample(fires, len(fires))
        material[override] = random.choice(["PAPIER", "KABEL"])
        power[override] = True
        material[akku] = "AKKU" if random.random() < cls.AKKU_CHANCE else random.choice(["PAPIER", "KABEL", "SERVER"])
        for r in rest:
            material[r] = random.choice(["PAPIER", "KABEL", "SERVER"])

        sequence = [{"rack": r, "agent": cls._agent(material[r], power[r])} for r in fires]

        return {
            "racks": [{"rack": r, "power": power[r], "material": material[r]} for r in cls.RACKS],
            "log": cls._log(fires, spare),
            "sequence": sequence,
            "step": 0,
            "p1_done": False,
            "release": {},
        }

    @classmethod
    def _agent(cls, material, power):
        agent = cls.MATERIALS[material]["agent"]
        if power and agent in ("WASSER", "SCHAUM"):
            return "CO2"
        return agent

    @classmethod
    def _log(cls, fires, spare):
        """Brandmelde-Log: echte Meldungen + ein Probealarm, sortiert nach ANGEZEIGTER
        Uhrzeit – wer die Zeitzonen (③) nicht beachtet, liest die falsche Reihenfolge."""
        start = random.randint(7 * 60, 20 * 60)
        utc = [start]
        for _ in fires[1:]:
            utc.append(utc[-1] + random.randint(3, 12))

        while True:
            sources = [random.choice(["BMZ", "RM"]) for _ in fires]
            shown = [t + (cls.RM_OFFSET if s == "RM" else 0) for t, s in zip(utc, sources)]
            if sorted(range(len(fires)), key=lambda i: shown[i]) != list(range(len(fires))):
                break

        entries = [
            {"minutes": m, "source": s, "rack": r, "test": False}
            for m, s, r in zip(shown, sources, fires)
        ]
        test_source = random.choice(["BMZ", "RM"])
        test_rack = random.choice([spare, *fires])
        test_utc = random.randint(start - 15, utc[-1] + 15)
        entries.append({
            "minutes": test_utc + (cls.RM_OFFSET if test_source == "RM" else 0),
            "source": test_source, "rack": test_rack, "test": True,
        })
        entries.sort(key=lambda e: e["minutes"])
        return [
            {"time": f"{e['minutes'] // 60:02d}:{e['minutes'] % 60:02d}",
             "source": e["source"], "rack": e["rack"], "test": e["test"]}
            for e in entries
        ]

    @classmethod
    def views(cls, state):
        release = {"armed": state["p1_done"], "window": cls.RELEASE_WINDOW}
        return {
            ROLE_M: {
                "type": "fire_log",
                "log": state["log"],
                "release": release,
                "note": notes.piece(notes.FIRE_NOTE, ROLE_M),
            },
            ROLE_P1: {
                "type": "valve_panel",
                "racks": cls.RACKS,
                "agents": cls.AGENTS,
                "power": {r["rack"]: r["power"] for r in state["racks"]},
                "sequence_len": len(state["sequence"]),
                "step": state["step"],
                "p_done": state["p1_done"],
                "note": notes.piece(notes.FIRE_NOTE, ROLE_P1),
            },
            ROLE_P2: {
                "type": "rack_rear",
                "rear": [
                    {"rack": r["rack"], "material": r["material"],
                     "label": cls.MATERIALS[r["material"]]["label"]}
                    for r in state["racks"]
                ],
                "release": release,
                "note": notes.piece(notes.FIRE_NOTE, ROLE_P2),
            },
        }

    @classmethod
    def handle_input(cls, state, player_name, role, data, now):
        if data.target == "valve_action" and role == ROLE_P1:
            if state["p1_done"]:
                return StepResult(Outcome.IGNORED, state)
            rack, _, agent = str(data.value).strip().upper().partition(":")
            expected = state["sequence"][state["step"]]
            if rack != expected["rack"] or agent != expected["agent"]:
                return StepResult(Outcome.WRONG, state)
            state["step"] += 1
            if state["step"] >= len(state["sequence"]):
                state["p1_done"] = True
            return StepResult(Outcome.PROGRESS, state)

        if data.target == "release" and role in (ROLE_M, ROLE_P2):
            if not state["p1_done"]:
                return StepResult(Outcome.IGNORED, state)
            other = ROLE_P2 if role == ROLE_M else ROLE_M
            pressed = state["release"].get(other)
            if pressed is not None and now - pressed <= cls.RELEASE_WINDOW:
                return StepResult(Outcome.SOLVED, state)
            # zu spät oder als Erster: dieser Druck wartet auf den anderen
            state["release"] = {role: now}
            return StepResult(Outcome.PROGRESS, state)

        return StepResult(Outcome.IGNORED, state)


# --------------------------------------------------------------------------- DataRescue
class DataRescueTask(PlayableObject):
    kind = "data_rescue"
    instruction = "Daten retten!"

    WORDS = ["SERVER", "BACKUP", "DATEN", "RETTEN", "SICHERN", "CLOUD"]
    # Binärwerte-Pool für die Rückseite: Einsen vorne (Leitstand: 128/64/32/16)
    # UND hinten (Rückseite: 8/4/2/1), damit beide gebraucht werden. Werte wie
    # 101 oder 110 fallen raus – die sähen selbst wie Binärzahlen aus.
    # (Früher nur Buchstaben 65–90: immer 010xxxxx, 128 und 32 kamen nie vor.)
    BINARY_VALUES = [
        v for v in range(17, 256)
        if v & 0b11110000 and v & 0b00001111 and set(str(v)) - {"0", "1"}
    ]

    @classmethod
    def create(cls, players):
        word = random.choice(cls.WORDS)
        p1_codes = [ord(c) for c in word]

        # Zwei unterschiedliche Werte zufällig ziehen
        p2_values = random.sample(cls.BINARY_VALUES, 2)
        p2_binary = [format(v, "08b") for v in p2_values]

        return {
            "p1_word": word,
            "p1_codes": p1_codes,
            "p2_values": p2_values,
            "p2_binary": p2_binary,
            "p1_unlocked": False,
            "p2_unlocked": False,
        }

    # Escape-Room-Verteilung (GAME_DESIGN.md, Aufgabe 3):
    #   Leitstand   hat die ASCII-Tabelle A–M und die oberen Bit-Stellenwerte
    #   Vorderseite hat die ASCII-Codes des Worts und die Tabelle N–Z
    #   Rückseite   hat die Binärzahlen und die unteren Bit-Stellenwerte
    # -> beide brauchen den Leitstand, um ihren Knopf freizuschalten.
    ASCII_HALF_MASTER = {chr(c): c for c in range(ord("A"), ord("M") + 1)}
    ASCII_HALF_P1 = {chr(c): c for c in range(ord("N"), ord("Z") + 1)}
    PLACE_VALUES_MASTER = [128, 64, 32, 16]
    PLACE_VALUES_P2 = [8, 4, 2, 1]

    @classmethod
    def views(cls, state):
        return {
            ROLE_M: {
                "type": "ascii_binary_tables",
                "ascii_half": cls.ASCII_HALF_MASTER,
                "place_values": cls.PLACE_VALUES_MASTER,
                "p1_status": "FREIGESCHALTET" if state["p1_unlocked"] else "GESPERRT",
                "p2_status": "FREIGESCHALTET" if state["p2_unlocked"] else "GESPERRT",
            },
            ROLE_P1: {
                "type": "ascii_puzzle",
                "ascii_codes": state["p1_codes"],
                "ascii_half": cls.ASCII_HALF_P1,
                "button_unlocked": state["p1_unlocked"],
            },
            ROLE_P2: {
                "type": "binary_puzzle",
                "binary_codes": state["p2_binary"],
                "place_values": cls.PLACE_VALUES_P2,
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
            if role == ROLE_M:
                return StepResult(Outcome.IGNORED, state)
            if not (state.get("p1_unlocked") and state.get("p2_unlocked")):
                return StepResult(Outcome.IGNORED, state)

            if role == ROLE_P1:
                state["sync_p1_time"] = now
            elif role == ROLE_P2:
                state["sync_p2_time"] = now

            t1 = state.get("sync_p1_time")
            t2 = state.get("sync_p2_time")

            if t1 is not None and t2 is not None:
                if abs(t1 - t2) <= 3:
                    return StepResult(Outcome.SOLVED, state)

            return StepResult(Outcome.PROGRESS, state)

        return StepResult(Outcome.IGNORED, state)


# --------------------------------------------------------------------------- Reboot
class RebootTask(PlayableObject):
    kind = "reboot"
    instruction = "Server neu starten!"

    # Finale (GAME_DESIGN.md): Jede Rolle kennt EINE Ziffer des Neustart-Codes,
    # die Reihenfolge ist die der Aufgaben. Nur der Leitstand hat das Terminal.
    #   Ziffer 1 (Alarm)          -> Rückseite
    #   Ziffer 2 (Löschprotokoll) -> Leitstand
    #   Ziffer 3 (Datenrettung)   -> Vorderseite
    DIGIT_FOR_ROLE = {ROLE_P2: 0, ROLE_M: 1, ROLE_P1: 2}

    @classmethod
    def create(cls, players, digits=None):
        return {"digits": list(digits or [])}

    @classmethod
    def views(cls, state):
        digits = state.get("digits") or []
        return {
            role: {
                "type": "reboot",
                "digit": digits[idx] if idx < len(digits) else None,
                "terminal": role == ROLE_M,
            }
            for role, idx in cls.DIGIT_FOR_ROLE.items()
        }

    @classmethod
    def handle_input(cls, state, player_name, role, data, now):
        if data.target != "reboot_code" or role != ROLE_M or not state.get("digits"):
            return StepResult(Outcome.IGNORED, state)
        versuch = "".join(str(data.value).split())
        if versuch != "".join(str(d) for d in state["digits"]):
            return StepResult(Outcome.WRONG, state)
        return StepResult(Outcome.SOLVED, state)


TASK_TYPES = {
    cls.kind: cls
    for cls in (ButtonTask, AlarmTask, FireProtocolTask, DataRescueTask, RebootTask)
}