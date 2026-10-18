# Test-Triage Backend

Stand nach der Triage: **138 grün · 23 übersprungen (veraltet) · 4 rot (gültig, Code fehlt)**
Vorher: 110 grün · 44 rot · 1 Datei, die nicht lud.

Maßstab für „veraltet" ist `JSON_Vertrag.md` (Events `event` + `payload`) und der aktuelle Code in `backend/backend/`.

## Ergebnis pro Gruppe

| Gruppe | Tests | Ursache | Maßnahme |
|---|---|---|---|
| Mehr-Spieler-Tests (`test_gameConsumer`, `test_redisHandler`, …) | 12 | `lupa` fehlte. `fakeredis` braucht es für `redis.lock()` (Lua) | `lupa` in `requirements.txt` |
| `test_gameLoop` | 4 | Test-Attrappe `snap()` kannte `score` nicht (echter `DataCenter.snapshot()` und Vertrag schon) | Attrappe ergänzt |
| `test_channelConsumers` | 1 | Test rief nicht existierende Methode `receive_bytes_from` auf | `receive_from` |
| `test_taskLoeschprotokoll` | 11 | falscher Import nach Umbenennung (`playable_object` → `playableObject`) | in PR #5 behoben |
| `test_consumers` | 3 | altes Protokoll (`action`/`type`), ersetzt durch `test_gameConsumer.py` | **skip** |
| `test_gameConsumer::test_register_assigns_role_and_broadcasts` | 1 | erwartet `role_assigned` schon beim Registrieren; gibt es erst nach `choose_role` | **skip** |
| `test_hostManager` | 14 | Alt-Design (`set_host`/`is_host`/…); aktueller `HostManager` kann nur `start()` | **skip** |
| `test_multiplayerManager` | 5 | Alt-Design (`add_player`/Heartbeat); Lobby läuft über `register_player`/`choose_role` | **skip** |
| `test_taskDatenRettung` | 4 | **gültig**: Sync-Button fehlt im Code | **bleibt rot** |

## Wie man „übersprungen" liest

`skip` heißt: **nicht kaputt, sondern nicht mehr gültig.** Der Grund steht an jedem Test (`pytest -rs` zeigt ihn an). Nichts wurde gelöscht, damit die Absicht erhalten bleibt.
Wer eine Host-Verwaltung oder Heartbeats wirklich bauen will, schreibt zuerst die Tests nach dem aktuellen Vertrag neu und entfernt dann den `skip`.

## Die 4 roten Tests sind Absicht (TDD-Rot)

`tests/test_taskDatenRettung.py` beschreibt Aufgabe 3 so, wie die README sie verspricht: Spieler 1 und 2 schalten ihren Button frei und **drücken ihn dann gleichzeitig** (Zeitfenster). `DataRescueTask.handle_input` in `playableObject.py` kennt aber keinen `sync_button`: die Aufgabe gilt schon als gelöst, sobald beide Antworten stimmen.

Zu tun: `sync_button` mit Zeitfenster in `DataRescueTask` umsetzen, bis die 4 Tests grün sind. Das ist **kein** Teil des MVP-Happy-Paths (`TODO_MVP_Schmaler_Pfad.md`).

## Lokal ausführen

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -rs
```

## Noch offen

- **Frontend-Tests:** auf `main` sind alle 7 Testdateien rot (veraltete Selektoren, fehlende Komponenten, ein Syntaxfehler in `ClientScreen.vue`). Eigene Triage, siehe separater PR.
- Das CI (`.github/workflows/ci.yml`) ist bewusst nicht blockierend. Nach der Triage kann es verschärft werden (`continue-on-error` entfernen).
