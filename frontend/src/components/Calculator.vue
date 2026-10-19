<!--
  Calculator — Taschenrechner für alle Rollen während des Spiels.

  Zu: liegt als kleine Taschenrechner-Grafik schräg und halb im Bild am rechten
  Rand, wie auf dem Tisch neben dem Bildschirm. Ein Klick zieht ihn herein (CSS-
  Übergang), die Aufgabe rückt zur Seite (PlayerScreen reserviert den Platz über
  v-model:open). „Wegschieben“ oder Esc legt ihn zurück. Auf dem Handy liegt er
  unten rechts. Die letzten Rechnungen hängen als Papierstreifen oben heraus.
  Gerechnet wird in utils/rechner.js (ohne eval). Tastatur geht, solange der
  Rechner den Fokus hat – Eingabefelder der Aufgaben bleiben unberührt.
-->
<template>
  <div class="calc" :class="{ 'is-open': offen }">
    <section
      ref="panel"
      class="calc-panel"
      tabindex="-1"
      aria-label="Taschenrechner"
      @keydown="taste"
    >
      <!-- Zu: der ganze sichtbare Teil ist der Griff -->
      <button
        v-if="!offen"
        class="calc-handle"
        type="button"
        aria-expanded="false"
        aria-controls="calc-body"
        aria-label="Taschenrechner hervorziehen"
        title="Taschenrechner"
        @click="oeffnen"
      ></button>

      <ol v-if="offen && verlauf.length" class="calc-history" aria-label="Letzte Rechnungen">
        <li v-for="(zeile, i) in verlauf" :key="i">{{ zeile }}</li>
      </ol>

      <div class="calc-top" aria-hidden="true">
        <span class="calc-brand">DRV<b>·</b>CALC</span>
        <span class="calc-solar"><i></i><i></i><i></i><i></i></span>
      </div>

      <div id="calc-body" class="calc-body" :inert="offen ? null : true">
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

        <button class="calc-close" type="button" @click="schliessen">
          Wegschieben <span aria-hidden="true">›</span>
        </button>
      </div>
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

async function oeffnen() {
  offen.value = true
  emit('update:open', true)
  await nextTick()
  panel.value?.focus({ preventScroll: true })
}

