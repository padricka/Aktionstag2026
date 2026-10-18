<!--
  WirePanel — Notabschaltung zum Kabelkappen (Aufgabe 1, Vorderseite; GAME_DESIGN.md).

  Ersetzt optisch die Hauptschalter: Jedes Kabel trägt das Symbol seines Steckplatzes.
  Kabel anklicken (oder Tab + Enter) wählt es aus, "KABEL KAPPEN" sendet `cut`.

  Props
    wires  Symbole in Steckplatz-Reihenfolge, z. B. view.switches
    seconds  optional: Restzeit in Sekunden, erscheint als rote Countdown-Anzeige
    state  "armed" | "checking" | "defused" | "error"  (vom Elternteil gesteuert,
           die Komponente prüft NICHT selbst)
             checking -> gekapptes Kabel sprüht Funken, Panel wartet
             defused  -> LED grün, "SYSTEM SICHER"
             error    -> Panel rüttelt, rot; zurück auf "armed" flickt das Kabel wieder
  Event
    cut({ index, symbol })

  Kabelfarben bewusst NICHT rot/gelb/grün/blau: die gehören in Aufgabe 1 zum Code.
  Alles SVG + CSS, skaliert mit der Containerbreite.
-->
<template>
  <div class="wp" :class="`wp--${state}`" role="group" :aria-label="ariaLabel">
    <svg class="wp__svg" viewBox="0 0 400 270" aria-hidden="false">
      <defs>
        <linearGradient id="wp-metal" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#454c55" />
          <stop offset=".5" stop-color="#2a2f36" />
          <stop offset="1" stop-color="#1a1d22" />
        </linearGradient>
        <pattern id="wp-hazard" width="22" height="22" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="11" height="22" fill="#f2c200" />
          <rect x="11" width="11" height="22" fill="#151515" />
        </pattern>
        <linearGradient id="wp-block" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#2b2f35" />
          <stop offset="1" stop-color="#121418" />
        </linearGradient>
        <clipPath v-for="(w, i) in layout" :id="`wp-top-${uid}-${i}`" :key="`ct${i}`">
          <rect :x="w.x - 40" y="0" width="80" :height="CUT_Y - GAP" />
        </clipPath>
        <clipPath v-for="(w, i) in layout" :id="`wp-bot-${uid}-${i}`" :key="`cb${i}`">
          <rect :x="w.x - 40" :y="CUT_Y + GAP" width="80" height="200" />
        </clipPath>
      </defs>

      <!-- Gehäuse -->
      <rect x="2" y="2" width="396" height="266" rx="6" fill="url(#wp-metal)" stroke="#0c0e11" stroke-width="3" />
      <circle v-for="p in RIVETS" :key="`${p[0]}-${p[1]}`" :cx="p[0]" :cy="p[1]" r="4" class="wp__rivet" />

      <!-- Warnstreifen + Titel -->
      <rect x="14" y="14" width="372" height="30" fill="url(#wp-hazard)" />
      <rect x="110" y="18" width="180" height="22" fill="#111" />
      <text x="200" y="34" class="wp__title" text-anchor="middle">{{ title }}</text>

      <!-- Status-LED -->
      <circle cx="360" cy="60" r="7" class="wp__led" />
      <text x="346" y="64" class="wp__ledtext" text-anchor="end">{{ ledText }}</text>

      <!-- Countdown (optional) -->
      <g v-if="seconds !== null" class="wp__timer" :class="{ 'is-low': seconds <= 30 }">
        <rect x="24" y="52" width="104" height="28" rx="2" />
        <text x="76" y="73" text-anchor="middle">{{ timerText }}</text>
      </g>

      <!-- Klemmleisten -->
      <rect x="24" y="86" width="352" height="20" fill="url(#wp-block)" stroke="#0a0b0d" />
      <rect x="24" y="226" width="352" height="20" fill="url(#wp-block)" stroke="#0a0b0d" />

      <!-- Kabel -->
      <g
        v-for="(w, i) in layout"
        :key="i"
        class="wp-wire"
        :class="{
          'is-selected': selected === i && cutIndex === null,
          'is-cut': cutIndex === i,
          'is-dim': state === 'defused' && cutIndex !== i,
        }"
        :style="{ '--wire': w.color, '--hi': w.highlight }"
        :role="interactive ? 'button' : undefined"
        :tabindex="interactive ? 0 : -1"
        :aria-label="`Kabel ${i + 1}: ${w.symbol}`"
        :aria-pressed="interactive ? selected === i : undefined"
        @click="select(i)"
        @keydown.enter.prevent="select(i)"
        @keydown.space.prevent="select(i)"
      >
        <!-- obere Hälfte -->
        <g class="wp-wire__half wp-wire__half--top" :style="{ transformOrigin: `${w.x}px 96px` }">
          <g :clip-path="cutIndex === i ? `url(#wp-top-${uid}-${i})` : undefined">
            <path :d="w.path" class="wp-wire__edge" /><path :d="w.path" class="wp-wire__core" />
            <path :d="w.path" class="wp-wire__shine" />
          </g>
          <circle v-if="cutIndex === i" :cx="w.cutX" :cy="CUT_Y - GAP" r="3.2" class="wp-wire__copper" />
        </g>
        <!-- untere Hälfte (nur sichtbar getrennt, wenn gekappt) -->
        <g v-if="cutIndex === i" class="wp-wire__half wp-wire__half--bot" :style="{ transformOrigin: `${w.x}px 236px` }">
          <g :clip-path="`url(#wp-bot-${uid}-${i})`">
            <path :d="w.path" class="wp-wire__edge" /><path :d="w.path" class="wp-wire__core" />
            <path :d="w.path" class="wp-wire__shine" />
          </g>
          <circle :cx="w.cutX" :cy="CUT_Y + GAP" r="3.2" class="wp-wire__copper" />
        </g>

        <!-- Schraubklemmen -->
        <circle :cx="w.x" cy="96" r="6" class="wp__screw" />
        <circle :cx="w.x" cy="236" r="6" class="wp__screw" />

        <!-- Anhänger mit Steckplatz + Symbol -->
        <g :transform="`translate(${w.x - 22} 172)`" class="wp-wire__tag">
          <rect width="44" height="40" rx="3" />
          <text x="6" y="12" class="wp-wire__slot">{{ i + 1 }}</text>
          <g transform="translate(12 10) scale(0.65)">
            <SymbolIcon :name="w.symbol" farbe="#14161a" :size="40" />
          </g>
        </g>

        <!-- Schnittmarke bei Auswahl -->
        <g v-if="selected === i && cutIndex === null" class="wp-wire__mark">
          <line :x1="w.cutX - 20" :y1="CUT_Y" :x2="w.cutX + 20" :y2="CUT_Y" />
        </g>

        <!-- Funken -->
        <g v-if="cutIndex === i && sparkKey" :key="sparkKey" class="wp-sparks">
          <circle
            v-for="(s, k) in SPARKS"
            :key="k"
            :cx="w.cutX"
            :cy="CUT_Y"
            r="1.8"
            :style="{ '--dx': `${s[0]}px`, '--dy': `${s[1]}px`, animationDelay: `${s[2]}s` }"
          />
        </g>

        <!-- großzügige, unsichtbare Klickfläche -->
        <path :d="w.path" class="wp-wire__hit" />
      </g>

      <!-- Blitz bei Fehler -->
      <rect class="wp__flash" x="0" y="0" width="400" height="270" />
    </svg>

    <button class="wp__cut" type="button" :disabled="!interactive || selected === null" @click="confirm">
      {{ buttonText }}
    </button>
  </div>
