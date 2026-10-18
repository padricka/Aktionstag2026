# JSON-Vertrag (Quelle der Wahrheit)

Alle Nachrichten haben die Form `{"event": "...", "payload": {...}}`.
WebSocket-URL: `ws://<host>:8000/ws/game/<game_id>/`

## REST (nur für den Host)

- `GET /create-game/` → `{"status": "success", "game_id": "<uuid>"}`
- `GET /force-start/?game_id=<id>` → startet das Spiel
  - 200 gestartet, 404 unbekannte ID, 409 läuft bereits oder beendet

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

---

## Server -> Client

// 1. Updates für den Raum/die Lobby (Broadcast an alle)
// status: "waiting" | "ready" | "running"
{
  "event": "lobby_update",
  "payload": {
    "status": "waiting",
    "players": ["Patrick", "Bene"],
    "ready_to_start": true
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
    "survived_seconds": 85
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
{
  "event": "error",
  "payload": {
    "message": "Lobby ist voll!"
  }
}

// 7. Antwort auf ping
{
  "event": "pong",
  "payload": {}
}

---