<!--
  SyncButton — Pilz-Notknopf unter einer Klappe (Aufgabe 3, Vorder- und Rückseite; GAME_DESIGN.md).

  Erst Klappe öffnen, dann drücken. Ein Ring um den Knopf läuft das Zeitfenster ab,
  in dem der Partner ebenfalls drücken muss (3 s laut GAME_DESIGN.md).
  Das Panel prüft nichts selbst — es meldet nur den Druck.

  Props
    unlocked  = view.button_unlocked; solange false, ist die Klappe verplombt
    state     "idle" | "waiting" | "synced" | "error" (vom Elternteil gesteuert)
                waiting -> Ring läuft ab, "WARTE AUF PARTNER"
                synced  -> grün, "DATEN GERETTET", keine Eingabe mehr
                error   -> Ring rot, rüttelt; zurück auf "idle", Klappe bleibt offen
    windowMs  Zeitfenster in Millisekunden (Default 3000)

  Event
    press()  -> player_input { target: "sync_button", value: "press" }

  Alles SVG + CSS, keine Bilder, skaliert mit der Containerbreite.
-->
<template>
  <div
    class="sb"
    :class="[`sb--${state}`, { 'is-cover-open': coverOpen, 'is-locked': !unlocked }]"
    role="group"
    :aria-label="ariaLabel"
  >
    <div class="sb__panel">
      <!-- Gehäuse: Platte, Schrauben, Warnschild -->
      <svg class="sb__base" viewBox="0 0 400 400" aria-hidden="true">
        <defs>
          <linearGradient id="sb-plate" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#3c434b" />
            <stop offset=".45" stop-color="#252a31" />
            <stop offset="1" stop-color="#14181d" />
          </linearGradient>
          <linearGradient id="sb-plate-edge" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="#59636f" />
            <stop offset="1" stop-color="#0a0c0f" />
          </linearGradient>
          <pattern id="sb-hazard" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="10" height="20" fill="#f2c200" />
            <rect x="10" width="10" height="20" fill="#171717" />
          </pattern>
          <radialGradient id="sb-socket" cx=".5" cy=".45" r=".55">
            <stop offset="0" stop-color="#0b0d10" />
            <stop offset=".8" stop-color="#05070a" />
            <stop offset="1" stop-color="#1b2027" />
          </radialGradient>
        </defs>

        <!-- Grundplatte -->
        <rect x="8" y="8" width="384" height="384" rx="14" fill="url(#sb-plate)" stroke="url(#sb-plate-edge)" stroke-width="4" />
        <rect x="22" y="22" width="356" height="356" rx="8" fill="none" stroke="#0b0d10" stroke-width="2" opacity=".7" />

        <!-- Schrauben -->
        <circle v-for="p in RIVETS" :key="`${p[0]}-${p[1]}`" :cx="p[0]" :cy="p[1]" r="5" class="sb__rivet" />

        <!-- Warnschild oben -->
        <rect x="60" y="38" width="280" height="34" rx="3" fill="url(#sb-hazard)" />
        <rect x="120" y="43" width="160" height="24" rx="2" fill="#101216" />
        <text x="200" y="61" class="sb__plaque" text-anchor="middle">NOT-STOPP</text>

        <!-- Typenschild unten -->
        <rect x="96" y="352" width="208" height="28" rx="3" fill="#0f1216" stroke="#000" stroke-width="1.5" />
        <text x="200" y="371" class="sb__plate-text" text-anchor="middle">DATENRETTUNG · SYNC</text>

        <!-- Fassung unter dem Pilz -->
        <g class="sb__socket">
          <circle cx="200" cy="240" r="86" fill="url(#sb-socket)" stroke="#0a0c0f" stroke-width="3" />
          <circle cx="200" cy="240" r="72" fill="none" stroke="#2b3138" stroke-width="1.5" stroke-dasharray="3 5" />
        </g>
      </svg>

      <!-- Zeitfenster-Ring -->
      <div class="sb__ring" :style="{ '--window': `${windowMs}ms` }" aria-hidden="true">
        <svg viewBox="0 0 200 200">
          <circle class="sb__ring-track" cx="100" cy="100" r="90" pathLength="100" />
          <circle class="sb__ring-run" cx="100" cy="100" r="90" pathLength="100" />
        </svg>
      </div>

      <!-- Der Pilz selbst -->
      <button
        class="sb__knopf"
        type="button"
        aria-label="Notknopf"
        :aria-disabled="!canPress"
        @click="press"
      >
        <span class="sb__knopf-collar" aria-hidden="true"></span>
        <span class="sb__knopf-dome" aria-hidden="true"></span>
      </button>

      <!-- Klappe mit Plombe -->
      <button
        class="sb__cover"
        type="button"
        aria-label="Klappe"
        :aria-expanded="coverOpen"
        @click="toggleCover"
      >
        <span class="sb__cover-face" aria-hidden="true">
          <span class="sb__cover-stripe"></span>
          <span class="sb__cover-label">{{ coverOpen ? 'GEÖFFNET' : 'KLAPPE ÖFFNEN' }}</span>
          <span class="sb__cover-note">NOTFALL · DATENRETTUNG</span>
          <span class="sb__cover-seal">{{ coverOpen ? 'OFFEN' : 'PLOMBE' }}</span>
        </span>
      </button>
    </div>

    <p class="sb__status" :class="`is-${statusKey}`" role="status" aria-live="polite">{{ statusText }}</p>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  unlocked: { type: Boolean, default: false },
  state: {
    type: String,
    default: 'idle',
    validator: (v) => ['idle', 'waiting', 'synced', 'error'].includes(v),
  },
  windowMs: { type: Number, default: 3000 },
})
const emit = defineEmits(['press'])

