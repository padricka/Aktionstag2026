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
                _line(7, "text", "Schrank unter Strom? Dann NIE"),
                _line(8, "text", "Wasser oder Schaum → CO2!"),
                _line(9, "text", "USV-Akku: NICHT löschen –"),
                _line(10, "text", "Schrank ABSCHOTTEN!"),
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
        # Rückseite kennt die falsch gestellte RM-Uhr, braucht das Log; Freigabe mit dem Leitstand
        R: {
            "part": 3,
            "torn": ["top"],
            "lines": [
                _line(0, "typed", "LÖSCHPLAN · TEIL 3/3"),
                _line(2, "rule", "③ Uhrzeiten im Log:"),
                _line(3, "text", "Die Rauchmelder (RM) sind falsch"),
                _line(4, "text", "eingestellt und gehen 2 h vor."),
                _line(5, "bold", "Bei RM-Zeiten immer 2 Stunden abziehen!"),
                _line(7, "rule", "④ Freigabe nur zu zweit:"),
                _line(8, "bold", "Leitstand + Rückseite drücken"),
                _line(9, "bold", "GLEICHZEITIG (max. 3 s)!"),
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
        # Leitstand rechnet die Nr. um – die steht auf der Platte bei der Rückseite
        M: {
            "part": 1,
            "torn": ["right", "bottom"],
            "lines": [
                _line(0, "typed", "DRV SCHWABEN · BACKUP-TEAM"),
                _line(1, "typed", "DATENRETTUNG · TEIL 1/3"),
                _line(3, "rule", "② Auf der Platte steht eine Nr."),
                _line(4, "text", "mit 4 Ziffern. Über den Ziffern"),
                _line(5, "text", "stehen die Werte 8 + 4 + 2 + 1."),
                _line(6, "text", "Zähl die Werte über jeder 1 zusammen."),
                _line(7, "beispiel", "0110 → 4 + 2 = 6"),
                _line(9, "strike", "Die erste Tabelle ist immer richtig."),
                _line(9, "red", "NEIN!"),
            ],
        },
        # Vorderseite wählt die Tabelle – Schlüsselbund hat der Leitstand, Tabellen die Rückseite
        V: {
            "part": 2,
            "torn": ["left", "bottom"],
            "lines": [
                _line(0, "stamp", "NUR FÜR TECHNIKER"),
                _line(1, "typed", "DATENRETTUNG · TEIL 2/3"),
                _line(3, "rule", "③ Im Schlüsselbund (Leitstand) den"),
                _line(4, "text", "GÜLTIGEN Schlüssel mit der Nr."),
                _line(5, "text", "von der Platte suchen – nie gesperrt!"),
                _line(6, "text", "Sein Name steht über der richtigen"),
                _line(7, "text", "Tabelle bei der Rückseite."),
                _line(8, "beispiel", "Nr. 6 · DELTA · gültig → Tabelle DELTA"),
            ],
        },
        # Rückseite wählt die Platte und liest vor – Backups und Code-Tabelle haben die anderen
        R: {
            "part": 3,
            "torn": ["top"],
            "lines": [
                _line(0, "typed", "DATENRETTUNG · TEIL 3/3"),
                _line(2, "rule", "① Richtige Backup-Platte: das"),
                _line(3, "text", "NEUESTE Backup mit Status OK."),
                _line(4, "text", "Datum = TAG.MONAT – erst den"),
                _line(5, "text", "Monat vergleichen, dann Tag!"),
                _line(6, "beispiel", "03.04. ist neuer als 28.03."),
                _line(8, "rule", "④ Die 6 Codes der richtigen Tabelle"),
                _line(9, "text", "der Reihe nach vorlesen. NICHT"),
                _line(10, "text", "rechnen – die Vorderseite sucht"),
                _line(11, "text", "jeden Code in ihrer Code-Tabelle."),
                _line(12, "beispiel", "0100 1101 → in der Code-Tabelle → R"),
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
                _line(7, "bold", "Die Etiketten siehst nur du – in der Teilekiste!"),
                _line(9, "rule", "② Vor JEDEM Einbau den Platz"),
                _line(10, "text", "in der Konsole auf WARTUNG –"),
                _line(11, "text", "sonst Stromschlag! Die Konsole"),
                _line(12, "text", "zählt ab 0:"),
                _line(13, "beispiel", "Schacht 1 = BAY 0 · Platz 2 = FAN 1"),
                _line(15, "rule", "⑥ Vor dem Hochfahren ALLE"),
                _line(16, "text", "Plätze aus der Wartung nehmen."),
            ],
        },
        # Vorderseite: Schächte + Lüfterwand – Etikett kennt der Leitstand, Warmgang die Rückseite
        V: {
            "part": 2,
            "torn": ["left", "bottom"],
            "lines": [
                _line(0, "stamp", "NUR FÜR TECHNIKER"),
                _line(1, "typed", "EINBAUANLEITUNG · TEIL 2/3"),
                _line(3, "rule", "③ Platte in den Schacht mit der"),
                _line(4, "text", "Nummer vom Etikett. Das Etikett"),
                _line(5, "text", "steht in der Teilekiste beim Leitstand."),
                _line(6, "text", "Rote LED = defekt, nicht nehmen!"),
                _line(8, "rule", "④ Lüfter in die Lücke der Wand."),
                _line(9, "text", "Der Pfeil zeigt immer zum"),
                _line(10, "bold", "WARMGANG: ← links oder rechts →"),
                _line(11, "text", "Wo der Warmgang ist, steht auf"),
                _line(12, "text", "dem Schild der Rückseite."),
                _line(14, "strike", "Pfeil zeigt immer nach rechts."),
                _line(14, "red", "falsch!"),
            ],
        },
        # Rückseite: Sicherungen + Schild – Spannung steht auf dem Etikett beim Leitstand
        R: {
            "part": 3,
            "torn": ["top"],
            "lines": [
                _line(0, "typed", "EINBAUANLEITUNG · TEIL 3/3"),
                _line(2, "rule", "⑤ Netzteil nur in den Schacht"),
                _line(3, "text", "mit HEILER Sicherung. Vorher den"),
                _line(4, "text", "Spannungsschalter einstellen:"),
                _line(5, "text", "115 V oder 230 V – die Zahl steht"),
                _line(6, "text", "auf dem Etikett des Netzteils"),
                _line(7, "text", "(Teilekiste beim Leitstand)."),
                _line(9, "rule", "⑦ Hochfahren: drei Schlüssel"),
                _line(10, "text", "Strom (Rückseite) → Kühlung"),
                _line(11, "text", "(Vorderseite) → System"),
                _line(12, "text", "(Leitstand). Je max. 5 s Abstand!"),
                _line(14, "sign", "– M. Kaiser, IT"),
            ],
        },
    },
}
