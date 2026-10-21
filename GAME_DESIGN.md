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
Es gelten: **9 Minuten** Startzeit (`DEFAULT_TIME` = 540 s, per `owner_settings` 60–1800 s). **Der Server brennt:** alle 3 s kostet das Feuer 1 Leben (`FIRE_EVERY`, in 9 Minuten ≈ 180 von 300), falsche Eingabe −60, gelöste Aufgabe +15 (max. 300). Sind die Leben weg oder läuft die Zeit ab (Leben → 0), ist der Server verloren. **Zeitbonus:** jede echt gelöste Aufgabe außer dem Finale gibt +60 s (`TIME_BONUS`); DEV-Modus: Zeit und Feuer stehen, Überspringen gibt keinen Bonus.

### Einsatzbesprechung (Intro am Beamer)

Bevor die Zeit läuft, sieht das Team am Beamer eine kurze **Einsatzbesprechung** (`IntroStory.vue`).
- **Ablauf:** Alle Rollen gewählt → ein Spieler drückt „Runde starten“ → ist ein Beamer verbunden, wechselt die Lobby in `status: "briefing"` (Handys: „Einsatzbesprechung läuft – schaut auf den Beamer“, Rollen sind fest). Ohne Beamer startet das Spiel wie bisher sofort.
- **Beamer weg?** Der Beamer meldet sich alle 10 s (`host_ping`); ohne Meldung gilt er nach 30 s als weg. Auf den Handys erscheint nach 20 s Besprechung der Notfall-Knopf „Kein Beamer da? Ohne Einsatzbesprechung starten“ – ist der Beamer wirklich weg, startet das Spiel direkt.
- **Story** (M. Kaiser, IT-Leitung, per Funk; Sprechblasen bauen sich wie getippt auf): ① Startbild, Brand in Raum B-04 · ② Nahaufnahme des Racks, „Systemausfall in 09:00“ · ③ das Rechenzentrum mit LEITSTAND / VORDERSEITE / RÜCKSEITE · ④ die drei echten Notizzettel · ⑤ „Redet miteinander – nicht durcheinander!“
- **Tutorial (letzte Seite):** ein echtes Notizblatt mit nummerierten Schritten (die Nummern geben die Reihenfolge vor) und der Taschenrechner, dazu die Regeln (Aufgaben + Finale, Fehler kosten Leben, Notizen, Taschenrechner, Punkte).
- **Bereit-Knopf:** Während der Einsatzbesprechung hat jedes Handy einen „Bereit“-Knopf (Event `player_ready`, wieder zurücknehmbar). Die letzte Folie wartet am Beamer („Warte auf Spieler … x/3 bereit“); sind alle drei bereit, startet der Countdown von selbst. Der Server lässt den Host-Start vorher nicht zu (`not_ready`), außer im DEV-Modus.
- **Start:** Erst „Einsatz starten“ am Beamer (oder automatisch, sobald alle bereit sind) → Übergang (Kamerafahrt, „Verbinde mit Rechenzentrum B-04…“, 3 – 2 – 1 – LOS!) → Host sendet `start_game` → das Spiel startet, Beamer und Handys blenden weich ein.
- **Ton (nur am Beamer):** Zu jeder Folie läuft ein Funkspruch von M. Kaiser (Start-Piep, Rauschen, End-Piep; `frontend/public/sound/intro-slide-N.mp3`). Die Folien laufen von selbst weiter (0,9 s nach dem Spruch; ohne Ton nach der Lesezeit), nur die letzte wartet auf alle „Bereit“. Dazu leise Serverraum-Ambience (im Intro leiser, im Spiel voller), Countdown-Piepse, „System online“ beim Start und Effekte für Fehler, gelöste Ziffer, Hilfe-Notiz, Sieg und Game Over. Regler: Einstellungen (Lautstärke, Musik, Soundeffekte, Funkspruch). Neu bauen: `python tools/sound/build_sounds.py` (braucht ffmpeg), Sprache mit `tools/sound/generate_voice.py` (VoiceStudio).
- **Bilder:** Szenen 2, 3, 5 sind Ausschnitte des Startbilds; eigene Bilder unter `frontend/src/assets/intro/szene-<n>.jpg` ersetzen sie automatisch (Prompts in `LIESMICH.md` dort). Die Sieg-/Niederlage-Bilder gehören nicht ins Intro.

