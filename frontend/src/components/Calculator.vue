<!--
  Calculator — Taschenrechner für alle Rollen während des Spiels.

  Zu: nur ein schmaler Griff am rechten Rand. Auf: Leiste rechts, die Aufgabe
  rückt zur Seite (PlayerScreen reserviert den Platz über v-model:open), damit
  die Zahlen der Aufgabe sichtbar bleiben. Auf dem Handy: unten als Leiste.
  Gerechnet wird in utils/rechner.js (ohne eval). Tastatur geht, solange der
  Rechner den Fokus hat – Eingabefelder der Aufgaben bleiben unberührt.
-->
<template>
  <div class="calc" :class="{ 'is-open': offen }">
    <button
      class="calc-handle"
      type="button"
      :aria-expanded="offen ? 'true' : 'false'"
      aria-controls="calc-panel"
      :title="offen ? 'Rechner schließen' : 'Rechner öffnen'"
      @click="umschalten"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="5" y="3" width="14" height="18" rx="1.5" />
        <path d="M8 7h8M8 11h2M12 11h2M16 11h0M8 14h2M12 14h2M8 17h2M12 17h2M16 14v3" />
      </svg>
      <span>Rechner</span>
    </button>

    <section
      v-if="offen"
      id="calc-panel"
      ref="panel"
      class="calc-panel"
      tabindex="-1"
      aria-label="Taschenrechner"
      @keydown="taste"
    >
      <div class="calc-display">
        <span class="calc-expr">{{ ausdruck }}</span>
        <span class="calc-result" :class="{ 'is-error': ergebnis === 'Fehler' }">{{ ergebnis }}</span>
      </div>

      <div class="calc-keys">
        <button
          v-for="k in TASTEN"
          :key="k"
          class="calc-key"
          :class="tastenKlasse(k)"
          type="button"
          @click="druecke(k)"
        >{{ k }}</button>
      </div>

      <ol v-if="verlauf.length" class="calc-history" aria-label="Letzte Rechnungen">
        <li v-for="(zeile, i) in verlauf" :key="i">{{ zeile }}</li>
      </ol>
    </section>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { berechne, zeigeZahl } from '../utils/rechner.js'

