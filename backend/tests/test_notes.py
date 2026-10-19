"""Zerrissene Notizzettel: jede Rolle bekommt nur ihr Stück, gerissen wird zwischen Wörtern."""
from backend import notes
from backend.playableObject import ROLE_M, ROLE_P1, ROLE_P2

ROLLEN = (ROLE_M, ROLE_P1, ROLE_P2)


def test_rollen_wie_im_spiel():
    assert (notes.M, notes.V, notes.R) == ROLLEN


def test_jede_rolle_bekommt_ein_stueck_mit_risskanten():
    for rolle in ROLLEN:
        stueck = notes.piece(notes.ALARM_NOTE, rolle)
        assert stueck["lines"], rolle
        assert stueck["torn"], rolle          # mindestens eine gerissene Kante
        assert set(stueck["torn"]) <= {"top", "right", "bottom", "left"}


def test_gerissen_wird_nur_zwischen_woertern():
    """Setzt man die Stücke einer Zeile zusammen, ergibt sich exakt der Originalsatz."""
    for zeile in notes.ALARM_NOTE["lines"]:
        teile = notes.split_line(zeile)
        assert " ".join(text for _, text in teile) == zeile["text"]
        for _, text in teile:
            assert text == text.strip() and text      # kein halbes Leerzeichen, nichts Leeres


def test_kein_stueck_kennt_den_text_der_anderen():
    leitstand = " ".join(z["text"] for z in notes.piece(notes.ALARM_NOTE, ROLE_M)["lines"])
    vorne = notes.piece(notes.ALARM_NOTE, ROLE_P1)["lines"]
    nur_vorne = [z["text"] for z in vorne if z["text"] not in leitstand]
    assert nur_vorne, "Vorderseite braucht eigenen Text, den der Leitstand nicht hat"


def test_saetze_reissen_ueber_die_stuecke():
    """Mindestens drei Zeilen sind auf zwei Rollen verteilt – sonst muss niemand vorlesen."""
    geteilt = [z for z in notes.ALARM_NOTE["lines"] if len(notes.split_line(z)) > 1]
    assert len(geteilt) >= 3


def test_zeilen_im_stueck_behalten_ihre_position():
    for rolle in ROLLEN:
        reihen = [z["row"] for z in notes.piece(notes.ALARM_NOTE, rolle)["lines"]]
        assert reihen == sorted(reihen)
