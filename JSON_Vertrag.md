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

// 4. Spiel starten (wenn alle drei Rollen besetzt sind)
// Vom Spieler: Ist ein Beamer (Host) verbunden, startet zuerst die Einsatzbesprechung –
//   status "briefing" (lobby_update an alle), das Spiel läuft noch NICHT. Ohne Beamer
//   startet das Spiel sofort. Während "briefing" ignoriert der Server weitere Starts von Spielern.
// Vom Host: startet das Spiel (nach dem Intro am Beamer: „Einsatz starten“ + Countdown).
//   Im "briefing" nur, wenn alle drei Spieler „Bereit“ gemeldet haben (lobby_update.all_ready);
//   sonst error mit code "not_ready". Im DEV-Modus entfällt diese Prüfung.
{
  "event": "start_game",
  "payload": {}
}

// 4a. „Bereit“ während der Einsatzbesprechung (nur Spieler mit Rolle, nur im Status "briefing")
// Jeder Spieler drückt den Knopf auf seinem Handy, wenn er das Intro verstanden hat.
// `ready` ist optional (Standard true); false nimmt die Meldung zurück.
// Der Server antwortet mit einem lobby_update an alle (players[].ready, all_ready).
// Fehler (event "error"): code "ready_denied" – nicht im briefing, ohne Rolle, vom Host
// oder ready kein Boolean.
{
  "event": "player_ready",
  "payload": { "ready": true }
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

// 8. Hilfe-Zettel vom Abreißblock reißen (nur Host, Spiel läuft)
// id = ein Thema aus game_tick.hints.available (beliebige Reihenfolge). Kostet 50 Punkte
// (DEV-Modus: gratis). Themen je Aufgabe: 1 → 4, 2 → 5, 3 → 6, Finale → 0.
// Danach game_tick an alle.
// Abgelehnt (nicht Host, id fehlt/unbekannt/schon abgerissen/Schritt erledigt, keine Hilfen,
// Spiel läuft nicht) → error "hint_denied".
{
  "event": "open_hint",
  "payload": { "id": "key" }
}

---

## Server -> Client

// 1. Updates für den Raum/die Lobby (Broadcast an alle)
// status: "waiting" | "ready" | "briefing" (Einsatzbesprechung am Beamer, Rollen fest,
//          Zeit läuft noch nicht) | "running" | "game_over" | "won"
{
  "event": "lobby_update",
  "payload": {
    "status": "waiting",
    "players": [
      { "name": "Patrick", "role": "MASTER", "ready": true },
      { "name": "Bene", "role": "FI-SI", "ready": false }
    ],
    "ready_to_start": true,
    "all_ready": false,   // true, sobald alle drei Rollen besetzt und alle Spieler „Bereit“ sind
    "dev_mode": false
  }
}

// 2. Regelmäßiges Game-State Update (Broadcast, jede Sekunde und sofort nach player_input)
// Jeder game_tick hat immer alle Felder: health, max_health, time_left, tasks, reboot_digits, hints.
// Spielregeln (Max-HP, Spielende, Aufgabenreihenfolge) kennt nur das Backend: Das Frontend
// zeigt health/max_health an, wählt die Ansicht über tasks[].kind und beendet das Spiel
// erst bei game_over, nicht selbst bei health 0 oder time_left 0.
{
  "event": "game_tick",
  "status": "alive",
  "payload": {
    "health": 85,
    "max_health": 300,
    "time_left": 120,
    "tasks": [
      {
        "task_id": "task-001",
        "kind": "alarm",
        "instruction": "Alarm verifizieren!",
        "view": { "type": "alarm_leds", "slots": 4, "burning_slot": 3,
                  "color_order": ["GELB", "ROT", "BLAU", "GRÜN"],
                  "keyboard": ["herz", "stern", "plus", "kreuz", "…12 Symbole, gemischt"],
                  "p_done": false }
      }
    ],
    "reboot_digits": [4, null, null],
    "hints": { "total": 4, "cost": 50,
               "available": [{ "id": "cable", "label": "Welches Kabel?" }, { "id": "symbols", "label": "Welches Symbol zuerst?" }, { "id": "scratch", "label": "Zerkratzter Aufkleber" }],
               "opened": [{ "id": "order", "label": "LED und Farbfolge", "text": "Die LED blinkt – der Code ist die Farbfolge rückwärts: …" }] }
  }
}

// "view" ist pro Spieler verschieden: Jeder bekommt NUR die Ansicht seiner Rolle
// (Escape Room: niemand kennt die Lösung allein). Das Frontend wählt die Komponente
// über view.type. Alle view-Typen und Felder: GAME_DESIGN.md, Abschnitt 5.
// Notizzettel: view.note = das eigene Stück des zerrissenen Zettels
//   { "id": "alarm", "title": "Wartungsnotiz", "part": 2, "of": 3, "torn": ["left", "bottom"],
//     "lines": [ { "row": 3, "style": "rule", "text": "① NIE das Kabel am brennenden" }, … ] }
//   Jedes Stück trägt vollständige Regeln (kein Satz reißt ab); anwenden kann man
//   sie nur mit den Fakten auf den Bildschirmen der anderen.
// Umgesetzt: Aufgabe 1 (alarm_leds / main_switches / code_stickers, mit note),
//            Aufgabe 2 (fire_log / valve_panel / rack_rear, mit note; Eingaben
//              target "valve_action" = "RACK:LÖSCHMITTEL" nur FI-SI, target "release"
//              = Vier-Augen-Freigabe von MASTER + FI-AE innerhalb release.window s),
//            Aufgabe 3 (rescue_log / rescue_terminal / packet_dump, mit note; Eingaben
//              "mount_disk" = Seriennummer nur FI-AE, "terminal_login" und danach
//              "rescue_word" = das gerettete Wort nur FI-SI),
//            Finale (reboot: {digit, terminal}; Eingabe target "reboot_code", nur MASTER).
// "hints": Abreißblock der laufenden Aufgabe für den Beamer: available = Themen, die noch passen
// (nicht abgerissen, Schritt laut Spielstand nicht erledigt; nur id + label), opened = abgerissene
// Zettel mit Text (in Abriss-Reihenfolge). Texte nicht abgerissener Themen gehen nie raus.
// "reboot_digits": Neustart-Code für den Beamer. Jede gelöste Aufgabe deckt ihre
// Ziffer auf (Aufgabe 1 -> Stelle 1 usw.), null = noch verdeckt.

// 3. Spielende (Broadcast)
// result: "meltdown" (HP 0 oder Zeit abgelaufen – dann HP 0) | "victory" (Neustart-Code richtig).
// score: Endpunkte = restliche HP + Aufgabenpunkte (200/250/300, unsichtbar ×2 bei schneller
//        Lösung) + Restzeit (nur bei victory) − 50 je Hilfe-Notiz, nie unter 0 (GAME_DESIGN „Punkte“).
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
// result: "correct" | "wrong" | "ignored" – bewusst ohne Punkte (der ×2 bleibt unsichtbar)
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
//   "register_denied" = player_register abgelehnt (Spiel läuft schon, Lobby voll) → das
//                    Frontend geht zurück zur ID-Eingabe und zeigt die Meldung.
//   "start_failed" = start_game abgelehnt (Lobby nicht vollständig, läuft schon, unbekannt);
//                    der Beamer macht das Intro wieder bedienbar.
//   "hint_denied"  = open_hint abgelehnt (nicht Host, Thema nicht auf dem Block, Aufgabe ohne
//                    Hilfen, Spiel läuft nicht).
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