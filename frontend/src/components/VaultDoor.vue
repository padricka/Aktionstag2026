<!--
  VaultDoor — interaktiver Tresor für das Finale (Neustart-Code, GAME_DESIGN.md).

  Modi
    mode="display"  Beamer: zeigt die bisher gefundenen Ziffern (digits, null = noch unbekannt).
    mode="input"    Leitstand: Zahlenräder drehen (Klick oben/unten, Mausrad, Pfeiltasten),
                    "Öffnen" sendet das Event `unlock` mit dem Code als String ("472").

  Zustand (vom Elternteil gesteuert, die Komponente prüft den Code NICHT selbst)
    state="locked" | "checking" | "open" | "error"
      checking -> Drehknopf wirbelt
      open     -> Riegel fahren zurück, Tür schwingt auf, dahinter fährt der Server hoch
      error    -> Tür rüttelt, Anzeige leuchtet rot

  Alles ist SVG + CSS (keine Bilder), skaliert mit der Breite des Containers.
-->
<template>
  <div
    class="vault"
    :class="[`vault--${state}`, `vault--${mode}`]"
    role="group"
    :aria-label="ariaLabel"
  >
    <div class="vault__frame">
      <!-- Inneres hinter der Tür: der Server fährt hoch -->
      <div class="vault__inside" aria-hidden="true">
        <div class="vd-rack">
          <div v-for="n in 6" :key="n" class="vd-rack__unit" :style="{ '--d': n }">
            <span class="vd-rack__led" /><span class="vd-rack__led" /><span class="vd-rack__led" />
            <span class="vd-rack__bar" />
          </div>
        </div>
        <div class="vd-inside__text">
          <span class="vd-inside__granted">ACCESS GRANTED</span>
          <span class="vd-inside__sub">SERVER REBOOT · ONLINE</span>
        </div>
      </div>

      <!-- Riegel: stecken im Rahmen, solange verriegelt -->
      <div class="vault__bolts" aria-hidden="true">
        <span v-for="n in 3" :key="n" class="vd-bolt" />
      </div>

      <!-- Die Tür -->
      <div class="vd-door">
        <div class="vd-door__face">
          <span v-for="c in ['tl', 'tr', 'bl', 'br']" :key="c" class="vd-rivet" :class="`vd-rivet--${c}`" />

          <!-- Linkes Bedienfeld -->
          <div class="vd-panel">
            <div class="vd-panel__label">NEUSTART-CODE</div>

            <div class="vd-panel__window" :class="{ 'is-error': state === 'error' }">
              <div
                v-for="(d, i) in shown"
                :key="i"
                class="vd-drum"
                :class="{ 'vd-drum--unknown': d === null, 'vd-drum--live': mode === 'input' }"
                :tabindex="interactive ? 0 : -1"
                role="spinbutton"
                :aria-label="`Ziffer ${i + 1}`"
                :aria-valuenow="d ?? undefined"
                aria-valuemin="0"
                aria-valuemax="9"
                @keydown.up.prevent="step(i, 1)"
                @keydown.down.prevent="step(i, -1)"
                @wheel.prevent="onWheel(i, $event)"
              >
                <button
                  v-if="interactive"
                  class="vd-drum__btn vd-drum__btn--up"
                  type="button"
                  tabindex="-1"
                  :aria-label="`Ziffer ${i + 1} erhöhen`"
                  @click="step(i, 1)"
                >▲</button>
                <div class="vd-drum__track" :style="{ transform: `translateY(calc(${-(d ?? 10)} * var(--drum-h)))` }">
                  <span v-for="n in 10" :key="n" class="vd-drum__digit">{{ n - 1 }}</span>
                  <span class="vd-drum__digit vd-drum__digit--q">?</span>
                </div>
                <button
                  v-if="interactive"
                  class="vd-drum__btn vd-drum__btn--down"
                  type="button"
                  tabindex="-1"
                  :aria-label="`Ziffer ${i + 1} verringern`"
                  @click="step(i, -1)"
                >▼</button>
              </div>
            </div>

            <button
              v-if="mode === 'input'"
              class="vd-panel__unlock"
              type="button"
              :disabled="!interactive"
              @click="unlock"
            >ÖFFNEN</button>
            <div v-else class="vd-panel__status">{{ statusText }}</div>
          </div>

          <!-- Drehknopf (Zahnrad) -->
          <div class="vd-dial" :style="{ '--rot': `${dialRot}deg` }" aria-hidden="true">
            <svg viewBox="0 0 100 100" class="vd-dial__svg">
              <defs>
                <radialGradient id="vd-metal" cx="40%" cy="35%" r="70%">
                  <stop offset="0%" stop-color="#7c8592" />
                  <stop offset="55%" stop-color="#3e4550" />
                  <stop offset="100%" stop-color="#1c2026" />
                </radialGradient>
                <radialGradient id="vd-hub" cx="40%" cy="35%" r="70%">
                  <stop offset="0%" stop-color="#9aa3ae" />
                  <stop offset="100%" stop-color="#2b3038" />
                </radialGradient>
              </defs>
              <g class="vd-dial__rotor">
                <g transform="translate(50 50)">
                  <rect
                    v-for="t in TEETH"
                    :key="t"
                    x="-2.6"
                    y="-47"
                    width="5.2"
                    height="7"
                    rx="1"
                    fill="#4a525d"
                    :transform="`rotate(${(t - 1) * (360 / TEETH)})`"
                  />
                </g>
                <circle cx="50" cy="50" r="41" fill="url(#vd-metal)" stroke="#15181d" stroke-width="1.2" />
                <g transform="translate(50 50)">
                  <line
                    v-for="t in 36"
                    :key="`tick${t}`"
                    x1="0" :y1="t % 3 === 1 ? -38 : -36.5" x2="0" y2="-34"
                    stroke="#c6ccd4" stroke-opacity=".55" stroke-width=".8"
                    :transform="`rotate(${(t - 1) * 10})`"
                  />
                  <g v-for="s in 3" :key="`spoke${s}`" :transform="`rotate(${(s - 1) * 120})`">
                    <rect x="-2.4" y="-31" width="4.8" height="26" rx="2.4" fill="#2a2f37" />
                    <rect x="-1.6" y="-30" width="3.2" height="24" rx="1.6" fill="#8b939e" />
                    <circle cx="0" cy="-31" r="4" fill="url(#vd-hub)" stroke="#15181d" stroke-width=".8" />
                  </g>
                </g>
                <circle cx="50" cy="50" r="9" fill="url(#vd-hub)" stroke="#15181d" stroke-width="1" />
                <circle cx="50" cy="50" r="3" fill="#15181d" />
              </g>
              <!-- feste Markierung oben -->
              <path d="M50 2 l3 5 h-6 z" fill="var(--vault-accent)" />
            </svg>
          </div>

          <!-- Scharniere rechts -->
          <span class="vd-hinge vd-hinge--top" aria-hidden="true" />
          <span class="vd-hinge vd-hinge--bottom" aria-hidden="true" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  mode: { type: String, default: 'display', validator: (v) => ['display', 'input'].includes(v) },
  state: {
    type: String,
    default: 'locked',
    validator: (v) => ['locked', 'checking', 'open', 'error'].includes(v),
  },
  // display: gefundene Ziffern (null = unbekannt). input: Startwerte der Räder.
  digits: { type: Array, default: () => [null, null, null] },
})

