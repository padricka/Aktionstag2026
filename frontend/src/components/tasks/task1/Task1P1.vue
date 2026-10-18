<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Hauptschalter</h2>
      <span class="role">Vorderseite</span>
    </header>

    <p class="hint">
      Frage den Leitstand, welcher Steckplatz blinkt — und betätige den Schalter an dieser Position.
    </p>

    <div class="symbols">
      <button
        v-for="(s, idx) in switches"
        :key="`${s}-${idx}`"
        class="symbol"
        :class="{ active: auswahl === s }"
        :disabled="erledigt"
        :aria-label="`Steckplatz ${idx + 1}: ${s}`"
        :aria-pressed="auswahl === s"
        @click="auswahl = s"
      >
        <span class="slot-pos">{{ idx + 1 }}</span>
        <SymbolIcon :name="s" :farbe="auswahl === s ? '#050a08' : '#ffffff'" :size="100" />
      </button>
    </div>

    <div class="foot">
      <button
        class="btn-action"
        :disabled="!auswahl || erledigt"
        @click="bestaetigen"
      >
        {{ erledigt ? 'Erledigt' : 'Hauptschalter betätigen' }}
      </button>
      <p v-if="serverError && !erledigt" class="msg-err">{{ serverError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import SymbolIcon from '../graphic-symbols/SymbolIcon.vue'

const props = defineProps({
  symbole: { type: Array, default: () => ['raute', 'dreieck', 'quadrat', 'kreis'] },
  view: { type: Object, default: null },
  serverError: { type: String, default: '' },
})
const emit = defineEmits(['solved', 'failed'])

const auswahl = ref(null)
const lokalGesendet = ref(false)

const switches = computed(() => props.view?.switches || props.symbole)
const pDone = computed(() => !!props.view?.p_done)
const erledigt = computed(() => pDone.value || lokalGesendet.value)

watch(() => props.serverError, (e) => {
  if (e && !pDone.value) lokalGesendet.value = false
})

watch(pDone, (done) => {
  if (done) lokalGesendet.value = true
})

function bestaetigen() {
  if (!auswahl.value || erledigt.value) return
  lokalGesendet.value = true
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
  position: relative;
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

.slot-pos {
  position: absolute;
  top: 10px;
  left: 12px;
  font-family: var(--mono);
  font-size: 12px;
  color: var(--fg-3);
  letter-spacing: 0.1em;
}

.symbol:hover:not(:disabled) {
  border-color: var(--green-border);
  background: var(--bg-1);
}

.symbol.active {
  background: var(--green);
  border-color: var(--green);
}

.symbol.active .slot-pos { color: #050a08; }

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
}

.btn-action:disabled { opacity: 0.35; cursor: not-allowed; }

.msg-err {
  font-size: 12px;
  color: var(--red);
  margin: 0;
}
</style>
