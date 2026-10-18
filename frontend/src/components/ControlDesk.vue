<!--
  ControlDesk — Steuerpult für Aufgabe 2, Vorderseite (GAME_DESIGN.md, frontend/PANELS.md).

  Drei Bedienteile, ein Auslöser:
    Drehregler   wählt das Ventil (role="slider", aria-label="Ventil")
    Schieberegler wählt die Farbe (role="slider", aria-label="Farbe")
    Manometer    zeigt den Fortschritt (role="progressbar", aria-valuenow/-max)
    Auslöser     schickt den Schritt (submit "VENTIL:FARBE")

  Pfeil rechts/oben = nächste Stellung, links/unten = vorherige, an den Enden ist
  Anschlag. Klick auf einen Regler dreht/schiebt eine Stellung weiter und läuft am
  Ende wieder auf die erste. In "checking" und "done" ist alles gesperrt; nach
  "error" bleiben die Regler stehen, der Hebel federt zurück.

  Das Panel prüft nichts selbst — es meldet nur `submit`.
  Alles CSS + SVG, keine Bilder, max-width 640px.
-->
<template>
  <div class="cd" :class="[`cd--${state}`, { 'is-locked': locked }]" role="group" :aria-label="ariaLabel">
    <div class="cd__panel">
      <span v-for="p in SCREWS" :key="p" class="cd__screw" :style="{ left: p[0], top: p[1] }"></span>

      <!-- Kopfleiste -->
      <header class="cd__header">
        <span class="cd__hazard"></span>
        <span class="cd__title">STEUERPULT · LÖSCHANLAGE</span>
        <span class="cd__hazard"></span>
        <span class="cd__lamp"><i class="cd__lamp-dot"></i>{{ lampText }}</span>
      </header>

      <div class="cd__body">
        <!-- ---------------------------------------------------------- Drehregler -->
        <div class="cd__unit">
          <span class="cd__unit-label">VENTIL</span>
          <div
            class="cd__dial"
            role="slider"
            aria-label="Ventil"
            tabindex="0"
            aria-valuemin="0"
            :aria-valuemax="Math.max(0, valves.length - 1)"
            :aria-valuenow="valveIdx"
            :aria-valuetext="valve"
            @click="cycle('valve')"
            @keydown="onKey($event, 'valve')"
          >
            <span
              v-for="(v, i) in valves"
              :key="`t-${v}`"
              class="cd__dial-tick"
              :class="{ 'is-active': i === valveIdx }"
              :style="{ transform: `rotate(${angleFor(i, valves.length)}deg)` }"
            ></span>
            <span class="cd__dial-face">
              <span class="cd__dial-knurl"></span>
              <span
                class="cd__dial-pointer"
                :style="{ transform: `rotate(${angleFor(valveIdx, valves.length)}deg)` }"
              ></span>
              <span class="cd__dial-cap"></span>
            </span>
          </div>
          <span class="cd__readout">{{ valve }}</span>
        </div>

        <!-- ------------------------------------------------------- Schieberegler -->
        <div class="cd__unit">
          <span class="cd__unit-label">FARBE</span>
          <div
            class="cd__slider"
            role="slider"
            aria-label="Farbe"
            tabindex="0"
            aria-valuemin="0"
            :aria-valuemax="Math.max(0, colors.length - 1)"
            :aria-valuenow="colorIdx"
            :aria-valuetext="color"
            @click="cycle('color')"
            @keydown="onKey($event, 'color')"
          >
            <span class="cd__rail">
              <span
                v-for="(c, i) in colors"
                :key="`s-${c}`"
                class="cd__slot"
                :class="{ 'is-active': i === colorIdx }"
                :style="{ '--slot': colorHex(c) }"
              ></span>
            </span>
            <span class="cd__handle" :style="{ '--pos': handlePos }">
              <i></i><i></i><i></i>
            </span>
          </div>
          <span class="cd__readout" :style="{ '--slot': colorHex(color) }">{{ color }}</span>
        </div>

        <!-- ------------------------------------------------------------ Manometer -->
        <div class="cd__unit">
          <span class="cd__unit-label">FORTSCHRITT</span>
          <div
            class="cd__gauge"
            role="progressbar"
            aria-label="Fortschritt"
            aria-valuemin="0"
            :aria-valuenow="step"
            :aria-valuemax="sequenceLen"
          >
            <svg viewBox="0 0 200 160" aria-hidden="true">
              <defs>
                <linearGradient id="cd-arc" x1="0" y1="1" x2="1" y2="0">
                  <stop offset="0" stop-color="#ffb830" />
                  <stop offset="1" stop-color="#00ff66" />
                </linearGradient>
              </defs>
              <path class="cd__gauge-arc" d="M 34.2 148 A 76 76 0 1 1 165.8 148" />
              <line
                v-for="t in ticks"
                :key="`k-${t.i}`"
                class="cd__gauge-tick"
                :class="{ 'is-done': t.i <= step }"
                :x1="t.x1" :y1="t.y1" :x2="t.x2" :y2="t.y2"
              />
              <g class="cd__gauge-needle" :style="{ transform: `rotate(${needleAngle}deg)` }">
                <line x1="100" y1="110" x2="100" y2="40" />
                <circle cx="100" cy="110" r="8" />
                <circle cx="100" cy="110" r="3" class="cd__gauge-hub" />
              </g>
            </svg>
            <span class="cd__gauge-value">{{ step }} / {{ sequenceLen }}</span>
          </div>
          <span class="cd__readout cd__readout--small">{{ valueText }}</span>
        </div>
      </div>

      <!-- ---------------------------------------------------------------- Auslöser -->
      <button class="cd__fire" type="button" aria-label="Auslösen" :disabled="locked" @click="fire">
        <span class="cd__fire-edge"></span>
        <span class="cd__fire-text">{{ fireText }}</span>
      </button>

      <p class="cd__status" role="status" aria-live="polite">{{ statusText }}</p>

      <span class="cd__flash" aria-hidden="true"></span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  valves: { type: Array, required: true },
  colors: { type: Array, required: true },
  step: { type: Number, default: 0 },
  sequenceLen: { type: Number, default: 3 },
  state: {
    type: String,
    default: 'idle',
    validator: (v) => ['idle', 'checking', 'error', 'done'].includes(v),
  },
})
const emit = defineEmits(['submit'])

