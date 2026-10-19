<!--
  Task3Master — Leitstand, Aufgabe 3 „Datenrettung" (view.type "rescue_key").

  Der Leitstand sieht den Schlüssel k als 4 Bit und hat die Rechenregel
  Binär → Dezimal. Umgerechnet wird hier nichts – das ist Teil des Rätsels.
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Datenrettung</h2>
      <span class="role">Leitstand</span>
    </header>

    <p class="hint">
      Wie man Binär in Dezimal umrechnet, steht in Regel ② auf deinem Teil der Anleitung –
      die Pakete liest dir die Rückseite vor. Den Schlüssel k brauchen die anderen zum Entschlüsseln.
    </p>

    <div v-if="!view" class="empty">Warte auf Task-Daten …</div>

    <div v-else class="body">
      <section class="panel">
        <span class="panel-label">Verschlüsselungs-Log · Schlüssel k (binär)</span>
        <div class="key">
          <div v-for="(bit, i) in bits" :key="i" class="key-col">
            <span class="key-bit">{{ bit }}</span>
            <span class="key-place">{{ PLACES[i] }}</span>
          </div>
        </div>
      </section>

      <aside v-if="view.note" class="note-col">
        <span class="panel-label">Dein Teil der Anleitung</span>
        <TornNote :note="view.note" :seed="noteSeed" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import TornNote from '../../TornNote.vue'

const props = defineProps({
  view: { type: Object, default: null },
  // gleiche Aufgabe → gleiche Risskante
  noteSeed: { type: String, default: '' },
})

const PLACES = [8, 4, 2, 1]

const bits = computed(() => String(props.view?.key || '').split(''))
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
  grid-template-columns: minmax(0, 1fr) minmax(300px, 420px);
  gap: 24px;
  overflow: auto;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 24px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
  align-self: start;
}

.panel-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.key {
  display: flex;
  justify-content: center;
  gap: 18px;
  padding: 24px;
  background: var(--bg);
  border: 1px solid var(--border-2);
}

.key-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  font-family: var(--mono);
}

.key-bit {
  font-size: 56px;
  font-weight: 700;
  color: var(--green);
  line-height: 1;
}

.key-place {
  font-size: 13px;
  color: var(--fg-3);
}

.note-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
}

@media (max-width: 1100px) {
  .body { grid-template-columns: minmax(0, 1fr); }
}
</style>