### Punkte

**Endpunkte = restliche Leben + Aufgabenpunkte + Restzeit (nur bei Sieg) − 50 je Hilfe-Notiz**, nie unter 0 (`DataCenter.snapshot`, ins Leaderboard geht dieser Wert).

| | Aufgabe 1 | Aufgabe 2 | Aufgabe 3 | Finale |
|---|---|---|---|---|
| Aufgabenpunkte (`TASK_POINTS`) | 200 | 250 | 300 | – |
| ×2, wenn gelöst innerhalb (`FAST_LIMIT`, ab Start der Aufgabe) | 1:30 | 2:30 | 3:30 | – |
| Hilfe-Notizen | 4 | 5 | 6 | – |

- Der **×2 ist unsichtbar:** Die Spieler erfahren ihn nicht (keine Anzeige, kein `score_gain` mehr in `input_result`), er steckt nur in der Endpunktzahl.
- **Beispiel Sieg:** 180 Leben + (200 ×2) + 250 + (300 ×2) + 95 s Restzeit − 2 Hilfen = 180 + 400 + 250 + 600 + 95 − 100 = **1425**.
- **Niederlage:** Leben sind 0, Restzeit zählt nicht – es bleiben die Aufgabenpunkte minus Hilfen.
- DEV-Überspringen gibt keine Aufgabenpunkte.

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

**Geschichte:** Das Passwort der Backup-Platte muss gerettet werden. Dafür muss die richtige Platte eingelegt, das Backup-Terminal entsperrt und das Passwort aus den Datenpaketen entschlüsselt werden – als **Kette**: Platte → Login → Pakete prüfen → Binär → Dezimal → Buchstabe → zurückschieben. Das Ergebnis ist immer **RENTE**, der Login ein DRV-Begriff (REHA, BUND oder DRV).

| | Leitstand (`MASTER`) | Vorderseite (`FI-SI`) | Rückseite (`FI-AE`) |
|---|---|---|---|
| **Sieht** | **Log:** Login-Name als Hex-Codes, **Backup-Jobs** (Datum, Platte, Status), **Schlüsselbund** (Key-ID, Schlüssel binär, Status aktiv/REVOKED/abgelaufen) | **ASCII-Tabelle** A=65 … Z=90, **Backup-Terminal** (erst gesperrt) | 4 **Backup-Platten**; nach dem Einlegen **6 Datenpakete** à 8 Bit (Prüfbit P abgesetzt) und die **Key-ID** im Paket-Kopf (binär) |
| **Zettel** | Anleitung Teil 1/3: Regeln ④ + ⑥ + Falle | Anleitung Teil 2/3: Regeln ② + ③ | Anleitung Teil 3/3: Regeln ① + ⑤ |
| **Eingabe** | – | `terminal_login`, danach `rescue_word` | `mount_disk` |