const SCREWS = [['8px', '8px'], ['calc(100% - 20px)', '8px'], ['8px', 'calc(100% - 20px)'], ['calc(100% - 20px)', 'calc(100% - 20px)']]
const SWEEP = 240 // Grad zwischen erster und letzter Stellung
const COLOR_HEX = {
  ORANGE: '#ff8c1a',
  ROT: '#ff3a4d',
  RED: '#ff3a4d',
  GRÜN: '#00ff66',
  GRUEN: '#00ff66',
  GREEN: '#00ff66',
  GELB: '#f2c200',
  YELLOW: '#f2c200',
  BLAU: '#4a7dff',
  BLUE: '#4a7dff',
  VIOLETT: '#8e5cf0',
  PURPLE: '#8e5cf0',
}

const valveIdx = ref(0)
const colorIdx = ref(0)

// Gesperrt nur in "checking" und im Erfolgszustand (PANELS.md, Regel 3).
const locked = computed(() => props.state === 'checking' || props.state === 'done')

const valve = computed(() => props.valves[valveIdx.value] ?? '—')
const color = computed(() => props.colors[colorIdx.value] ?? '—')

const handlePos = computed(() => {
  const n = props.colors.length
  if (n <= 1) return '50%'
  return `${(colorIdx.value / (n - 1)) * 100}%`
})
const needleAngle = computed(() => {
  const max = Math.max(1, props.sequenceLen)
  const frac = Math.min(1, Math.max(0, props.step / max))
  return -120 + frac * SWEEP
})

