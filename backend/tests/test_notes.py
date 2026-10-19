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


# ------------------------------------------------------------------ Aufgabe 2 · Löschplan
def test_loeschplan_hat_teile_1_bis_3_mit_risskanten():
    teile = {r: notes.piece(notes.FIRE_NOTE, r) for r in ROLLEN}
    assert {t["title"] for t in teile.values()} == {"Löschplan"}
    assert (teile[ROLE_M]["part"], teile[ROLE_P1]["part"], teile[ROLE_P2]["part"]) == (1, 2, 3)
    for t in teile.values():
        assert t["of"] == 3 and t["torn"]
        assert any(f"TEIL {t['part']}/3" in z["text"] for z in t["lines"])
        reihen = [z["row"] for z in t["lines"]]
        assert reihen == sorted(reihen)


def test_loeschplan_regeln_stehen_bei_dem_der_die_fakten_nicht_hat():
    """① Löschmittel (Leitstand: Brandgut/Strom kennen die anderen), ② Reihenfolge
    (Vorderseite: Log hat der Leitstand), ③ Uhrzeiten + ④ Freigabe (Rückseite)."""
    regeln = {
        r: [z["text"][0] for z in notes.piece(notes.FIRE_NOTE, r)["lines"] if z["style"] == "rule"]
        for r in ROLLEN
    }
    assert regeln == {ROLE_M: ["①"], ROLE_P1: ["②"], ROLE_P2: ["③", "④"]}


def test_loeschplan_hat_die_falle_wasser_geht_immer():
    zeilen = notes.piece(notes.FIRE_NOTE, ROLE_M)["lines"]
    assert any(z["style"] == "strike" and "Wasser" in z["text"] for z in zeilen)


# ------------------------------------------------------------------ Aufgabe 3 · Datenrettung
def test_datenrettung_hat_teile_1_bis_3_mit_risskanten():
    teile = {r: notes.piece(notes.RESCUE_NOTE, r) for r in ROLLEN}
    assert {t["title"] for t in teile.values()} == {"Datenrettung"}
    assert (teile[ROLE_M]["part"], teile[ROLE_P1]["part"], teile[ROLE_P2]["part"]) == (1, 2, 3)
    for t in teile.values():
        assert t["of"] == 3 and t["torn"]
        assert any(f"TEIL {t['part']}/3" in z["text"] for z in t["lines"])
        reihen = [z["row"] for z in t["lines"]]
        assert reihen == sorted(reihen)


def test_datenrettung_regeln_stehen_bei_dem_der_die_fakten_nicht_hat():
    """① Einsen zählen (Vorderseite: Pakete hat die Rückseite), ② Binär → Dezimal
    (Leitstand: Pakete hat die Rückseite), ③ ASCII + ④ Caesar (Rückseite: Tabelle hat
    die Vorderseite, den Schlüssel der Leitstand)."""
    regeln = {
        r: [z["text"][0] for z in notes.piece(notes.RESCUE_NOTE, r)["lines"] if z["style"] == "rule"]
        for r in ROLLEN
    }
    assert regeln == {ROLE_M: ["②"], ROLE_P1: ["①"], ROLE_P2: ["③", "④"]}


def test_datenrettung_jede_regel_hat_ein_rechenbeispiel():
    """Auch für Nicht-Informatiker: zu jeder Regel steht ein Beispiel (Zeile mit „Bsp“)."""
    for rolle in ROLLEN:
        zeilen = notes.piece(notes.RESCUE_NOTE, rolle)["lines"]
        regeln = sum(z["style"] == "rule" for z in zeilen)
        beispiele = sum(z["text"].startswith("Bsp") for z in zeilen)
        assert beispiele >= regeln, rolle


def test_datenrettung_hat_die_falle_rot13():
    zeilen = notes.piece(notes.RESCUE_NOTE, ROLE_P2)["lines"]
    assert any(z["style"] == "strike" and "ROT13" in z["text"] for z in zeilen)