**Die Anleitung** (`backend/notes.py`, `RESCUE_NOTE`) – jede Regel vollständig, **mit Rechenbeispiel** (auch ohne Informatik-Vorwissen lösbar), und jeweils bei dem, der die Fakten dazu nicht sieht. Nummern in der Reihenfolge, in der man sie braucht:
- **①** *(Rückseite)* Richtige Platte = das **neueste** Backup mit Status **OK**. Datum ist TAG.MONAT – erst Monat, dann Tag vergleichen. *Bsp: 03.04. ist neuer als 28.03.* *Die Backup-Jobs hat der Leitstand.*
- **②** *(Vorderseite)* Login-Name in **Hex**: erste Ziffer · 16 + zweite, A=10 … F=15; dann Zahl → Buchstabe in der ASCII-Tabelle. *Bsp: 0x4E → 4 · 16 + 14 = 78 → N.* *Die Hex-Codes hat der Leitstand.*
- **③** *(Vorderseite)* Pakete prüfen: Einsen zählen, **gerade** → heil, **ungerade** → weglassen. *Bsp: 1 1000011 → 4 Einsen → heil.* *Die Pakete hat die Rückseite.*
- **④** *(Leitstand)* Binär → Dezimal: erstes Bit = Prüfbit, zählt nicht; 64 32 16 8 4 2 1. Key-ID und Schlüssel: 4 Bit = 8 4 2 1. *Bsp: 1 1000011 → 64 + 2 + 1 = 67; 0110 → 6.* *Die Pakete hat die Rückseite.*
- **⑤** *(Rückseite)* Schlüssel k = der **aktive** Eintrag mit der Key-ID aus dem Paket-Kopf – nie REVOKED, nie abgelaufen. *Den Schlüsselbund hat der Leitstand.*
- **⑥** *(Leitstand)* Jeden Buchstaben um k im Alphabet **zurück**, vor A kommt Z. *Bsp k = 3: F → C.* *Die Buchstaben kommen von der Vorderseite.*
- **Fallen:** das allerneueste Backup ist immer FEHLER; Datum als Text verglichen („28.03.“ > „03.04.“) führt zur falschen Platte; zur Key-ID gibt es einen REVOKED-Zwilling; „Immer ROT13“ durchgestrichen (k ist 1–9).

**So entsteht die Runde** (Backend rechnet rückwärts): RENTE → um k **vor** → ASCII → Prüfbit so, dass jedes heile Paket eine gerade Anzahl Einsen hat; ein Paket mit falschem Prüfbit an zufälliger Stelle. Backups über einen Monatswechsel (zwei Ende Monat m, zwei Anfang m+1, das neueste FEHLER).

**Lösung (Beispiel):**
1. Backups: 22.03. SN-1356 OK, 27.03. SN-4471 OK, 03.04. SN-9083 OK, 07.04. SN-2210 FEHLER → ① **SN-9083** einlegen.
2. Login `0x52 0x45 0x48 0x41` → ② 82 69 72 65 → **REHA**.
3. Paket-Kopf `KEY-ID 0110` → ④ 6 → ⑤ aktiver Schlüssel mit ID 6 = `0011` → k = 3 (der REVOKED-Zwilling `0111` wäre falsch).
4. Pakete `0 1010101`, `0 1001000`, `1 1001011`, `1 1010001`, `1 1010111`, `0 1001000` → ③ Paket 3 (5 Einsen) weg → ④ 85, 72, 81, 87, 72 → U H Q W H → ⑥ je 3 zurück → **RENTE**.

Falsche Platte, falscher Login oder falsches Wort kosten Leben. **Belohnungsziffer sichtbar für:** Vorderseite.

### Finale — Neustart (`kind: "reboot"`, neu)

| | Leitstand (`MASTER`) | Vorderseite (`FI-SI`) | Rückseite (`FI-AE`) |
|---|---|---|---|
| **Sieht** | Ziffer aus Aufgabe 2, Neustart-Terminal | Ziffer aus Aufgabe 3 | Ziffer aus Aufgabe 1 |
| **Eingabe** | `reboot_code`: 3 Ziffern in Aufgabenreihenfolge (1-2-3) | – | – |

Jeder kennt **eine** Ziffer, die Reihenfolge ist die der Aufgaben. Richtig → `status: "won"`, der Beamer zeigt den Sieg. Falsch → −60 HP wie überall.

### Hilfe-Notizen (Beamer)

Kommt ein Team nicht weiter, reißt der **Host am Beamer** einen Zettel vom **Abreißblock** ab (`open_hint` mit `id`). Alle sehen ihn am Beamer als gelben Zettel mit Risskante.
- **Ein Thema je Schritt:** Auf dem Block stehen die Hilfe-Themen der laufenden Aufgabe (z. B. „Backup-Platte“, „Login (Hex)“, „Key-ID / Schlüssel“). Der Host wählt **das Thema, an dem das Team gerade hängt** – keine feste Reihenfolge.
- **Nur was noch passt:** Themen, deren Schritt laut Spielstand schon erledigt ist (`done`), stehen nicht mehr auf dem Block – z. B. „Backup-Platte“, sobald sie eingelegt ist. Schon abgerissene Zettel bleiben sichtbar.
- **Passend zur Runde:** Die Texte erzeugt das Backend aus dem Aufgabenstand (`PlayableObject.hints(state)` → `{id, label, text, done}`), z. B. „0x42 = 4 · 16 + 2 = 66 = B“.
- **Kosten:** jeder abgerissene Zettel **−50 Punkte** (`HINT_COST`), im DEV-Modus gratis. Der Abzug gilt fürs ganze Spiel (`hint_penalty`).
- **Anzahl Themen:** Aufgabe 1 → 4, Aufgabe 2 → 5, Aufgabe 3 → 6, Finale → keine.