const ticks = computed(() => {
  const max = Math.max(1, props.sequenceLen)
  return Array.from({ length: max + 1 }, (_, i) => {
    const rad = ((210 - (i / max) * SWEEP) * Math.PI) / 180
    const r1 = 76
    const r2 = i % 1 === 0 ? 64 : 68
    return {
      i,
      x1: 100 + r1 * Math.cos(rad),
      y1: 110 - r1 * Math.sin(rad),
      x2: 100 + r2 * Math.cos(rad),
      y2: 110 - r2 * Math.sin(rad),
    }
  })
})

const valueText = computed(() => (props.step >= props.sequenceLen ? 'VOLL' : `${props.step} SCHRITT`))
const lampText = computed(
  () => ({ idle: 'BEREIT', checking: 'PRÜFE', error: 'STÖRUNG', done: 'OK' })[props.state],
)
const fireText = computed(() => {
  if (props.state === 'done') return 'GELÖST'
  if (props.state === 'checking') return 'PRÜFE …'
  return 'AUSLÖSEN'
})
const statusText = computed(() => {
  return {
    idle: 'SCHRITT WÄHLEN UND AUSLÖSEN',
    checking: 'PRÜFE SCHRITT …',
    error: 'FEHLER — REGLER KORRIGIEREN',
    done: 'LÖSCHANLAGE GEFLUTET',
  }[props.state]
})
const ariaLabel = computed(() => `Steuerpult, Zustand ${lampText.value}`)

function angleFor(i, n) {
  if (n <= 1) return 0
  return -SWEEP / 2 + (i / (n - 1)) * SWEEP
}
function colorHex(name) {
  return COLOR_HEX[String(name).toUpperCase()] ?? 'var(--amber, #ffb830)'
}
function clamp(v, max) {
  return Math.min(Math.max(0, v), max)
}

function stepBy(kind, dir) {
  if (locked.value) return
  if (kind === 'valve') {
    valveIdx.value = clamp(valveIdx.value + dir, props.valves.length - 1)
  } else {
    colorIdx.value = clamp(colorIdx.value + dir, props.colors.length - 1)
  }
}

// Klick: eine Stellung weiter, am Ende wieder auf die erste.
function cycle(kind) {
  if (locked.value) return
  if (kind === 'valve') {
    const n = props.valves.length
    if (n) valveIdx.value = (valveIdx.value + 1) % n
  } else {
    const n = props.colors.length
    if (n) colorIdx.value = (colorIdx.value + 1) % n
  }
}

function onKey(e, kind) {
  if (!['ArrowRight', 'ArrowUp', 'ArrowLeft', 'ArrowDown'].includes(e.key)) return
  e.preventDefault()
  const dir = e.key === 'ArrowRight' || e.key === 'ArrowUp' ? 1 : -1
  stepBy(kind, dir)
}

function fire() {
  if (locked.value) return
  emit('submit', `${valve.value}:${color.value}`)
}

// Neue Runde mit kürzerer Liste darf keinen Index außerhalb lassen.
watch(
  () => props.valves.length,
  (n) => (valveIdx.value = clamp(valveIdx.value, Math.max(0, n - 1))),
)
watch(
  () => props.colors.length,
  (n) => (colorIdx.value = clamp(colorIdx.value, Math.max(0, n - 1))),
)
</script>

<style scoped>
.cd {
  width: 100%;
  max-width: 640px;
  margin-inline: auto;
  font-family: 'Share Tech Mono', ui-monospace, monospace;
}

