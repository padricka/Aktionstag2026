<!--
  Task3Master — Leitstand, Aufgabe 3 „Datenrettung" (view.type "ascii_binary_tables").

  Der Leitstand hat keine Eingabe. Sein Beitrag ist die Tabelle A–M und die
  oberen Stellenwerte 128/64/32/16: die Vorderseite hat nur N–Z, die Rückseite
  nur 8/4/2/1. Dazu sieht er, ob P1 und P2 ihren Sync-Knopf schon freigeschaltet
  haben (p1_status / p2_status).
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Datenrettung</h2>
      <span class="role">Leitstand</span>
    </header>

    <p class="hint">
      Deine Tabellenhälfte und die oberen Stellenwerte sind der Schlüssel für beide Seiten.
      Sag sie Vorderseite (N–Z fehlt dir) und Rückseite (8/4/2/1 fehlt dir) an.
    </p>

    <div class="body">
      <section class="panel">
        <span class="panel-label">ASCII-Tabelle · A–M</span>
        <div class="grid ascii-table">
          <div v-for="item in asciiHalf" :key="item.char" class="cell">
            <span class="cell-key">{{ item.char }}</span>
            <span class="cell-val">{{ item.dec }}</span>
          </div>
        </div>
      </section>

      <div class="side">
        <section class="panel">
          <span class="panel-label">Stellenwerte · obere Bits</span>
          <div class="places">
            <span v-for="wert in placeValues" :key="wert" class="place-value">{{ wert }}</span>
          </div>
        </section>

        <section class="panel">
          <span class="panel-label">Status</span>
          <div class="status-row">
            <span class="status-name">Vorderseite</span>
            <span class="status-value" :class="statusClass(p1Status)">{{ p1Status }}</span>
          </div>
          <div class="status-row">
            <span class="status-name">Rückseite</span>
            <span class="status-value" :class="statusClass(p2Status)">{{ p2Status }}</span>
          </div>
          <p v-if="beideFrei" class="status-hint">
            Beide Knöpfe sind frei – jetzt müssen Vorderseite und Rückseite
            innerhalb von 3 Sekunden drücken.
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  view: { type: Object, default: null },
})

// Tabellenhälfte und Stellenwerte kommen fertig vom Server (nichts wird gerechnet).
const asciiHalf = computed(() =>
  Object.entries(props.view?.ascii_half || {})
    .map(([char, dec]) => ({ char, dec }))
    .sort((a, b) => a.dec - b.dec),
)

const placeValues = computed(() => props.view?.place_values || [])

const p1Status = computed(() => props.view?.p1_status || 'GESPERRT')
const p2Status = computed(() => props.view?.p2_status || 'GESPERRT')

const beideFrei = computed(
  () => p1Status.value === 'FREIGESCHALTET' && p2Status.value === 'FREIGESCHALTET',
)

function statusClass(wert) {
  return wert === 'FREIGESCHALTET' ? 'is-open' : 'is-locked'
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

.body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 24px;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
  min-height: 0;
  overflow-y: auto;
}

.panel-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.grid {
  display: grid;
  gap: 8px;
  align-content: start;
}

.ascii-table { grid-template-columns: repeat(3, 1fr); }

.cell {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
}

.cell-key { font-size: 24px; font-weight: 700; color: var(--fg); letter-spacing: 0.05em; }
.cell-val { font-size: 22px; font-weight: 700; color: var(--green); letter-spacing: 0.05em; }

.side {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 0;
}

.places {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.place-value {
  display: block;
  padding: 22px 8px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 40px;
  font-weight: 700;
  color: var(--fg);
  text-align: center;
  letter-spacing: 0.05em;
}

.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
}

.status-name { font-size: 14px; color: var(--fg-2); }

.status-value {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.status-value.is-open { color: var(--green); }
.status-value.is-locked { color: var(--fg-3); }

.status-hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--green);
  letter-spacing: 0.03em;
}

@media (max-width: 1100px) {
  .body { grid-template-columns: 1fr; overflow-y: auto; }
  .ascii-table { grid-template-columns: repeat(2, 1fr); }
  .cell-key { font-size: 20px; }
  .cell-val { font-size: 18px; }
  .place-value { font-size: 30px; padding: 16px 8px; }
}
</style>
