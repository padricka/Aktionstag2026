# STATUS — DRV-BOX

**Stand:** 2026-10-18 · Ziel: spielbarer Happy Path bis **Freitag** (Code-Freeze laut `TODO_MVP_Schmaler_Pfad.md`).
Regeln: `AGENTS.md`. Testdetails: `TRIAGE.md`. Diese Datei bei jedem relevanten PR aktuell halten.

## Wo wir stehen

| Bereich | Stand | Quelle |
|---|---|---|
| Backend-Tests | 138 grün · 23 übersprungen (veraltet) · **4 rot (Absicht)** | `TRIAGE.md` |
| Frontend-Tests | 13 grün · 1 übersprungen (`ClientScreen`) | PR #8 |
| CI | läuft bei jedem PR/Push, **nicht blockierend** | `.github/workflows/ci.yml` |
| Sicherheit | `SECRET_KEY`-Fallback nur noch bei `DEBUG=True` | PR #2 |

> Die Zahlen gelten, sobald PR #7 (Backend-Triage) und PR #8 (Frontend-Specs) gemerged sind. Vorher stand `main` bei 44 roten Backend-Tests und 7 roten Frontend-Dateien.

## Was laut Tests schon funktioniert (Backend)
Die grünen Tests in `test_gameConsumer.py`, `test_redisHandler.py`, `test_dataCenter.py`, `test_gameLoop.py` und den Task-Tests decken ab: Verbinden und `lobby_update`, `player_register`, `choose_role` (`role_assigned`), `owner_settings`, `start_game`, `game_tick`, `player_input` (`input_result`), `game_over`, Aufgabe 1 „Alarm" und Aufgabe 2 „Löschprotokoll".
**Einschränkung:** Das läuft in den Tests mit `fakeredis` und In-Memory-Channel-Layer. Ein echter Durchlauf mit Docker und Redis ist **noch nicht geprüft** (siehe Aufgabe 1).

## Nächste Aufgaben (Reihenfolge)

1. **I1 Happy Path einmal real durchspielen** (`docker compose up --build -d`, Beamer + Master + 2 Spieler im Browser). Ergebnis als Liste „was geht / was nicht" festhalten. Erst das zeigt, wo es wirklich hakt.
2. **F1 Frontend am Vertrag ausrichten.** Senden nutzt schon `{event, payload}`. Offen: ob die Komponenten eingehende Nachrichten über `event` oder noch über `type` auswerten (die Tests nutzen noch `type`). Danach Tests mitziehen.
3. **`ClientScreen.vue` entscheiden:** ungenutzt (App nutzt `PlayerScreen.vue`), hat einen Template-Fehler. Löschen samt Spec, oder Spec auf `PlayerScreen.vue` umstellen.
4. **Aufgabe 3 „Datenrettung":** `sync_button` mit Zeitfenster in `DataRescueTask` (`backend/backend/playableObject.py`). Die 4 roten Tests in `test_taskDatenRettung.py` sind die Spezifikation. Kein Teil des MVP-Happy-Paths.
5. **CI verschärfen:** in `ci.yml` die beiden `continue-on-error: true` entfernen, sobald die Punkte 1–3 durch sind.
6. **Oberfläche überarbeiten** (nach grünem Happy Path): Beamer-, Master- und zwei Spieler-Ansicht sind aktuell reine Konsolenoptik.

## Offene Entscheidungen (nicht technisch)

- **Master-Rolle:** Aktuell ist der Master ein Spielfeld-Spieler mit dem Manual (Antworten). Ist das so gewollt, oder soll das Manual getrennt/digital laufen? Vor dem UI-Redesign klären.
- **Theme-Switcher** (Dark/Light/„Girl"-Modus, ehemals PR #1) wurde geschlossen, nicht gemerged. Kann nach dem Happy Path neu aufgesetzt werden.
- **Host-Verwaltung:** Der aktuelle `HostManager` kann nur `start()`, ein Host-Check ist „bewusst noch nicht drin". Die alten Tests dazu sind übersprungen. Wenn Host-Rechte gewollt sind: zuerst Tests nach dem Vertrag neu schreiben.

## Zuletzt erledigt
PR #2 SECRET_KEY · PR #3 ARIA-Labels · PR #5 Übergabe-Schaden · PR #6 CI · PR #7 Backend-Triage · PR #8 Frontend-Specs. Doppelter Sicherheits-PR #4 geschlossen.
