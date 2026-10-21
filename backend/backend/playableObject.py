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
    message: str = ""        # bei WRONG: was falsch war (geht an den Spieler)
    persist: bool = False    # bei WRONG: Zustand trotzdem speichern (z. B. Schlüssel zurück)


def hint(hint_id: str, label: str, text: str, done: bool) -> dict:
    """Ein Hilfe-Thema: id fürs Abreißen, label für den Block, text für den Zettel."""
    return {"id": hint_id, "label": label, "text": text, "done": bool(done)}


class PlayableObject(ABC):
    kind: str
    instruction: str
    # Hilfe-Themen, die der Host am Beamer vom Abreißblock reißen kann (GAME_DESIGN.md)
    HINTS = 0

    @classmethod
    def hints(cls, state: dict) -> list[dict]:
        """Alle Hilfe-Themen dieser Runde in Lösungs-Reihenfolge, je {id, label, text, done};
        done = der Schritt ist laut Spielstand schon erledigt (Thema kommt vom Block)."""
        return []

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

    # ------------------------------------------------------------- Hilfe-Notizen
    # Ein Thema je Schritt; „done“ sagt, ob der Schritt laut Spielstand schon erledigt ist
    HINTS = 4
    SYMBOL_NAMES = {
        "raute": "Raute", "dreieck": "Dreieck (leer)", "quadrat": "Quadrat", "kreis": "Kreis",
        "dreieck-runter": "Dreieck nach unten (leer)", "dreieck-runter-voll": "Dreieck nach unten (voll)",
        "kreuz": "Kreuz", "stern": "Stern",
    }

    @classmethod
    def hints(cls, state):
        brand = state["burning_slot"]
        kappen = cls._cut_index(brand - 1) + 1
        order = list(reversed(state["color_order"])) if state["led"] == "blinkt" else state["color_order"]
        if state["scratched"]:
            kratzer = (f"Der zerkratzte {state['scratched'].lower()}e Aufkleber zählt als "
                       f"{cls.SYMBOL_NAMES[state['broken_symbol']]} – das Symbol vom kaputten Kabel an der roten Stelle.")
        else:
            kratzer = "Diesmal ist kein Aufkleber zerkratzt – Regel ③ braucht ihr in dieser Runde nicht."
        code_offen = not state["cmd_ok"]
        return [
            hint("cable", "Welches Kabel?",
                 f"Die LED ist rot an Stelle {brand}. Die Vorderseite kappt deshalb das Kabel an "
                 f"Stelle {kappen} ({'links' if brand % 2 == 0 else 'rechts'} daneben) – nie das kaputte.",
                 state["switch_ok"]),
            hint("order", "LED und Farbfolge",
                 f"Die LED {state['led']} – der Code ist die Farbfolge "
                 f"{'rückwärts' if state['led'] == 'blinkt' else 'vorwärts'}: {' → '.join(order)}.",
                 not code_offen),
            hint("symbols", "Welches Symbol zuerst?",
                 f"Der Code beginnt mit: {cls.SYMBOL_NAMES[state['solution'][0]]}. Die Rückseite sagt, "
                 "welches Symbol auf den anderen Farben klebt.",
                 not code_offen),
            hint("scratch", "Zerkratzter Aufkleber", kratzer, not code_offen),
        ]

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

    # ------------------------------------------------------------- Hilfe-Notizen
    HINTS = 5

    @classmethod
    def hints(cls, state):
        probe = next(e for e in state["log"] if e["test"])
        reihenfolge = " → ".join(s["rack"] for s in state["sequence"])
        racks = {r["rack"]: r for r in state["racks"]}
        strom = next(
            i for i, s in enumerate(state["sequence"])
            if racks[s["rack"]]["power"] and racks[s["rack"]]["material"] in ("PAPIER", "KABEL")
        )
        rack = state["sequence"][strom]["rack"]
        geloescht = state["p1_done"]
        return [
            hint("probe", "Probealarm?",
                 f"Die Meldung „{probe['time']} {probe['source']} Schrank {probe['rack']}“ ist mit [TEST] "
                 "markiert – nur ein Probealarm, ignorieren.",
                 geloescht or state["step"] > 0),
            hint("order", "Reihenfolge",
                 f"Die Rauchmelder (RM) gehen 2 Stunden vor: bei RM-Zeiten 2 Stunden abziehen. Gelöscht wird in dieser "
                 f"Reihenfolge: {reihenfolge}.",
                 geloescht),
            hint("power", "Strom / CO2",
                 f"Schrank {rack} steht unter Strom und hat {cls.MATERIALS[racks[rack]['material']]['label']} – "
                 "dort kein Wasser und kein Schaum, sondern CO2.",
                 state["step"] > strom),
            hint("agents", "Löschmittel",
                 "Löschmittel: " + ", ".join(f"{s['rack']}: {s['agent']}" for s in state["sequence"]) + ".",
                 geloescht),
            hint("release", "Freigabe",
                 "Leitstand und Rückseite zählen laut „3, 2, 1“ und drücken gleichzeitig FREIGABE – "
                 "höchstens 3 Sekunden Abstand. Einzeln drücken reicht nicht.",
                 False),
        ]

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

    # 6-Buchstaben-Wörter der Rentenversicherung – eins wird gerettet, ein anderes ist die Falle
    WORDS = ["RENTEN", "ANTRAG", "WAISEN", "WITWEN"]
    DISKS = 4
    KEY_NAMES = ["ALPHA", "BRAVO", "DELTA", "ECHO", "KILO", "SIERRA"]

    # Escape-Room-Verteilung (GAME_DESIGN.md, Aufgabe 3, leichte Fassung) – das Wort als Kette:
    #   Platte (Backups beim Leitstand) → Nr. auf der Platte, 4-stellig binär → gültiger
    #   Schlüssel im Schlüsselbund → dessen Tabelle (Rückseite) → Codes in der Code-Tabelle
    #   der Vorderseite nachschlagen → Wort. Nichts muss lang gerechnet werden.
    #   Die Regeln dazu (notes.RESCUE_NOTE) stehen jeweils bei einem anderen.
    @classmethod
    def create(cls, players):
        word, decoy = random.sample(cls.WORDS, 2)
        # Code-Tabelle frei erfunden (kein ASCII): 26 verschiedene 8-stellige Codes, jede Runde neu
        codes = random.sample(range(256), 26)
        code_table = {chr(ord("A") + i): format(c, "08b") for i, c in enumerate(codes)}
        keys, key_nr, key_name, other_name = cls._keyring()
        tables = [
            {"name": key_name, "rows": [code_table[c] for c in word]},
            {"name": other_name, "rows": [code_table[c] for c in decoy]},
        ]
        random.shuffle(tables)
        backups, serial = cls._backups()
        return {
            "word": word,
            "decoy": decoy,
            "code_table": code_table,
            "keys": keys,
            "key_nr": key_nr,
            "key_name": key_name,
            "tables": tables,
            "backups": backups,
            "serial": serial,
            "disks": random.sample([b["serial"] for b in backups], cls.DISKS),
            "mounted": False,
        }

    @classmethod
    def _keyring(cls):
        """Schlüsselbund: zwei gültige (der richtige und der zur Falle-Tabelle) und zwei
        gesperrte. Nr. 1–15 (passt in 4 Stellen), Namen und Nr. alle verschieden."""
        nummern = random.sample(range(1, 16), 4)
        namen = random.sample(cls.KEY_NAMES, 4)
        keys = [
            {"nr": n, "name": name, "status": status}
            for n, name, status in zip(nummern, namen, ["gültig", "gültig", "gesperrt", "gesperrt"])
        ]
        key_nr, key_name, other_name = nummern[0], namen[0], namen[1]
        keys.sort(key=lambda s: s["nr"])
        return keys, key_nr, key_name, other_name

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
                "backups": state["backups"],
                "keys": state["keys"],
                "note": notes.piece(notes.RESCUE_NOTE, ROLE_M),
            },
            ROLE_P1: {
                "type": "rescue_terminal",
                "code_table": state["code_table"],
                "word_len": len(state["word"]),
                "note": notes.piece(notes.RESCUE_NOTE, ROLE_P1),
            },
            ROLE_P2: {
                "type": "packet_dump",
                "disks": state["disks"],
                "mounted": mounted,
                "key_id": format(state["key_nr"], "04b") if mounted else None,
                "tables": state["tables"] if mounted else None,
                "note": notes.piece(notes.RESCUE_NOTE, ROLE_P2),
            },
        }

    # ------------------------------------------------------------- Hilfe-Notizen
    HINTS = 5

    @classmethod
    def hints(cls, state):
        nr = state["key_nr"]
        bits = format(nr, "04b")
        werte = [w for w, z in zip((8, 4, 2, 1), bits) if z == "1"]
        erster = state["word"][0]
        return [
            hint("disk", "Backup-Platte",
                 "Das neueste Backup ist kaputt (FEHLER). Datum: erst Monat, dann Tag vergleichen – "
                 f"die richtige Platte ist {state['serial']}.",
                 state["mounted"]),
            hint("number", "Nr. auf der Platte",
                 f"Auf der Platte steht {bits}: über den Einsen stehen {' + '.join(map(str, werte))} = {nr}.",
                 False),
            hint("key", "Welcher Schlüssel?",
                 f"Im Schlüsselbund ist der gültige Schlüssel mit Nr. {nr}: {state['key_name']}.",
                 False),
            hint("table", "Welche Tabelle?",
                 f"Die richtige Tabelle ist {state['key_name']} – die andere ergibt ein falsches Wort.",
                 False),
            hint("word", "Codes nachschlagen",
                 f"Der erste Code der richtigen Tabelle ist {state['code_table'][erster]} – in der "
                 f"Code-Tabelle ist das ein {erster}. Das Wort hat 6 Buchstaben.",
                 False),
        ]

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

        if data.target == "rescue_word" and role == ROLE_P1:
            if not value:
                return StepResult(Outcome.IGNORED, state)
            if value != state["word"]:
                return StepResult(Outcome.WRONG, state)
            return StepResult(Outcome.SOLVED, state)

        return StepResult(Outcome.IGNORED, state)