| Aufgabe | Themen (`id`) – erledigt, wenn … | Zettel (gekürzt, `…` = aus der Runde) |
|---|---|---|
| 1 Alarm | `cable` Kabel gekappt · `order`, `symbols`, `scratch` Code richtig | „Es brennt Platz …, kappt Platz …“ · „LED … → Farbfolge …“ · „Code beginnt mit …“ · was der zerkratzte Aufkleber zählt (oder: keiner zerkratzt) |
| 2 Löschprotokoll | `probe` erstes Rack gelöscht · `order`, `agents` alle gelöscht · `power` dieses Rack gelöscht · `release` nie | Probealarm-Meldung · Reihenfolge … → … → … · „Rack … unter Strom → CO2“ · alle Löschmittel · Freigabe auf „3, 2, 1“ |
| 3 Datenrettung | `disk` Platte drin · `login` angemeldet · `parity`, `convert`, `key`, `decrypt` erst mit dem Wort | richtige Platte · erster Login-Buchstabe in Hex vorgerechnet · kaputtes Paket · ein Paket umgerechnet · Key-ID → k · erster Buchstabe entschlüsselt |

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
| 3 | MASTER | `rescue_log` | `login_hex: ["0x52", …]`, `backups: [{date: "TT.MM.", serial, status: "OK"/"FEHLER"} ×4]`, `keys: [{id, key: "0011", status: "aktiv"/"REVOKED"/"abgelaufen"} ×4]`, `note` |
| 3 | FI-SI | `rescue_terminal` | `ascii_table: {"A":65,…"Z":90}`, `login_len`, `logged_in`, `word_len: 5`, `note` |
| 3 | FI-AE | `packet_dump` | `disks: [4 Seriennummern]`, `mounted`, `key_id: "0110"` / `packets: ["01010101", …]` (beide null bis eingelegt), `note` |
| 4 | alle | `reboot` | `digit: 0..9` (eigene Ziffer), `terminal: true` nur bei MASTER |

**Zettel:** Jede Ansicht mit Notizzettel hat `note: {id, title, part, of, torn: ["top"/"right"/"bottom"/"left"…], lines: [{row, style, text}]}` – nur das eigene Stück (Teil `part` von `of`), jede Regel darauf vollständig (`style`: typed, stamp, rule, text, strike, red, sign). Die Form der Risskante würfelt das Frontend (`TornNote.vue`, gleiche Aufgabe = gleiche Kante).

**Beamer:** `game_tick` erhält zusätzlich `reboot_digits: [d1|null, d2|null, d3|null]`, damit der Beamer die gefundenen Ziffern anzeigt.
`game_tick` enthält außerdem `hints: {total, cost, available: [{id, label}], opened: [{id, label, text}]}` – Themen auf dem Abreißblock und abgerissene Zettel der laufenden Aufgabe (Texte nur der abgerissenen).

Neue Eingaben: `open_hint` (nur Host, `{id}` = Thema vom Abreißblock), `reboot_code` (MASTER, Wert `"d1d2d3"`), `release` (Aufgabe 2, MASTER und FI-AE, Wert `"press"`; gelöst, wenn beide innerhalb von `window` Sekunden drücken). `valve_action` hat jetzt den Wert `"RACK:LÖSCHMITTEL"`, `release_pw` entfällt. Aufgabe 3: `mount_disk` (FI-AE, Seriennummer), `terminal_login` und danach `rescue_word` (FI-SI) statt `ascii_answer` / `binary_answer` / `sync_button`. Alle anderen `target`-Namen bleiben wie bisher.
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
