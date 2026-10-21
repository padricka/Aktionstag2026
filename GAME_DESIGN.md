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
4. **Die Rätsel hängen zusammen.** Jede gelöste Aufgabe öffnet einen Fundort mit einem Hardware-Teil. Im Finale bauen die drei damit den Server wieder zusammen und fahren ihn mit drei Schlüsseln hoch. Das ist der Escape-Moment.
5. **Jeder kommt dran.** Über das Spiel verteilt hat jede Rolle Eingaben, keine ist nur Zuschauer.

## 3. Rollen: drei gleichberechtigte Techniker

| Rollen-ID (technisch, bleibt) | Anzeigename | Steht … | sieht typischerweise |
|---|---|---|---|
| `MASTER` | **Leitstand** | im Kontrollraum | Monitore, Logs, Terminal |
| `FI-SI` | **Vorderseite** | vor dem Server-Rack | Steckplätze, Hauptschalter, Ventile |
| `FI-AE` | **Rückseite** | hinter dem Server-Rack | Kabel, Aufkleber, Wartungspanel |

- **Die Rollen-IDs bleiben unverändert** (`MASTER`, `FI-SI`, `FI-AE`), damit Lobby, Redis, Tests und Frontend-Routing nicht brechen. Geändert werden nur Anzeigenamen und Inhalte. Umbenennen der IDs ist eine Aufgabe nach Freitag.
- Es gibt **kein Handbuch** mehr. Die bisherigen `Task*Master`-Komponenten werden zu normalen Ansichten des Leitstands.
- Der **Beamer** (`HostScreen`) spielt nicht mit. Er zeigt Zeit, Leben und den **brennenden Server** (`BrennenderServer.vue`): je weniger Leben, desto mehr Flammen und Rauch (Stufe 1–3), ein Fehler lässt das Feuer auflodern, beim Sieg geht es aus und die LEDs werden grün. Daneben die drei Teile fürs Finale, als Umriss bis sie gefunden sind.

## 4. Die Aufgaben

Ablauf: **Alarm → Löschprotokoll → Datenrettung → Reparatur (Finale)**. Danach ist das Spiel gewonnen (`status: "won"`).
Es gelten: **9 Minuten** Startzeit (`DEFAULT_TIME` = 540 s, per `owner_settings` 60–1800 s). **Der Server brennt:** alle 3 s kostet das Feuer 1 Leben (`FIRE_EVERY`, in 9 Minuten ≈ 180 von 300), falsche Eingabe −30 (`MISTAKE_DAMAGE`), gelöste Aufgabe +15 (max. 300). Sind die Leben weg oder läuft die Zeit ab (Leben → 0), ist der Server verloren. **Zeitbonus:** jede echt gelöste Aufgabe außer dem Finale gibt +60 s (`TIME_BONUS`); DEV-Modus: Zeit und Feuer stehen, Überspringen gibt keinen Bonus.

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
| Aufgabenpunkte (`TASK_POINTS`) | 200 | 250 | 300 | 350 |
| ×2, wenn gelöst innerhalb (`FAST_LIMIT`, ab Start der Aufgabe) | 1:30 | 2:30 | 3:30 | 3:00 |
| Hilfe-Notizen | 4 | 5 | 5 | 6 |

- Der **×2 ist unsichtbar:** Die Spieler erfahren ihn nicht (keine Anzeige, kein `score_gain` mehr in `input_result`), er steckt nur in der Endpunktzahl.
- **Beispiel Sieg:** 180 Leben + (200 ×2) + 250 + (300 ×2) + 350 (Finale nach über 3:00) + 95 s Restzeit − 2 Hilfen = 180 + 400 + 250 + 600 + 350 + 95 − 100 = **1775**.
- **Niederlage:** Leben sind 0, Restzeit zählt nicht – es bleiben die Aufgabenpunkte minus Hilfen.
- DEV-Überspringen gibt keine Aufgabenpunkte.

Jede der drei Aufgaben öffnet beim Lösen einen **Fundort** mit einem Teil fürs Finale (siehe „Fundorte und Teilekiste“).

### Aufgabe 1 — Alarm verifizieren (`kind: "alarm"`)

