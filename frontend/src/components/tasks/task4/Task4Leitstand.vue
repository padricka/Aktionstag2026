<!--
  Finale · Leitstand (view.type "repair_console", GAME_DESIGN.md „Finale“):
  Teilekiste mit Etiketten → Teile an Vorderseite/Rückseite geben; Management-Konsole
  (zählt ab 0!) → Plätze auf Wartung schalten; zuletzt der Schlüssel „System“.
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Finale · Server reparieren</h2>
      <span class="role">Leitstand</span>
    </header>

    <p class="hint">
      Gib die Teile an die Richtigen weiter und schalte vor jedem Einbau den Platz in der Konsole
      auf Wartung. Die Etiketten stehen nur hier – lies sie vor.
    </p>

    <div v-if="!view" class="empty">Warte auf Task-Daten …</div>

    <div v-else class="body">
      <div class="main-col">
        <!-- was falsch war (vom Server), oben gut sichtbar -->
        <p v-if="serverError" class="msg-err" role="alert">{{ serverError }}</p>
        <section class="panel">
          <span class="panel-label">Teilekiste</span>
          <ul class="teile">
            <li v-for="t in view.parts" :key="t.id" class="teil-zeile" :class="`ort--${ortKlasse(t.ort)}`">
              <TeilGrafik class="teil-bild" :teil="t.id" :dreht="t.id === 'fan' && t.ort === 'eingebaut'" />
              <div class="teil-info">
                <strong>{{ t.name }}</strong>
                <span v-if="t.label" class="etikett">{{ t.label }}</span>
                <span class="ort">{{ ortText(t.ort) }}</span>
              </div>
              <div v-if="t.ort !== 'eingebaut'" class="geben">
                <button class="geben-vorne" type="button" :disabled="t.ort === 'FI-SI'" @click="geben(t.id, 'FI-SI')">
                  → Vorderseite
                </button>
                <button class="geben-hinten" type="button" :disabled="t.ort === 'FI-AE'" @click="geben(t.id, 'FI-AE')">
                  → Rückseite
                </button>
              </div>
            </li>
          </ul>
        </section>

        <section class="panel konsole">
          <span class="panel-label">Management-Konsole · iRMC</span>
          <div class="konsole-schirm">
            <div v-for="gruppe in gruppen" :key="gruppe.art" class="konsole-gruppe">
              <span class="konsole-titel">{{ gruppe.titel }}</span>
              <button
                v-for="i in gruppe.anzahl"
                :key="i"
                class="konsole-platz"
                :class="{ 'is-wartung': inWartung(gruppe.art, i - 1) }"
                :data-art="gruppe.art"
                type="button"
                @click="wartung(gruppe.art, i - 1)"
              >
                <span class="platz-name">{{ gruppe.kurz }} {{ i - 1 }}</span>
                <span class="platz-status">{{ inWartung(gruppe.art, i - 1) ? 'WARTUNG' : 'AKTIV' }}</span>
              </button>
            </div>
          </div>
        </section>

        <section class="panel">
          <span class="panel-label">Hochfahren</span>
          <div class="schluessel-reihe">
            <SchluesselSchalter
              label="System"
              :bereit="view.phase === 'start'"
              :gedreht="(view.keys || []).includes('system')"
              @drehen="emit('eingabe', { target: 'key', value: 'system' })"
            />
            <p class="schluessel-stand">
              {{ view.phase === 'start' ? `Schlüssel gedreht: ${(view.keys || []).length}/3` : 'Erst alle Teile einbauen.' }}
            </p>
          </div>
        </section>

      </div>

      <aside v-if="view.note" class="note-col">
        <span class="panel-label">Dein Teil der Einbauanleitung</span>
        <TornNote :note="view.note" :seed="noteSeed" />
      </aside>
    </div>

    <div v-if="victory" class="sieg">SERVER FÄHRT HOCH …</div>
  </div>
</template>

<script setup>
import TornNote from '../../TornNote.vue'
import TeilGrafik from '../../TeilGrafik.vue'
import SchluesselSchalter from './SchluesselSchalter.vue'

