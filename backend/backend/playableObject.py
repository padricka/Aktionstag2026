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

    WORD = "RENTE"
    LOGINS = ["REHA", "BUND", "DRV"]     # Rentenversicherung, kurz – Hex soll machbar bleiben
    PACKETS = len(WORD) + 1              # ein beschädigtes Paket dazu
    DISKS = 4
    ASCII_TABLE = {chr(c): c for c in range(ord("A"), ord("Z") + 1)}

    # Escape-Room-Verteilung (GAME_DESIGN.md, Aufgabe 3) – das Wort als Kette:
    #   RENTE → Caesar um k VOR → ASCII-Code → Prüfbit + 7 Bit (gerade Anzahl Einsen)
    #   Leitstand: Log (Login in Hex, Backup-Jobs, Schlüsselbund)
    #   Vorderseite: ASCII-Tabelle, Terminal (erst Login, dann das Wort)
    #   Rückseite: Backup-Platten, nach dem Einlegen Pakete + Key-ID im Paket-Kopf
    #   Die Regeln dazu (notes.RESCUE_NOTE) stehen jeweils bei einem anderen.
    @classmethod
    def create(cls, players):
        login = random.choice(cls.LOGINS)
        keys, key_id, k = cls._keyring()
        cipher = "".join(chr((ord(c) - ord("A") + k) % 26 + ord("A")) for c in cls.WORD)
        packets = [cls._packet(ord(c), healthy=True) for c in cipher]
        corrupt = random.randrange(cls.PACKETS)
        packets.insert(corrupt, cls._packet(random.choice(list(cls.ASCII_TABLE.values())), healthy=False))
        backups, serial = cls._backups()
        return {
            "word": cls.WORD,
            "login": login,
            "keys": keys,
            "key_id": key_id,
            "k": k,
            "cipher": cipher,
            "packets": packets,
            "corrupt": corrupt,
            "backups": backups,
            "serial": serial,
            "disks": random.sample([b["serial"] for b in backups], cls.DISKS),
            "mounted": False,
            "logged_in": False,
        }

    @staticmethod
    def _packet(code, healthy):
        """Prüfbit vorne + 7 Bit ASCII; heil = gerade Anzahl Einsen insgesamt."""
        bits = format(code, "07b")
        parity = bits.count("1") % 2
        return f"{parity if healthy else 1 - parity}{bits}"

    @staticmethod
    def _keyring():
        """Schlüsselbund: der richtige (aktiv), sein REVOKED-Zwilling mit gleicher ID,
        ein anderer aktiver und ein abgelaufener. Schlüssel 1–9, alle verschieden."""
        key_id, other_id, old_id = random.sample(range(1, 16), 3)
        k, twin, other, old = random.sample(range(1, 10), 4)
        keys = [
            {"id": key_id, "key": format(k, "04b"), "status": "aktiv"},
            {"id": key_id, "key": format(twin, "04b"), "status": "REVOKED"},
            {"id": other_id, "key": format(other, "04b"), "status": "aktiv"},
            {"id": old_id, "key": format(old, "04b"), "status": "abgelaufen"},
        ]
        random.shuffle(keys)
        keys.sort(key=lambda s: s["id"])
        return keys, key_id, k

    @classmethod
    def _backups(cls):
        """Vier Backup-Jobs über einen Monatswechsel: zwei Ende Monat m, zwei Anfang m+1.
        Das allerneueste ist FEHLER, das richtige das zweitneueste. Als Text verglichen
        („28.03.“ > „03.04.“) sieht ein altes Backup neuer aus – die Falle zu ①."""
        month = random.randint(1, 11)
        early = sorted(random.sample(range(20, 29), 2))
        late = sorted(random.sample(range(1, 10), 2))
        dates = [(month, d) for d in early] + [(month + 1, d) for d in late]
        serials = random.sample(range(1000, 10000), cls.DISKS)
        status = ["OK", "OK", "OK", "FEHLER"]                  # chronologisch, neuestes kaputt
        backups = [
            {"date": f"{d:02d}.{m:02d}.", "serial": f"SN-{s}", "status": st}
            for (m, d), s, st in zip(dates, serials, status)
        ]
        serial = backups[2]["serial"]
        random.shuffle(backups)
        return backups, serial

    @classmethod
    def views(cls, state):
        mounted = state["mounted"]
        return {
            ROLE_M: {
                "type": "rescue_log",
                "login_hex": [f"0x{ord(c):02X}" for c in state["login"]],
                "backups": state["backups"],
                "keys": state["keys"],
                "note": notes.piece(notes.RESCUE_NOTE, ROLE_M),
            },
            ROLE_P1: {
                "type": "rescue_terminal",
                "ascii_table": cls.ASCII_TABLE,
                "login_len": len(state["login"]),
                "logged_in": state["logged_in"],
                "word_len": len(state["word"]),
                "note": notes.piece(notes.RESCUE_NOTE, ROLE_P1),
            },
            ROLE_P2: {
                "type": "packet_dump",
                "disks": state["disks"],
                "mounted": mounted,
                "key_id": format(state["key_id"], "04b") if mounted else None,
                "packets": state["packets"] if mounted else None,
                "note": notes.piece(notes.RESCUE_NOTE, ROLE_P2),
            },
        }

    @classmethod
    def handle_input(cls, state, player_name, role, data, now):
        value = str(data.value).strip().upper()

        if data.target == "mount_disk" and role == ROLE_P2:
            if state["mounted"]:
                return StepResult(Outcome.IGNORED, state)
            if value != state["serial"]:
                return StepResult(Outcome.WRONG, state)
            state["mounted"] = True
            return StepResult(Outcome.PROGRESS, state)

        if data.target == "terminal_login" and role == ROLE_P1:
            if state["logged_in"] or not value:
                return StepResult(Outcome.IGNORED, state)
            if value != state["login"]:
                return StepResult(Outcome.WRONG, state)
            state["logged_in"] = True
            return StepResult(Outcome.PROGRESS, state)

        if data.target == "rescue_word" and role == ROLE_P1:
            if not state["logged_in"] or not value:
                return StepResult(Outcome.IGNORED, state)
            if value != state["word"]:
                return StepResult(Outcome.WRONG, state)
            return StepResult(Outcome.SOLVED, state)

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