const RIVETS = [
  [26, 26], [374, 26], [26, 374], [374, 374],
  [26, 200], [374, 200],
]

// Die Klappe ist die einzige „Eingabe" des Panels; ihr Zustand gehört ihm selbst.
const coverOpen = ref(false)

// Gesperrt: verplombt, Klappe zu, oder das Fenster läuft / ist vorbei.
const canPress = computed(
  () => props.unlocked && coverOpen.value && (props.state === 'idle' || props.state === 'error'),
)

const statusText = computed(() => {
  if (!props.unlocked) return 'VERPLOMBT'
  return {
    idle: 'BEREIT',
    waiting: 'WARTE AUF PARTNER',
    synced: 'DATEN GERETTET',
    error: 'NICHT SYNCHRON',
  }[props.state]
})
const statusKey = computed(() => (props.unlocked ? props.state : 'locked'))
const ariaLabel = computed(() => `Sync-Knopf, Zustand ${statusText.value}`)

// Plombe wieder drauf, wenn die Aufgabe neu beginnt.
watch(
  () => props.unlocked,
  (frei) => {
    if (!frei) coverOpen.value = false
  },
)

function toggleCover() {
  if (!props.unlocked) return
  coverOpen.value = !coverOpen.value
}

function press() {
  if (!canPress.value) return
  emit('press')
}
</script>

<style scoped>
.sb {
  width: 100%;
  max-width: 640px;
  margin-inline: auto;
  display: grid;
  gap: 14px;
  font-family: 'Share Tech Mono', ui-monospace, monospace;
}

.sb__panel {
  /* quadratisch, aber so gedeckelt, dass Panel + Status auf einen Bildschirm passen */
  width: min(100%, 520px);
  margin-inline: auto;
  position: relative;
  aspect-ratio: 1 / 1;
  perspective: 1000px;
}

.sb__base {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  filter: drop-shadow(0 14px 22px rgba(0, 0, 0, .65));
}

