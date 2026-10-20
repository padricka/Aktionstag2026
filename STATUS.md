# STATUS — DRV-BOX

**Stand:** 2026-10-18 · Ziel: spielbarer Happy Path bis **Freitag** (Code-Freeze laut `TODO_MVP_Schmaler_Pfad.md`).
Regeln: `AGENTS.md`. Testdetails: `TRIAGE.md`. Diese Datei bei jedem relevanten PR aktuell halten.

## Wo wir stehen

| Bereich | Stand | Quelle |
|---|---|---|
| Backend-Tests | **347** grün · 23 übersprungen · **0 rot** | nach `fix/wiedereinstieg` (Docker, Python 3.13) |
| Frontend-Tests | **308** grün | nach `fix/wiedereinstieg` (Docker, Node 22) |
| CI | läuft bei jedem PR/Push, **nicht blockierend** | `.github/workflows/ci.yml` |
| Sicherheit | `SECRET_KEY`-Fallback nur noch bei `DEBUG=True` | PR #2 |
| Live-Pfad Frontend | `App` → `StartMenu` / `HostScreen` / `PlayerScreen` (Master = Rolle in PlayerScreen + `Task*Master`) | Cleanup |

## Was laut Tests schon funktioniert (Backend)
Die grünen Tests in `test_gameConsumer.py`, `test_redisHandler.py`, `test_dataCenter.py`, `test_gameLoop.py` und den Task-Tests decken ab: Verbinden und `lobby_update`, `player_register`, `choose_role` (`role_assigned`), `owner_settings`, `start_game`, `game_tick`, `player_input` (`input_result`), `game_over`, Aufgabe 1 „Alarm" und Aufgabe 2 „Löschprotokoll".
**Einschränkung:** Das läuft in den Tests mit `fakeredis` und In-Memory-Channel-Layer. Ein echter Durchlauf mit Docker und Redis ist **noch nicht geprüft** (siehe Aufgabe 1).

## Nächste Aufgaben (Reihenfolge)

> **Neu:** Der Escape-Room-Umbau aus `GAME_DESIGN.md` (Pakete B1–B4, F1) läuft parallel zu den Punkten unten. Die Paketaufteilung dort regelt, wer welche Datei anfasst.


1. ~~**I1 Happy Path einmal real durchspielen**~~ — laut Team am 2026-10-19 gespielt, das Spiel läuft. Offene Punkte bitte hier ergänzen. Ursprünglich: (`docker compose up --build -d`, Beamer + Master + 2 Spieler im Browser). Ergebnis als Liste „was geht / was nicht" festhalten.
2. **F1 Frontend am Vertrag ausrichten.** Senden nutzt schon `{event, payload}`. Offen: ob eingehende Nachrichten überall über `event` (nicht `type`) ausgewertet werden. Danach Tests mitziehen.
3. ~~**`ClientScreen.vue` entscheiden**~~ — erledigt: gelöscht (ungenutzt, kaputt). Master bleibt als Rolle in `PlayerScreen`.
4. ~~**Aufgabe 3 „Datenrettung":** `sync_button` mit Zeitfenster in `DataRescueTask`.~~ — erledigt in #26, die 4 Tests sind grün.
5. **CI verschärfen:** `continue-on-error` entfernen, sobald Happy Path + Frontend-Triage stabil sind.
6. **Oberfläche überarbeiten** (nach grünem Happy Path).

## Offene Entscheidungen (nicht technisch)

