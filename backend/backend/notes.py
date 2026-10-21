"""Notizzettel (GAME_DESIGN.md §4). Jede Rolle bekommt ihr Stück eines Zettels.

Der Zettel sieht zerrissen aus, aber kein Satz ist zerteilt: Jedes Stück trägt
eine VOLLSTÄNDIGE Regel – und zwar die, die der Spieler allein nicht anwenden
kann, weil die nötigen Fakten auf den Bildschirmen der anderen stehen.
„Ich kenne die Regel, du kennst die Fakten“ – so muss man reden.
"""

# Gleiche Werte wie ROLE_M / ROLE_P1 / ROLE_P2 in playableObject (dort importiert
# dieses Modul, deshalb hier ohne Rückimport)
M, V, R = "MASTER", "FI-SI", "FI-AE"


def _line(row, style, text):
    return {"row": row, "style": style, "text": text}


def piece(note, role):
    """Das Stück einer Rolle für die Ansicht: Teil x/3, gerissene Kanten, Zeilen."""
    p = note["pieces"][role]
    return {
        "id": note["id"],
        "title": note["title"],
        "part": p["part"],
        "of": len(note["pieces"]),
        "torn": p["torn"],
        "lines": p["lines"],
    }


# ------------------------------------------------------------------ Aufgabe 1 · Alarm
# Stile: typed (Schreibmaschine), stamp, rule (Regelanfang), text, strike (Falle), red, sign
ALARM_NOTE = {
    "id": "alarm",
    "title": "Wartungsnotiz",
    "pieces": {
        # Leitstand sieht LED + Farbfolge, braucht von der Rückseite die Aufkleber
        M: {
            "part": 1,
            "torn": ["right", "bottom"],
            "lines": [
                _line(0, "typed", "DRV SCHWABEN · RAUM B-04"),
                _line(1, "typed", "WARTUNGSNOTIZ · TEIL 1/3"),
                _line(3, "rule", "② Shutdown-Code = die Farbfolge"),
                _line(4, "text", "vom Monitor, Farbe für Farbe."),
                _line(5, "text", "Blinkt die LED, dann die"),
                _line(6, "text", "Farbfolge RÜCKWÄRTS eingeben!"),
                _line(8, "strike", "Code fängt immer mit ★ an."),
                _line(8, "red", "stimmt nicht!"),
            ],
        },
        # Vorderseite sieht die Kabel, braucht vom Leitstand die rote Stelle
        V: {
            "part": 2,
            "torn": ["left", "bottom"],
            "lines": [
                _line(0, "stamp", "NUR FÜR TECHNIKER"),
                _line(1, "typed", "WARTUNGSNOTIZ · TEIL 2/3"),
                _line(3, "rule", "① NIE das Kabel an der ROTEN Stelle"),
                _line(4, "text", "kappen – das ist kaputt! Stattdessen:"),
                _line(5, "text", "Stelle 2 oder 4 → das Kabel"),
                _line(6, "text", "LINKS daneben kappen."),
                _line(7, "text", "Stelle 1 oder 3 → das Kabel"),
                _line(8, "text", "RECHTS daneben kappen."),
            ],
        },
        # Rückseite sieht den Kratzer, braucht die rote Stelle (Leitstand) + Symbol (Vorderseite)
        R: {
            "part": 3,
            "torn": ["top"],
            "lines": [
                _line(0, "typed", "WARTUNGSNOTIZ · TEIL 3/3"),
                _line(2, "rule", "③ Ist ein Aufkleber zerkratzt,"),
                _line(3, "text", "gilt dort das Symbol vom"),
                _line(4, "text", "KAPUTTEN Kabel (an der roten"),
                _line(5, "text", "Stelle) – nicht vom gekappten!"),
                _line(7, "sign", "– M. Kaiser, IT"),
            ],
        },
    },
}


