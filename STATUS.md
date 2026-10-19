# STATUS — DRV-BOX

**Stand:** 2026-10-18 · Ziel: spielbarer Happy Path bis **Freitag** (Code-Freeze laut `TODO_MVP_Schmaler_Pfad.md`).
Regeln: `AGENTS.md`. Testdetails: `TRIAGE.md`. Diese Datei bei jedem relevanten PR aktuell halten.

## Wo wir stehen

| Bereich | Stand | Quelle |
|---|---|---|
| Backend-Tests | **173** grün · 23 übersprungen · **0 rot** | nach #34 + `feat/binaer-stellenwerte` (Docker, Python 3.13) |
| Frontend-Tests | **162** grün | nach #34 + `feat/binaer-stellenwerte` (Docker, Node 22) |
| CI | läuft bei jedem PR/Push, **nicht blockierend** | `.github/workflows/ci.yml` |
| Sicherheit | `SECRET_KEY`-Fallback nur noch bei `DEBUG=True` | PR #2 |
| Live-Pfad Frontend | `App` → `StartMenu` / `HostScreen` / `PlayerScreen` (Master = Rolle in PlayerScreen + `Task*Master`) | Cleanup |

## Was laut Tests schon funktioniert (Backend)
Die grünen Tests in `test_gameConsumer.py`, `test_redisHandler.py`, `test_dataCenter.py`, `test_gameLoop.py` und den Task-Tests decken ab: Verbinden und `lobby_update`, `player_register`, `choose_role` (`role_assigned`), `owner_settings`, `start_game`, `game_tick`, `player_input` (`input_result`), `game_over`, Aufgabe 1 „Alarm" und Aufgabe 2 „Löschprotokoll".
**Einschränkung:** Das läuft in den Tests mit `fakeredis` und In-Memory-Channel-Layer. Ein echter Durchlauf mit Docker und Redis ist **noch nicht geprüft** (siehe Aufgabe 1).

## Nächste Aufgaben (Reihenfolge)

> **Neu:** Der Escape-Room-Umbau aus `GAME_DESIGN.md` (Pakete B1–B4, F1) läuft parallel zu den Punkten unten. Die Paketaufteilung dort regelt, wer welche Datei anfasst.


1. **I1 Happy Path einmal real durchspielen** (`docker compose up --build -d`, Beamer + Master + 2 Spieler im Browser). Ergebnis als Liste „was geht / was nicht" festhalten.
2. **F1 Frontend am Vertrag ausrichten.** Senden nutzt schon `{event, payload}`. Offen: ob eingehende Nachrichten überall über `event` (nicht `type`) ausgewertet werden. Danach Tests mitziehen.
3. ~~**`ClientScreen.vue` entscheiden**~~ — erledigt: gelöscht (ungenutzt, kaputt). Master bleibt als Rolle in `PlayerScreen`.
4. **Aufgabe 3 „Datenrettung":** `sync_button` mit Zeitfenster in `DataRescueTask`. Die 4 roten Tests sind die Spezifikation. Kein Teil des MVP-Happy-Paths.
5. **CI verschärfen:** `continue-on-error` entfernen, sobald Happy Path + Frontend-Triage stabil sind.
6. **Oberfläche überarbeiten** (nach grünem Happy Path).

## Offene Entscheidungen (nicht technisch)

- ~~**Master-Rolle**~~ — **entschieden (2026-10-18):** Escape Room mit drei gleichberechtigten Technikern (Leitstand, Vorderseite, Rückseite), kein Handbuch, keiner kennt die Lösung. Spezifikation und Arbeitspakete: **`GAME_DESIGN.md`**. Rollen-IDs (`MASTER`, `FI-SI`, `FI-AE`) bleiben technisch unverändert.
- **Theme-Switcher** (ehemals PR #1) geschlossen — nach Happy Path neu aufsetzen.
- **Host-Verwaltung:** `HostManager` kann nur `start()`. Alte Tests übersprungen.

## Zuletzt erledigt
Aufgabe 3: Hinweis erklärt Binär → Dezimal, Binärwerte mit Einsen vorne und hinten (`feat/binaer-stellenwerte`) · PR #2–#9 · Cleanup: toter Frontend-Code, Attrappen `HealthBar`/`SwitchPanel`, Spielzeug-`ChannelConsumer`, Root-/Test-`package.json`, `Spam-Schutz.txt`.
