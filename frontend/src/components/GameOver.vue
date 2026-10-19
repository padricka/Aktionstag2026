<template>
  <div class="end" :class="istSieg ? 'is-win' : 'is-lose'">
    <!-- Bild vollständig und scharf; die unscharfe Kopie füllt nur den Rand -->
    <img class="end-blur" :src="bild" alt="" aria-hidden="true" />
    <img class="end-bild" :src="bild" :alt="bildAlt" />
    <div class="end-vignette" aria-hidden="true"></div>

    <Transition name="scrim">
      <div v-if="offen" class="end-scrim" @click="schliessen"></div>
    </Transition>

    <Transition name="sheet" appear @after-enter="fokusAufKarte">
      <section
        v-if="offen"
        ref="karte"
        class="end-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="end-titel"
        tabindex="-1"
      >
        <span class="hud hud-tl" aria-hidden="true"></span>
        <span class="hud hud-tr" aria-hidden="true"></span>
        <span class="hud hud-bl" aria-hidden="true"></span>
        <span class="hud hud-br" aria-hidden="true"></span>

        <button ref="closeBtn" class="end-close" aria-label="Punkte ausblenden" @click="schliessen">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>
        </button>

        <p id="end-titel" class="end-status" :class="istSieg ? 'win' : 'lose'">
          <span class="end-dot" aria-hidden="true"></span>
          {{ istSieg ? 'Mission erfüllt' : 'Server ausgefallen' }}
        </p>

        <p class="end-score">{{ score }}</p>
        <p class="end-label">Punkte</p>

        <p class="end-meta">Überlebt · {{ survivedSeconds }}s</p>

        <!-- Bestenliste: Top 5 kommen mit game_over vom Backend -->
        <section v-if="leaderboard?.top?.length" class="end-board" aria-label="Bestenliste Top 5">
          <h2 class="end-board-title">Bestenliste · Top 5</h2>
          <ol>
            <li
              v-for="e in leaderboard.top"
              :key="e.rank"
              :class="{ 'is-own': e.rank === leaderboard.rank }"
            >
              <span class="end-board-rank" :class="`r${e.rank}`">{{ e.rank }}</span>
              <span class="end-board-team">{{ (e.players || []).join(' · ') }}</span>
              <span class="end-board-score">{{ e.score }}</span>
            </li>
          </ol>
          <p v-if="leaderboard.rank === null" class="end-board-own">DEV-Modus · diese Runde wird nicht gewertet</p>
          <p v-else-if="leaderboard.rank > leaderboard.top.length" class="end-board-own">
            Euer Platz: {{ leaderboard.rank }} von {{ leaderboard.total }}
          </p>
        </section>

        <!-- Platz für weitere Zusatzinhalte -->
        <slot />

        <div v-if="showExit || showRestart" class="end-actions">
          <button v-if="showExit" class="end-btn end-exit" @click="$emit('exit')">
            Spiel beenden
          </button>
          <button
            v-if="showRestart"
            class="end-btn end-btn-primary restart-btn"
            :disabled="restarting"
            @click="$emit('restart')"
          >
            {{ restarting ? 'Neustart …' : 'Neustart' }}
          </button>
        </div>
      </section>
    </Transition>

    <Transition name="bar">
      <nav v-if="!offen" class="end-bar" aria-label="Spielende">
        <div class="end-bar-left">
          <button v-if="showExit" class="end-btn end-exit" @click="$emit('exit')">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
            Spiel beenden
          </button>
        </div>

        <button
          ref="handle"
          class="end-handle"
          aria-label="Punkte anzeigen"
          :aria-expanded="offen ? 'true' : 'false'"
          @click="oeffnen"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 15l6-6 6 6" /></svg>
          <span>Punkte</span>
        </button>

        <div class="end-bar-right">
          <button
            v-if="showRestart"
            class="end-btn end-btn-primary restart-btn"
            :disabled="restarting"
            @click="$emit('restart')"
          >
            {{ restarting ? 'Neustart …' : 'Neustart' }}
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v4h-4" /></svg>
          </button>
        </div>
      </nav>
    </Transition>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  result: { type: String, default: 'meltdown' },
  score: { type: Number, default: 0 },
  survivedSeconds: { type: Number, default: 0 },
  showRestart: { type: Boolean, default: false },
  showExit: { type: Boolean, default: false },
  restarting: { type: Boolean, default: false },
  // { rank, total, top: [{ rank, players, score }] } aus game_over.leaderboard
  leaderboard: { type: Object, default: null },
})

defineEmits(['restart', 'exit'])

const istSieg = computed(() => props.result === 'victory')

const bild = computed(() => {
  const name = istSieg.value ? 'win-screen2.jpg' : 'game-over2.jpg'
  return new URL(`../assets/${name}`, import.meta.url).href
})

const bildAlt = computed(() => (istSieg.value
  ? 'Zeitung: Team löscht brennenden Server der DRV Schwaben – Sieg'
  : 'Fernseh-Nachrichten: Server-Totalverlust bei der DRV Schwaben – Niederlage'))