const props = defineProps({
  view: { type: Object, default: null },
  noteSeed: { type: String, default: '' },
  serverError: { type: String, default: '' },
  victory: { type: Boolean, default: false },
})
const emit = defineEmits(['eingabe'])

const gruppen = [
  { art: 'bay', titel: 'Festplatten', kurz: 'BAY', anzahl: props.view?.console?.bay || 4 },
  { art: 'fan', titel: 'Lüfter', kurz: 'FAN', anzahl: props.view?.console?.fan || 3 },
  { art: 'psu', titel: 'Netzteile', kurz: 'PSU', anzahl: props.view?.console?.psu || 2 },
]

const ORTE = { kiste: 'in der Kiste', 'FI-SI': 'bei der Vorderseite', 'FI-AE': 'bei der Rückseite', eingebaut: 'eingebaut ✓' }
const ortText = (ort) => ORTE[ort] || ort
const ortKlasse = (ort) => ({ 'FI-SI': 'vorne', 'FI-AE': 'hinten' })[ort] || ort

const inWartung = (art, i) => (props.view?.wartung || []).includes(`${art}:${i}`)

function geben(teil, an) {
  emit('eingabe', { target: 'give', value: `${teil}:${an}` })
}

function wartung(art, i) {
  emit('eingabe', { target: 'maintenance', value: `${art}:${i}` })
}
</script>

<style scoped src="./finale.css"></style>
<style scoped>
.teile { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
.teil-zeile {
  display: grid;
  grid-template-columns: 84px 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 10px 12px;
  background: var(--bg);
  border: 1px solid var(--border-2);
}
.teil-zeile.ort--eingebaut { border-color: var(--green-border); }
.teil-info { display: flex; flex-direction: column; gap: 4px; font-family: var(--mono); }
.teil-info strong { color: var(--fg); font-size: 15px; }
.etikett {
  align-self: flex-start;
  padding: 2px 8px;
  background: #f3eee1;
  color: #1a1d22;
  font-weight: 700;
  font-size: 14px;
  transform: rotate(-1.5deg);
}
.ort { font-size: 12px; color: var(--fg-3); }
.ort--eingebaut .ort { color: var(--green); }
.ort--vorne .ort, .ort--hinten .ort { color: var(--amber); }
.geben { display: flex; flex-direction: column; gap: 6px; }
.geben button {
  padding: 6px 12px;
  background: var(--bg-2);
  border: 1px solid var(--border-3);
  color: var(--fg-2);
  font-family: var(--mono);
  font-size: 12px;
  cursor: pointer;
}
.geben button:hover:not(:disabled) { border-color: var(--green-border); color: var(--green); }
.geben button:disabled { opacity: 0.4; cursor: default; }

/* Konsole: grüner Text auf Schwarz wie ein echtes Management-Interface */
.konsole-schirm {
  display: grid;
  gap: 12px;
  padding: 14px;
  background: #030604;
  border: 1px solid #12301c;
  box-shadow: inset 0 0 24px rgba(0, 255, 102, 0.06);
  font-family: var(--mono);
}
.konsole-gruppe { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.konsole-titel { width: 100px; font-size: 12px; color: var(--fg-3); letter-spacing: 0.08em; }
.konsole-platz {
  display: grid;
  gap: 2px;
  min-width: 82px;
  padding: 6px 10px;
  background: #07120b;
  border: 1px solid #1d4a2c;
  color: var(--green);
  font-family: var(--mono);
  text-align: left;
  cursor: pointer;
}
.platz-name { font-size: 13px; font-weight: 700; }
.platz-status { font-size: 10px; letter-spacing: 0.12em; opacity: 0.8; }
.konsole-platz.is-wartung {
  background: rgba(255, 184, 48, 0.12);
  border-color: var(--amber-border);
  color: var(--amber);
  box-shadow: 0 0 12px rgba(255, 184, 48, 0.2);
}
</style>