const emit = defineEmits(['unlock'])

const TEETH = 28
const local = ref(props.digits.map((d) => d ?? 0))
const dialRot = ref(0)

watch(
  () => props.digits,
  (neu, alt) => {
    if (props.mode === 'input') {
      local.value = neu.map((d) => d ?? 0)
    } else {
      // Beamer: für jede neu gefundene Ziffer dreht der Knopf ein Stück mit.
      const neuGefunden = neu.filter((d, i) => d !== null && (alt?.[i] ?? null) === null).length
      dialRot.value += neuGefunden * 120
    }
  },
  { deep: true },
)

watch(
  () => props.state,
  (s) => {
    if (s === 'checking' || s === 'open') dialRot.value += 720
  },
)

const shown = computed(() => (props.mode === 'input' ? local.value : props.digits))
const interactive = computed(
  () => props.mode === 'input' && (props.state === 'locked' || props.state === 'error'),
)

const statusText = computed(
  () =>
    ({
      locked: `GESPERRT · ${props.digits.filter((d) => d !== null).length}/3`,
      checking: 'PRÜFE …',
      open: 'OFFEN',
      error: 'FALSCHER CODE',
    })[props.state],
)

const ariaLabel = computed(() =>
  props.state === 'open' ? 'Tresor geöffnet' : `Tresor, Zustand ${statusText.value}`,
)

