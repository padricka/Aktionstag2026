<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Löschprotokoll</h2>
      <span class="role">Leitstand</span>
    </header>

    <p class="hint">
      Lies den anderen das Brandmelde-Log vor. Welches Löschmittel ein Rack braucht, sagt Regel ①
      auf deinem Teil des Löschplans – Brandgut und Strom kennen nur die anderen.
    </p>

    <div v-if="!view" class="empty">Warte auf Task-Daten …</div>

    <div v-else class="body">
      <div class="main-col">
        <section class="panel">
          <span class="panel-label">Brandmelde-Log · sortiert nach angezeigter Uhrzeit</span>
          <ol class="log">
            <li
              v-for="(e, i) in log"
              :key="i"
              class="log-row"
              :class="{ 'is-test': e.test }"
            >
              <span class="log-time">{{ e.time }}</span>
              <span class="log-source">{{ e.source }}</span>
              <span class="log-text">
                <span v-if="e.test" class="log-tag">[TEST]</span>
                Brandalarm · Rack <strong>{{ e.rack }}</strong>
              </span>
            </li>
          </ol>
          <p class="log-legend">BMZ = Brandmeldezentrale · RM = Rauchmelder im Raum</p>
        </section>

        <ReleaseButton
          :armed="!!view.release?.armed"
          :window="view.release?.window || 3"
          partner="Rückseite"
          @press="emit('solved', { target: 'release' })"
        />
      </div>

      <aside v-if="view.note" class="note-col">
        <span class="panel-label">Dein Teil des Löschplans</span>
        <TornNote :note="view.note" :seed="noteSeed" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import TornNote from '../../TornNote.vue'
import ReleaseButton from './ReleaseButton.vue'

const props = defineProps({
  view: { type: Object, default: null },
  // gleiche Aufgabe → gleiche Risskante
  noteSeed: { type: String, default: '' },
})

const emit = defineEmits(['solved'])

const log = computed(() => props.view?.log || [])
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

.main-col {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
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

.log {
  list-style: none;
  margin: 0;
  padding: 12px 0;
  background: var(--bg);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
}

.log-row {
  display: grid;
  grid-template-columns: 70px 50px 1fr;
  gap: 14px;
  align-items: baseline;
  padding: 8px 18px;
  font-size: 17px;
  color: var(--fg-2);
}

.log-row + .log-row { border-top: 1px dashed var(--border-2); }

.log-time { color: var(--green); font-weight: 700; }
.log-source { color: var(--amber); font-weight: 600; }
.log-text strong { color: var(--fg); letter-spacing: 0.06em; }

.log-tag {
  color: var(--fg-3);
  font-weight: 700;
  margin-right: 6px;
}

.log-row.is-test { color: var(--fg-3); }

.log-legend { margin: 0; font-size: 12px; color: var(--fg-3); }

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