**Geschichte:** An einer Stelle ist ein Kabel kaputt (LED rot). Die Stelle muss abgeschaltet und das System mit dem Shutdown-Code heruntergefahren werden.

| | Leitstand (`MASTER`) | Vorderseite (`FI-SI`) | Rückseite (`FI-AE`) |
|---|---|---|---|
| **Sieht** | LED-Leiste „Stelle 1–4“ (beschriftet), eine LED ist rot – die LED **blinkt oder leuchtet dauerhaft** (jede Runde neu). Die **Farbfolge** vom Monitor (z. B. „ROT → GELB → GRÜN → BLAU"). | 4 Kabel, beschriftet mit **Symbolen**, an Stelle 1–4. | Die 4 **Code-Symbole** auf **farbigen** Aufklebern, gemischt. Manchmal ist **einer zerkratzt** (Farbe sichtbar, Symbol nicht). |
| **Zettel** | Wartungsnotiz Teil 1/3: Regel ② + Falle | Wartungsnotiz Teil 2/3: Regel ① | Wartungsnotiz Teil 3/3: Regel ③ |
| **Eingabe** | `shutdown_cmd`: 4 Symbole in der richtigen Reihenfolge | `main_switch`: Symbol des richtigen Kabels | – |

**Die zerrissene Wartungsnotiz** (`backend/notes.py`, `ALARM_NOTE`): Jede Rolle hat ein Stück, oben steht „TEIL x/3“. Das Stück **sieht** zerrissen aus, aber **kein Satz ist zerteilt**: Jedes Stück trägt eine vollständige Regel – genau die, die sein Spieler **nicht allein anwenden** kann, weil die nötigen Fakten bei den anderen stehen. „Ich kenne die Regel, du kennst die Fakten.“
- **①** *(Vorderseite)* **Nie** das Kabel an der **roten Stelle** kappen – das ist kaputt! Stelle 2 oder 4 → das Kabel **links** daneben, Stelle 1 oder 3 → **rechts** daneben. *Die rote Stelle kennt nur der Leitstand.*
- **②** *(Leitstand)* Shutdown-Code = die Farbfolge vom Monitor, Farbe für Farbe. **Blinkt die LED → rückwärts.** *Welches Symbol auf welcher Farbe klebt, kennt nur die Rückseite.*
- **③** *(Rückseite)* Ist ein Aufkleber zerkratzt, gilt dort **das Symbol vom kaputten Kabel** (an der roten Stelle) – nicht vom gekappten. *Die Stelle kennt der Leitstand, das Symbol dort die Vorderseite.*
- **Falle** *(Leitstand)*: „Code fängt immer mit ★ an.“ – durchgestrichen, „stimmt nicht!“.

**Lösung (Beispiel):** Stelle 3 ist rot, die LED blinkt, GELB zerkratzt. ① Stelle 3 → Kabel rechts daneben, Stelle 4. ② blinkt → Farbfolge rückwärts. ③ für GELB gilt das Symbol vom kaputten Kabel an Stelle 3. Die Leitstand-Tastatur enthält deshalb auch die Kabel-Symbole.
Gelöst, wenn beide Eingaben stimmen (Reihenfolge egal). **Fundort:** Ersatzteilschrank → Netzteil.

### Aufgabe 2 — Löschprotokoll (`kind: "fire_protocol"`)

**Geschichte:** Drei von vier Serverschränken (Racks) brennen. Jedes muss mit dem **richtigen Löschmittel** gelöscht werden, in der Reihenfolge der Brandmeldungen. Danach wird die Anlage im **Vier-Augen-Prinzip** freigegeben.

| | Leitstand (`MASTER`) | Vorderseite (`FI-SI`) | Rückseite (`FI-AE`) |
|---|---|---|---|
| **Sieht** | **Brandmelde-Log**: Uhrzeit, Quelle (BMZ/RM), Schrank – 3 echte Meldungen + ein `[TEST]`-Probealarm, sortiert nach *angezeigter* Uhrzeit. | Steuerpult (Schrank × Löschmittel), Fortschritt. **Welcher Schrank unter Strom steht.** | **Brandgut** hinter jedem Schrank (Papierarchiv, Kabelbaum, Server, USV-Akku). |
| **Zettel** | Löschplan Teil 1/3: Regel ① + Falle | Löschplan Teil 2/3: Regel ② | Löschplan Teil 3/3: Regeln ③ + ④ |
| **Eingabe** | `release` (Freigabe-Knopf) | `valve_action`: `RACK:LÖSCHMITTEL`, Rack für Rack | `release` (Freigabe-Knopf) |

**Der Löschplan** (`backend/notes.py`, `FIRE_NOTE`) – wie bei Aufgabe 1: jede Regel vollständig auf einem Stück, und zwar bei dem, der die Fakten dazu **nicht** sieht.
- **①** *(Leitstand)* Papier → WASSER, Kabel → SCHAUM, Server → INERTGAS. **Schrank unter Strom: nie Wasser oder Schaum → CO2.** **USV-Akku: nicht löschen → Schrank ABSCHOTTEN.** *Brandgut kennt die Rückseite, Strom die Vorderseite.*
- **②** *(Vorderseite)* Gelöscht wird in der Reihenfolge der Meldungen, **älteste zuerst**. `[TEST]`-Meldungen sind Probealarme → ignorieren. *Das Log hat der Leitstand.*
- **③** *(Rückseite)* Die Rauchmelder (RM) sind falsch eingestellt und gehen 2 Stunden vor. **Bei RM-Zeiten immer 2 Stunden abziehen!** (auf dem Zettel fett mit Textmarker) *Das Log hat der Leitstand.*
- **④** *(Rückseite)* Freigabe nur zu zweit: **Leitstand + Rückseite drücken GLEICHZEITIG (max. 3 s)!** (fett)
- **Falle** *(Leitstand)*: „Wasser geht immer.“ – durchgestrichen, „NEIN!“.

**Garantiert in jeder Runde:** Wer die Uhrzeiten ohne ③ vergleicht, bekommt die falsche Reihenfolge. Mindestens ein brennendes Rack mit Papier/Kabel steht unter Strom (① Strom-Regel). Ein USV-Akku brennt in etwa jeder zweiten Runde.

**Lösung (Beispiel):** Log: `09:41 BMZ A-02`, `09:44 BMZ [TEST] B-02`, `11:38 RM B-01`, `11:47 RM A-01`. Mit ③: B-01 = 09:38, A-01 = 09:47 → Reihenfolge **B-01, A-02, A-01** (TEST ignoriert). Rückseite: B-01 Kabelbaum, A-02 USV-Akku, A-01 Papierarchiv. Vorderseite: B-01 Strom an, A-01 stromlos. ① → `B-01:CO2`, `A-02:ABSCHOTTEN`, `A-01:WASSER`. Danach drücken Leitstand und Rückseite auf „3, 2, 1“ die Freigabe.
Falscher Schrank / falsches Löschmittel kostet Leben; wer zu spät drückt, wartet nur erneut (der andere muss nochmal). **Fundort:** Lager → Lüfter.

### Aufgabe 3 — Datenrettung (`kind: "data_rescue"`)

**Geschichte:** Das Passwort der Backup-Platte muss gerettet werden: die richtige Platte einlegen, die Nr. auf der Platte umrechnen, den gültigen Schlüssel finden – seine Tabelle enthält die Codes des Passworts. Die Codes werden **nicht gerechnet**, nur in der Code-Tabelle nachgeschlagen. Das Passwort ist ein 6-Buchstaben-Wort der Rentenversicherung (`WORDS`: RENTEN, ANTRAG, WAISEN, WITWEN).

**Leichte Fassung** (`feat/leichter-datenrettung`, nach Rückmeldung von Nicht-ITlern): kein Login, kein Prüfbit, kein ASCII, kein Verschieben um k, kein Taschenrechner. Gerechnet wird nur eine 4-stellige Binärzahl (8 4 2 1).

| | Leitstand (`MASTER`) | Vorderseite (`FI-SI`) | Rückseite (`FI-AE`) |
|---|---|---|---|
| **Sieht** | **Backup-Jobs** (Datum, Platte, Status), **Schlüsselbund** (Nr., Name, gültig/gesperrt – **zwei gültige**) | **Code-Tabelle** A–Z: 8-stelliger Code je Buchstabe (frei erfunden, jede Runde neu), **Backup-Terminal** | 4 **Backup-Platten**; nach dem Einlegen die **Nr. der Platte** (4-stellig binär) und **zwei Tabellen** à 6 Codes, überschrieben mit dem Namen eines gültigen Schlüssels |
| **Zettel** | Anleitung Teil 1/3: Regel ② + Falle | Anleitung Teil 2/3: Regel ③ | Anleitung Teil 3/3: Regeln ① + ④ |
| **Eingabe** | – | `rescue_word` | `mount_disk` |

**Die Anleitung** (`backend/notes.py`, `RESCUE_NOTE`) – jede Regel vollständig, das Beispiel mittig eingerahmt (Zettel-Stil `beispiel`):
- **①** *(Rückseite)* Richtige Platte = das **neueste** Backup mit Status **OK**. Datum ist TAG.MONAT – erst Monat, dann Tag vergleichen. *Bsp: 03.04. ist neuer als 28.03.* *Die Backup-Jobs hat der Leitstand.*
- **②** *(Leitstand)* Die Nr. auf der Platte hat 4 Ziffern, darüber stehen die Werte 8 · 4 · 2 · 1 – die Werte über jeder 1 zusammenzählen. *Bsp: 0110 → 4 + 2 = 6.* *Die Nr. sieht die Rückseite.*
- **③** *(Vorderseite)* Im Schlüsselbund den **gültigen** Schlüssel mit dieser Nr. suchen – nie gesperrt. Sein Name steht über der richtigen Tabelle. *Bsp: Nr. 6 · DELTA · gültig → Tabelle DELTA.* *Schlüsselbund beim Leitstand, Tabellen bei der Rückseite.*
- **④** *(Rückseite)* Die 6 Codes der richtigen Tabelle der Reihe nach vorlesen, **nicht rechnen** – die Vorderseite sucht jeden Code in ihrer Code-Tabelle. *Die Code-Tabelle hat die Vorderseite.*
- **Fallen:** das allerneueste Backup ist immer FEHLER; Datum als Text verglichen („28.03.“ > „03.04.“) führt zur falschen Platte; die zweite Tabelle gehört zum anderen **gültigen** Schlüssel und ergibt ein anderes echtes Wort; „Die erste Tabelle ist immer richtig.“ – durchgestrichen.

**Lösung (Beispiel):**
1. Backups: 22.03. SN-1356 OK, 27.03. SN-4471 OK, 03.04. SN-9083 OK, 07.04. SN-2210 FEHLER → ① **SN-9083** einlegen.
2. Auf der Platte: `0110` → ② **6**.
3. Schlüsselbund: Nr. 6 · DELTA · gültig, Nr. 9 · ECHO · gültig, … → ③ **Tabelle DELTA**.
4. Rückseite liest die 6 Codes aus Tabelle DELTA vor → Vorderseite schlägt nach → **RENTEN** (Tabelle ECHO ergäbe z. B. ANTRAG – falsch).

Falsche Platte oder falsches Wort kosten Leben. **Fundort:** Datentresor → Backup-Platte.

### Finale — Server reparieren (`kind: "repair"`)

**Geschichte:** Mit den drei Teilen aus den Fundorten wird der Server repariert und hochgefahren. 350 Aufgabenpunkte (×2 innerhalb 3:00) und 6 Hilfe-Notizen (Wer bekommt was? · Wartung und Konsole · Welcher Plattenschacht? · Wie herum der Lüfter? · Netzteil · Hochfahren); die Lage wird jede Runde neu ausgelost (`RepairTask`, Tests: `test_taskReparatur.py`).

| | Leitstand (`MASTER`) | Vorderseite (`FI-SI`) | Rückseite (`FI-AE`) |
|---|---|---|---|
| **Sieht** | **Teilekiste** mit Etiketten (Platte „RAID-Platz n“, Netzteil „115/230 V“, Lüfter) und wo jedes Teil gerade ist · **Management-Konsole** BAY 0–3, FAN 0–2, PSU 0–1 mit Schalter Wartung | 4 Plattenschächte (LED grün = belegt, rot = defekt, aus = leer) · Lüfterwand mit einer Lücke · Teile in der Hand | 2 Netzteilschächte (Sicherung ok/durch) · Gang-Schild an der Rückwand (Warmgang/Kaltgang) · Teile in der Hand |
| **Zettel** | Einbauanleitung Teil 1/3: ① Reihenfolge + wer was einbaut, ④ Wartung vor jedem Einbau, Konsole zählt ab 0, ⑤ vor dem Hochfahren alle Wartungen aus | Teil 2/3: ② Platte in den Schacht vom Etikett, rote LED = defekt; Lüfterpfeil vom Kaltgang zum Warmgang (Falle: „immer nach vorne“) | Teil 3/3: ③ Netzteil nur in den Schacht mit heiler Sicherung, Spannung vom Etikett; ⑥ Schlüssel Strom → Kühlung → System, je max. 5 s |
| **Eingabe** | `give` `"disk:FI-SI"` · `maintenance` `"bay:2"` (Umschalter) · `key` `"system"` | `install_disk` `"3"` · `install_fan` `"2:hinten"` · `return` `"psu"` · `key` `"kuehlung"` | `install_psu` `"1:230"` · `return` `"disk"` · `key` `"strom"` |

- **Reihenfolge:** Platte → Lüfter → Netzteil. Jeder Einbau braucht den Platz in der Konsole auf **Wartung** (sonst Stromschlag); die Konsole zählt ab 0 (Schacht 3 = BAY 2).
- **Lüfter:** Die Luft strömt vom Kaltgang zum Warmgang – das Schild sieht nur die Rückseite, einbauen muss die Vorderseite.
- **Weitergeben:** Wer ein Teil bekommt, das bei ihm nicht passt, gibt es ohne Strafe zurück (kostet nur Zeit).
- **Drei-Schlüssel-Start:** Wenn alles eingebaut und keine Wartung mehr an ist. Falsche Reihenfolge oder Wartung noch an → Fehler, alle Schlüssel zurück; mehr als 5 s Pause → von vorn.
- **Fehler** kosten 30 Leben und `input_result.message` sagt, was falsch war (z. B. „Stromschlag! Platz 3 war nicht in Wartung.“).
- **Sieg:** dritter Schlüssel → `status: "won"`; auf den Handys „Server fährt hoch“, am Beamer geht das Feuer aus.

### Fundorte und Teilekiste

Nach jeder der drei Aufgaben öffnet sich ein Fundort und das Team bekommt ein Teil, mit dem es im Finale den Server repariert (`FUNDORTE` in `dataCenter.py`, `game_tick.parts`):

| Aufgabe | Fundort | Teil | Etikett (pro Runde ausgelost) |
|---|---|---|---|
| 1 Alarm | **Ersatzteilschrank** – das Schloss war vom Alarm blockiert | **Netzteil** | 115 V oder 230 V |
| 2 Löschprotokoll | **Lager** hinter der Brandschutztür – entriegelt nach dem Löschen | **Lüfter** | Pfeil = Luftstrom |
| 3 Datenrettung | **Datentresor** | **Backup-Platte** mit den geretteten Daten | RAID-Platz 1–4 |

- **Zwischenszene** (`Zwischenszene.vue`, gut 4 s, beim Datentresor gut 5 s): **Uhr und Feuer stehen** so lange (`PAUSE_NACH`: 5 s, Datentresor 6 s, vor Aufgabe 2 plus 12 s und vor Aufgabe 3 plus 10 s Tutorial), das ×2-Fenster der nächsten Aufgabe beginnt erst danach. Auf allen Handys und groß am Beamer öffnet sich der Fundort (Schranktüren, Schiebetür, beim Datentresor der bekannte Tresor `VaultDoor` – SVG/CSS), das Teil kommt zum Vorschein, dann die Titelkarte der nächsten Aufgabe. Wer später dazukommt, sieht keine Szene für alte Teile.
- **Tutorial Löschanlage** (`TutorialLoeschanlage.vue`, 12 s, `TUTORIAL_MS` in `Zwischenszene.vue`): vor Aufgabe 2 zeigt die Zwischenszene nach der Titelkarte ein vereinfachtes Steuerpult in fünf Schritten – ① Schrank wählen, ② Löschmittel wählen, ③ AUSLÖSEN → gelöscht, „So NICHT“: Wasser auf einen Schrank unter Strom → Stromschlag −30, ④ Freigabe: Leitstand + Rückseite gleichzeitig. Nur Anzeige, Uhr und Feuer stehen.
- **Tutorial Binär** (`TutorialBinaer.vue`, 10 s, `TUTORIAL_MS`): vor Aufgabe 3 zeigt die Zwischenszene nach der Titelkarte in fünf Bildern, wie man die Nr. auf der Platte ausrechnet (8 4 2 1 über 0110 → 4 + 2 = 6) und dass die langen Codes **nicht gerechnet**, sondern in der Code-Tabelle nachgeschlagen werden (0100 1101 → R). Nur Anzeige, Uhr und Feuer stehen.
- **Teilekiste** (`Teilekiste.vue`, nur Leitstand): liegt halb im Bild am linken Rand wie der Taschenrechner rechts, ein Klick zieht sie herein. Drei Fächer mit Zeichnung (`TeilGrafik.vue`), gefundene Teile mit Etikett – die Etiketten braucht das Team im Finale.

### Hilfe-Notizen (Beamer)

Kommt ein Team nicht weiter, reißt der **Host am Beamer** einen Zettel vom **Abreißblock** ab (`open_hint` mit `id`). Alle sehen ihn am Beamer als gelben Zettel mit Risskante.
- **Ein Thema je Schritt:** Auf dem Block stehen die Hilfe-Themen der laufenden Aufgabe (z. B. „Backup-Platte“, „Login (Hex)“, „Key-ID / Schlüssel“). Der Host wählt **das Thema, an dem das Team gerade hängt** – keine feste Reihenfolge.
- **Nur was noch passt:** Themen, deren Schritt laut Spielstand schon erledigt ist (`done`), stehen nicht mehr auf dem Block – z. B. „Backup-Platte“, sobald sie eingelegt ist. Schon abgerissene Zettel bleiben sichtbar.
- **Passend zur Runde:** Die Texte erzeugt das Backend aus dem Aufgabenstand (`PlayableObject.hints(state)` → `{id, label, text, done}`), z. B. „0x42 = 4 · 16 + 2 = 66 = B“.
- **Kosten:** jeder abgerissene Zettel **−50 Punkte** (`HINT_COST`), im DEV-Modus gratis. Der Abzug gilt fürs ganze Spiel (`hint_penalty`).
- **Anzahl Themen:** Aufgabe 1 → 4, Aufgabe 2 → 5, Aufgabe 3 → 5, Finale → 6.

| Aufgabe | Themen (`id`) – erledigt, wenn … | Zettel (gekürzt, `…` = aus der Runde) |
|---|---|---|
| 1 Alarm | `cable` Kabel gekappt · `order`, `symbols`, `scratch` Code richtig | „Die LED ist rot an Stelle …, kappt Stelle …“ · „LED … → Farbfolge …“ · „Code beginnt mit …“ · was der zerkratzte Aufkleber zählt (oder: keiner zerkratzt) |
| 2 Löschprotokoll | `probe` erstes Rack gelöscht · `order`, `agents` alle gelöscht · `power` dieses Rack gelöscht · `release` nie | Probealarm-Meldung · Reihenfolge … → … → … · „Rack … unter Strom → CO2“ · alle Löschmittel · Freigabe auf „3, 2, 1“ |
| 3 Datenrettung | `disk` Platte drin · `number`, `key`, `table`, `word` erst mit dem Wort | richtige Platte · Nr. der Platte vorgerechnet · gültiger Schlüssel zur Nr. · richtige Tabelle · erster Code nachgeschlagen |

## 5. Schnittstelle (für paralleles Arbeiten)

Transport bleibt wie im `JSON_Vertrag.md`: Jeder Spieler bekommt im `game_tick` pro Aufgabe ein Feld `view`, **nur für seine Rolle**. Das Frontend wählt die Komponente über `view.type`. Eingaben gehen als `player_input` mit `target` und `value`.

`view`-Payloads (Feldnamen verbindlich, damit Front- und Backend unabhängig voneinander arbeiten können):

| Aufgabe | Rolle | `view.type` | Felder |
|---|---|---|---|
| 1 | MASTER | `alarm_leds` | `slots: 4`, `burning_slot: 1..4`, `led: "blinkt" / "leuchtet"`, `color_order: [..4 Farben..]`, `keyboard: [12 Symbole]` (Code- und Kabel-Symbole + Ablenker, pro Aufgabe gemischt), `p_done`, `note` |
| 1 | FI-SI | `main_switches` | `switches: [4 Symbole an Stelle 1–4]`, `p_done`, `note` |
| 1 | FI-AE | `code_stickers` | `stickers: [{symbol, color} ×4]` (gemischt; zerkratzt: `{symbol: null, color, scratched: true}`), `note` |
| 2 | MASTER | `fire_log` | `log: [{time: "HH:MM", source: "BMZ"/"RM", rack, test}]` (nach angezeigter Uhrzeit sortiert), `release: {armed, window}`, `note` |
| 2 | FI-SI | `valve_panel` | `racks: [4 Rack-IDs]`, `agents: [WASSER, SCHAUM, CO2, INERTGAS, ABSCHOTTEN]`, `power: {rack: true/false}`, `sequence_len`, `step`, `p_done`, `note` |
| 2 | FI-AE | `rack_rear` | `rear: [{rack, material, label} ×4]`, `release: {armed, window}`, `note` |
| 3 | MASTER | `rescue_log` | `backups: [{date: "TT.MM.", serial, status: "OK"/"FEHLER"} ×4]`, `keys: [{nr, name, status: "gültig"/"gesperrt"} ×4]` (zwei gültig), `note` |
| 3 | FI-SI | `rescue_terminal` | `code_table: {"A": "01001101", … "Z": …}` (frei erfunden, jede Runde neu), `word_len: 6`, `note` |
| 3 | FI-AE | `packet_dump` | `disks: [4 Seriennummern]`, `mounted`, `key_id: "0110"` / `tables: [{name, rows: [6 Codes]} ×2]` (beide null bis eingelegt), `note` |
| 4 | MASTER | `repair_console` | `parts: [{id, name, label, ort: kiste/FI-SI/FI-AE/eingebaut}]`, `console: {bay: 4, fan: 3, psu: 2}`, `wartung: ["bay:2", …]`, `installed`, `phase: einbau/start`, `keys`, `note` |
| 4 | FI-SI | `repair_front` | `bays: [{nr, led: gruen/rot/aus}]`, `fan_slots: [{nr, belegt}]`, `hand: [{id, name}]`, `installed`, `phase`, `keys`, `note` |
| 4 | FI-AE | `repair_back` | `psu_bays: [{nr, sicherung: ok/durch}]`, `gang: Warmgang/Kaltgang`, `hand`, `installed`, `phase`, `keys`, `note` |

**Zettel:** Jede Ansicht mit Notizzettel hat `note: {id, title, part, of, torn: ["top"/"right"/"bottom"/"left"…], lines: [{row, style, text}]}` – nur das eigene Stück (Teil `part` von `of`), jede Regel darauf vollständig (`style`: typed, stamp, rule, text, bold, strike, red, sign; bold = fett mit Textmarker). Die Form der Risskante würfelt das Frontend (`TornNote.vue`, gleiche Aufgabe = gleiche Kante).

**Beamer:** `game_tick` erhält zusätzlich `parts` (gefundene Teile), damit der Beamer sie neben dem brennenden Server zeigt.
`game_tick` enthält außerdem `hints: {total, cost, available: [{id, label}], opened: [{id, label, text}]}` – Themen auf dem Abreißblock und abgerissene Zettel der laufenden Aufgabe (Texte nur der abgerissenen).

Neue Eingaben: `open_hint` (nur Host, `{id}` = Thema vom Abreißblock), Finale: `give`, `maintenance`, `install_disk`/`install_fan`/`install_psu`, `return`, `key` (siehe Finale), `release` (Aufgabe 2, MASTER und FI-AE, Wert `"press"`; gelöst, wenn beide innerhalb von `window` Sekunden drücken). `valve_action` hat jetzt den Wert `"RACK:LÖSCHMITTEL"`, `release_pw` entfällt. Aufgabe 3: `mount_disk` (FI-AE, Seriennummer) und `rescue_word` (FI-SI, kein Login mehr) statt `ascii_answer` / `binary_answer` / `sync_button`. Alle anderen `target`-Namen bleiben wie bisher.
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
