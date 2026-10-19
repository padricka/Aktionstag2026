"""Notizzettel: jede Rolle hat ihr Stück mit VOLLSTÄNDIGEN Regeln.

Der Zettel sieht zerrissen aus, aber kein Satz ist zerteilt: Jeder kann seine
Regel komplett lesen – anwenden kann er sie nur mit den Fakten der anderen.
"""
from backend import notes
from backend.playableObject import ROLE_M, ROLE_P1, ROLE_P2

ROLLEN = (ROLE_M, ROLE_P1, ROLE_P2)


def test_rollen_wie_im_spiel():
    assert (notes.M, notes.V, notes.R) == ROLLEN


def test_jede_rolle_bekommt_ein_stueck_mit_risskanten():
    for rolle in ROLLEN:
        stueck = notes.piece(notes.ALARM_NOTE, rolle)
        assert stueck["lines"], rolle
        assert stueck["torn"], rolle          # sieht abgerissen aus
        assert set(stueck["torn"]) <= {"top", "right", "bottom", "left"}


def test_stuecke_sind_als_teil_1_bis_3_erkennbar():
    teile = [notes.piece(notes.ALARM_NOTE, r) for r in ROLLEN]
    assert sorted(t["part"] for t in teile) == [1, 2, 3]
    assert all(t["of"] == 3 for t in teile)
    for t in teile:
        assert any(f"TEIL {t['part']}/3" in z["text"] for z in t["lines"])


def test_jede_regel_steht_komplett_auf_einem_stueck():
    """Eine Regel (①, ②, ③) beginnt und endet auf demselben Stück – kein Satz reißt ab."""
    gesehen = {}
    for rolle in ROLLEN:
        for z in notes.piece(notes.ALARM_NOTE, rolle)["lines"]:
            for nummer in "①②③":
                if z["text"].startswith(nummer):
                    assert nummer not in gesehen, f"{nummer} steht auf zwei Stücken"
                    gesehen[nummer] = rolle
    assert set(gesehen) == {"①", "②", "③"}


def test_jede_rolle_hat_genau_eine_regel():
    regeln = {}
    for rolle in ROLLEN:
        regeln[rolle] = [z for z in notes.piece(notes.ALARM_NOTE, rolle)["lines"] if z["style"] == "rule"]
        assert len(regeln[rolle]) == 1, rolle
    # wer welche Regel hat: der, der sie NICHT allein anwenden kann
    assert regeln[ROLE_P1][0]["text"].startswith("①")   # Vorderseite: Kabel – Platz kennt der Leitstand
    assert regeln[ROLE_M][0]["text"].startswith("②")    # Leitstand: Code – Aufkleber kennt die Rückseite
    assert regeln[ROLE_P2][0]["text"].startswith("③")   # Rückseite: Kratzer – Platz + Symbol kennen die anderen


def test_zeilen_im_stueck_behalten_ihre_reihenfolge():
    for rolle in ROLLEN:
        reihen = [z["row"] for z in notes.piece(notes.ALARM_NOTE, rolle)["lines"]]
        assert reihen == sorted(reihen)