// Karte ist von Anfang an da und gleitet per CSS herein (Transition "appear")
const offen = ref(true)
const karte = ref(null)
const closeBtn = ref(null)
const handle = ref(null)

function fokusAufKarte() {
  closeBtn.value?.focus({ preventScroll: true })
}

async function schliessen() {
  if (!offen.value) return
  offen.value = false
  await nextTick()
  handle.value?.focus({ preventScroll: true })
}

async function oeffnen() {
  offen.value = true
  await nextTick()
  fokusAufKarte()
}

function onKey(e) {
  if (e.key === 'Escape') schliessen()
}

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
/* Eigene, feste Farben: das Bild ist immer dunkel, auch im hellen Theme */
.end {
  --end-fg: #eaf4ee;
  --end-fg-2: #a9bdb0;
  --end-fg-3: #6f8a79;
  --end-panel: rgba(6, 12, 9, 0.86);
  --end-line: rgba(234, 244, 238, 0.12);
  --accent: var(--green, #00ff66);
  --accent-soft: var(--green-bg, rgba(0, 255, 102, 0.1));
  --accent-line: var(--green-border, rgba(0, 255, 102, 0.35));
  --ease-spring: cubic-bezier(0.22, 1.25, 0.36, 1);
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);

  position: fixed;
  inset: 0;
  z-index: 999;
  overflow: hidden;
  background: #020403;
  color: var(--end-fg);
  font-family: var(--mono);
}

.end.is-lose {
  --accent: var(--red, #ff3a4d);
  --accent-soft: var(--red-bg, rgba(255, 58, 77, 0.1));
  --accent-line: var(--red-border, rgba(255, 58, 77, 0.4));
}

/* ---------------------------------------------------------------- Bild */
.end-blur {
  position: absolute;
  inset: -40px;
  width: calc(100% + 80px);
  height: calc(100% + 80px);
  object-fit: cover;
  filter: blur(36px) brightness(0.4) saturate(1.15);
}

.end-bild {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  animation: kenburns 24s ease-out both;
}

@keyframes kenburns {
  from { transform: scale(1); }
  to   { transform: scale(1.035); }
}

.end-vignette {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(120% 90% at 50% 45%, transparent 55%, rgba(0, 0, 0, 0.55) 100%),
    linear-gradient(to top, rgba(0, 0, 0, 0.7) 0, transparent 22%);
}

/* ---------------------------------------------------------------- Abdunklung hinter der Karte */
.end-scrim {
  position: absolute;
  inset: 0;
  background: rgba(2, 6, 4, 0.45);
  backdrop-filter: blur(2px);
  cursor: pointer;
}

.scrim-enter-active,
.scrim-leave-active { transition: opacity 0.35s ease; }
.scrim-enter-from,
.scrim-leave-to { opacity: 0; }

/* ---------------------------------------------------------------- Karte */
.end-card {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: min(460px, calc(100vw - 32px));
  max-height: calc(100vh - 48px);
  overflow-y: auto;
  padding: 40px 40px 28px;
  text-align: center;
  background:
    linear-gradient(180deg, var(--accent-soft), transparent 140px),
    var(--end-panel);
  border: 1px solid var(--end-line);
  border-top: 2px solid var(--accent);
  box-shadow:
    0 40px 90px rgba(0, 0, 0, 0.65),
    0 0 0 1px rgba(0, 0, 0, 0.4),
    0 -12px 60px -20px var(--accent-line);
  backdrop-filter: blur(16px) saturate(1.2);
  outline: none;
}

/* HUD-Eckmarken passend zur Terminal-Optik */
.hud {
  position: absolute;
  width: 14px;
  height: 14px;
  border-color: var(--accent);
  border-style: solid;
  opacity: 0.8;
  pointer-events: none;
}
.hud-tl { top: 8px;    left: 8px;  border-width: 1px 0 0 1px; }
.hud-tr { top: 8px;    right: 8px; border-width: 1px 1px 0 0; opacity: 0; }
.hud-bl { bottom: 8px; left: 8px;  border-width: 0 0 1px 1px; }
.hud-br { bottom: 8px; right: 8px; border-width: 0 1px 1px 0; }

.sheet-enter-active {
  transition:
    transform 0.7s var(--ease-spring) 0.45s,
    opacity 0.35s ease 0.45s;
}
.sheet-leave-active {
  transition:
    transform 0.45s cubic-bezier(0.55, 0, 0.75, 0.2),
    opacity 0.3s ease 0.1s;
}
.sheet-enter-from,
.sheet-leave-to {
  transform: translate(-50%, calc(-50% + 70vh));
  opacity: 0;
}

.end-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  background: transparent;
  border: 1px solid var(--end-line);
  color: var(--end-fg-2);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s, transform 0.15s;
}
.end-close svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
}
.end-close:hover {
  color: var(--end-fg);
  border-color: var(--accent-line);
  background: var(--accent-soft);
}
.end-close:active { transform: scale(0.94); }

.end-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 22px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid var(--accent-line);
}

.end-dot {
  width: 7px;
  height: 7px;
  background: var(--accent);
  box-shadow: 0 0 10px var(--accent);
  animation: puls 1.6s ease-in-out infinite;
}

