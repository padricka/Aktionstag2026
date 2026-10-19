"""Zerrissene Notizzettel (GAME_DESIGN.md §4). Jede Rolle bekommt nur ihr Stück.

Gerissen wird zwischen Wörtern, nie mitten im Wort: Jede Zeile steht hier als
ganzer Satz, dazu, wer wie viele Wörter davon bekommt. Ein Satz geht so auf dem
Nachbarstück weiter – die Spieler müssen sich die Zeilen gegenseitig vorlesen.
Die Rissstellen liegen absichtlich in jeder Zeile woanders (unregelmäßiger Riss).
"""

# Gleiche Werte wie ROLE_M / ROLE_P1 / ROLE_P2 in playableObject (dort importiert
# dieses Modul, deshalb hier ohne Rückimport)
M, V, R = "MASTER", "FI-SI", "FI-AE"


def _line(row, style, text, *split):
    """split: (Rolle, Anzahl Wörter), …; die letzte Rolle bekommt den Rest (None)."""
    return {"row": row, "style": style, "text": text, "split": list(split)}


def split_line(line):
    """[(Rolle, Text), …] – ganze Wörter je Rolle, in Lesereihenfolge."""
    words = line["text"].split(" ")
    out, pos = [], 0
    for role, count in line["split"]:
        take = words[pos:] if count is None else words[pos:pos + count]
        pos += len(take)
        if take:
            out.append((role, " ".join(take)))
    return out


def piece(note, role):
    """Das Stück einer Rolle für die Ansicht: Zeilen mit Position, gerissene Kanten."""
    lines = []
    for line in note["lines"]:
        for owner, text in split_line(line):
            if owner == role:
                lines.append({"row": line["row"], "style": line["style"], "text": text})
    return {"id": note["id"], "title": note["title"], "torn": note["torn"][role], "lines": lines}


# ------------------------------------------------------------------ Aufgabe 1 · Alarm
# Leitstand = oben links, Vorderseite = oben rechts, Rückseite = unten.
# Stile: typed (Schreibmaschine), stamp, rule (Regelanfang), text, strike (Falle), red, sign
ALARM_NOTE = {
    "id": "alarm",
    "title": "Wartungsnotiz",
    "torn": {M: ["right", "bottom"], V: ["left", "bottom"], R: ["top"]},
    "lines": [
        _line(0, "typed", "DRV SCHWABEN · RAUM B-04", (M, None)),
        _line(0, "stamp", "NUR FÜR TECHNIKER", (V, None)),
        _line(1, "typed", "WARTUNGSNOTIZ: ALARM & NOT-AUS", (M, 2), (V, None)),
        _line(3, "rule", "① Brennt ein Steckplatz: NIE sein eigenes Kabel kappen!", (M, 4), (V, None)),
        _line(4, "text", "Gerade Nummer → das Kabel links daneben,", (M, 4), (V, None)),
        _line(5, "text", "ungerade Nummer → das Kabel rechts daneben.", (M, 3), (V, None)),
        _line(7, "rule", "② Shutdown-Code = die Farbfolge vom Monitor –", (M, 2), (V, None)),
        _line(8, "text", "aber nur, wenn die LED dauerhaft leuchtet.", (M, 5), (V, None)),
        _line(9, "text", "Blinkt sie → die Farbfolge rückwärts lesen!", (M, 3), (V, None)),
        _line(10, "strike", "Der Code fängt immer mit ★ an.", (M, 3), (V, None)),
        _line(10, "red", "stimmt nicht!", (V, None)),
        _line(12, "rule", "③ Ein Aufkleber zerkratzt? Dann gilt dort", (R, None)),
        _line(13, "text", "das Symbol vom Kabel am Brandplatz –", (R, None)),
        _line(14, "text", "also von dem, das ihr NICHT kappt!", (R, None)),
        _line(16, "sign", "– M. Kaiser, IT", (R, None)),
    ],
}