# ------------------------------------------------------------------ Aufgabe 2 · Löschprotokoll
FIRE_NOTE = {
    "id": "fire",
    "title": "Löschplan",
    "pieces": {
        # Leitstand kennt die Löschmittel, braucht Brandgut (Rückseite) + Strom (Vorderseite)
        M: {
            "part": 1,
            "torn": ["right", "bottom"],
            "lines": [
                _line(0, "typed", "DRV SCHWABEN · BRANDSCHUTZ"),
                _line(1, "typed", "LÖSCHPLAN · TEIL 1/3"),
                _line(3, "rule", "① Löschmittel je Brandgut:"),
                _line(4, "text", "Papier → WASSER"),
                _line(5, "text", "Kabel → SCHAUM"),
                _line(6, "text", "Server → INERTGAS"),
                _line(7, "text", "Rack unter Strom? Dann NIE"),
                _line(8, "text", "Wasser oder Schaum → CO2!"),
                _line(9, "text", "USV-Akku: NICHT löschen –"),
                _line(10, "text", "Rack ABSCHOTTEN!"),
                _line(12, "strike", "Wasser geht immer."),
                _line(12, "red", "NEIN!"),
            ],
        },
        # Vorderseite löscht, braucht das Log vom Leitstand
        V: {
            "part": 2,
            "torn": ["left", "bottom"],
            "lines": [
                _line(0, "stamp", "NUR FÜR TECHNIKER"),
                _line(1, "typed", "LÖSCHPLAN · TEIL 2/3"),
                _line(3, "rule", "② Gelöscht wird in der"),
                _line(4, "text", "Reihenfolge der Meldungen –"),
                _line(5, "text", "die ÄLTESTE zuerst!"),
                _line(6, "text", "[TEST]-Meldungen sind nur"),
                _line(7, "text", "Probealarme → ignorieren."),
            ],
        },
        # Rückseite kennt die Zeitzonen, braucht das Log; Freigabe mit dem Leitstand
        R: {
            "part": 3,
            "torn": ["top"],
            "lines": [
                _line(0, "typed", "LÖSCHPLAN · TEIL 3/3"),
                _line(2, "rule", "③ Uhrzeiten im Log: BMZ zeigt"),
                _line(3, "text", "UTC, Rauchmelder (RM) zeigen"),
                _line(4, "text", "Ortszeit = UTC + 2 Stunden."),
                _line(5, "text", "RM-Zeit also MINUS 2 h!"),
                _line(7, "rule", "④ Freigabe nur zu zweit:"),
                _line(8, "text", "Leitstand + Rückseite drücken"),
                _line(9, "text", "GLEICHZEITIG (max. 3 s)."),
                _line(11, "sign", "– M. Kaiser, IT"),
            ],
        },
    },
}


# ------------------------------------------------------------------ Aufgabe 3 · Datenrettung
# Mit Rechenbeispielen – die Regeln sollen auch ohne Informatik-Vorwissen klappen.
# Nummern in der Reihenfolge, in der man sie braucht.
RESCUE_NOTE = {
    "id": "rescue",
    "title": "Datenrettung",
    "pieces": {
        # Leitstand rechnet um und entschlüsselt – Pakete/Buchstaben haben die anderen
        M: {
            "part": 1,
            "torn": ["right", "bottom"],
            "lines": [
                _line(0, "typed", "DRV SCHWABEN · BACKUP-TEAM"),
                _line(1, "typed", "DATENRETTUNG · TEIL 1/3"),
                _line(3, "rule", "④ Binär → Dezimal:"),
                _line(4, "text", "1. Bit = Prüfbit, zählt NICHT!"),
                _line(5, "text", "Die 7 Bits danach sind wert:"),
                _line(6, "typed", "P · 64 · 32 · 16 · 8 · 4 · 2 · 1"),
                _line(7, "text", "Addiere alle Werte mit einer 1."),
                _line(8, "text", "Bsp: 1 1000011"),
                _line(9, "text", "→ 64 + 2 + 1 = 67"),
                _line(10, "text", "Key-ID: 4 Bits = 8 · 4 · 2 · 1"),
                _line(11, "text", "Bsp: 0110 → 4 + 2 = 6"),
                _line(13, "rule", "⑥ Jeden Buchstaben um k"),
                _line(14, "text", "im Alphabet ZURÜCK schieben."),
                _line(15, "text", "Bsp k = 3: F → E → D → C"),
                _line(16, "text", "Vor A kommt wieder Z."),
                _line(18, "strike", "Immer ROT13"),
                _line(18, "red", "stimmt nicht!"),
            ],
        },
        # Vorderseite meldet sich an und prüft – Hex hat der Leitstand, Pakete die Rückseite
        V: {
            "part": 2,
            "torn": ["left", "bottom"],
            "lines": [
                _line(0, "stamp", "NUR FÜR TECHNIKER"),
                _line(1, "typed", "DATENRETTUNG · TEIL 2/3"),
                _line(3, "rule", "② Login-Name steht in HEX:"),
                _line(4, "text", "0x + zwei Ziffern. Erste · 16,"),
                _line(5, "text", "zweite dazu. A=10 B=11 C=12"),
                _line(6, "text", "D=13 E=14 F=15."),
                _line(7, "text", "Bsp: 0x4E → 4 · 16 + 14 = 78"),
                _line(8, "text", "Zahl → Buchstabe: ASCII-Tabelle"),
                _line(9, "text", "Bsp: 78 → N (auch bei Paketen)"),
                _line(11, "rule", "③ Pakete prüfen: Einsen zählen!"),
                _line(12, "text", "GERADE Anzahl → Paket heil."),
                _line(13, "text", "UNGERADE → kaputt, weglassen!"),
                _line(14, "text", "Bsp: 1 1000011 → 4× 1 → heil"),
            ],
        },
        # Rückseite wählt Platte und Schlüssel – Daten dazu stehen im Log des Leitstands
        R: {
            "part": 3,
            "torn": ["top"],
            "lines": [
                _line(0, "typed", "DATENRETTUNG · TEIL 3/3"),
                _line(2, "rule", "① Richtige Backup-Platte: das"),
                _line(3, "text", "NEUESTE Backup mit Status OK."),
                _line(4, "text", "Datum = TAG.MONAT – erst den"),
                _line(5, "text", "Monat vergleichen, dann Tag!"),
                _line(6, "text", "Bsp: 03.04. neuer als 28.03."),
                _line(8, "rule", "⑤ Schlüssel k: Die Key-ID steht"),
                _line(9, "text", "im Paket-Kopf. Nimm den AKTIVEN"),
                _line(10, "text", "Schlüssel mit dieser ID –"),
                _line(11, "text", "nie REVOKED, nie abgelaufen!"),
                _line(12, "text", "Bsp: ID 6 → „KEY-ID 6 · aktiv“"),
                _line(14, "sign", "– M. Kaiser, IT"),
            ],
        },
    },
}