const props = defineProps({
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['update:open'])

const TASTEN = ['C', '⌫', '÷', '×', '7', '8', '9', '−', '4', '5', '6', '+', '1', '2', '3', '=', '0', ',']
const OPERATOREN = ['+', '−', '×', '÷']
const VERLAUF_MAX = 5

const offen = ref(props.open)
const panel = ref(null)
const ausdruck = ref('')
const ergebnis = ref('')
const verlauf = ref([])
let gerechnet = false   // nach "=": Ziffer startet neu, Operator rechnet weiter

watch(() => props.open, (v) => { offen.value = v })

async function umschalten() {
  offen.value = !offen.value
  emit('update:open', offen.value)
  if (offen.value) {
    await nextTick()
    panel.value?.focus()
  }
}

function endetMitOperator() {
  return OPERATOREN.some((op) => ausdruck.value.endsWith(` ${op} `))
}

function aktuelleZahl() {
  return ausdruck.value.split(' ').at(-1)
}

function druecke(k) {
  if (/^[0-9]$/.test(k)) return ziffer(k)
  if (k === ',') return komma()
  if (OPERATOREN.includes(k)) return operator(k)
  if (k === '=') return rechnen()
  if (k === '⌫') return loeschen()
  if (k === 'C') return alles()
}

function ziffer(z) {
  if (gerechnet) { ausdruck.value = ''; ergebnis.value = ''; gerechnet = false }
  ausdruck.value += z
}

function komma() {
  if (gerechnet) { ausdruck.value = ''; ergebnis.value = ''; gerechnet = false }
  const zahl = aktuelleZahl()
  if (zahl.includes(',')) return
  ausdruck.value += zahl === '' || zahl === '−' ? '0,' : ','
}

function operator(op) {
  if (gerechnet) {
    gerechnet = false
    if (ergebnis.value === 'Fehler' || ergebnis.value === '') return
    ausdruck.value = ergebnis.value
  }
  if (ausdruck.value === '' || ausdruck.value === '−') {
    if (op === '−') ausdruck.value = '−'   // Vorzeichen
    return
  }
  if (endetMitOperator()) ausdruck.value = ausdruck.value.slice(0, -3)
  ausdruck.value += ` ${op} `
}

function rechnen() {
  if (!ausdruck.value || gerechnet) return
  const wert = berechne(ausdruck.value)
  ergebnis.value = wert === null ? 'Fehler' : zeigeZahl(wert)
  if (wert !== null) {
    verlauf.value = [`${ausdruck.value.trim()} = ${ergebnis.value}`, ...verlauf.value].slice(0, VERLAUF_MAX)
  }
  gerechnet = true
}

function loeschen() {
  gerechnet = false
  ergebnis.value = ''
  ausdruck.value = endetMitOperator() ? ausdruck.value.slice(0, -3) : ausdruck.value.slice(0, -1)
}

function alles() {
  gerechnet = false
  ausdruck.value = ''
  ergebnis.value = ''
}

const TASTATUR = { '*': '×', x: '×', '/': '÷', '-': '−', '+': '+', ',': ',', '.': ',', Enter: '=', '=': '=', Backspace: '⌫', Delete: 'C', c: 'C', C: 'C' }

function taste(e) {
  if (e.key === 'Escape') {
    e.preventDefault()
    offen.value = false
    emit('update:open', false)
    return
  }
  const k = /^[0-9]$/.test(e.key) ? e.key : TASTATUR[e.key]
  if (!k) return
  e.preventDefault()
  druecke(k)
}

function tastenKlasse(k) {
  return {
    'is-op': OPERATOREN.includes(k),
    'is-eq': k === '=',
    'is-fn': k === 'C' || k === '⌫',
    'is-wide': k === '0',
  }
}
</script>

<style scoped>
.calc {
  --calc-w: 280px;
}

.calc-handle {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 40;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 8px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
  border-right: none;
  color: var(--fg-2);
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  cursor: pointer;
}

.calc-handle span { writing-mode: vertical-rl; transform: rotate(180deg); }
.calc-handle svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.6; }
.calc-handle:hover { color: var(--green); border-color: var(--green-border); }

.is-open .calc-handle { right: var(--calc-w); color: var(--green); }

.calc-panel {
  position: fixed;
  top: 56px;
  right: 0;
  bottom: 16px;
  width: var(--calc-w);
  z-index: 40;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  border-right: none;
  box-shadow: -12px 0 24px rgba(0, 0, 0, 0.35);
  outline: none;
  overflow-y: auto;
}

.calc-panel:focus-visible { border-color: var(--green-border); }

.calc-display {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  min-height: 78px;
  padding: 12px 14px;
  background: var(--bg);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  overflow-wrap: anywhere;
}

.calc-expr { font-size: 16px; color: var(--fg-2); min-height: 20px; text-align: right; }
.calc-result { font-size: 30px; font-weight: 700; color: var(--green); min-height: 34px; }
.calc-result.is-error { color: var(--red); font-size: 22px; }

.calc-keys {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.calc-key {
  padding: 14px 0;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
  color: var(--fg);
  font-family: var(--mono);
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
}

.calc-key:hover { border-color: var(--border-3); }
.calc-key:active { transform: translateY(1px); }
.calc-key.is-op { color: var(--amber); }
.calc-key.is-fn { color: var(--fg-3); }
.calc-key.is-eq { background: var(--green-bg); border-color: var(--green-border); color: var(--green); grid-row: span 2; }
.calc-key.is-wide { grid-column: span 2; }

.calc-history {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: var(--mono);
  font-size: 13px;
  color: var(--fg-3);
  text-align: right;
}

.calc-history li:first-child { color: var(--fg-2); }

/* Handy: unten als Leiste statt rechts */
@media (max-width: 700px) {
  .calc-panel {
    top: auto;
    left: 0;
    width: auto;
    height: 50vh;
    bottom: 0;
    border-right: 1px solid var(--border-2);
    box-shadow: 0 -12px 24px rgba(0, 0, 0, 0.35);
  }
  .is-open .calc-handle { right: 0; top: auto; bottom: calc(50vh + 8px); transform: none; }
  .calc-key { padding: 10px 0; }
}
</style>
