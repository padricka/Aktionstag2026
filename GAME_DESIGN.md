# GAME_DESIGN.md — DRV-BOX als Escape Room

**Status:** freigegeben (2026-10-18) · Ziel: umgesetzt bis Freitag 2026-10-23
**Ersetzt** das bisherige Prinzip „ein Master mit Handbuch sagt Spieler 1 und 2, was sie tun müssen".
Bei Widerspruch zu `README.md` gilt dieses Dokument; die README wird mit der Umsetzung nachgezogen.

---

## 1. Warum der Umbau

Bisher sieht der Master bei jeder Aufgabe **die fertige Lösung** (z. B. in Aufgabe 2 die komplette Ventil-Sequenz und die Passwort-Vorschau). Spieler 1 und 2 führen nur aus, was er vorliest. Es gibt nichts zu knobeln.

Ein Escape Room funktioniert anders: **Niemand kennt die Lösung, jeder hat ein Puzzleteil.** Erst wenn alle beschreiben, was sie sehen, und gemeinsam kombinieren, geht die Tür auf.

## 2. Grundregeln

1. **Niemand hat die Lösung, jeder hat ein Teil.** Keine Ansicht enthält genug Information, um eine Aufgabe allein zu lösen.
2. **Hinweise sind Fundstücke, keine Anleitung.** Sie sehen aus wie Dinge im Serverraum: LED-Leiste, Aufkleber, Logzeile, Notizzettel, Kabelbeschriftung.
3. **Kombinieren statt Diktieren.** Mindestens eine Aufgabe verlangt Schlussfolgern (z. B. Reihenfolge aus Farben ableiten), nicht nur Weitersagen.
4. **Die Rätsel hängen zusammen.** Jede gelöste Aufgabe gibt eine Ziffer frei. Am Ende tippen die drei gemeinsam den **Neustart-Code** ein. Das ist der Escape-Moment.
5. **Jeder kommt dran.** Über das Spiel verteilt hat jede Rolle Eingaben, keine ist nur Zuschauer.

## 3. Rollen: drei gleichberechtigte Techniker

| Rollen-ID (technisch, bleibt) | Anzeigename | Steht … | sieht typischerweise |
|---|---|---|---|
| `MASTER` | **Leitstand** | im Kontrollraum | Monitore, Logs, Terminal |
| `FI-SI` | **Vorderseite** | vor dem Server-Rack | Steckplätze, Hauptschalter, Ventile |
| `FI-AE` | **Rückseite** | hinter dem Server-Rack | Kabel, Aufkleber, Wartungspanel |

- **Die Rollen-IDs bleiben unverändert** (`MASTER`, `FI-SI`, `FI-AE`), damit Lobby, Redis, Tests und Frontend-Routing nicht brechen. Geändert werden nur Anzeigenamen und Inhalte. Umbenennen der IDs ist eine Aufgabe nach Freitag.
- Es gibt **kein Handbuch** mehr. Die bisherigen `Task*Master`-Komponenten werden zu normalen Ansichten des Leitstands.
- Der **Beamer** (`HostScreen`) spielt nicht mit. Er zeigt Health, Zeit, die aktuelle Aufgabe und die **drei Ziffernfelder des Neustart-Codes** (`_ _ _`), die sich beim Lösen füllen.

## 4. Die Aufgaben

Ablauf: **Alarm → Löschprotokoll → Datenrettung → Neustart**. Danach ist das Spiel gewonnen (`status: "won"`).
Unverändert gelten: falsche Eingabe −60 HP, gelöste Aufgabe +15 HP, Score = Restzeit × Multiplikator. **Zeitbonus:** jede echt gelöste Aufgabe gibt +90 s (`TIME_BONUS`), gewertet wird die Restzeit davor; DEV-Überspringen gibt keinen Bonus.

Jede Aufgabe legt beim Erzeugen eine **Belohnungsziffer** (0–9) fest. Beim Lösen wird sie für das Finale gespeichert und erscheint auf dem Beamer und bei der in der Tabelle genannten Rolle.

### Aufgabe 1 — Alarm verifizieren (`kind: "alarm"`)

**Geschichte:** Ein Steckplatz brennt. Er muss abgeschaltet und das System mit dem Shutdown-Code heruntergefahren werden.

