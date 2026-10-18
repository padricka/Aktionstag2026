<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Löschprotokoll</h2>
      <span class="role">Leitstand</span>
    </header>

    <p class="hint">
      Lies deinen Log-Schritt und das Fragment vor. Die anderen haben die fehlenden Teile —
      gemeinsam ergibt sich die Reihenfolge und das Passwort (Punkte sortieren).
    </p>

    <div v-if="!view" class="empty">Warte auf Task-Daten …</div>

    <div v-else class="body">
      <section class="panel">
        <span class="panel-label">System-Log · ein Schritt</span>
        <div class="clue">
          <span class="clue-step">Schritt {{ clue.step }}</span>
          <span class="clue-valve">{{ clue.valve }}</span>
          <span class="clue-color">
            <span class="color-dot" :style="{ background: colorHex(clue.color) }"></span>
            {{ clue.color }}
          </span>
        </div>
      </section>

      <section class="panel">
        <span class="panel-label">Passwort-Fragment</span>
        <div class="fragment">
          <span class="fragment-dots">{{ dotsLabel(fragment.dots) }}</span>
          <span class="fragment-text">{{ fragment.text }}</span>
        </div>
        <p class="frag-hint">Punkte = Sortierreihenfolge (● zuerst, ●●● zuletzt).</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  view: { type: Object, default: null },
})

const COLOR_HEX = {
  ORANGE: '#ff8a00',
  RED: '#ff0055',
  GREEN: '#00ff66',
}

const clue = computed(() => props.view?.clue || { step: '–', valve: '–', color: '–' })
const fragment = computed(() => props.view?.fragment || { dots: 0, text: '–' })

function colorHex(name) {
  return COLOR_HEX[String(name || '').toUpperCase()] || '#555'
}

function dotsLabel(n) {
  const count = Math.max(0, Number(n) || 0)
  return '●'.repeat(count) || '–'
}
</script>

<style scoped>
.task {
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background: var(--bg-1);
  border: 1px solid var(--border);
  padding: 28px 36px;
  overflow: hidden;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.title { font-size: 16px; font-weight: 700; color: var(--fg); margin: 0; }

.role {
  font-size: 11px;
  font-weight: 600;
  color: var(--green);
  padding: 4px 12px;
  border: 1px solid var(--green-border);
  letter-spacing: 0.15em;
}

.hint { font-size: 13px; color: var(--fg-3); margin: 0 0 24px 0; }

.empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fg-3);
}

.body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 28px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
}

.panel-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.clue {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 18px;
  padding: 28px 24px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
}

.clue-step {
  font-family: var(--mono);
  font-size: 18px;
  font-weight: 700;
  color: var(--green);
  letter-spacing: 0.08em;
}

.clue-valve {
  font-family: var(--mono);
  font-size: 28px;
  font-weight: 700;
  color: var(--fg);
  letter-spacing: 0.1em;
}

.clue-color {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--mono);
  font-size: 18px;
  font-weight: 600;
}

.color-dot {
  width: 22px;
  height: 22px;
  border: 1px solid var(--border-3);
}

.fragment {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 36px 24px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
}

.fragment-dots {
  font-size: 22px;
  letter-spacing: 0.2em;
  color: var(--amber, #ffb830);
}

.fragment-text {
  font-family: var(--mono);
  font-size: 40px;
  font-weight: 700;
  color: var(--green);
  letter-spacing: 0.12em;
}

.frag-hint {
  font-size: 12px;
  color: var(--fg-3);
  margin: 0;
  text-align: center;
}
</style>