.cd__panel {
  position: relative;
  display: grid;
  gap: 12px;
  padding: 16px 16px 14px;
  border-radius: 10px;
  border: 3px solid #0a0c0f;
  background:
    repeating-linear-gradient(180deg, rgba(255, 255, 255, .025) 0 2px, transparent 2px 5px),
    linear-gradient(160deg, #3a4149 0%, #262c33 48%, #151a1f 100%);
  box-shadow: inset 0 2px 0 rgba(255, 255, 255, .08), 0 14px 24px rgba(0, 0, 0, .6);
}

.cd__screw {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #8f99a4, #4a525c 60%, #1b2026);
  box-shadow: inset 0 0 0 1px #0b0e12, 0 1px 2px rgba(0, 0, 0, .6);
}

/* ---------------------------------------------------------------- Kopfleiste */
.cd__header {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto;
  align-items: center;
  gap: 8px;
}
.cd__hazard {
  height: 14px;
  border-radius: 2px;
  background: repeating-linear-gradient(45deg, #f2c200 0 8px, #171717 8px 16px);
  opacity: .8;
}
.cd__title {
  padding: 5px 12px;
  border-radius: 3px;
  background: #0f1216;
  border: 1px solid #000;
  color: #f2c200;
  font-size: 12px;
  letter-spacing: 3px;
  white-space: nowrap;
}
.cd__lamp {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 4px 10px;
  border-radius: 3px;
  background: #0d1014;
  border: 1px solid #000;
  color: #93a1ad;
  font-size: 10px;
  letter-spacing: 2px;
}
.cd__lamp-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--amber, #ffb830);
  box-shadow: 0 0 8px var(--amber, #ffb830);
}
.cd--checking .cd__lamp-dot { animation: cd-blink .5s steps(2, start) infinite; }
.cd--error .cd__lamp-dot { background: var(--red, #ff3a4d); box-shadow: 0 0 9px var(--red, #ff3a4d); animation: cd-blink .3s steps(2, start) infinite; }
.cd--done .cd__lamp-dot { background: var(--green, #00ff66); box-shadow: 0 0 10px var(--green, #00ff66); animation: none; }

/* ------------------------------------------------------------------- Einheiten */
.cd__body {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
}

.cd__unit {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 10px 8px 8px;
  border-radius: 6px;
  border: 1px solid #0a0c0f;
  background: linear-gradient(180deg, #1a1f25, #0f1317);
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, .7);
}
.cd__unit-label {
  font-size: 9px;
  letter-spacing: 2px;
  color: #7b8894;
}

.cd__readout {
  min-width: 84%;
  padding: 3px 6px;
  text-align: center;
  border-radius: 2px;
  background: #08090b;
  border: 1px solid #000;
  color: var(--slot, var(--amber, #ffb830));
  font-size: 13px;
  letter-spacing: 2px;
  text-shadow: 0 0 8px currentColor;
}
.cd__readout--small { font-size: 10px; letter-spacing: 1px; color: #8fa0ac; text-shadow: none; }

/* ------------------------------------------------------------------ Drehregler */
.cd__dial {
  position: relative;
  width: 100%;
  max-width: 150px;
  aspect-ratio: 1 / 1;
  border-radius: 50%;
  cursor: pointer;
  outline: none;
  touch-action: manipulation;
}
.cd__dial-tick {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 2px;
  height: 12px;
  margin: -78px 0 0 -1px;
  transform-origin: 50% 78px;
  background: #4c565f;
  border-radius: 1px;
  transition: background .2s, box-shadow .2s;
}
.cd__dial-tick.is-active {
  background: var(--amber, #ffb830);
  box-shadow: 0 0 8px var(--amber, #ffb830);
}
.cd__dial-face {
  position: absolute;
  inset: 14%;
  display: block;
  border-radius: 50%;
  background: radial-gradient(circle at 34% 26%, #5a646e, #333a42 45%, #14181d 100%);
  box-shadow: inset 0 -6px 12px rgba(0, 0, 0, .7), inset 0 4px 8px rgba(255, 255, 255, .1), 0 8px 14px rgba(0, 0, 0, .6);
}
.cd__dial-knurl {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: repeating-conic-gradient(from 0deg, rgba(255, 255, 255, .14) 0 2deg, rgba(0, 0, 0, .3) 2deg 4deg);
  mask: radial-gradient(circle, transparent 62%, #000 64%);
  -webkit-mask: radial-gradient(circle, transparent 62%, #000 64%);
}
.cd__dial-pointer {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 4px;
  height: 46%;
  margin-left: -2px;
  margin-top: -46%;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--red, #ff3a4d), #8d1017);
  box-shadow: 0 0 6px rgba(255, 58, 77, .6);
  transform-origin: 50% 100%;
  transition: transform .25s cubic-bezier(.3, 1.4, .5, 1);
}
.cd__dial-cap {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 26%;
  aspect-ratio: 1 / 1;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: radial-gradient(circle at 36% 30%, #7d8792, #3b434b 60%, #1a1f24);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .25), 0 2px 4px rgba(0, 0, 0, .6);
}
.cd__dial:active .cd__dial-face { transform: scale(.98); }
.cd__dial:focus-visible .cd__dial-face { box-shadow: 0 0 0 3px var(--amber, #ffb830), inset 0 -6px 12px rgba(0, 0, 0, .7); }

/* --------------------------------------------------------------- Schieberegler */
.cd__slider {
  position: relative;
  width: 100%;
  height: 74px;
  display: grid;
  place-items: center;
  cursor: pointer;
  outline: none;
}
.cd__rail {
  position: absolute;
  left: 4%;
  right: 4%;
  top: 50%;
  height: 16px;
  transform: translateY(-50%);
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  gap: 3px;
  padding: 2px;
  border-radius: 4px;
  background: #0a0c0f;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, .9);
}
.cd__slot {
  border-radius: 2px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--slot) 55%, #000), var(--slot));
  opacity: .35;
  transition: opacity .2s, box-shadow .2s;
}
.cd__slot.is-active {
  opacity: 1;
  box-shadow: 0 0 10px var(--slot);
}
.cd__handle {
  position: absolute;
  left: calc(6% + (var(--pos) * 0.88));
  top: 50%;
  width: 30px;
  height: 44px;
  transform: translate(-50%, -50%);
  border-radius: 5px;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 3px;
  background: linear-gradient(180deg, #8d99a4 0%, #4b545e 38%, #2a3138 100%);
  border: 1px solid #0a0c0f;
  box-shadow: 0 4px 8px rgba(0, 0, 0, .7), inset 0 1px 0 rgba(255, 255, 255, .3);
  transition: left .25s cubic-bezier(.3, 1.4, .5, 1);
}
.cd__handle i {
  width: 16px;
  height: 2px;
  border-radius: 1px;
  background: rgba(0, 0, 0, .45);
  box-shadow: 0 1px 0 rgba(255, 255, 255, .18);
}
.cd__slider:focus-visible .cd__handle { box-shadow: 0 0 0 3px var(--amber, #ffb830), 0 4px 8px rgba(0, 0, 0, .7); }

/* ------------------------------------------------------------------- Manometer */
.cd__gauge {
  position: relative;
  width: 100%;
  max-width: 150px;
}
.cd__gauge svg { display: block; width: 100%; height: auto; }
.cd__gauge-arc {
  fill: none;
  stroke: url(#cd-arc);
  stroke-width: 6;
  stroke-linecap: round;
  opacity: .35;
}
.cd__gauge-tick { stroke: #59636d; stroke-width: 2.5; stroke-linecap: round; transition: stroke .25s; }
.cd__gauge-tick.is-done { stroke: var(--green, #00ff66); }
.cd__gauge-needle line { stroke: var(--red, #ff3a4d); stroke-width: 4; stroke-linecap: round; }
.cd__gauge-needle circle { fill: #2a3138; stroke: #0a0c0f; stroke-width: 2; }
.cd__gauge-needle .cd__gauge-hub { fill: var(--red, #ff3a4d); stroke: none; }
.cd__gauge-needle {
  transform-box: view-box;
  transform-origin: 100px 110px;
  transition: transform .45s cubic-bezier(.3, 1.5, .5, 1);
  filter: drop-shadow(0 0 4px rgba(255, 58, 77, .5));
}
.cd__gauge-value {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 2%;
  text-align: center;
  font-size: 12px;
  letter-spacing: 2px;
  color: #93a1ad;
}

/* ------------------------------------------------------------------- Auslöser */
.cd__fire {
  position: relative;
  margin-top: 2px;
  padding: 14px 20px;
  border: 2px solid #2b0508;
  border-radius: 6px;
  background: linear-gradient(180deg, #d32735 0%, #9d121e 55%, #6d0a13 100%);
  color: #fff;
  font: inherit;
  font-size: 20px;
  letter-spacing: 6px;
  cursor: pointer;
  box-shadow: 0 6px 0 #3d070c, 0 10px 18px rgba(0, 0, 0, .55), inset 0 1px 0 rgba(255, 255, 255, .3);
  transition: transform .08s, box-shadow .08s, background .3s;
}
.cd__fire:active:not(:disabled) { transform: translateY(4px); box-shadow: 0 2px 0 #3d070c, inset 0 1px 0 rgba(255, 255, 255, .3); }
.cd__fire:focus-visible { outline: 3px solid var(--amber, #ffb830); outline-offset: 2px; }
.cd__fire:disabled {
  cursor: default;
  color: #98a4ae;
  background: linear-gradient(180deg, #333a42, #1d2329);
  box-shadow: 0 4px 0 #0d1115, inset 0 1px 0 rgba(255, 255, 255, .08);
}
.cd--checking .cd__fire:disabled { color: var(--amber, #ffb830); }
.cd--done .cd__fire:disabled { color: var(--green, #00ff66); background: linear-gradient(180deg, #16401f, #0a2311); box-shadow: 0 4px 0 #05130a, 0 0 22px rgba(0, 255, 102, .35); }
.cd__fire-edge {
  position: absolute;
  inset: 3px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, .12);
  pointer-events: none;
}
.cd__fire-text { position: relative; }
.cd--error .cd__fire { animation: cd-blink-red .35s steps(2, start) 3; }

/* --------------------------------------------------------------------- Status */
.cd__status {
  margin: 0;
  text-align: center;
  font-size: 12px;
  letter-spacing: 3px;
  color: #7d8a95;
}
.cd--checking .cd__status { color: var(--amber, #ffb830); animation: cd-pulse .9s ease-in-out infinite; }
.cd--error .cd__status { color: var(--red, #ff3a4d); }
.cd--done .cd__status { color: var(--green, #00ff66); text-shadow: 0 0 10px rgba(0, 255, 102, .5); }

/* ------------------------------------------------------------------- Fehler */
.cd__flash {
  position: absolute;
  inset: 0;
  border-radius: 8px;
  background: var(--red, #ff3a4d);
  opacity: 0;
  pointer-events: none;
}
.cd--error .cd__flash { animation: cd-flash .5s ease-out; }
.cd--error .cd__panel { animation: cd-shake .45s; }
.cd--done .cd__panel { box-shadow: inset 0 2px 0 rgba(255, 255, 255, .08), 0 0 26px rgba(0, 255, 102, .3), 0 14px 24px rgba(0, 0, 0, .6); }
.cd--done .cd__title { color: var(--green, #00ff66); }

@keyframes cd-blink { 50% { opacity: .25; } }
@keyframes cd-blink-red {
  50% { background: linear-gradient(180deg, #ff5566, #a3121f); box-shadow: 0 6px 0 #3d070c, 0 0 22px rgba(255, 58, 77, .6); }
}
@keyframes cd-pulse { 50% { opacity: .5; } }
@keyframes cd-flash { 0% { opacity: .4; } 100% { opacity: 0; } }
@keyframes cd-shake {
  10%, 90% { transform: translateX(-2px); }
  20%, 80% { transform: translateX(4px); }
  30%, 50%, 70% { transform: translateX(-7px); }
  40%, 60% { transform: translateX(7px); }
}

@media (prefers-reduced-motion: reduce) {
  .cd__lamp-dot, .cd__status, .cd__flash, .cd__panel, .cd__fire,
  .cd__dial-pointer, .cd__handle, .cd__gauge-needle { animation: none !important; transition: none !important; }
}
</style>