- ~~**Master-Rolle**~~ — **entschieden (2026-10-18):** Escape Room mit drei gleichberechtigten Technikern (Leitstand, Vorderseite, Rückseite), kein Handbuch, keiner kennt die Lösung. Spezifikation und Arbeitspakete: **`GAME_DESIGN.md`**. Rollen-IDs (`MASTER`, `FI-SI`, `FI-AE`) bleiben technisch unverändert.
- **Theme-Switcher** (ehemals PR #1) geschlossen — nach Happy Path neu aufsetzen.
- **Host-Verwaltung:** `HostManager` kann nur `start()`. Alte Tests übersprungen.

## Zuletzt erledigt
Wiedereinstieg: laufende Runde läuft nach Server-Neustart weiter, wer nach Spielende (neu) verbindet bekommt das echte Ergebnis (`fix/wiedereinstieg`) · Beamer-Anwesenheit per Meldung alle 10 s statt Zähler (nach Server-Absturz kein Geister-Beamer), Notfall-Knopf „Ohne Einsatzbesprechung starten“ auf den Handys (`fix/beamer-anwesenheit`) · Verbindung: automatisches Wiederverbinden mit Banner (Spieler + Beamer), Beamer-Sitzung in der Adresse (F5 bleibt in der Sitzung), Knöpfe hängen nicht mehr bei „erneut versuchen“, abgelehnter Beitritt führt zurück zur ID-Eingabe, gescheiterter Start macht das Intro wieder bedienbar (`fix/verbindung`) · Spielschleife stabil: nur eine Schleife pro Sitzung, Start nur mit voller Lobby, Schleife endet still bei Neustart/abgelaufenem Spielstand (keine Geister-Einträge), einzelne Tick-Fehler beenden die Runde nicht, Sitzung lebt nach Spielende wieder 12 h, kein Zeitabzug/−60 nach dem Sieg (`fix/spielschleife`) · Weiche Übergänge: Bildschirmwechsel (Menü, Spieler, Beamer, Leaderboard), Einstellungen, Spielphasen, Aufgabenwechsel, Menü-Auftritt, Leaderboard-Zeilen (`feat/transitions`) · Einsatzbesprechung am Beamer vor dem Start: Story mit Sprechblasen, Tutorial mit Notizblatt und Taschenrechner, Übergang mit Countdown 3-2-1-LOS, neuer Status `briefing` (`feat/intro`) · Neue Punktevergabe: Leben sinken nur durch Fehler, Zeit abgelaufen → Leben 0; Endpunkte = Leben + Aufgabenpunkte 200/250/300 (unsichtbar ×2 bei Lösung in 1:30/2:30/3:30) + Restzeit bei Sieg − Hilfen (`feat/punktevergabe`) · Hilfe-Notizen am Beamer: Host öffnet sie der Reihe nach, immer konkreter, passend zur Runde (Aufgabe 1: 4, 2: 5, 3: 6), je −50 Punkte (`feat/hilfe-notizen`) · Taschenrechner für alle Rollen: liegt als Grafik halb im Bild, wird per Klick hereingezogen, Aufgabe rückt zur Seite (`feat/taschenrechner`) · Beamer: Neustart und „Spiel beenden“ nach Spielende, „Neue Runde“ nach Sieg (`fix/host-neustart`) · Aufgabe 3 neu: Datenrettung als Kette – Backup-Platte wählen, Hex-Login (REHA/BUND/DRV), Prüfbit, Binär → Dezimal, ASCII, Schlüsselbund mit Key-ID, Caesar um k; Ergebnis immer RENTE, Anleitung mit Rechenbeispielen, ohne Sync-Knopf (`feat/datenrettung-aufgabe3`) · Aufgabe 2 neu: Löschmittel je Brandgut (Strom-Regel, Akku-Falle), Brandmelde-Log mit UTC/Ortszeit und Probealarm, Vier-Augen-Freigabe, Löschplan Teil 1–3/3 (`feat/loeschprotokoll-aufgabe2`) · Aufgabe 1 mit zerrissener Wartungsnotiz (Teil 1–3/3, je eine vollständige Regel ①–③, LED blinkt/leuchtet, zerkratzter Aufkleber) · Zeitbonus +90 s pro gelöster Aufgabe (`feat/zeitbonus`) · Aufgabe 3: Hinweis erklärt Binär → Dezimal, Binärwerte mit Einsen vorne und hinten (`feat/binaer-stellenwerte`) · Gleichzeitige Eingaben (z. B. Sync-Knopf) gehen nicht mehr verloren (`fix/gleichzeitige-eingaben`) · Leaderboard: jede Runde in `backend/data/leaderboard.json`, Top 5 im Punkte-Popup, Seite im Hauptmenü (20 pro Seite) · Spielende-Bildschirm: Bild voll sichtbar, Punkte-Karte als Popup, Leiste mit Spiel beenden / Neustart (`feat/spielende-screen`) · Neustart mit groß getippter Sitzungs-ID wirft nicht mehr raus (`fix/neustart-sitzungs-id`) · Spielregeln nur im Backend: vollständiger `game_tick` (`max_health`, `kind`, `reboot_digits`), Spielende nur per `game_over`, Tastatur Aufgabe 1 vom Backend · #40 DEV-Modus am Beamer · #35 Lobby-Platz wird bei Verbindungsabbruch ohne Rolle frei · #36 vertippte Sitzungs-ID wird abgelehnt · #37 `game_over` nur einmal pro Runde · #38 nach Neustart automatisch zurück in die Rollenwahl · PR #2–#9 · Cleanup: toter Frontend-Code, Attrappen `HealthBar`/`SwitchPanel`, Spielzeug-`ChannelConsumer`, Root-/Test-`package.json`, `Spam-Schutz.txt`.
