<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Schrank-Rückseite</h2>
      <span class="role">Rückseite</span>
    </header>

    <p class="hint">
      Du siehst, was in jedem Schrank steckt – sag es dem Leitstand. Regel ③ auf deinem Teil des
      Löschplans erklärt, wie man die Uhrzeiten im Log liest. Zum Schluss: Freigabe zu zweit (④).
    </p>

    <div v-if="!view" class="empty">Warte auf Task-Daten …</div>

    <div v-else class="body">
      <div class="main-col">
        <section class="panel">
          <span class="panel-label">Brandgut hinter den Schränken</span>
          <ul class="rear">
            <li v-for="r in rear" :key="r.rack" class="rear-item">
              <span class="rear-rack">{{ r.rack }}</span>
              <span class="rear-label">{{ r.label }}</span>
            </li>
          </ul>
        </section>

        <ReleaseButton
          :armed="!!view.release?.armed"
          :window="view.release?.window || 3"
          partner="Leitstand"
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

const rear = computed(() => props.view?.rear || [])
</script>

<style scoped>
.task {
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: 1200px;
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

.rear {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.rear-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 18px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  border-left: 4px solid var(--border-3);
}

.rear-rack {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--fg-3);
  letter-spacing: 0.12em;
}

.rear-label {
  font-family: var(--mono);
  font-size: 19px;
  font-weight: 700;
  color: var(--fg);
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
