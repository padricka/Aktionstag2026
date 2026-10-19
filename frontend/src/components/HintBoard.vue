<!--
  HintBoard — Hilfe-Notizen am Beamer (nur Host, GAME_DESIGN.md „Hilfe-Notizen“).

  Der Host öffnet die Hilfen der laufenden Aufgabe der Reihe nach (open → Server-
  Event open_hint). Anzahl, Texte und Kosten kommen fertig vom Backend
  (game_tick.hints); hier wird nichts gerechnet. Die neueste Hilfe steht oben.
-->
<template>
  <aside class="hint-board" aria-label="Hilfe-Notizen">
    <div class="hint-head">
      <span class="hint-title">Hilfe-Notizen</span>
      <span v-if="opened.length && !dev" class="hint-cost">bisher −{{ opened.length * hints.cost }} Punkte</span>
    </div>

    <button class="hint-open" type="button" :disabled="alleOffen || warte" @click="oeffnen">
      <template v-if="alleOffen">Alle Hilfen offen</template>
      <template v-else-if="warte">Öffne …</template>
      <template v-else>
        Hilfe {{ opened.length + 1 }} von {{ hints.total }} öffnen
        <span class="hint-price">{{ dev ? 'kostenlos (DEV)' : `−${hints.cost} Punkte` }}</span>
      </template>
    </button>
    <p v-if="error" class="hint-error">{{ error }}</p>

    <TransitionGroup name="hint" tag="ol" class="hint-list">
      <li v-for="n in neuesteZuerst" :key="n.nr" class="hint-note">
        <span class="hint-nr">Hilfe {{ n.nr }}</span>
        <p class="hint-text">{{ n.text }}</p>
      </li>
    </TransitionGroup>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  // { total, opened: [Texte], cost } aus game_tick.hints
  hints: { type: Object, required: true },
  dev: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['open'])

const warte = ref(false)

const opened = computed(() => props.hints?.opened || [])
const alleOffen = computed(() => opened.value.length >= (props.hints?.total || 0))
const neuesteZuerst = computed(() =>
  opened.value.map((text, i) => ({ nr: i + 1, text })).reverse(),
)

// Antwort vom Server: neue Hilfe da oder Ablehnung → wieder frei
watch(() => opened.value.length, () => { warte.value = false })
watch(() => props.error, (e) => { if (e) warte.value = false })

function oeffnen() {
  if (alleOffen.value || warte.value) return
  warte.value = true
  emit('open')
}
</script>

<style scoped>
.hint-board {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  min-height: 0;
  overflow-y: auto;
}

.hint-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.hint-title {
  font-family: var(--mono);
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--fg-3);
}

.hint-cost { font-family: var(--mono); font-size: 13px; color: var(--amber); }

.hint-open {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: var(--amber-bg);
  border: 1px solid var(--amber-border);
  color: var(--amber);
  font-family: var(--mono);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.06em;
  cursor: pointer;
}

.hint-open:hover:not(:disabled) { border-color: var(--amber); }
.hint-open:disabled { opacity: 0.5; cursor: default; }
.hint-price { font-size: 12px; font-weight: 400; opacity: 0.85; }

.hint-error { margin: 0; font-size: 13px; color: var(--red); }

.hint-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Notizzettel wie die Aufgaben-Notizen, nur gelb (Haftnotiz) */
.hint-note {
  padding: 12px 16px 14px;
  background: #f7e98c;
  color: #2a2a1e;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.35);
  transform: rotate(-0.8deg);
}

.hint-note:nth-child(even) { transform: rotate(0.7deg); }

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

.hint-enter-active { transition: transform 0.45s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.45s; }
.hint-enter-from { opacity: 0; transform: translateY(-14px) rotate(-4deg); }

@media (prefers-reduced-motion: reduce) {
  .hint-enter-active { transition: none; }
}
</style>
