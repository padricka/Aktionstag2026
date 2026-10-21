# Test-Triage Backend

Aktueller Stand (nach `feat/finale-reparatur`): **376 grün · 36 übersprungen (veraltet) · 0 rot** – Frontend **363 grün · 2 übersprungen**.
Die aktuellen Zahlen stehen immer in `STATUS.md`; diese Datei erklärt die übersprungenen Tests.

Stand direkt nach der Triage: 138 grün · 23 übersprungen · 4 rot (gültig, Code fehlt).
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
| `test_taskNeustart` | 13 | altes Finale (Neustart-Code mit Belohnungsziffern); das Finale ist seit `feat/finale-reparatur` die Reparatur (`test_taskReparatur.py`) | **skip** (ganze Datei) |
| Frontend `PlayerScreen.spec.js`: „sendet beim Finale reboot_code …“, „zeigt das Finale auch der Vorderseite …“ | 2 | prüfen `reboot_code` des alten Finales | **skip** (`it.skip`) |
| `test_taskDatenRettung` | 4 | damals gültig: Sync-Button fehlte im Code | **erledigt**: Aufgabe 3 neu entworfen ohne Sync-Knopf (Entscheidung im Team), Tests nach neuer Spezifikation (`feat/datenrettung-aufgabe3`) |

## Wie man „übersprungen" liest

`skip` heißt: **nicht kaputt, sondern nicht mehr gültig.** Der Grund steht an jedem Test (`pytest -rs` zeigt ihn an). Nichts wurde gelöscht, damit die Absicht erhalten bleibt.
Wer eine Host-Verwaltung oder Heartbeats wirklich bauen will, schreibt zuerst die Tests nach dem aktuellen Vertrag neu und entfernt dann den `skip`.

## Die 4 roten Tests (erledigt)

`tests/test_taskDatenRettung.py` beschreibt Aufgabe 3 so, wie die README sie verspricht: Spieler 1 und 2 schalten ihren Button frei und **drücken ihn dann gleichzeitig** (Zeitfenster). `DataRescueTask.handle_input` in `playableObject.py` kennt aber keinen `sync_button`: die Aufgabe gilt schon als gelöst, sobald beide Antworten stimmen.

Erledigt: Aufgabe 3 wurde später als Kette neu entworfen (Backup-Platte, Hex-Login, Prüfbit, Binär, ASCII, Caesar → RENTE) – **bewusst ohne** Sync-Knopf. Die alten Tests wurden durch die neue Spezifikation ersetzt (GAME_DESIGN.md, Aufgabe 3); `sync_button` wird jetzt ausdrücklich abgelehnt.

## Lokal ausführen

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -rs
```

## Noch offen / erledigt danach

- **Frontend-Specs:** alle Bildschirme und alle Aufgaben-Ansichten (Task1–Task4, auch Leitstand) haben eigene Specs (312 grün). Cleanup entfernte ungenutzte Screens (`ClientScreen`, `MasterScreen`-Hülle) und Attrappen (`HealthBar`, `SwitchPanel`) samt Specs.
- **`ChannelConsumer`** (Spielzeug-`/ws/channel/`) samt Test entfernt — nicht Teil des Spiels.
- Das CI (`.github/workflows/ci.yml`) ist bewusst nicht blockierend. Nach Happy Path verschärfen (`continue-on-error` entfernen).
- **Altes Finale aufräumen:** `Task4Reboot.vue` (Neustart-Terminal) wird seit `feat/finale-reparatur` nicht mehr verwendet, seine Spec läuft noch grün. Zusammen mit `tests/test_taskNeustart.py` und den zwei übersprungenen PlayerScreen-Tests entfernen, sobald das neue Finale abgenommen ist. `VaultDoor.vue` bleibt (Datentresor in der Zwischenszene).