</template>

<script setup>
import { computed, ref, watch, useId } from 'vue'
import SymbolIcon from './tasks/graphic-symbols/SymbolIcon.vue'

const props = defineProps({
  wires: { type: Array, required: true },
  seconds: { type: Number, default: null },
  state: {
    type: String,
    default: 'armed',
    validator: (v) => ['armed', 'checking', 'defused', 'error'].includes(v),
  },
})
const emit = defineEmits(['cut'])

const uid = useId()
const CUT_Y = 146
const GAP = 9
const RIVETS = [[12, 12], [388, 12], [12, 258], [388, 258]]
// Weiß, Schwarz, Violett, Braun (+ Reserve) — keine Code-Farben aus Aufgabe 1.
const COLORS = [
  ['#e9e7e1', '#ffffff'],
  ['#3a3d43', '#9aa1ab'],
  ['#8e5cf0', '#c4a6ff'],
  ['#8b5a2b', '#c78d55'],
  ['#9aa3ad', '#d8dde2'],
  ['#3d6e70', '#7fb3b5'],
]
// [dx, dy, Verzögerung] der Funken
const SPARKS = [
  [-26, -18, 0], [24, -22, 0.02], [-30, 8, 0.05], [30, 10, 0.03],
  [-12, -32, 0.08], [14, 28, 0.06], [-20, 26, 0.1], [22, -6, 0.12],
]