# --------------------------------------------------------------------------- Reparatur
class RepairTask(PlayableObject):
    kind = "repair"
    instruction = "Server reparieren und hochfahren!"

    # Finale (GAME_DESIGN.md): die Teile aus den Fundorten einbauen, dann der
    # Drei-Schlüssel-Start. Wer was sieht und welche Regel wo steht: test_taskReparatur.py.
    BAYS = 4
    FAN_SLOTS = 3
    PSU_BAYS = 2
    KEY_ORDER = [(ROLE_P2, "strom"), (ROLE_P1, "kuehlung"), (ROLE_M, "system")]
    KEY_WINDOW = 5.0   # Sekunden zwischen zwei Schlüsseln
    PARTS = {
        "disk": {"name": "Backup-Platte", "role": ROLE_P1},
        "fan": {"name": "Lüfter", "role": ROLE_P1},
        "psu": {"name": "Netzteil", "role": ROLE_P2},
    }
    ORDER = ["disk", "fan", "psu"]

    @classmethod
    def create(cls, players, parts_spec=None):
        spec = parts_spec or {}
        disk_label = (spec.get("disk") or {}).get("label") or f"RAID-Platz {random.randint(1, cls.BAYS)}"
        psu_label = (spec.get("psu") or {}).get("label") or random.choice(["115 V", "230 V"])
        disk_bay = int(disk_label.split()[-1])

        # Schächte: Ziel leer, dazu ein weiterer leerer, einer mit roter LED (defekt), einer belegt
        andere = [n for n in range(1, cls.BAYS + 1) if n != disk_bay]
        random.shuffle(andere)
        bays = ["aus"] * cls.BAYS
        bays[andere[0] - 1] = "rot"
        bays[andere[1] - 1] = "gruen"

        gang = random.choice(["Warmgang", "Kaltgang"])   # Schild auf der Rückseite
        psu_bay = random.randint(1, cls.PSU_BAYS)
        fuses = ["durch"] * cls.PSU_BAYS
        fuses[psu_bay - 1] = "ok"

        return {
            "labels": {"disk": disk_label, "psu": psu_label, "fan": (spec.get("fan") or {}).get("label", "")},
            "disk_bay": disk_bay,
            "bays": bays,
            "fan_slot": random.randint(1, cls.FAN_SLOTS),
            "gang": gang,
            # Luft strömt vom Kaltgang zum Warmgang: hinten Warmgang → Pfeil nach hinten
            "fan_dir": "hinten" if gang == "Warmgang" else "vorne",
            "psu_bay": psu_bay,
            "fuses": fuses,
            "volt": psu_label.split()[0],
            "orte": {teil: "kiste" for teil in cls.PARTS},
            "wartung": [],
            "keys": [],
        }

    @classmethod
    def _eingebaut(cls, state):
        return {teil: state["orte"][teil] == "eingebaut" for teil in cls.PARTS}

    @classmethod
    def _phase(cls, state):
        return "start" if all(cls._eingebaut(state).values()) else "einbau"

    @classmethod
    def _hand(cls, state, role):
        return [{"id": t, "name": cls.PARTS[t]["name"]} for t in cls.ORDER if state["orte"][t] == role]

    @classmethod
    def views(cls, state):
        gemeinsam = {
            "installed": cls._eingebaut(state),
            "phase": cls._phase(state),
            "keys": [k["key"] for k in state["keys"]],
        }
        return {
            ROLE_M: {
                "type": "repair_console",
                "parts": [
                    {"id": t, "name": cls.PARTS[t]["name"], "label": state["labels"][t], "ort": state["orte"][t]}
                    for t in cls.ORDER
                ],
                "console": {"bay": cls.BAYS, "fan": cls.FAN_SLOTS, "psu": cls.PSU_BAYS},
                "wartung": list(state["wartung"]),
                "note": notes.piece(notes.REPAIR_NOTE, ROLE_M),
                **gemeinsam,
            },
            ROLE_P1: {
                "type": "repair_front",
                # eingebaute Platte: ihr Schacht leuchtet jetzt grün
                "bays": [
                    {"nr": i + 1, "led": "gruen" if gemeinsam["installed"]["disk"] and i + 1 == state["disk_bay"] else led}
                    for i, led in enumerate(state["bays"])
                ],
                "fan_slots": [{"nr": n, "belegt": n != state["fan_slot"] or gemeinsam["installed"]["fan"]}
                              for n in range(1, cls.FAN_SLOTS + 1)],
                "hand": cls._hand(state, ROLE_P1),
                "note": notes.piece(notes.REPAIR_NOTE, ROLE_P1),
                **gemeinsam,
            },
            ROLE_P2: {
                "type": "repair_back",
                "psu_bays": [{"nr": i + 1, "sicherung": f} for i, f in enumerate(state["fuses"])],
                "gang": state["gang"],
                "hand": cls._hand(state, ROLE_P2),
                "note": notes.piece(notes.REPAIR_NOTE, ROLE_P2),
                **gemeinsam,
            },
        }

    # ------------------------------------------------------------- Hilfe-Notizen
    # In Lösungs-Reihenfolge; „done“ nach Spielstand (eingebaut, weitergegeben)
    HINTS = 6

    @classmethod
    def hints(cls, state):
        orte, eingebaut = state["orte"], cls._eingebaut(state)
        bay, slot, psu = state["disk_bay"], state["fan_slot"], state["psu_bay"]
        rot = state["bays"].index("rot") + 1
        richtig_verteilt = (orte["disk"] in (ROLE_P1, "eingebaut") and orte["fan"] in (ROLE_P1, "eingebaut")
                            and orte["psu"] in (ROLE_P2, "eingebaut"))
        richtung = "nach hinten ins Rack" if state["fan_dir"] == "hinten" else "nach vorne zu euch"
        return [
            hint("give", "Wer bekommt was?",
                 "Platte und Lüfter gehören zur Vorderseite, das Netzteil zur Rückseite. "
                 "Eingebaut wird in dieser Reihenfolge: Platte → Lüfter → Netzteil.",
                 richtig_verteilt),
            hint("maintenance", "Wartung und Konsole",
                 "Vor jedem Einbau schaltet der Leitstand den Platz auf WARTUNG, danach wieder zurück. "
                 f"Die Konsole zählt ab 0: Schacht {bay} = BAY {bay - 1}, Lüfterplatz {slot} = FAN {slot - 1}, "
                 f"Netzteilschacht {psu} = PSU {psu - 1}.",
                 all(eingebaut.values())),
            hint("disk", "Welcher Plattenschacht?",
                 f"Auf dem Etikett steht {state['labels']['disk']}: Die Platte kommt in Schacht {bay}. "
                 f"Schacht {rot} mit der roten LED ist defekt.",
                 eingebaut["disk"]),
            hint("fan", "Wie herum der Lüfter?",
                 f"Hinter dem Rack ist der {state['gang']}. Die Luft strömt vom Kaltgang zum Warmgang – "
                 f"der Pfeil zeigt {richtung} ({state['fan_dir']}). Er kommt in die Lücke, Platz {slot}.",
                 eingebaut["fan"]),
            hint("psu", "Netzteil",
                 f"Heil ist die Sicherung in Schacht {psu}. Den Spannungsschalter vorher auf "
                 f"{state['labels']['psu']} stellen – so steht es auf dem Etikett.",
                 eingebaut["psu"]),
            hint("keys", "Hochfahren",
                 "Erst alle Plätze in der Konsole aus der Wartung nehmen. Dann die Schlüssel: Strom "
                 "(Rückseite) → Kühlung (Vorderseite) → System (Leitstand), jeweils innerhalb von 5 Sekunden.",
                 False),
        ]

    @staticmethod
    def _fehler(state, text, persist=False):
        return StepResult(Outcome.WRONG, state, message=text, persist=persist)

    @classmethod
    def handle_input(cls, state, player_name, role, data, now):
        target = data.target
        value = str(data.value).strip()

        if role == ROLE_M and target == "give":
            teil, _, an = value.partition(":")
            if teil not in cls.PARTS or an not in (ROLE_P1, ROLE_P2) or state["orte"].get(teil) == "eingebaut":
                return StepResult(Outcome.IGNORED, state)
            state["orte"][teil] = an
            return StepResult(Outcome.PROGRESS, state)

        if target == "return" and role in (ROLE_P1, ROLE_P2):
            if state["orte"].get(value) != role:
                return StepResult(Outcome.IGNORED, state)
            state["orte"][value] = "kiste"
            return StepResult(Outcome.PROGRESS, state)

        if role == ROLE_M and target == "maintenance":
            art, _, idx = value.partition(":")
            grenzen = {"bay": cls.BAYS, "fan": cls.FAN_SLOTS, "psu": cls.PSU_BAYS}
            if art not in grenzen or not idx.isdigit() or int(idx) >= grenzen[art]:
                return StepResult(Outcome.IGNORED, state)
            platz = f"{art}:{int(idx)}"
            if platz in state["wartung"]:
                state["wartung"].remove(platz)
            else:
                state["wartung"].append(platz)
            return StepResult(Outcome.PROGRESS, state)

        if target in ("install_disk", "install_fan", "install_psu"):
            return cls._einbau(state, role, target, value)

        if target == "key":
            return cls._schluessel(state, role, value, now)

        return StepResult(Outcome.IGNORED, state)

    @classmethod
    def _einbau(cls, state, role, target, value):
        teil = target.removeprefix("install_")
        if state["orte"].get(teil) != role:
            return StepResult(Outcome.IGNORED, state)   # Teil nicht in der Hand

        vorher = cls.ORDER[: cls.ORDER.index(teil)]
        if any(state["orte"][t] != "eingebaut" for t in vorher):
            return cls._fehler(state, "Falsche Reihenfolge – erst Platte, dann Lüfter, Netzteil zuletzt.")

        nummer, _, extra = value.partition(":")
        if not nummer.isdigit():
            return StepResult(Outcome.IGNORED, state)
        nummer = int(nummer)
        art = {"disk": "bay", "fan": "fan", "psu": "psu"}[teil]
        if f"{art}:{nummer - 1}" not in state["wartung"]:
            return cls._fehler(state, f"Stromschlag! Platz {nummer} war nicht in Wartung.")

        if teil == "disk":
            led = state["bays"][nummer - 1] if 1 <= nummer <= cls.BAYS else None
            if led == "rot":
                return cls._fehler(state, f"Schacht {nummer} hat eine rote LED – dort ist alles defekt.")
            if led == "gruen":
                return cls._fehler(state, f"Schacht {nummer} ist schon belegt.")
            if nummer != state["disk_bay"]:
                return cls._fehler(state, "Falscher Schacht – die Nummer steht auf dem Etikett der Platte.")
        elif teil == "fan":
            if nummer != state["fan_slot"]:
                return cls._fehler(state, f"Lüfterplatz {nummer} ist schon belegt.")
            if extra != state["fan_dir"]:
                return cls._fehler(state, "Lüfter verkehrt herum – die Luft muss vom Kaltgang zum Warmgang.")
        else:
            if not 1 <= nummer <= cls.PSU_BAYS or state["fuses"][nummer - 1] != "ok":
                return cls._fehler(state, f"Schacht {nummer}: Sicherung durchgebrannt.")
            if extra != state["volt"]:
                return cls._fehler(state, "Falsche Spannung – sie steht auf dem Etikett des Netzteils.")

        state["orte"][teil] = "eingebaut"
        return StepResult(Outcome.PROGRESS, state)

    @classmethod
    def _schluessel(cls, state, role, value, now):
        if cls._phase(state) != "start" or (role, value) not in cls.KEY_ORDER:
            return StepResult(Outcome.IGNORED, state)
        if state["wartung"]:
            state["keys"] = []
            return cls._fehler(state, "Not-Aus: Ein Platz ist noch in Wartung.", persist=True)

        keys = state["keys"]
        if keys and now - keys[-1]["t"] > cls.KEY_WINDOW:
            keys = []   # zu langsam: von vorn
        if (role, value) != cls.KEY_ORDER[len(keys)]:
            state["keys"] = []
            return cls._fehler(state, "Falsche Reihenfolge der Schlüssel – alle zurück, von vorn.", persist=True)

        state["keys"] = keys + [{"key": value, "t": now}]
        if len(state["keys"]) == len(cls.KEY_ORDER):
            return StepResult(Outcome.SOLVED, state)
        return StepResult(Outcome.PROGRESS, state)


TASK_TYPES = {
    cls.kind: cls
    for cls in (ButtonTask, AlarmTask, FireProtocolTask, DataRescueTask, RepairTask)
}