# Effekt-Panels

Aufwendige, interaktive Bedienelemente für die Aufgaben (siehe `GAME_DESIGN.md`).
Ein Panel ist **nur Darstellung und Bedienung**: Es kennt weder WebSocket noch Spiellogik.
Die Task-Komponente (`components/tasks/taskN/…`) reicht `view`-Daten als Props hinein,
übersetzt Events in `player_input` und steuert den Zustand über `state`.

| Panel | Datei | Wo | Status |
|---|---|---|---|
| Tresor | `VaultDoor.vue` | Finale: Beamer + Leitstand | fertig (PR #21) |
| Kabelpanel | `WirePanel.vue` | Aufgabe 1, Vorderseite (`main_switches`) | fertig, **Mustervorlage** |
| Steuerpult | `ControlDesk.vue` | Aufgabe 2, Vorderseite (`valve_panel`) | fertig |
| Sync-Knopf | `SyncButton.vue` | Aufgabe 3, Vorder- + Rückseite | Tests liegen bereit |

## Regeln für jedes Panel

1. **Zustand kommt von außen.** Prop `state` mit festen Werten, validiert. Das Panel prüft nie
   selbst, ob eine Eingabe richtig ist.
2. **Eingabe geht als Event raus**, mit fertig formatiertem Wert. Kein `fetch`, kein Socket.
3. **Gesperrt heißt gesperrt:** in `checking` und im Erfolgszustand keine Events.
4. **Nach `error` → zurück auf den Grundzustand** setzt das Panel seine Eingabe zurück
   (wie das Kabel, das wieder geflickt wird).
5. **Nur SVG + CSS**, keine Bilder. Skaliert mit der Containerbreite (`viewBox` oder `cqw`),
   `max-width: 640px`.
6. **Klassen mit eigenem Präfix** (`wp-`, `vd-`, …): globale Klassen aus `style.css`
   wie `.panel` schlagen sonst durch.
7. **Farben:** Akzente über `var(--amber)`, `var(--green)`, `var(--red)` mit Fallback.
   Grün = geschafft, Rot = Fehler, Bernstein = Auswahl/Warten.
8. **Fühlbar:** jeder Klick hat eine sichtbare Reaktion (Glühen, Einrasten, Federn).
   Fehler = Rütteln + roter Blitz. Erfolg = grünes Leuchten.
9. **Barrierearm:** Bedienteile per Tastatur erreichbar, `aria-label` auf Deutsch,
   `@media (prefers-reduced-motion: reduce)` schaltet Animationen ab.
10. **Vorschau:** jedes Panel bekommt eine `<section>` in `src/dev/PanelsDemo.vue`
    (`http://localhost:5173/panels-demo.html`), mit einer simulierten Prüfung per `setTimeout`.
11. **Tests:** `tests/<Panel>.spec.js` mit Vitest. Geprüft wird das Verhalten (Events, Sperren,
    Zustände), nicht das Aussehen.

## Schnittstellen

### WirePanel (fertig)
- Props: `wires: string[]` (Symbole, = `view.switches`), `state: "armed"|"checking"|"defused"|"error"`, `seconds?: number`
- Event: `cut({ index, symbol })` → `player_input { target: "main_switch", value: symbol }`
- Kabelfarben bewusst nicht rot/gelb/grün/blau (das sind in Aufgabe 1 die Code-Farben).

### ControlDesk (Aufgabe 2, Vorderseite)
Industriepult: **Drehregler** wählt das Ventil, **Schieberegler** wählt die Farbe,
**Manometer** zeigt den Fortschritt, **Hebel/Knopf „AUSLÖSEN"** schickt den Schritt.
- Props:
  - `valves: string[]` (= `view.valves`, z. B. `["V-31","V-32","V-33"]`)
  - `colors: string[]` (= `view.colors`, z. B. `["ORANGE","RED","GREEN"]`)
  - `step: number` (bereits erledigte Schritte, = `view.step`)
  - `sequenceLen: number` (= `view.sequence_len`)
  - `state: "idle"|"checking"|"error"|"done"`
- Event: `submit("V-32:RED")` → `player_input { target: "valve_action", value }`
- Startstellung: erstes Ventil, erste Farbe. Drehregler per Klick/Pfeiltasten, Schieberegler per Klick/Pfeiltasten.
- Nach `error` → `idle`: Regler bleiben stehen (der Spieler korrigiert nur), aber der Hebel federt zurück.
- Ideen: Manometer-Nadel zittert leicht, springt pro Schritt ein Segment weiter; bei `done` rauscht Wasser (blaue Partikel) und das Pult leuchtet grün.

### SyncButton (Aufgabe 3, Vorder- und Rückseite)
Großer roter **Pilz-Notknopf unter einer Klappe**. Erst Klappe öffnen, dann drücken.
Ein **Ring** um den Knopf läuft die 3 Sekunden ab, in denen der Partner drücken muss.
- Props:
  - `unlocked: boolean` (= `view.button_unlocked`; vorher ist die Klappe verplombt)
  - `state: "idle"|"waiting"|"synced"|"error"`
  - `windowMs: number` (Default `3000`)
- Event: `press()` → `player_input { target: "sync_button", value: "press" }`
- Ablauf: Klappe öffnen (`cover-open`-Klasse) → Druck → Elternteil setzt `waiting` (Ring läuft ab, „WARTE AUF PARTNER") → `synced` (grün, „DATEN GERETTET") oder `error` (Ring rot, zurück auf `idle`, Klappe bleibt offen).
- Gesperrt: solange `unlocked` false, und in `waiting`/`synced`.