| | Leitstand (`MASTER`) | Vorderseite (`FI-SI`) | Rückseite (`FI-AE`) |
|---|---|---|---|
| **Sieht** | LED-Leiste mit 4 Steckplätzen, einer ist rot – die LED **blinkt oder leuchtet dauerhaft** (jede Runde neu). Die **Farbfolge** vom Monitor (z. B. „ROT → GELB → GRÜN → BLAU"). | 4 Kabel, beschriftet mit **Symbolen**, in Steckplatz-Reihenfolge 1–4. | Die 4 **Code-Symbole** auf **farbigen** Aufklebern, gemischt. Manchmal ist **einer zerkratzt** (Farbe sichtbar, Symbol nicht). |
| **Zettel** | Wartungsnotiz Teil 1/3: Regel ② + Falle | Wartungsnotiz Teil 2/3: Regel ① | Wartungsnotiz Teil 3/3: Regel ③ |
| **Eingabe** | `shutdown_cmd`: 4 Symbole in der richtigen Reihenfolge | `main_switch`: Symbol des richtigen Kabels | – |

**Die zerrissene Wartungsnotiz** (`backend/notes.py`, `ALARM_NOTE`): Jede Rolle hat ein Stück, oben steht „TEIL x/3“. Das Stück **sieht** zerrissen aus, aber **kein Satz ist zerteilt**: Jedes Stück trägt eine vollständige Regel – genau die, die sein Spieler **nicht allein anwenden** kann, weil die nötigen Fakten bei den anderen stehen. „Ich kenne die Regel, du kennst die Fakten.“
- **①** *(Vorderseite)* **Nie** das Kabel am brennenden Platz kappen! Gerade Platznummer → das Kabel **links** daneben, ungerade → **rechts** daneben. *Den brennenden Platz kennt nur der Leitstand.*
- **②** *(Leitstand)* Shutdown-Code = die Farbfolge vom Monitor, Farbe für Farbe. **Blinkt die LED → rückwärts.** *Welches Symbol auf welcher Farbe klebt, kennt nur die Rückseite.*
- **③** *(Rückseite)* Ist ein Aufkleber zerkratzt, gilt dort **das Symbol vom Kabel am brennenden Platz** – nicht vom gekappten. *Den Platz kennt der Leitstand, das Symbol dort die Vorderseite.*
- **Falle** *(Leitstand)*: „Code fängt immer mit ★ an.“ – durchgestrichen, „stimmt nicht!“.

**Lösung (Beispiel):** Platz 3 brennt, LED blinkt, GELB zerkratzt. ① 3 ist ungerade → Kabel von Platz 4. ② blinkt → Farbfolge rückwärts. ③ für GELB gilt das Symbol vom Kabel an Platz 3. Die Leitstand-Tastatur enthält deshalb auch die Kabel-Symbole.
Gelöst, wenn beide Eingaben stimmen (Reihenfolge egal). **Belohnungsziffer sichtbar für:** Rückseite.

### Aufgabe 2 — Löschprotokoll (`kind: "fire_protocol"`)

**Geschichte:** Drei von vier Racks brennen. Jedes muss mit dem **richtigen Löschmittel** gelöscht werden, in der Reihenfolge der Brandmeldungen. Danach wird die Anlage im **Vier-Augen-Prinzip** freigegeben.

| | Leitstand (`MASTER`) | Vorderseite (`FI-SI`) | Rückseite (`FI-AE`) |
|---|---|---|---|
| **Sieht** | **Brandmelde-Log**: Uhrzeit, Quelle (BMZ/RM), Rack – 3 echte Meldungen + ein `[TEST]`-Probealarm, sortiert nach *angezeigter* Uhrzeit. | Steuerpult (Rack × Löschmittel), Fortschritt. **Welches Rack unter Strom steht.** | **Brandgut** hinter jedem Rack (Papierarchiv, Kabelbaum, Server, USV-Akku). |
| **Zettel** | Löschplan Teil 1/3: Regel ① + Falle | Löschplan Teil 2/3: Regel ② | Löschplan Teil 3/3: Regeln ③ + ④ |
| **Eingabe** | `release` (Freigabe-Knopf) | `valve_action`: `RACK:LÖSCHMITTEL`, Rack für Rack | `release` (Freigabe-Knopf) |

**Der Löschplan** (`backend/notes.py`, `FIRE_NOTE`) – wie bei Aufgabe 1: jede Regel vollständig auf einem Stück, und zwar bei dem, der die Fakten dazu **nicht** sieht.
- **①** *(Leitstand)* Papier → WASSER, Kabel → SCHAUM, Server → INERTGAS. **Rack unter Strom: nie Wasser oder Schaum → CO2.** **USV-Akku: nicht löschen → ABSCHOTTEN.** *Brandgut kennt die Rückseite, Strom die Vorderseite.*
- **②** *(Vorderseite)* Gelöscht wird in der Reihenfolge der Meldungen, **älteste zuerst**. `[TEST]`-Meldungen sind Probealarme → ignorieren. *Das Log hat der Leitstand.*
- **③** *(Rückseite)* BMZ (Brandmeldezentrale) zeigt **UTC**, Rauchmelder (RM) zeigen **Ortszeit = UTC + 2 h** → bei RM 2 Stunden abziehen. *Das Log hat der Leitstand.*
- **④** *(Rückseite)* Freigabe nur zu zweit: Leitstand und Rückseite drücken **innerhalb von 3 Sekunden**.
- **Falle** *(Leitstand)*: „Wasser geht immer.“ – durchgestrichen, „NEIN!“.

**Garantiert in jeder Runde:** Wer die Uhrzeiten ohne ③ vergleicht, bekommt die falsche Reihenfolge. Mindestens ein brennendes Rack mit Papier/Kabel steht unter Strom (① Strom-Regel). Ein USV-Akku brennt in etwa jeder zweiten Runde.

**Lösung (Beispiel):** Log: `09:41 BMZ A-02`, `09:44 BMZ [TEST] B-02`, `11:38 RM B-01`, `11:47 RM A-01`. Mit ③: B-01 = 09:38, A-01 = 09:47 UTC → Reihenfolge **B-01, A-02, A-01** (TEST ignoriert). Rückseite: B-01 Kabelbaum, A-02 USV-Akku, A-01 Papierarchiv. Vorderseite: B-01 Strom an, A-01 stromlos. ① → `B-01:CO2`, `A-02:ABSCHOTTEN`, `A-01:WASSER`. Danach drücken Leitstand und Rückseite auf „3, 2, 1“ die Freigabe.
Falsches Rack/Löschmittel kostet Leben; wer zu spät drückt, wartet nur erneut (der andere muss nochmal). **Belohnungsziffer sichtbar für:** Leitstand.

### Aufgabe 3 — Datenrettung (`kind: "data_rescue"`)

**Geschichte:** Zwei Datenblöcke sind verschlüsselt. Erst wenn beide entschlüsselt sind, kann die Rettung **gleichzeitig** ausgelöst werden.

| | Leitstand (`MASTER`) | Vorderseite (`FI-SI`) | Rückseite (`FI-AE`) |
|---|---|---|---|
| **Sieht** | **Halbe** ASCII-Tabelle (A–M) und die **oberen Bit-Stellenwerte** (128, 64, 32, 16). | Das Wort als ASCII-Zahlen (z. B. `83 69 82 86 69 82`). Die **andere Hälfte** der ASCII-Tabelle (N–Z). | Zwei 8-stellige Binärzahlen (z. B. `10100110`; Werte 17–255 mit Einsen in **beiden** Hälften, keine wie 101/110). Die **unteren Bit-Stellenwerte** (8, 4, 2, 1). |
| **Eingabe** | – | `ascii_answer` (Wort), danach `sync_button` | `binary_answer` (Dezimalwerte), danach `sync_button` |

**Lösung:** Vorderseite und Rückseite brauchen jeweils auch die Tabellenhälfte des Leitstands. Beide schalten so ihren Button frei. **Dann drücken Vorderseite und Rückseite innerhalb eines Zeitfensters (3 Sekunden).**
Die bestehenden Tests in `test_taskDatenRettung.py` beschreiben den Sync-Button bereits. **Belohnungsziffer sichtbar für:** Vorderseite.

**Rückseite – Hinweis:** erklärt die Regel („Addiere die Stellenwerte aller Stellen mit einer 1“, Beispiel `0000 0101 = 4 + 1 = 5`) und dass die Werte der ersten vier Stellen nur der Leitstand kennt. Er nennt 128, 64, 32, 16 bewusst nicht. Der Leitstand sieht seine Werte den ersten vier der acht Stellen zugeordnet.

### Finale — Neustart (`kind: "reboot"`, neu)

| | Leitstand (`MASTER`) | Vorderseite (`FI-SI`) | Rückseite (`FI-AE`) |
|---|---|---|---|
| **Sieht** | Ziffer aus Aufgabe 2, Neustart-Terminal | Ziffer aus Aufgabe 3 | Ziffer aus Aufgabe 1 |
| **Eingabe** | `reboot_code`: 3 Ziffern in Aufgabenreihenfolge (1-2-3) | – | – |

Jeder kennt **eine** Ziffer, die Reihenfolge ist die der Aufgaben. Richtig → `status: "won"`, der Beamer zeigt den Sieg. Falsch → −60 HP wie überall.

## 5. Schnittstelle (für paralleles Arbeiten)

Transport bleibt wie im `JSON_Vertrag.md`: Jeder Spieler bekommt im `game_tick` pro Aufgabe ein Feld `view`, **nur für seine Rolle**. Das Frontend wählt die Komponente über `view.type`. Eingaben gehen als `player_input` mit `target` und `value`.

`view`-Payloads (Feldnamen verbindlich, damit Front- und Backend unabhängig voneinander arbeiten können):

| Aufgabe | Rolle | `view.type` | Felder |
|---|---|---|---|
| 1 | MASTER | `alarm_leds` | `slots: 4`, `burning_slot: 1..4`, `led: "blinkt" / "leuchtet"`, `color_order: [..4 Farben..]`, `keyboard: [12 Symbole]` (Code- und Kabel-Symbole + Ablenker, pro Aufgabe gemischt), `p_done`, `note` |
| 1 | FI-SI | `main_switches` | `switches: [4 Symbole in Steckplatz-Reihenfolge]`, `p_done`, `note` |
| 1 | FI-AE | `code_stickers` | `stickers: [{symbol, color} ×4]` (gemischt; zerkratzt: `{symbol: null, color, scratched: true}`), `note` |
| 2 | MASTER | `fire_log` | `log: [{time: "HH:MM", source: "BMZ"/"RM", rack, test}]` (nach angezeigter Uhrzeit sortiert), `release: {armed, window}`, `note` |
| 2 | FI-SI | `valve_panel` | `racks: [4 Rack-IDs]`, `agents: [WASSER, SCHAUM, CO2, INERTGAS, ABSCHOTTEN]`, `power: {rack: true/false}`, `sequence_len`, `step`, `p_done`, `note` |
| 2 | FI-AE | `rack_rear` | `rear: [{rack, material, label} ×4]`, `release: {armed, window}`, `note` |
| 3 | MASTER | `ascii_binary_tables` | `ascii_half: {"A":65,…"M":77}`, `place_values: [128,64,32,16]` |
| 3 | FI-SI | `ascii_puzzle` | `ascii_codes`, `ascii_half: {"N":78,…"Z":90}`, `button_unlocked` |
| 3 | FI-AE | `binary_puzzle` | `binary_codes`, `place_values: [8,4,2,1]`, `button_unlocked` |
| 4 | alle | `reboot` | `digit: 0..9` (eigene Ziffer), `terminal: true` nur bei MASTER |

**Zettel:** Jede Ansicht mit Notizzettel hat `note: {id, title, part, of, torn: ["top"/"right"/"bottom"/"left"…], lines: [{row, style, text}]}` – nur das eigene Stück (Teil `part` von `of`), jede Regel darauf vollständig (`style`: typed, stamp, rule, text, strike, red, sign). Die Form der Risskante würfelt das Frontend (`TornNote.vue`, gleiche Aufgabe = gleiche Kante).

**Beamer:** `game_tick` erhält zusätzlich `reboot_digits: [d1|null, d2|null, d3|null]`, damit der Beamer die gefundenen Ziffern anzeigt.

Neue Eingaben: `reboot_code` (MASTER, Wert `"d1d2d3"`), `release` (Aufgabe 2, MASTER und FI-AE, Wert `"press"`; gelöst, wenn beide innerhalb von `window` Sekunden drücken). `valve_action` hat jetzt den Wert `"RACK:LÖSCHMITTEL"`, `release_pw` entfällt. Alle anderen `target`-Namen bleiben wie bisher.
`JSON_Vertrag.md` wird mit dem Backend-PR um die neuen `view`-Typen ergänzt.

## 6. Umsetzung und Aufteilung

Damit niemand dieselbe Datei gleichzeitig umbaut:

| Paket | Dateien | Zuständig |
|---|---|---|
| **B1** Alarm umbauen (TDD) | `playableObject.py` (`AlarmTask`), `test_taskAlarm.py` | Backend |
| **B2** Löschprotokoll umbauen (TDD) | `playableObject.py` (`FireProtocolTask`), `test_taskLoeschprotokoll.py` | Backend |
| **B3** Sync-Button Datenrettung | `playableObject.py` (`DataRescueTask.handle_input`). Spezifikation: die 4 roten Tests | einzelnes, abgegrenztes Paket |
| **B4** Datenrettung-Ansichten + Finale + Belohnungsziffern | `playableObject.py` (`DataRescueTask.views`, neue `RebootTask`), `dataCenter.py`, Tests | Backend, nach B3 |
| **F1** Ansichten pro Rolle | `frontend/src/components/tasks/*`, `PlayerScreen.vue` (Anzeigenamen), Beamer-Ziffern in `HostScreen.vue` | Frontend, kann sofort mit Beispiel-Payloads aus Abschnitt 5 starten |
| **I1** Echter Durchlauf | `docker compose`, 4 Browser | vor und nach dem Umbau |

**Reihenfolge Backend:** B1 → B2 parallel zu B3 → B4. Jedes Paket ist ein eigener PR mit Testzahlen vorher/nachher (siehe `AGENTS.md`).

## 7. Bewusst nicht bis Freitag

- Rollen-IDs umbenennen (`MASTER` → `LEITSTAND` usw.)
- Neue Rätseltypen über die vier hier beschriebenen hinaus
- Zufällige Rollenzuteilung der Hinweise (Hinweise sind fest einer Rolle zugeordnet)
- Theme-Switcher und visuelles Redesign (kommt nach dem spielbaren Stand)