@keyframes puls {
  50% { opacity: 0.35; }
}

.end-score {
  margin: 0;
  font-size: clamp(56px, 11vw, 84px);
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.02em;
  color: var(--end-fg);
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 32px var(--accent-line);
}

.end-label {
  margin: 8px 0 22px;
  font-size: 11px;
  color: var(--end-fg-3);
  text-transform: uppercase;
  letter-spacing: 0.3em;
}

.end-meta {
  margin: 0;
  padding-top: 16px;
  border-top: 1px solid var(--end-line);
  font-size: 12px;
  color: var(--end-fg-2);
  letter-spacing: 0.06em;
}

/* ---------------------------------------------------------------- Bestenliste */
.end-board {
  margin-top: 20px;
  text-align: left;
}

.end-board-title {
  margin: 0 0 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: var(--end-fg-3);
}

.end-board ol {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 4px;
}

.end-board li {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 7px 10px;
  font-size: 13px;
  background: rgba(234, 244, 238, 0.03);
  border: 1px solid transparent;
}

.end-board li.is-own {
  background: var(--accent-soft);
  border-color: var(--accent-line);
}

.end-board-rank {
  display: grid;
  place-items: center;
  height: 22px;
  font-weight: 700;
  font-size: 12px;
  color: var(--end-fg-2);
  border: 1px solid var(--end-line);
}
.end-board-rank.r1 { color: #ffd66b; border-color: rgba(255, 214, 107, 0.5); }
.end-board-rank.r2 { color: #d9e2ec; border-color: rgba(217, 226, 236, 0.45); }
.end-board-rank.r3 { color: #e7a272; border-color: rgba(231, 162, 114, 0.45); }

.end-board-team {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--end-fg);
}

.end-board-score {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--end-fg);
}

.end-board li.is-own .end-board-score { color: var(--accent); }

.end-board-own {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--end-fg-2);
  text-align: center;
  letter-spacing: 0.04em;
}

.end-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 24px;
}
.end-actions .end-btn:only-child { grid-column: 1 / -1; }

/* ---------------------------------------------------------------- Knöpfe */
.end-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 46px;
  padding: 0 22px;
  font-family: var(--mono);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--end-fg);
  background: rgba(6, 12, 9, 0.6);
  border: 1px solid var(--end-line);
  backdrop-filter: blur(10px);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s, transform 0.15s, box-shadow 0.15s;
}
.end-btn svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.end-btn:hover:not(:disabled) {
  border-color: rgba(234, 244, 238, 0.35);
  background: rgba(20, 30, 24, 0.75);
}
.end-btn:active:not(:disabled) { transform: translateY(1px); }
.end-btn:disabled { opacity: 0.5; cursor: wait; }

.end-btn-primary {
  color: #04100a;
  background: var(--accent);
  border-color: var(--accent);
  box-shadow: 0 10px 30px -10px var(--accent);
}
.end.is-lose .end-btn-primary { color: #1a0306; }
.end-btn-primary:hover:not(:disabled) {
  background: var(--accent);
  border-color: var(--accent);
  box-shadow: 0 14px 36px -10px var(--accent);
  filter: brightness(1.08);
}

.end-btn:focus-visible,
.end-close:focus-visible,
.end-handle:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}

/* ---------------------------------------------------------------- Leiste unten */
.end-bar {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: end;
  gap: 16px;
  padding: 0 clamp(16px, 4vw, 48px) clamp(16px, 3.5vh, 36px);
}
.end-bar-left  { justify-self: start; }
.end-bar-right { justify-self: end; }

.end-handle {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 18px 6px;
  background: rgba(6, 12, 9, 0.6);
  border: 1px solid var(--end-line);
  backdrop-filter: blur(10px);
  color: var(--end-fg);
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.end-handle svg {
  width: 22px;
  height: 22px;
  fill: none;
  stroke: var(--accent);
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
  animation: hoch 1.8s ease-in-out infinite;
}
.end-handle:hover {
  border-color: var(--accent-line);
  background: rgba(20, 30, 24, 0.75);
}

@keyframes hoch {
  50% { transform: translateY(-4px); }
}

.bar-enter-active { transition: transform 0.5s var(--ease-out) 0.15s, opacity 0.4s ease 0.15s; }
.bar-leave-active { transition: transform 0.2s ease, opacity 0.15s ease; }
.bar-enter-from,
.bar-leave-to {
  transform: translateY(24px);
  opacity: 0;
}

@media (max-width: 560px) {
  .end-card { padding: 36px 22px 22px; }
  .end-bar { grid-template-columns: 1fr 1fr; }
  .end-handle { grid-column: 1 / -1; grid-row: 1; justify-self: center; }
  .end-bar-left, .end-bar-right { grid-row: 2; }
  .end-btn { padding: 0 14px; font-size: 12px; }
}

@media (prefers-reduced-motion: reduce) {
  .end-bild,
  .end-dot,
  .end-handle svg { animation: none; }
  .sheet-enter-active,
  .sheet-leave-active,
  .bar-enter-active,
  .bar-leave-active,
  .scrim-enter-active,
  .scrim-leave-active { transition: none; }
}
</style>
