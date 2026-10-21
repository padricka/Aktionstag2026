# 🔥 DRV-BOX 🔥

> **Drei Spieler. Ein brennender Server. Keine vollständigen Informationen.**  
> Kommunikation, Teamwork und schnelle Entscheidungen entscheiden darüber, ob der Server gerettet werden kann.

**DRV-BOX** ist ein webbasiertes kooperatives Multiplayer-Spiel, bei dem drei Spieler gemeinsam versuchen, einen kritischen Server vor dem endgültigen Ausfall zu bewahren.

Das Besondere: **Keiner der Spieler besitzt alle Informationen.** Die benötigten Hinweise sind auf die drei Spieler verteilt. Nur durch Kommunikation und Zusammenarbeit können die richtigen Entscheidungen getroffen und der Server gerettet werden.

---

## Projektbeschreibung

Drei Spieler bilden ein **Server-Rettungsteam**
Der Server befindet sich in einem kritischen Zustand und droht vollständig auszufallen. Um ihn zu retten, müssen die Spieler verschiedene Aufgaben und Rätsel lösen.

Doch es gibt ein Problem:

> **Jeder Spieler verfügt nur über einen Teil der Informationen.**
>Zusätzlich sieht jede Rolle etwas anderes:

| Rolle | Sicht |
|---|---|
|**Host**| Zeigt den Spielstand auf dem Beamer, *spielt nicht mit*: Einsatzbesprechung vor dem Start, Zeit, Leben, den brennenden Server mit den gefundenen Teilen und die Hilfe-Notizen |
|**Master** (Leitstand) | Sitzt im Kontrollraum: Monitore, Logs, Terminal |
|**Spieler 1** (Vorderseite) | Steht vor dem Server-Rack: Steckplätze, Schalter, Ventile |
|**Spieler 2** (Rückseite) | Steht hinter dem Server-Rack: Kabel, Aufkleber, Backup-Platten |

Es gibt kein Handbuch: Jede Rolle hat ein Stück einer zerrissenen Notiz mit Regeln, die sie allein nicht anwenden kann – die nötigen Fakten sehen die anderen. Details: `GAME_DESIGN.md`.

Dadurch müssen die Spieler ständig miteinander kommunizieren, Informationen weitergeben und gemeinsam Entscheidungen treffen.

### 🔥😱 Der Server brennt. Die Zeit läuft. 

Nur wenn das Team schnell und effektiv zusammenarbeitet, kann der Server gerettet werden.

---

## Die drei Aufgaben

1. **Alarm verifizieren:** Der Master sieht, an welcher Stelle (1–4) die LED rot ist, ob die LED blinkt oder leuchtet, und die Farbfolge. Spieler 1 sieht die Kabel mit Symbolen und kappt das richtige – nie das kaputte an der roten Stelle. Spieler 2 sieht, welches Symbol auf welcher Farbe klebt (manchmal ist ein Aufkleber zerkratzt). Mit der dreigeteilten Wartungsnotiz tippt der Master den Shutdown-Code.
2. **Richtiges Löschprotokoll:** Der Master hat das Brandmelde-Log (mit Zeitzonen und Probealarm), Spieler 1 sieht den Strom an den Racks und löscht, Spieler 2 kennt das Brandgut. Mit dem dreigeteilten Löschplan wählen sie Reihenfolge und Löschmittel. Am Ende geben Master und Spieler 2 gleichzeitig frei (Vier-Augen-Prinzip).
3. **Datenrettung:** Spieler 2 legt die richtige Backup-Platte ein und liest danach die Datenpakete vor (binär, eins beschädigt). Spieler 1 meldet sich mit einem Hex-codierten Namen am Backup-Terminal an und hat die ASCII-Tabelle. Der Master hat das Log mit Backups und Schlüsselbund. Mit der dreigeteilten Anleitung (mit Rechenbeispielen) entschlüsseln sie das Wort RENTE.

**Nach jeder Aufgabe** öffnet sich ein Fundort (Ersatzteilschrank, Lager, Datentresor) mit einem Teil: Netzteil, Lüfter, Backup-Platte.

**Finale – Server reparieren:** Der Master verteilt die Teile und schaltet in seiner Konsole die Plätze auf Wartung (die Konsole zählt ab 0!), Spieler 1 baut Platte und Lüfter ein, Spieler 2 das Netzteil – nach der dreigeteilten Einbauanleitung. Zum Schluss fahren alle drei den Server mit ihren Schlüsseln hoch: Strom → Kühlung → System.

---

## Planungsphase
Zu Beginn des Projekts wurden verschiedene Projektideen gesammelt und gemeinsam im Team besprochen. Dabei wurde besonders darauf geachtet, welche Idee innerhalb der vorgegebenen drei Wochen realistisch umgesetzt werden kann und gleichzeitig genügend Möglichkeiten für die einzelnen Teammitglieder bietet.

Nachdem die Entscheidung auf DRV-BOX gefallen war, wurde die grundlegende Struktur des Projekts geplant. Dafür wurde ein UML-Diagramm erstellt, um die wichtigsten Komponenten und deren Zusammenhänge darzustellen.

Anschließend wurde ein Gantt-Diagramm erstellt, in dem die verfügbaren Arbeitszeiten und Aufgaben auf die drei Entwicklungswochen verteilt wurden. So konnten die Zuständigkeiten im Team festgelegt und wichtige Entwicklungsphasen sowie Meilensteine geplant werden.

