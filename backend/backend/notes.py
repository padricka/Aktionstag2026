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
        # Vorderseite sieht die Kabel, braucht vom Leitstand den brennenden Platz
        V: {
            "part": 2,
            "torn": ["left", "bottom"],
            "lines": [
                _line(0, "stamp", "NUR FÜR TECHNIKER"),
                _line(1, "typed", "WARTUNGSNOTIZ · TEIL 2/3"),
                _line(3, "rule", "① NIE das Kabel am brennenden"),
                _line(4, "text", "Platz kappen! Stattdessen:"),
                _line(5, "text", "gerade Platznummer → das Kabel"),
                _line(6, "text", "LINKS daneben, ungerade → das"),
                _line(7, "text", "Kabel RECHTS daneben."),
            ],
        },
        # Rückseite sieht den Kratzer, braucht Platz (Leitstand) + Symbol (Vorderseite)
        R: {
            "part": 3,
            "torn": ["top"],
            "lines": [
                _line(0, "typed", "WARTUNGSNOTIZ · TEIL 3/3"),
                _line(2, "rule", "③ Ist ein Aufkleber zerkratzt,"),
                _line(3, "text", "gilt dort das Symbol vom Kabel"),
                _line(4, "text", "am BRENNENDEN Platz –"),
                _line(5, "text", "nicht vom gekappten!"),
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
RESCUE_NOTE = {
    "id": "rescue",
    "title": "Datenrettung",
    "pieces": {
        # Leitstand rechnet um, die Pakete liest ihm die Rückseite vor
        M: {
            "part": 1,
            "torn": ["right", "bottom"],
            "lines": [
                _line(0, "typed", "DRV SCHWABEN · BACKUP-TEAM"),
                _line(1, "typed", "DATENRETTUNG · TEIL 1/3"),
                _line(3, "rule", "② Binär → Dezimal:"),
                _line(4, "text", "1. Bit = Prüfbit, zählt NICHT!"),
                _line(5, "text", "Die 7 Bits danach sind wert:"),
                _line(6, "typed", "P · 64 · 32 · 16 · 8 · 4 · 2 · 1"),
                _line(7, "text", "Addiere alle Werte mit einer 1."),
                _line(8, "text", "Bsp: 1 1000011"),
                _line(9, "text", "→ 64 + 2 + 1 = 67"),
                _line(11, "text", "Schlüssel hat 4 Bits: 8 · 4 · 2 · 1"),
                _line(12, "text", "Bsp: 0101 → 4 + 1 = 5"),
            ],
        },
        # Vorderseite prüft, welche Pakete heil sind – die Pakete sieht die Rückseite
        V: {
            "part": 2,
            "torn": ["left", "bottom"],
            "lines": [
                _line(0, "stamp", "NUR FÜR TECHNIKER"),
                _line(1, "typed", "DATENRETTUNG · TEIL 2/3"),
                _line(3, "rule", "① Erst prüfen: Einsen zählen!"),
                _line(4, "text", "GERADE Anzahl → Paket heil."),
                _line(5, "text", "UNGERADE → Paket beschädigt,"),
                _line(6, "text", "komplett weglassen!"),
                _line(7, "text", "Bsp: 1 1000011 → 4 Einsen → heil"),
                _line(8, "text", "Bsp: 0 1000011 → 3 → kaputt"),
            ],
        },
        # Rückseite entschlüsselt – Tabelle hat die Vorderseite, Schlüssel der Leitstand
        R: {
            "part": 3,
            "torn": ["top"],
            "lines": [
                _line(0, "typed", "DATENRETTUNG · TEIL 3/3"),
                _line(2, "rule", "③ Zahl → Buchstabe: in der"),
                _line(3, "text", "ASCII-Tabelle nachsehen."),
                _line(4, "text", "Bsp: 67 → C"),
                _line(6, "rule", "④ Das Wort ist verschoben!"),
                _line(7, "text", "Jeden Buchstaben um k Stellen"),
                _line(8, "text", "im Alphabet ZURÜCK."),
                _line(9, "text", "Bsp k = 3: F → E → D → C"),
                _line(10, "text", "Vor A kommt wieder Z."),
                _line(12, "strike", "Immer ROT13"),
                _line(12, "red", "stimmt nicht!"),
                _line(14, "sign", "– M. Kaiser, IT"),
            ],
        },
    },
}