.sb__rivet { fill: #7c858f; stroke: #10131a; stroke-width: 2; }
.sb__plaque { fill: #f2c200; font-size: 15px; letter-spacing: 4px; font-family: inherit; }
.sb__plate-text { fill: #6e7a85; font-size: 10px; letter-spacing: 2px; font-family: inherit; }

/* ---------------------------------------------------------------- Zeitfenster */
.sb__ring {
  position: absolute;
  left: 50%;
  top: 60%;
  width: 62%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 3;
}
.sb__ring svg { display: block; width: 100%; height: auto; transform: rotate(-90deg); }
.sb__ring-track { fill: none; stroke: #191d23; stroke-width: 9; }
.sb__ring-run {
  fill: none;
  stroke: var(--amber, #ffb830);
  stroke-width: 7;
  stroke-linecap: round;
  stroke-dasharray: 100;
  stroke-dashoffset: 0;
  opacity: 0;
  transition: opacity .2s;
}

/* Ablauf: der Ring leert sich über genau das Zeitfenster */
.sb--waiting .sb__ring-run {
  opacity: 1;
  filter: drop-shadow(0 0 5px var(--amber, #ffb830));
  animation: sb-drain var(--window, 3000ms) linear forwards;
}
.sb--synced .sb__ring-run {
  opacity: 1;
  stroke: var(--green, #00ff66);
  filter: drop-shadow(0 0 7px var(--green, #00ff66));
}
.sb--error .sb__ring-run {
  opacity: 1;
  stroke: var(--red, #ff3a4d);
  filter: drop-shadow(0 0 7px var(--red, #ff3a4d));
}

/* ---------------------------------------------------------------- Pilz */
.sb__knopf {
  position: absolute;
  left: 50%;
  top: 60%;
  width: 34%;
  aspect-ratio: 1 / 1;
  transform: translate(-50%, -50%);
  z-index: 4;
  padding: 0;
  border: 0;
  background: none;
  cursor: pointer;
  outline: none;
}
.sb__knopf-collar,
.sb__knopf-dome {
  position: absolute;
  border-radius: 50%;
}
.sb__knopf-collar {
  inset: -9%;
  background: radial-gradient(circle at 50% 30%, #4a525c, #1b2027 62%, #0a0c10);
  box-shadow: inset 0 -4px 10px rgba(0, 0, 0, .7), 0 0 0 2px #07090c;
}
.sb__knopf-dome {
  inset: 0;
  background: radial-gradient(circle at 34% 26%, #ff9c8c 0%, #e02330 34%, #9c1119 66%, #4a050a 100%);
  box-shadow:
    inset 0 -8px 14px rgba(0, 0, 0, .55),
    inset 0 6px 10px rgba(255, 255, 255, .28),
    0 10px 18px rgba(0, 0, 0, .65);
  transition: transform .12s ease, box-shadow .12s ease, filter .2s;
}
.sb__knopf-dome::after {
  content: '';
  position: absolute;
  left: 24%;
  top: 16%;
  width: 34%;
  height: 22%;
  border-radius: 50%;
  background: linear-gradient(160deg, rgba(255, 255, 255, .55), rgba(255, 255, 255, 0));
  transform: rotate(-18deg);
}
.sb__knopf:active .sb__knopf-dome,
.sb__knopf:focus-visible .sb__knopf-dome {
  transform: translateY(4px) scale(.97);
  box-shadow: inset 0 -4px 10px rgba(0, 0, 0, .6), 0 4px 10px rgba(0, 0, 0, .6);
}
.sb__knopf:focus-visible .sb__knopf-collar { box-shadow: 0 0 0 3px var(--amber, #ffb830), 0 0 0 2px #07090c; }

/* Gepresst: der Pilz bleibt unten, solange gewartet wird */
.sb--waiting .sb__knopf-dome,
.sb--synced .sb__knopf-dome { transform: translateY(4px) scale(.97); }
.sb--synced .sb__knopf-dome {
  background: radial-gradient(circle at 34% 26%, #b6ffd2 0%, #22c55e 36%, #12803c 70%, #06301a 100%);
  filter: drop-shadow(0 0 14px rgba(0, 255, 102, .5));
}
.sb--error .sb__knopf-dome { animation: sb-shake .42s; }

/* ---------------------------------------------------------------- Klappe */
.sb__cover {
  position: absolute;
  left: 7%;
  right: 7%;
  top: 41%;
  height: 45%;
  z-index: 6;
  padding: 0;
  border: 0;
  background: none;
  cursor: pointer;
  outline: none;
  transform-origin: top center;
  transform-style: preserve-3d;
  transition: transform .48s cubic-bezier(.2, .9, .3, 1);
}
.sb__cover-face {
  position: absolute;
  inset: 0;
  border-radius: 8px;
  border: 2px solid #0a0c0f;
  background:
    repeating-linear-gradient(180deg, rgba(255, 255, 255, .03) 0 2px, transparent 2px 6px),
    linear-gradient(165deg, #414952 0%, #232930 55%, #14181d 100%);
  box-shadow:
    inset 0 2px 0 rgba(255, 255, 255, .09),
    inset 0 -10px 18px rgba(0, 0, 0, .5),
    0 10px 18px rgba(0, 0, 0, .6);
}
.sb__socket { opacity: 0; transition: opacity .3s .15s; }
.is-cover-open .sb__socket { opacity: 1; }

.sb__cover-stripe {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 9px;
  border-radius: 6px 6px 0 0;
  background: repeating-linear-gradient(45deg, #f2c200 0 9px, #171717 9px 18px);
  opacity: .75;
}
.sb__cover-label {
  position: absolute;
  left: 0;
  right: 0;
  top: 30%;
  text-align: center;
  color: #aab6c1;
  font-size: 12px;
  letter-spacing: 3px;
}
.sb__cover-note {
  position: absolute;
  left: 0;
  right: 0;
  top: 41%;
  text-align: center;
  color: #5d6873;
  font-size: 9px;
  letter-spacing: 2px;
}
/* Griff-Kerbe am unteren Rand: zeigt, wo man zieht */
.sb__cover-face::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 6%;
  width: 22%;
  height: 7px;
  transform: translateX(-50%);
  border-radius: 4px;
  background: linear-gradient(180deg, #0c0f13, #5a6572);
  box-shadow: 0 1px 0 rgba(255, 255, 255, .12);
}
.sb__cover-seal {
  position: absolute;
  right: 6%;
  bottom: 8%;
  width: 17%;
  max-width: 62px;
  aspect-ratio: 1 / 1;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 9px;
  letter-spacing: 1px;
  color: #ffe9a8;
  background: radial-gradient(circle at 40% 32%, #f2c200, #b3810b 62%, #6b4c04);
  border: 2px solid #4d3602;
  box-shadow: 0 4px 10px rgba(0, 0, 0, .55), inset 0 1px 0 rgba(255, 255, 255, .35);
  transform: rotate(-6deg);
}
.is-locked .sb__cover-seal {
  color: #ffd9dc;
  background: radial-gradient(circle at 40% 32%, #ff5d6a, #b3121f 62%, #5c060d);
  border-color: #460509;
}
.sb__cover:focus-visible .sb__cover-face { box-shadow: 0 0 0 3px var(--amber, #ffb830); }

/* Offen: die Klappe klappt nach oben weg, der Pilz wird frei */
.is-cover-open .sb__cover { transform: rotateX(-106deg); }
.is-cover-open .sb__cover-seal,
.is-cover-open .sb__cover-stripe { opacity: 0; }

.sb__panel::before {
  /* Scharnierlinie */
  content: '';
  position: absolute;
  left: 7%;
  right: 7%;
  top: 41%;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(180deg, #6a7481, #1a1e24);
  z-index: 7;
  pointer-events: none;
}

/* ---------------------------------------------------------------- Status */
.sb__status {
  margin: 0;
  text-align: center;
  letter-spacing: 4px;
  font-size: 15px;
  color: var(--amber, #ffb830);
  transition: color .25s;
}
.sb__status.is-idle { color: #7d8a95; }
.sb__status.is-waiting { color: var(--amber, #ffb830); animation: sb-pulse .9s ease-in-out infinite; }
.sb__status.is-synced { color: var(--green, #00ff66); text-shadow: 0 0 10px rgba(0, 255, 102, .5); }
.sb__status.is-error { color: var(--red, #ff3a4d); }
.sb__status.is-locked { color: #8d3a44; }

.sb--waiting .sb__panel { animation: none; }
.sb--error .sb__panel { animation: sb-shake .42s; }

@keyframes sb-drain { to { stroke-dashoffset: 100; } }
@keyframes sb-pulse { 50% { opacity: .45; } }
@keyframes sb-shake {
  10%, 90% { transform: translateX(-2px); }
  20%, 80% { transform: translateX(4px); }
  30%, 50%, 70% { transform: translateX(-7px); }
  40%, 60% { transform: translateX(7px); }
}

@media (prefers-reduced-motion: reduce) {
  .sb__ring-run,
  .sb__status,
  .sb__cover,
  .sb__knopf-dome,
  .sb--error .sb__panel,
  .sb--error .sb__knopf-dome { animation: none !important; transition: none !important; }
  .sb--waiting .sb__ring-run { opacity: 1; }
}
</style>