---

### Zielgruppe

DRV-BOX richtet sich an **Jugendliche und Erwachsene**, die Spaß an kooperativen Multiplayer-Spielen, Rätseln und Teamwork haben.

Das Spiel ist besonders für Gruppen geeignet, die gemeinsam an einer Aufgabe arbeiten und dabei auf Kommunikation angewiesen sind. Durch die unterschiedlichen Einschränkungen der Spieler entsteht eine besondere Herausforderung, bei der **Zusammenarbeit, Kommunikation und schnelles Handeln** gefragt sind.


### Zeitanspruch 

Die Entwicklung ist in vier Hauptphasen unterteilt. Der Zeitaufwand bezieht sich auf die Netto-Arbeitszeit pro Entwickler-Rolle (Backend / Frontend), basierend auf ca. 8h pro Arbeitstag:

| Phase | Aufwand pro Rolle (ca.) | Fokus | Kernaufgaben |
| :--- | :--- | :--- | :--- |
| **Phase 0: Planung & Analyse** | 8h-16h | Planung | Projektthema, Klassendiagramm, Gantt-Diagramm |
| **Phase 1: Fundament** | 12h | Setup & TDD | JSON-Verträge, Docker/Redis Basis, Basis-Tests |
| **Phase 2: Core-Loop** | 44h | MVP Entwicklung | Lobby, Vue UI, Async Tick-Schleife, WebSocket-Integration |
| **Phase 3: Stabilität** | 28h | Polishing & QA | Task-Validierung, Redis-Locks, LAN-Generalprobe, MVP Meilenstein |
| **Phase 4: Puffer/Extras**| 4h | Erweiterungen | PostgreSQL Highscores, Audio-API, Cypress E2E |

>#### Geplant: 96 Stunden
>#### Gesamt: TBD
---

## Tech-Stack

- **Backend:** Python, Django, Django Channels, Daphne
- **Frontend:** Vue.js 3, Tailwind CSS, Vite
- **In-Memory Store & Channel Layer:** Redis
- **Containerisierung:** Docker, Docker Compose
- **Tests:** Pytest, Vitest, Postman (optional Cypress)

## Repository-Struktur

- `docker-compose.yml`: Definiert die Container für Backend, Frontend und Redis.
- `backend/`: Django-Anwendung, WebSocket-Consumer und Tests.
- `frontend/`: Vue-Single-Page-Application für Host- und Client-Ansichten.
- `JSON_Vertrag.md`: Festgelegte Datenstrukturen für die WebSocket-Kommunikation.
- `GameTask.md`: Beschreibung der drei Aufgaben.

---

## Wie kann man das Spiel ausführen?

### Voraussetzungen

- Docker muss installiert sein. Siehe Link : https://docs.docker.com/desktop/setup/install/windows-install/
- Python 3.13.x 
- Das Projekt muss über Git importiert bzw. geklont worden sein.

### Anwendung starten

Im Hauptverzeichnis des Projekts folgenden Befehl ausführen:

```bash
docker compose up --build -d
```
### Testing 

### Backend
Alle folgenden Befehle im Ordner `backend` ausführen.


Für lokale Tests ein virtuelles Environment erstellen:
```powershell
python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Alle Tests runnen (für html output wird ein Ordner in \backend erstellt)
```powershell
python -m pytest
```
---

### Happy Path

Voraussetzung: `docker compose up --build -d` ist durchgelaufen (siehe oben).

1. `http://localhost:5173/` als **Host (Beamer)** öffnen → „Als Host“. Der Host **erzeugt die Sitzungs-ID** und zeigt sie groß an.
2. Auf den Spieler-Laptops `http://localhost:5173/` → „Als Spieler“, **genau diese ID** und einen Namen eingeben, dann Rolle wählen (Master / Spieler 1 / Spieler 2).
3. Am Beamer müssen die drei Slots gefüllt sein (gleiche ID!). Weitere Beitritte über die maximale Spielerzahl hinaus werden abgelehnt.
4. Ein Spieler drückt „Runde starten“ → am Beamer läuft die **Einsatzbesprechung** (Story + Tutorial). Dort durchklicken und „Einsatz starten“ drücken – nach dem Countdown beginnt das Spiel. (Notfall ohne Intro: `http://localhost:8000/force-start/?game_id=<ID-vom-Beamer>`)
5. Host wechselt auf Live-Ansicht (Zeit + Server-HP). Die Zeit läuft (9 Minuten), das Feuer frisst alle 3 s ein Leben, Fehler kosten 30.
6. Aufgaben lösen: richtig gibt +15 HP (max. 300) und eine neue Aufgabe, falsch kostet 30 HP.
7. Bei 0 HP oder abgelaufener Zeit (dann fallen die Leben auf 0) erscheint Game Over bei allen. Punkte: siehe GAME_DESIGN.md, Abschnitt „Punkte“.

> Falls die ID schon über `create-game/` erzeugt wurde: Host mit  
> `http://localhost:5173/?game_id=<id>` öffnen (sonst erzeugt der Host eine **neue** Sitzung).

| Was | Wert |
|---|---|
| Frontend | `http://localhost:5173/` |
| Host mit fester ID | `http://localhost:5173/?game_id=<id>` |
| Start (vorläufig) | `http://localhost:8000/force-start/?game_id=<id>` |
| Stoppen | `docker compose down` |
