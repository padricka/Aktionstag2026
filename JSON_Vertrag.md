# JSON-Vertrag (Quelle der Wahrheit)

Alle Nachrichten haben die Form `{"event": "...", "payload": {...}}`.
WebSocket-URL: `ws://<host>:8000/ws/game/<game_id>/`

## REST (nur für den Host)

- `GET /create-game/` → `{"status": "success", "game_id": "<uuid>"}`
- `GET /force-start/?game_id=<id>` → startet das Spiel
  - 200 gestartet, 404 unbekannte ID, 409 läuft bereits oder beendet
- `GET /leaderboard/?page=1&per_page=20` → alle Runden, höchste Punktzahl zuerst
  (Gleichstand: ältere Runde vorn). `per_page` 1–100, Seite wird auf 1…pages begrenzt.
  ```
  {"entries": [{"rank": 1, "players": ["Anna", "Ben", "Cem"], "score": 900,
                "result": "victory", "survived_seconds": 200,
                "created_at": "2026-10-19T12:30:00+00:00", "id": "…", "game_id": "…"}],
   "page": 1, "per_page": 20, "total": 45, "pages": 3}
  ```
  Gespeichert in `backend/data/leaderboard.json` (Docker-Volume `leaderboard`).

---

## Client -> Server

// 1. Spieler registriert sich in der Lobby
{
  "event": "player_register",
  "payload": {
    "player_name": "Patrick"
  }
}

// 2. Ersteller passt Einstellungen an (nur vor dem Start)
{
  "event": "owner_settings",
  "payload": {
    "players": 2,
    "time": 300
  }
}

// 3. In-Game Aktion eines Spielers
{
  "event": "player_input",
  "payload": {
    "action_type": "button_press",
    "target": "reactor_vent",
    "value": "open"
  }
}

// 4. Spiel starten (Host, aktuell ohne Host-Check)
{
  "event": "start_game",
  "payload": {}
}

// 5. Verbindungstest
{
  "event": "ping",
  "payload": {}
}

// 6. DEV-Modus umschalten (nur Host-Verbindung = nach host_register, nur vor dem Start)
// Im DEV-Modus steht die Zeit (kein Tick-Verlust), Fehler kosten keine HP.
// Der Stand kommt per lobby_update ("dev_mode") an alle und übersteht den Neustart.
{
  "event": "dev_mode",
  "payload": { "enabled": true }
}

// 7. Aktuelle Aufgabe für alle überspringen (nur Host, nur im DEV-Modus, Spiel läuft)
// Wie gelöst, aber ohne Punkte und ohne HP-Bonus; die Ziffer fürs Finale wird aufgedeckt.
// Danach game_tick mit der nächsten Aufgabe, beim Finale game_over "victory".
{
  "event": "dev_skip_task",
  "payload": {}
}

---

## Server -> Client

// 1. Updates für den Raum/die Lobby (Broadcast an alle)
// status: "waiting" | "ready" | "running"
{
  "event": "lobby_update",
  "payload": {
    "status": "waiting",
    "players": ["Patrick", "Bene"],
    "ready_to_start": true,
    "dev_mode": false
  }
}

// 2. Regelmäßiges Game-State Update (Broadcast, jede Sekunde und sofort nach player_input)
{
  "event": "game_tick",
  "status": "alive",
  "payload": {
    "health": 85,
    "time_left": 120,
    "tasks": [
      {
        "task_id": "task-001",
        "kind": "alarm",
        "instruction": "Alarm verifizieren!",
        "view": { "type": "alarm_leds", "slots": 4, "burning_slot": 3,
                  "color_order": ["GELB", "ROT", "BLAU", "GRÜN"], "p_done": false }
      }
    ],
    "reboot_digits": [4, null, null]
  }
}

// "view" ist pro Spieler verschieden: Jeder bekommt NUR die Ansicht seiner Rolle
// (Escape Room: niemand kennt die Lösung allein). Das Frontend wählt die Komponente
// über view.type. Alle view-Typen und Felder: GAME_DESIGN.md, Abschnitt 5.
// Umgesetzt: Aufgabe 1 (alarm_leds / main_switches / code_stickers),
//            Aufgabe 2 (fire_log / valve_panel / password_input),
//            Aufgabe 3 (ascii_binary_tables / ascii_puzzle / binary_puzzle),
//            Finale (reboot: {digit, terminal}; Eingabe target "reboot_code", nur MASTER).
// "reboot_digits": Neustart-Code für den Beamer. Jede gelöste Aufgabe deckt ihre
// Ziffer auf (Aufgabe 1 -> Stelle 1 usw.), null = noch verdeckt.

// 3. Spielende (Broadcast)
// result: "meltdown" (HP 0 oder Zeit abgelaufen) | "victory" (Neustart-Code richtig).
{
  "event": "game_over",
  "payload": {
    "result": "meltdown",
    "score": 450,
    "survived_seconds": 85,
    // Diese Runde wurde ins Leaderboard eingetragen (genau einmal pro Runde).
    // rank: Platz dieser Runde; null im DEV-Modus (wird nicht gewertet).
    // top: die besten 5 Runden. leaderboard ist null, falls Speichern fehlschlug.
    "leaderboard": {
      "rank": 7,
      "total": 23,
      "top": [{"rank": 1, "players": ["Anna", "Ben", "Cem"], "score": 900, "result": "victory"}]
    }
  }
}

// 4. Rolle und Hinweise (nur an den Client, der sich registriert hat)
{
  "event": "role_assigned",
  "payload": {
    "player_name": "Patrick",
    "role": "BLINDER",
    "hints": {}
  }
}

// 5. Ergebnis der eigenen Eingabe (nur an den Absender von player_input)
// result: "correct" | "wrong" | "ignored"
{
  "event": "input_result",
  "payload": {
    "result": "correct"
  }
}

// 6. Fehler (nur an den Absender)
// "code" ist optional und maschinenlesbar. Bisher:
//   "unknown_game" = die Sitzungs-ID aus der URL gibt es nicht (vertippt oder abgelaufen).
//                    Kommt direkt nach dem Verbinden; danach schließt der Server die
//                    Verbindung (Close-Code 4404). Es wird keine Lobby angelegt.
//   "dev_denied"   = dev_mode / dev_skip_task abgelehnt (nicht Host, DEV-Modus aus,
//                    Spiel läuft schon bzw. noch nicht, enabled kein true/false).
{
  "event": "error",
  "payload": {
    "message": "Unbekannte Sitzungs-ID",
    "code": "unknown_game"
  }
}

// 7. Antwort auf ping
{
  "event": "pong",
  "payload": {}
}

---