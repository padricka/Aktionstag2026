<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Defekte Komponente abschalten</h2>
      <span class="role">P1</span>
    </header>

    <p class="hint">Frage den Master nach dem Symbol der defekten Komponente.</p>

    <div class="symbols">
      <button
        v-for="s in symbole"
        :key="s"
        class="symbol"
        :class="{ active: auswahl === s }"
        :disabled="abgesendet"
        :aria-label="`Symbol: ${s}`"
        :aria-pressed="auswahl === s"
        @click="auswahl = s"
      >
        <SymbolIcon :name="s" :farbe="auswahl === s ? '#050a08' : '#ffffff'" :size="120" />
      </button>
    </div>

    <div class="foot">
      <button
        class="btn-action"
        :disabled="!auswahl || abgesendet"
        @click="bestaetigen"
      >
        {{ abgesendet ? 'Gesendet' : 'Hauptschalter betätigen' }}
      </button>
      <p v-if="serverError" class="msg-err">{{ serverError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import SymbolIcon from '../graphic-symbols/SymbolIcon.vue'

const props = defineProps({
  symbole:     { type: Array,  default: () => ['raute', 'dreieck', 'quadrat', 'kreis'] },
  serverError: { type: String, default: '' }
})
const emit = defineEmits(['solved', 'failed'])

const auswahl    = ref(null)
const abgesendet = ref(false)

watch(() => props.serverError, (e) => { if (e) abgesendet.value = false })

function bestaetigen() {
  if (!auswahl.value) return
  abgesendet.value = true
  emit('solved', { player: 'P1', value: auswahl.value })
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
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.title {
  font-size: 16px;
  font-weight: 700;
  color: var(--fg);
  margin: 0;
}

.role {
  font-size: 11px;
  font-weight: 600;
  color: var(--green);
  padding: 4px 12px;
  border: 1px solid var(--green-border);
  letter-spacing: 0.15em;
}

.hint {
  font-size: 13px;
  color: var(--fg-3);
  margin: 0 0 24px 0;
}

.symbols {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  padding: 8px 0;
  min-height: 0;
}

.symbol {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
  cursor: pointer;
  min-height: 240px;
  padding: 20px;
  transition: border-color 0.15s, background 0.15s;
}

.symbol:hover:not(:disabled) {
  border-color: var(--green-border);
  background: var(--bg-1);
}

.symbol.active {
  background: var(--green);
  border-color: var(--green);
}

.symbol:disabled { opacity: 0.4; cursor: not-allowed; }

.foot {
  padding-top: 22px;
  margin-top: 16px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.btn-action {
  padding: 14px 64px;
  background: var(--green);
  color: #050a08;
  border: none;
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.15em;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-action:hover:not(:disabled) { background: #4dff8f; }
.btn-action:disabled { opacity: 0.35; cursor: not-allowed; }

.msg-err {
  font-size: 12px;
  color: var(--red);
  margin: 0;
}
</style>