const selected = ref(null)
const cutIndex = ref(null)
const sparkKey = ref(0)

const layout = computed(() => {
  const n = props.wires.length
  return props.wires.map((symbol, i) => {
    const x = 24 + (352 * (i + 0.5)) / n
    const sway = i % 2 === 0 ? 22 : -22
    const [color, highlight] = COLORS[i % COLORS.length]
    return {
      symbol,
      x,
      color,
      highlight,
      // S-Kurve von Klemme zu Klemme
      path: `M ${x} 96 C ${x + sway} 125, ${x - sway} 170, ${x} 236`,
      // x-Position der Kurve auf Schnitthöhe (Bezier bei t≈0.35)
      cutX: x + sway * 0.3,
    }
  })
})

const interactive = computed(() => props.state === 'armed' || props.state === 'error')

watch(
  () => props.state,
  (s) => {
    // Zurück auf "armed" (nach Fehler oder für eine neue Runde) flickt das Panel wieder zusammen.
    if (s === 'armed') {
      cutIndex.value = null
      selected.value = null
    }
  },
)

const title = computed(() => (props.state === 'defused' ? 'SYSTEM SICHER' : 'NOTABSCHALTUNG'))
const ledText = computed(
  () => ({ armed: 'SCHARF', checking: 'PRÜFE', defused: 'SICHER', error: 'FEHLER' })[props.state],
)
const buttonText = computed(() => {
  if (props.state === 'defused') return 'ENTSCHÄRFT'
  if (props.state === 'checking') return 'PRÜFE …'
  return selected.value === null ? 'KABEL WÄHLEN' : `KABEL ${selected.value + 1} KAPPEN`
})
const timerText = computed(() => {
  const t = Math.max(0, Math.floor(props.seconds ?? 0))
  return `${String(Math.floor(t / 60)).padStart(2, '0')}:${String(t % 60).padStart(2, '0')}`
})
const ariaLabel = computed(() => `Notabschaltung, Zustand ${ledText.value}`)

function select(i) {
  if (!interactive.value) return
  if (cutIndex.value !== null) cutIndex.value = null
  selected.value = selected.value === i ? null : i
}

function confirm() {
  if (!interactive.value || selected.value === null) return
  const i = selected.value
  cutIndex.value = i
  sparkKey.value += 1
  emit('cut', { index: i, symbol: props.wires[i] })
}
</script>

<style scoped>
.wp {
  width: 100%;
  max-width: 640px;
  margin-inline: auto;
  display: grid;
  gap: 14px;
  font-family: 'Share Tech Mono', ui-monospace, monospace;
}
.wp__svg { width: 100%; height: auto; display: block; overflow: visible; filter: drop-shadow(0 10px 18px rgba(0, 0, 0, .6)); }

