<!--
  HintBoard — Abreißblock mit Hilfe-Notizen am Beamer (nur Host, GAME_DESIGN.md „Hilfe-Notizen“).

  Auf dem gelben Block stehen die Themen, die gerade passen (game_tick.hints.available –
  was laut Spielstand schon erledigt ist, steht nicht mehr drauf). Ein Klick reißt den
  Zettel zu genau diesem Thema ab (open(id) → Server-Event open_hint). Der abgerissene
  Zettel fällt mit Risskante unter den Block, der neueste oben. Themen, Texte und Kosten
  kommen fertig vom Backend; hier wird nichts gerechnet.
-->
<template>
  <aside class="hint-board" aria-label="Hilfe-Notizen">
    <div class="pad" :class="{ 'is-tearing': !!warte }">
      <div class="pad-glue" aria-hidden="true"></div>
      <div class="pad-sheet">
        <p class="pad-title">Hilfe – wobei hängt ihr?</p>
        <ul v-if="available.length" class="pad-topics">
          <li v-for="t in available" :key="t.id">
            <button
              class="hint-topic"
              type="button"
              :disabled="!!warte"
              @click="abreissen(t.id)"
            >
              <span class="hint-label">{{ t.label }}</span>
              <span class="hint-price">{{ dev ? 'gratis' : `−${hints.cost}` }}</span>
            </button>
          </li>
        </ul>
        <p v-else class="pad-empty">Keine passende Hilfe mehr für diesen Schritt.</p>
      </div>
      <div class="pad-stack" aria-hidden="true"><i></i><i></i></div>
    </div>

    <p v-if="opened.length && !dev" class="hint-cost">bisher −{{ opened.length * hints.cost }} Punkte</p>
    <p v-if="error" class="hint-error">{{ error }}</p>

    <TransitionGroup name="tear" tag="ol" class="hint-list">
      <li v-for="(n, i) in neuesteZuerst" :key="n.id" class="hint-note" :style="{ '--tilt': `${i % 2 ? 1.2 : -1.4}deg` }">
        <span class="hint-nr">{{ n.label }}</span>
        <p class="hint-text">{{ n.text }}</p>
      </li>
    </TransitionGroup>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  // { total, cost, available: [{id, label}], opened: [{id, label, text}] } aus game_tick.hints
  hints: { type: Object, required: true },
  dev: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['open'])

const warte = ref(null)   // id des Zettels, der gerade abgerissen wird

const available = computed(() => props.hints?.available || [])
const opened = computed(() => props.hints?.opened || [])
const neuesteZuerst = computed(() => [...opened.value].reverse())

// Antwort vom Server: Zettel ist da oder abgelehnt → Block wieder frei
watch(() => opened.value.length, () => { warte.value = null })
watch(() => props.error, (e) => { if (e) warte.value = null })

function abreissen(id) {
  if (warte.value) return
  warte.value = id
  emit('open', id)
}
</script>

<style scoped>
.hint-board {
  --pad-paper: #f7e98c;
  --pad-ink: #2a2a1e;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 14px;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

/* ------------------------------------------------------------------ Block */
.pad {
  position: relative;
  transform: rotate(-1.5deg);
  filter: drop-shadow(0 10px 14px rgba(0, 0, 0, 0.45));
}

.pad-glue {
  height: 16px;
  border-radius: 3px 3px 0 0;
  background: linear-gradient(180deg, #5a4a2a, #3b3020);
}

.pad-sheet {
  position: relative;
  z-index: 1;
  padding: 12px 16px 16px;
  background:
    repeating-linear-gradient(to bottom, transparent 0, transparent 31px, rgba(150, 120, 40, 0.25) 31px, rgba(150, 120, 40, 0.25) 32px),
    var(--pad-paper);
  color: var(--pad-ink);
  transform-origin: 50% 0;
  transition: transform 0.25s ease-out;
}

/* angedeutete Blätter darunter */
.pad-stack i {
  display: block;
  height: 4px;
  margin: 0 4px;
  background: #e9d97a;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.pad-stack i + i { margin: 0 8px; background: #dccb6c; }

/* beim Abreißen hebt sich das oberste Blatt kurz an */
.pad.is-tearing .pad-sheet { transform: rotate(-3deg) translateY(4px) scaleY(0.98); }

.pad-title {
  margin: 0 0 8px;
  font-family: 'Caveat', 'Segoe Print', 'Bradley Hand', cursive;
  font-size: 26px;
  font-weight: 700;
}

.pad-topics { list-style: none; margin: 0; padding: 0; }

.hint-topic {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
  padding: 2px 4px;
  min-height: 32px;
  border: none;
  background: none;
  color: var(--pad-ink);
  font-family: 'Caveat', 'Segoe Print', 'Bradley Hand', cursive;
  font-size: 23px;
  text-align: left;
  cursor: pointer;
}

.hint-topic::before { content: '☐'; font-size: 18px; margin-right: 2px; }
.hint-topic:hover:not(:disabled) { background: rgba(0, 0, 0, 0.06); }
.hint-topic:hover:not(:disabled) .hint-label { text-decoration: underline; text-decoration-thickness: 2px; }
.hint-topic:disabled { cursor: wait; opacity: 0.6; }
.hint-label { flex: 1; }
.hint-price { font-family: var(--mono); font-size: 12px; color: #8a3a1a; white-space: nowrap; }

.pad-empty {
  margin: 0;
  font-family: 'Caveat', 'Segoe Print', cursive;
  font-size: 21px;
  opacity: 0.7;
}

.hint-cost { margin: 4px 0 0; font-family: var(--mono); font-size: 13px; color: var(--amber); text-align: right; }
.hint-error { margin: 0; font-size: 13px; color: var(--red); }

/* ------------------------------------------------------------ Abgerissene Zettel */
.hint-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hint-note {
  padding: 16px 16px 14px;
  background: var(--pad-paper);
  color: var(--pad-ink);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.35);
  transform: rotate(var(--tilt, -1deg));
  /* gezackte Abrisskante oben */
  clip-path: polygon(0 7px, 4% 2px, 9% 6px, 14% 1px, 20% 5px, 26% 0, 31% 6px, 37% 2px, 43% 7px, 49% 1px,
    55% 5px, 61% 0, 66% 6px, 72% 2px, 78% 6px, 84% 1px, 90% 5px, 95% 0, 100% 6px, 100% 100%, 0 100%);
}

.hint-nr {
  display: block;
  margin-bottom: 4px;
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #6b5d1a;
}

.hint-text {
  margin: 0;
  font-family: 'Caveat', 'Segoe Print', 'Bradley Hand', cursive;
  font-size: 23px;
  line-height: 1.2;
}

/* Zettel wird vom Block abgerissen und fällt nach unten */
.tear-enter-active { transition: transform 0.6s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.35s; }
.tear-enter-from { opacity: 0; transform: translateY(-120px) rotate(-14deg) scale(0.96); }
.tear-move { transition: transform 0.45s ease; }

@media (prefers-reduced-motion: reduce) {
  .tear-enter-active, .tear-move, .pad-sheet { transition: none; }
}
</style>
