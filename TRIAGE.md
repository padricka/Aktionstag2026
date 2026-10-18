# Test-Triage Backend

Stand nach B3: **150 grün · 23 übersprungen (veraltet) · 0 rot**
Stand nach der Triage: 138 grün · 23 übersprungen · 4 rot (gültig, Code fehlt).
Vorher: 110 grün · 44 rot · 1 Datei, die nicht lud.

Maßstab für „veraltet" ist `JSON_Vertrag.md` (Events `event` + `payload`) und der aktuelle Code in `backend/backend/`.

## Ergebnis pro Gruppe

| Gruppe | Tests | Ursache | Maßnahme |
|---|---|---|---|
| Mehr-Spieler-Tests (`test_gameConsumer`, `test_redisHandler`, …) | 12 | `lupa` fehlte. `fakeredis` braucht es für `redis.lock()` (Lua) | `lupa` in `requirements.txt` |
| `test_gameLoop` | 4 | Test-Attrappe `snap()` kannte `score` nicht (echter `DataCenter.snapshot()` und Vertrag schon) | Attrappe ergänzt |
| `test_channelConsumers` | 1 | Spielzeug-Consumer `/ws/channel/` | **entfernt** im Cleanup (Consumer + Test) |
| `test_taskLoeschprotokoll` | 11 | falscher Import nach Umbenennung (`playable_object` → `playableObject`) | in PR #5 behoben |
| `test_consumers` | 3 | altes Protokoll (`action`/`type`), ersetzt durch `test_gameConsumer.py` | **skip** |
| `test_gameConsumer::test_register_assigns_role_and_broadcasts` | 1 | erwartet `role_assigned` schon beim Registrieren; gibt es erst nach `choose_role` | **skip** |
| `test_hostManager` | 14 | Alt-Design (`set_host`/`is_host`/…); aktueller `HostManager` kann nur `start()` | **skip** |
| `test_multiplayerManager` | 5 | Alt-Design (`add_player`/Heartbeat); Lobby läuft über `register_player`/`choose_role` | **skip** |
| `test_taskDatenRettung` | 4 | **gültig**: Sync-Button fehlte im Code | **grün** (B3) |

## Wie man „übersprungen" liest

`skip` heißt: **nicht kaputt, sondern nicht mehr gültig.** Der Grund steht an jedem Test (`pytest -rs` zeigt ihn an). Nichts wurde gelöscht, damit die Absicht erhalten bleibt.
Wer eine Host-Verwaltung oder Heartbeats wirklich bauen will, schreibt zuerst die Tests nach dem aktuellen Vertrag neu und entfernt dann den `skip`.

## Die 4 roten Tests waren Absicht (TDD-Rot) — mit B3 erledigt

`tests/test_taskDatenRettung.py` beschreibt Aufgabe 3 so, wie die README sie verspricht: Spieler 1 und 2 schalten ihren Button frei und **drücken ihn dann gleichzeitig** (Zeitfenster). `DataRescueTask.handle_input` in `playableObject.py` kannte keinen `sync_button`: die Aufgabe galt schon als gelöst, sobald beide Antworten stimmen.

Umgesetzt in B3: `sync_button` mit `SYNC_WINDOW = 3.0`. Erster Druck = `progress`, zweiter Druck im Fenster = `solved`, zweiter Druck zu spät = `wrong` (beide müssen neu drücken), Doppeldruck desselben Spielers = `ignored`, `MASTER` = `ignored`. Kein Teil des MVP-Happy-Paths (`TODO_MVP_Schmaler_Pfad.md`).

**Offene Entscheidung aus B3:** `test_both_buttons_within_window_solve` fordert `score == 50` nach der Rettung. Das widerspricht `GAME_DESIGN.md` §4 („Score = Restzeit × Multiplikator", mit `DEFAULT_TIME=300` und Multiplikator 3 wären es 900). Der Test ist die Spezifikation, deshalb trägt `DataRescueTask` jetzt `fixed_score = 50`, das `DataCenter._score_for_solve` Vorrang vor der Multiplikator-Regel gibt. Soll die Restzeit-Regel auch für Aufgabe 3 gelten, muss der Test angepasst werden — dann `fixed_score` entfernen.

## Lokal ausführen

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -rs
```

## Noch offen / erledigt danach

- **Frontend-Specs:** App/StartMenu/HostScreen + PlayerScreen/Settings/GameOver/Task1P2/useGameSocket (43 grün). Cleanup entfernte ungenutzte Screens (`ClientScreen`, `MasterScreen`-Hülle) und Attrappen (`HealthBar`, `SwitchPanel`) samt Specs. Task2/Task3 und Master-Views noch ohne eigene Specs.
- **`ChannelConsumer`** (Spielzeug-`/ws/channel/`) samt Test entfernt — nicht Teil des Spiels.
- Das CI (`.github/workflows/ci.yml`) ist bewusst nicht blockierend. Nach Happy Path verschärfen (`continue-on-error` entfernen).