function schliessen() {
  offen.value = false
  emit('update:open', false)
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
  if (!offen.value) return
  if (e.key === 'Escape') {
    e.preventDefault()
    schliessen()
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
/* ------------------------------------------------------------- Lage und Bewegung */
.calc-panel {
  --calc-ease: cubic-bezier(0.22, 1, 0.36, 1);
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 40;
  width: 236px;
  padding: 14px 14px 10px;
  box-sizing: border-box;
  border-radius: 18px;
  background: linear-gradient(160deg, #3a3f48 0%, #262a31 55%, #1d2026 100%);
  box-shadow:
    -6px 22px 34px rgba(0, 0, 0, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    inset 0 -4px 0 rgba(0, 0, 0, 0.45);
  outline: none;
  transform-origin: 100% 100%;
  /* zu: halb über den rechten Rand hinaus, schräg wie auf dem Tisch abgelegt */
  transform: translateX(62%) translateY(14px) rotate(-14deg);
  transition: transform 0.6s var(--calc-ease), box-shadow 0.6s var(--calc-ease);
}

.calc:not(.is-open) .calc-panel:hover {
  transform: translateX(54%) translateY(8px) rotate(-11deg);
}

.is-open .calc-panel {
  transform: none;
  box-shadow:
    -10px 26px 44px rgba(0, 0, 0, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    inset 0 -4px 0 rgba(0, 0, 0, 0.45);
}

.calc-handle {
  position: absolute;
  inset: 0;
  z-index: 2;
  border: none;
  border-radius: 18px;
  background: transparent;
  cursor: grab;
}

.calc-handle:focus-visible { outline: 2px solid var(--green); outline-offset: 3px; }

/* ------------------------------------------------------------------- Gehäuse */
.calc-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.calc-brand {
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #c9ced6;
}

.calc-brand b { color: var(--green); }

.calc-solar {
  display: grid;
  grid-template-columns: repeat(4, 14px);
  gap: 2px;
  padding: 2px;
  background: #15171b;
  border-radius: 3px;
}

.calc-solar i {
  display: block;
  height: 12px;
  background: linear-gradient(180deg, #4a3a2c, #2c2219);
}

.calc-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Display: grünliches LCD */
.calc-display {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  min-height: 64px;
  padding: 8px 10px;
  border-radius: 6px;
  background: linear-gradient(180deg, #b7c6a0, #a6b78e);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.45);
  color: #1c2818;
  font-family: var(--mono);
  overflow-wrap: anywhere;
  text-align: right;
}

.calc-expr { font-size: 13px; min-height: 16px; opacity: 0.75; }
.calc-result { font-size: 28px; font-weight: 700; min-height: 32px; line-height: 1.1; }
.calc-result.is-error { color: #8a1c14; font-size: 20px; }

/* Tasten */
.calc-keys {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 7px;
}

.calc-key {
  padding: 11px 0;
  border: none;
  border-radius: 8px;
  background: linear-gradient(180deg, #4a505a, #353a42);
  box-shadow: 0 3px 0 #15171b, inset 0 1px 0 rgba(255, 255, 255, 0.15);
  color: #eef1f5;
  font-family: var(--mono);
  font-size: 17px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.06s, box-shadow 0.06s;
}

.calc-key:active { transform: translateY(3px); box-shadow: 0 0 0 #15171b, inset 0 1px 0 rgba(255, 255, 255, 0.1); }
.calc-key.is-op { background: linear-gradient(180deg, #6a5a3a, #4f4329); color: #ffd27a; }
.calc-key.is-fn { background: linear-gradient(180deg, #6b3b3b, #4e2a2a); color: #ffc9c4; }
.calc-key.is-eq {
  grid-row: span 2;
  background: linear-gradient(180deg, #2f7a4f, #1f5a39);
  color: #e6ffef;
}
.calc-key.is-wide { grid-column: span 2; }

.calc-close {
  align-self: center;
  padding: 4px 10px;
  border: none;
  background: none;
  color: #9aa3ae;
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  cursor: pointer;
}

.calc-close:hover { color: var(--green); }

/* Papierstreifen mit den letzten Rechnungen, hängt oben heraus */
.calc-history {
  position: absolute;
  bottom: calc(100% - 6px);
  left: 26px;
  right: 26px;
  z-index: -1;
  margin: 0;
  padding: 10px 10px 12px;
  list-style: none;
  display: flex;
  flex-direction: column-reverse;
  gap: 3px;
  background: #f3eee1;
  color: #2a2a2a;
  font-family: var(--mono);
  font-size: 12px;
  text-align: right;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.25);
  /* gezackte Abrisskante oben */
  clip-path: polygon(0 6px, 6% 0, 12% 6px, 18% 0, 24% 6px, 30% 0, 36% 6px, 42% 0, 48% 6px, 54% 0, 60% 6px, 66% 0, 72% 6px, 78% 0, 84% 6px, 90% 0, 96% 6px, 100% 0, 100% 100%, 0 100%);
  animation: druck 0.3s ease-out;
}

.calc-history li { opacity: 0.6; }
.calc-history li:first-child { opacity: 1; font-weight: 700; }

@keyframes druck {
  from { transform: translateY(12px); }
  to { transform: none; }
}

/* Handy: liegt unten rechts, kommt von unten */
@media (max-width: 700px) {
  .calc-panel {
    right: 12px;
    bottom: 12px;
    transform: translateY(62%) translateX(10%) rotate(-10deg) scale(0.85);
  }
  .calc:not(.is-open) .calc-panel:hover { transform: translateY(56%) translateX(10%) rotate(-8deg) scale(0.85); }
  .is-open .calc-panel { transform: scale(0.85); }
}

@media (prefers-reduced-motion: reduce) {
  .calc-panel, .calc-key { transition: none; }
  .calc-history { animation: none; }
}
</style>