function step(i, delta) {
  if (!interactive.value) return
  const next = [...local.value]
  next[i] = (next[i] + delta + 10) % 10
  local.value = next
  dialRot.value += delta * 36
}

function onWheel(i, e) {
  step(i, e.deltaY < 0 ? 1 : -1)
}

function unlock() {
  if (!interactive.value) return
  emit('unlock', local.value.join(''))
}
</script>

<style scoped>
/* Alle Maße in cqw (Prozent der Containerbreite): der Tresor skaliert stufenlos. */
.vault {
  --vault-accent: var(--amber, #ffb830);
  --metal-1: #4b525c;
  --metal-2: #2c3138;
  --metal-3: #1b1f24;
  container-type: inline-size;
  width: 100%;
  max-width: 640px;
  margin-inline: auto;
  font-family: 'Share Tech Mono', ui-monospace, monospace;
}
.vault--open { --vault-accent: var(--green, #00ff66); }
.vault--error { --vault-accent: var(--red, #ff3a4d); }

.vault__frame {
  position: relative;
  aspect-ratio: 16 / 10.5;
  perspective: 160cqw;
  background:
    radial-gradient(ellipse at 50% 120%, rgba(0, 0, 0, .55), transparent 70%),
    linear-gradient(145deg, #15191d, #0b0d10);
  border: .5cqw solid #262b31;
  box-shadow: inset 0 0 6cqw rgba(0, 0, 0, .9), 0 3cqw 6cqw rgba(0, 0, 0, .6);
  overflow: visible;
}

/* ---------- Inneres (hinter der Tür) ---------- */
.vault__inside {
  position: absolute;
  inset: 3cqw;
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  align-items: center;
  gap: 3cqw;
  padding: 3cqw;
  background: radial-gradient(circle at 30% 50%, rgba(0, 255, 102, .14), transparent 65%), #050806;
  box-shadow: inset 0 0 4cqw #000;
}
.vd-rack { display: grid; gap: 1.2cqw; }
.vd-rack__unit {
  display: flex; align-items: center; gap: 1cqw;
  height: 4cqw; padding: 0 1.5cqw;
  background: linear-gradient(180deg, #1d2420, #111613);
  border: .2cqw solid #26302a;
}
.vd-rack__led { width: 1cqw; height: 1cqw; border-radius: 50%; background: #233229; }
.vd-rack__bar { flex: 1; height: .6cqw; background: #18201b; }
.vd-inside__text { display: grid; gap: 1cqw; color: var(--green, #00ff66); text-shadow: 0 0 2cqw rgba(0, 255, 102, .6); }
.vd-inside__granted { font-size: 5cqw; letter-spacing: .3cqw; }
.vd-inside__sub { font-size: 2.4cqw; color: var(--fg-2, #a3b5a9); text-shadow: none; }

.vault--open .vd-rack__led { animation: led-on .25s calc(1.6s + var(--d) * .12s) forwards; }
.vault--open .vd-rack__led:nth-child(2) { animation-delay: calc(1.7s + var(--d) * .12s); }
.vault--open .vd-rack__bar {
  background: linear-gradient(90deg, var(--green, #00ff66) 0 0, #18201b 0);
  animation: bar-fill .8s calc(1.8s + var(--d) * .12s) forwards;
}
.vd-inside__text { opacity: 0; }
.vault--open .vd-inside__text { animation: fade-in .6s 2.2s forwards; }

/* ---------- Riegel ---------- */
.vault__bolts {
  position: absolute; left: 1cqw; top: 15%; bottom: 15%;
  display: flex; flex-direction: column; justify-content: space-between;
  z-index: 3; pointer-events: none;
}
.vd-bolt {
  width: 6cqw; height: 2.6cqw;
  background: linear-gradient(180deg, #a7b0bb, #59616c 55%, #3b4149);
  border: .2cqw solid #1b1f24;
  transition: transform .45s cubic-bezier(.5, 0, .7, 1) .7s, opacity .3s ease 1.4s;
}
/* Riegel fahren in die Tür und verschwinden mit ihr beim Aufschwingen */
.vault--open .vd-bolt { transform: translateX(6cqw); opacity: 0; }

/* ---------- Tür ---------- */
.vd-door {
  position: absolute; inset: 1.5cqw;
  transform-origin: 100% 50%;
  transform-style: preserve-3d;
  transition: transform 1.3s cubic-bezier(.55, .05, .25, 1) 1.2s;
  z-index: 2;
}
.vault--open .vd-door { transform: rotateY(108deg); }

.vd-door__face {
  position: absolute; inset: 0;
  display: grid; grid-template-columns: 1.15fr 1fr; align-items: center;
  gap: 3cqw; padding: 4cqw 7cqw 4cqw 5cqw;
  background:
    repeating-linear-gradient(90deg, rgba(255, 255, 255, .025) 0 .15cqw, transparent .15cqw .45cqw),
    linear-gradient(160deg, var(--metal-1), var(--metal-2) 45%, var(--metal-3));
  border: .35cqw solid #14171b;
  box-shadow:
    inset 0 .3cqw 0 rgba(255, 255, 255, .12),
    inset 0 -.4cqw 0 rgba(0, 0, 0, .5),
    inset 0 0 0 1.4cqw rgba(0, 0, 0, .12),
    0 2cqw 4cqw rgba(0, 0, 0, .55);
  backface-visibility: hidden;
}
.vault--error .vd-door { animation: shake .45s; }

.vd-rivet {
  position: absolute; width: 1.8cqw; height: 1.8cqw; border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #c3cad3, #5b636e 60%, #2a2f36);
  box-shadow: 0 .2cqw .3cqw rgba(0, 0, 0, .6);
}
.vd-rivet--tl { top: 2cqw; left: 2cqw; } .vd-rivet--tr { top: 2cqw; right: 2cqw; }
.vd-rivet--bl { bottom: 2cqw; left: 2cqw; } .vd-rivet--br { bottom: 2cqw; right: 2cqw; }

.vd-hinge {
  position: absolute; right: -1.2cqw; width: 2.4cqw; height: 12cqw;
  background: linear-gradient(90deg, #2a2f36, #8a929c 45%, #3a4048);
  border: .2cqw solid #14171b;
}
.vd-hinge--top { top: 12%; } .vd-hinge--bottom { bottom: 12%; }

/* ---------- Bedienfeld ---------- */
.vd-panel { display: grid; gap: 2cqw; }
.vd-panel__label { font-size: 2.2cqw; letter-spacing: .5cqw; color: #c9d0d8; opacity: .75; }

.vd-panel__window {
  display: flex; gap: 1.4cqw; padding: 1.4cqw;
  background: linear-gradient(180deg, #07090b, #121519);
  border: .3cqw solid #0b0d10;
  box-shadow: inset 0 .6cqw 1.4cqw rgba(0, 0, 0, .9), 0 .2cqw 0 rgba(255, 255, 255, .08);
  transition: box-shadow .3s;
}
.vault--open .vd-panel__window,
.vd-panel__window.is-error { box-shadow: inset 0 0 2cqw var(--vault-accent), 0 0 2cqw var(--vault-accent); }

.vd-drum {
  position: relative; flex: 1;
  --drum-h: 9cqw;
  height: var(--drum-h); overflow: hidden;
  background: linear-gradient(180deg, #0c0f12 0%, #1d2228 50%, #0c0f12 100%);
  border: .2cqw solid #262b31;
  outline: none;
}
.vd-drum:focus-visible { box-shadow: 0 0 0 .4cqw var(--vault-accent); }
.vd-drum::after { /* Glas-Reflex */
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(180deg, rgba(0, 0, 0, .65), transparent 30% 70%, rgba(0, 0, 0, .65));
}
.vd-drum__track { transition: transform .55s cubic-bezier(.3, 1.4, .5, 1); }
.vd-drum__digit {
  display: grid; place-items: center; height: var(--drum-h);
  font-size: 6.5cqw; color: var(--vault-accent);
  text-shadow: 0 0 1.6cqw color-mix(in srgb, var(--vault-accent) 70%, transparent);
}
.vd-drum__digit--q { color: #4a525d; text-shadow: none; }
.vd-drum__btn {
  position: absolute; left: 0; right: 0; z-index: 2; height: 50%;
  border: 0; background: transparent; color: transparent; cursor: pointer;
  font-size: 1.6cqw;
}
.vd-drum__btn:hover { color: rgba(255, 255, 255, .55); }
.vd-drum__btn--up { top: 0; display: flex; align-items: flex-start; justify-content: center; }
.vd-drum__btn--down { bottom: 0; display: flex; align-items: flex-end; justify-content: center; }

.vd-panel__unlock, .vd-panel__status {
  justify-self: start;
  padding: 1.2cqw 3.4cqw;
  font: inherit; font-size: 2.4cqw; letter-spacing: .4cqw;
  color: #e6ebf0;
  background: linear-gradient(180deg, #5b636e, #343a42);
  border: .25cqw solid #14171b;
  box-shadow: inset 0 .25cqw 0 rgba(255, 255, 255, .18), 0 .4cqw .8cqw rgba(0, 0, 0, .5);
}
.vd-panel__unlock { cursor: pointer; }
.vd-panel__unlock:hover:not(:disabled) { color: var(--vault-accent); }
.vd-panel__unlock:active:not(:disabled) { transform: translateY(.2cqw); box-shadow: inset 0 .3cqw .6cqw rgba(0, 0, 0, .6); }
.vd-panel__unlock:disabled { opacity: .55; cursor: default; }
.vd-panel__status { color: var(--vault-accent); background: #15181c; }

/* ---------- Drehknopf ---------- */
.vd-dial { justify-self: center; width: 100%; max-width: 26cqw; filter: drop-shadow(0 1.2cqw 1.6cqw rgba(0, 0, 0, .7)); }
.vd-dial__svg { display: block; width: 100%; height: auto; }
.vd-dial__rotor {
  transform-origin: 50px 50px;
  transform: rotate(var(--rot));
  transition: transform .6s cubic-bezier(.3, 1.3, .5, 1);
}
.vault--checking .vd-dial__rotor,
.vault--open .vd-dial__rotor { transition-duration: 1.1s; transition-timing-function: cubic-bezier(.2, .8, .2, 1); }

/* ---------- Animationen ---------- */
@keyframes led-on { to { background: var(--green, #00ff66); box-shadow: 0 0 1cqw var(--green, #00ff66); } }
@keyframes bar-fill { to { background: var(--green-bg, rgba(0, 255, 102, .25)); } }
@keyframes fade-in { to { opacity: 1; } }
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-1.4cqw) rotate(-.4deg); }
  40% { transform: translateX(1.2cqw) rotate(.3deg); }
  60% { transform: translateX(-.8cqw); }
  80% { transform: translateX(.5cqw); }
}

@media (prefers-reduced-motion: reduce) {
  .vd-door, .vd-bolt, .vd-dial__rotor, .vd-drum__track { transition-duration: .01s !important; transition-delay: 0s !important; }
  .vault--error .vd-door { animation: none; }
}
</style>