# ------------------------------------------------------------------ Finale · Reparatur
# Jedes Stück: die Regeln, für die man die Fakten der anderen braucht (Etiketten hat
# der Leitstand, Schächte die Vorderseite, Sicherungen und Gang-Schild die Rückseite).
REPAIR_NOTE = {
    "id": "repair",
    "title": "Einbauanleitung",
    "pieces": {
        # Leitstand: Teilekiste + Konsole – muss wissen, wer was einbaut und welcher Platz
        M: {
            "part": 1,
            "torn": ["right", "bottom"],
            "lines": [
                _line(0, "typed", "DRV SCHWABEN · RAUM B-04"),
                _line(1, "typed", "EINBAUANLEITUNG · TEIL 1/3"),
                _line(3, "rule", "① Reihenfolge: erst Platte,"),
                _line(4, "text", "dann Lüfter, Netzteil ZULETZT."),
                _line(5, "text", "Platte + Lüfter → Vorderseite,"),
                _line(6, "text", "Netzteil → Rückseite."),
                _line(8, "rule", "④ Vor jedem Einbau den Platz"),
                _line(9, "text", "in der Konsole auf WARTUNG –"),
                _line(10, "text", "sonst Stromschlag!"),
                _line(11, "text", "Konsole zählt ab 0:"),
                _line(12, "text", "Schacht 1 = BAY 0, Platz 2 = FAN 1"),
                _line(14, "rule", "⑤ Vor dem Hochfahren ALLE"),
                _line(15, "text", "Plätze aus der Wartung nehmen."),
            ],
        },
        # Vorderseite: Schächte + Lüfterwand – Etikett kennt der Leitstand, Gang die Rückseite
        V: {
            "part": 2,
            "torn": ["left", "bottom"],
            "lines": [
                _line(0, "stamp", "NUR FÜR TECHNIKER"),
                _line(1, "typed", "EINBAUANLEITUNG · TEIL 2/3"),
                _line(3, "rule", "② Platte in den Schacht mit"),
                _line(4, "text", "der Nummer vom Etikett"),
                _line(5, "text", "(RAID-Platz). Rote LED = defekt!"),
                _line(7, "rule", "Lüfter in die Lücke der Wand."),
                _line(8, "text", "Der Pfeil zeigt, wohin die Luft"),
                _line(9, "text", "strömt: immer vom KALTGANG"),
                _line(10, "text", "zum WARMGANG."),
                _line(12, "strike", "Pfeil zeigt immer nach vorne."),
                _line(12, "red", "falsch!"),
            ],
        },
        # Rückseite: Sicherungen + Gang-Schild – Spannung steht auf dem Etikett beim Leitstand
        R: {
            "part": 3,
            "torn": ["top"],
            "lines": [
                _line(0, "typed", "EINBAUANLEITUNG · TEIL 3/3"),
                _line(2, "rule", "③ Netzteil nur in den Schacht"),
                _line(3, "text", "mit HEILER Sicherung. Vorher"),
                _line(4, "text", "den Spannungsschalter auf den"),
                _line(5, "text", "Wert vom Etikett stellen!"),
                _line(7, "rule", "⑥ Hochfahren: drei Schlüssel"),
                _line(8, "text", "Strom (Rückseite) → Kühlung"),
                _line(9, "text", "(Vorderseite) → System"),
                _line(10, "text", "(Leitstand). Je max. 5 s Abstand!"),
                _line(12, "sign", "– M. Kaiser, IT"),
            ],
        },
    },
}