.wp__rivet { fill: #6b737d; stroke: #15181c; stroke-width: 1.5; }
.wp__screw { fill: #9aa2ac; stroke: #2a2e34; stroke-width: 2; }
.wp__title { fill: #f2c200; font-size: 14px; letter-spacing: 3px; font-family: inherit; }
.wp--defused .wp__title { fill: var(--green, #00ff66); }
.wp__ledtext { fill: #8c96a0; font-size: 10px; letter-spacing: 2px; font-family: inherit; }

/* Status-LED */
.wp__led { fill: var(--red, #ff3a4d); filter: drop-shadow(0 0 4px var(--red, #ff3a4d)); animation: blink 1s steps(2, start) infinite; }
.wp--checking .wp__led { fill: var(--amber, #ffb830); filter: drop-shadow(0 0 4px var(--amber, #ffb830)); animation-duration: .3s; }
.wp--defused .wp__led { fill: var(--green, #00ff66); filter: drop-shadow(0 0 6px var(--green, #00ff66)); animation: none; }
.wp--error .wp__led { animation-duration: .15s; }

/* Kabel */
.wp-wire { cursor: pointer; outline: none; }
.wp--checking .wp-wire, .wp--defused .wp-wire { cursor: default; }
.wp-wire__core { fill: none; stroke: var(--wire); stroke-width: 10; stroke-linecap: round; }
.wp-wire__edge { fill: none; stroke: #0b0c0e; stroke-width: 13; stroke-linecap: round; opacity: .8; }
.wp-wire__shine { fill: none; stroke: var(--hi); stroke-width: 2.5; stroke-linecap: round; opacity: .55; transform: translateX(-2px); }
.wp-wire__hit { fill: none; stroke: transparent; stroke-width: 34; pointer-events: stroke; }
.wp-wire:hover .wp-wire__core,
.wp-wire:focus-visible .wp-wire__core { filter: drop-shadow(0 0 5px var(--amber, #ffb830)); }
.wp-wire.is-selected .wp-wire__core { filter: drop-shadow(0 0 7px var(--amber, #ffb830)) drop-shadow(0 0 2px var(--amber, #ffb830)); }
.wp-wire.is-dim { opacity: .35; transition: opacity .6s .3s; }
.wp-wire__copper { fill: #d9893b; stroke: #6d3a10; stroke-width: 1; }

.wp-wire__tag rect { fill: #e9e2c8; stroke: #8a8270; stroke-width: 1.5; }
.wp-wire__slot { fill: #3a3a3a; font-size: 10px; font-family: inherit; }
.wp-wire.is-selected .wp-wire__tag rect { fill: #ffe79a; }

.wp__timer rect { fill: #140405; stroke: #050101; stroke-width: 2; }
.wp__timer text { fill: #ff3a3a; font-size: 22px; letter-spacing: 3px; font-family: inherit; filter: drop-shadow(0 0 4px rgba(255, 40, 40, .8)); }
.wp__timer.is-low text { animation: blink .5s steps(2, start) infinite; }
.wp--defused .wp__timer text { fill: var(--green, #00ff66); filter: drop-shadow(0 0 4px rgba(0, 255, 102, .7)); animation: none; }
.wp-wire__mark line { stroke: var(--amber, #ffb830); stroke-width: 2; stroke-dasharray: 4 3; animation: dash .6s linear infinite; }

/* Gekappt: die Enden federn auseinander */
.wp-wire__half { transform-box: view-box; transition: transform .45s cubic-bezier(.2, 1.6, .4, 1); }
.wp-wire.is-cut .wp-wire__half--top { transform: rotate(-11deg); }
.wp-wire.is-cut .wp-wire__half--bot { transform: rotate(9deg); }
.wp--error .wp-wire.is-cut .wp-wire__core { stroke: #3a2a22; }

/* Funken */
.wp-sparks circle {
  fill: #ffd27a;
  filter: drop-shadow(0 0 3px #ffb830);
  transform-box: fill-box;
  opacity: 0;
  animation: spark .55s ease-out forwards;
}
.wp--checking .wp-sparks circle { animation-iteration-count: 3; }

/* Fehler: Blitz + Rütteln */
.wp__flash { fill: var(--red, #ff3a4d); opacity: 0; pointer-events: none; }
.wp--error .wp__flash { animation: flash .5s ease-out; }
.wp--error .wp__svg { animation: shake .45s; }
.wp--defused .wp__svg { filter: drop-shadow(0 0 22px rgba(0, 255, 102, .25)) drop-shadow(0 10px 18px rgba(0, 0, 0, .6)); }

/* Knopf */
.wp__cut {
  justify-self: center;
  min-width: 60%;
  padding: 14px 22px;
  font: inherit;
  font-size: 17px;
  letter-spacing: 3px;
  color: #fff;
  background: linear-gradient(180deg, #c3202f, #7d0f19);
  border: 2px solid #3d070c;
  border-radius: 4px;
  box-shadow: 0 4px 0 #3d070c, 0 0 18px rgba(255, 58, 77, .25);
  cursor: pointer;
}
.wp__cut:active:not(:disabled) { transform: translateY(3px); box-shadow: 0 1px 0 #3d070c; }
.wp__cut:disabled { cursor: default; background: #2a2f36; color: #6b737d; border-color: #15181c; box-shadow: 0 4px 0 #15181c; }
.wp--defused .wp__cut { color: var(--green, #00ff66); }

@keyframes blink { to { opacity: .25; } }
@keyframes dash { to { stroke-dashoffset: -14; } }
@keyframes spark {
  0% { opacity: 1; transform: translate(0, 0) scale(1.4); }
  100% { opacity: 0; transform: translate(var(--dx), var(--dy)) scale(.3); }
}
@keyframes flash { 0% { opacity: .45; } 100% { opacity: 0; } }
@keyframes shake {
  10%, 90% { transform: translateX(-2px); }
  20%, 80% { transform: translateX(4px); }
  30%, 50%, 70% { transform: translateX(-7px); }
  40%, 60% { transform: translateX(7px); }
}

@media (prefers-reduced-motion: reduce) {
  .wp__led, .wp__timer text, .wp-wire__mark line, .wp-sparks circle, .wp--error .wp__svg, .wp--error .wp__flash { animation: none !important; }
  .wp-wire__half { transition: none; }
}
</style>
