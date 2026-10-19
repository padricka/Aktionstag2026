<template>
  <div
    v-if="note"
    class="tn"
    :class="tornClasses"
    role="note"
    :aria-label="`Dein Stück der ${note.title || 'Notiz'}`"
  >
    <div class="tn-paper" :style="paperStyle">
      <div
        v-for="r in rows"
        :key="r.row"
        class="tn-row"
        :data-row="r.row"
        :style="`top: calc(${r.row} * var(--tn-line))`"
      >
        <span
          v-for="(l, i) in r.lines"
          :key="i"
          class="tn-text"
          :class="`is-${l.style || 'text'}`"
        >{{ l.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * Ein Stück eines zerrissenen Notizzettels. Nur Darstellung (PANELS.md):
 * Text und gerissene Kanten kommen fertig vom Backend (view.note), gerissen
 * wird dort zwischen ganzen Wörtern. Hier entsteht nur die Form der Risskante –
 * unregelmäßig, aber für dieselbe Aufgabe (seed) immer gleich.
 */
const props = defineProps({
  // { id, title, torn: ['right','bottom',…], lines: [{ row, style, text }] }
  note: { type: Object, default: null },
  // z. B. die task_id: gleiche Aufgabe → gleiche Risskante
  seed: { type: String, default: '' },
})

const rows = computed(() => {
  const byRow = new Map()
  for (const l of props.note?.lines || []) {
    if (!byRow.has(l.row)) byRow.set(l.row, [])
    byRow.get(l.row).push(l)
  }
  return [...byRow.entries()].sort((a, b) => a[0] - b[0]).map(([row, lines]) => ({ row, lines }))
})

const lineCount = computed(() => (rows.value.length ? rows.value.at(-1).row + 1 : 1))
const torn = computed(() => new Set(props.note?.torn || []))
const tornClasses = computed(() => [...torn.value].map((s) => `torn-${s}`))

// Kleiner deterministischer Zufall aus dem seed (FNV-1a + mulberry32)
function zufall(seed) {
  let h = 2166136261
  for (const ch of `${props.note?.id || ''}:${seed}`) {
    h ^= ch.charCodeAt(0)
    h = Math.imul(h, 16777619)
  }
  return () => {
    h = (h + 0x6d2b79f5) | 0
    let t = h
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// Risskante: viele unregelmäßige Zacken, ab und zu ein tieferer Biss
function kante(r, n, tiefe) {
  return Array.from({ length: n + 1 }, (_, i) => {
    const biss = r() < 0.15 ? 1.8 : 1
    return { t: (i / n) * 100, d: (0.25 + r() * 0.75) * tiefe * biss }
  })
}

const clipPath = computed(() => {
  const r = zufall(props.seed)
  const pts = []
  const p = (x, y) => pts.push(`${x.toFixed(2)}% ${y.toFixed(2)}%`)
  if (torn.value.has('top')) kante(r, 22, 2.2).forEach(({ t, d }) => p(t, d))
  else { p(0, 0); p(100, 0) }
  if (torn.value.has('right')) kante(r, 26, 3.2).forEach(({ t, d }) => p(100 - d, t))
  else p(100, 100)
  if (torn.value.has('bottom')) kante(r, 22, 2.2).forEach(({ t, d }) => p(100 - t, 100 - d))
  else p(0, 100)
  if (torn.value.has('left')) kante(r, 26, 3.2).forEach(({ t, d }) => p(d, 100 - t))
  return `polygon(${pts.join(', ')})`
})

const paperStyle = computed(() => `clip-path: ${clipPath.value}; --tn-lines: ${lineCount.value}`)
</script>

<style scoped>
.tn {
  --tn-line: 32px;
  --tn-pad: 18px;
  --tn-pad-top: var(--tn-pad);
  --tn-pad-right: var(--tn-pad);
  --tn-pad-bottom: var(--tn-pad);
  --tn-pad-left: 46px;
  --tn-ink: #22304d;
  --tn-red: #b2281f;
  width: 100%;
  max-width: 520px;
  /* Schatten folgt der gerissenen Form */
  filter: drop-shadow(0 10px 14px rgba(0, 0, 0, 0.45));
}

/* gerissene Kanten: mehr Abstand, damit kein Wort an den Zacken klebt */
.torn-top    { --tn-pad-top: 30px; }
.torn-right  { --tn-pad-right: 34px; }
.torn-bottom { --tn-pad-bottom: 30px; }
.torn-left   { --tn-pad-left: 34px; }

.tn-paper {
  position: relative;
  box-sizing: border-box;
  height: calc(var(--tn-lines) * var(--tn-line) + var(--tn-pad-top) + var(--tn-pad-bottom));
  background-color: #f5f0e4;
  background-image:
    radial-gradient(circle at 22% 30%, rgba(150, 110, 50, 0.07), transparent 45%),
    radial-gradient(circle at 78% 75%, rgba(150, 110, 50, 0.08), transparent 50%),
    repeating-linear-gradient(to bottom, transparent 0, transparent calc(var(--tn-line) - 1px), rgba(110, 140, 190, 0.4) calc(var(--tn-line) - 1px), rgba(110, 140, 190, 0.4) var(--tn-line));
  background-position: 0 0, 0 0, 0 var(--tn-pad-top);
  background-repeat: no-repeat, no-repeat, repeat-y;
  font-family: 'Caveat', 'Segoe Print', 'Bradley Hand', 'Comic Sans MS', cursive;
  color: var(--tn-ink);
}

/* roter Heftrand nur, wo das Blatt nicht abgerissen ist */
.tn:not(.torn-left) .tn-paper::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 34px;
  width: 2px;
  background: rgba(206, 86, 86, 0.5);
}

.tn-row {
  position: absolute;
  left: var(--tn-pad-left);
  right: var(--tn-pad-right);
  margin-top: var(--tn-pad-top);
  height: var(--tn-line);
  display: flex;
  align-items: center;
  gap: 14px;
  white-space: nowrap;
}

.tn-text { font-size: 23px; line-height: 1; }

.is-text   { font-weight: 500; }
.is-rule   { font-weight: 700; }
.is-sign   { font-weight: 700; font-size: 25px; transform: rotate(-3deg); margin-left: auto; }
.is-strike {
  font-weight: 500;
  color: #6a7487;
  text-decoration: line-through;
  text-decoration-color: var(--tn-red);
  text-decoration-thickness: 3px;
}
.is-red    { font-weight: 700; font-size: 25px; color: var(--tn-red); transform: rotate(-5deg); }
.is-typed,
.is-stamp {
  font-family: 'Special Elite', 'Courier New', Courier, monospace;
  font-size: 14px;
  letter-spacing: 0.06em;
  color: #333;
}
.is-stamp {
  margin-left: auto;
  padding: 2px 8px;
  border: 2px solid rgba(178, 40, 34, 0.8);
  color: rgba(178, 40, 34, 0.9);
  transform: rotate(6deg);
}
</style>
