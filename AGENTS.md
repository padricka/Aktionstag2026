# AGENTS.md — Arbeitsregeln für alle, die an DRV-BOX mitarbeiten

Gilt für alle, die am Projekt arbeiten, auch für automatische Coding-Assistenten. Bitte zuerst lesen, dann `STATUS.md` (aktueller Stand und nächste Aufgaben).

**DRV-BOX** ist ein kooperatives 3-Spieler-Browserspiel („Server retten"). Backend: Python, Django Channels, Redis. Frontend: Vue 3, Vite, Tailwind. Spielidee: `README.md`.

## Wahrheitsquellen (in dieser Reihenfolge)
1. `JSON_Vertrag.md` — Events und Payloads zwischen Frontend und Backend (`event` + `payload`). **Bei Widerspruch gewinnt der Vertrag.**
2. `README.md` — Spielidee, Rollen, die drei Aufgaben.
3. `TODO_MVP_Schmaler_Pfad.md` — der Happy Path, den wir zuerst fertig haben wollen.
4. `TRIAGE.md` — welche Tests gültig, veraltet oder bewusst rot sind.
5. `STATUS.md` — aktueller Stand, Backlog, offene Entscheidungen.

## Arbeitsregeln

1. **Tests sind die Spezifikation (TDD).** Erst Test, dann Code. Ein roter Test, dessen Code fehlt, ist kein Fehler, sondern eine Aufgabe.
2. **Nie einen Test löschen oder abschwächen, um grün zu werden.** Das hat schon einmal einen echten Fehler versteckt.
   - Test prüft ein altes Design → `skip` **mit Begründung** und Eintrag in `TRIAGE.md`.
   - Test ist gültig, Code fehlt → Code schreiben.
3. **Kleine PRs, ein Thema pro PR, nie direkt auf `main`.** Branch-Präfixe: `feat/`, `fix/`, `test/`, `chore/`, `docs/`. Kein Redesign im Bugfix-PR, kein Bugfix im Redesign-PR.
4. **„Fertig" heißt: Tests wirklich ausgeführt.** Nenne im PR die Zahlen (bestanden/fehlgeschlagen/übersprungen) vorher und nachher. Behaupte nichts, was du nicht gelaufen bist.
5. **Das CI blockiert (noch) nicht.** Rot erscheint als gelbe Warnung am PR. Die Warnung lesen, nicht ignorieren. Nach der Triage wird es verschärft.
6. **Kein langer, unbeaufsichtigter Lauf mit großem Auftrag** („repariere alles"). Ein Auftrag = ein Thema, danach Kontrolle (Diff und echter Testlauf), erst dann der nächste.
7. **Ein eigener Klon pro Person/Agent.** Zusammengeführt wird nur über Branches und PRs auf GitHub, nie durch Kopieren zwischen Arbeitsordnern.
8. **Vor jedem Start `git pull` auf `main`.** Andere arbeiten parallel.
9. Keine Zugangsdaten oder Schlüssel ins Repo. Paketmanager ist **npm** (keine `pnpm-lock.yaml`/`yarn.lock`).
10. Skripte in `package.json` müssen unter **Windows** laufen (kein `NODE_ENV=test befehl`).

## Tests ausführen

Backend (Ordner `backend`, Python 3.13 empfohlen):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -rs        # -rs zeigt die Gründe übersprungener Tests
```
Frontend (Ordner `frontend`):
```powershell
npm ci
npx vitest run
```
Der Backend-Lauf braucht **kein** laufendes Redis (`fakeredis`, In-Memory-Channel-Layer). Das Spiel selbst starten: `docker compose up --build -d` (siehe README).

## Stolpersteine (schon einmal passiert)

- **`lupa` fehlt** → alle Tests mit Redis-Lock (`choose_role`) laufen in Timeouts. Steht jetzt in `requirements.txt`.
- **`pytest-cov`** wird von `pytest.ini` verlangt (`--cov`), muss installiert sein.
- **Nach einer Umbenennung Importe und Tests mitziehen** (`playable_object` → `playableObject` hat eine ganze Testdatei gesperrt).
- **Doppelte Dateien:** echte Module liegen in `backend/backend/`. Ein gleichnamiges Modul direkt in `backend/` ist ein Überbleibsel.
- **`.Jules/` und `.jules/`** existieren nebeneinander (Journal-Dateien automatischer Aufgaben). Nicht umbenennen oder zusammenlegen, sonst finden die Aufgaben ihre Notizen nicht. Unter Windows landen beide im selben Ordner, das ist harmlos.
- **Live-Pfad Frontend:** `App` → `StartMenu` / `HostScreen` / `PlayerScreen`. Master ist eine **Rolle in `PlayerScreen`** (lädt `Task*Master`), kein separates `MasterScreen`.
- **Frontend-Tests senden teils noch `type` statt `event`.** Sie bilden das Frontend vor der Vertragsanpassung ab (Aufgabe F1).
- Git-Warnung „LF will be replaced by CRLF" unter Windows ist harmlos.
