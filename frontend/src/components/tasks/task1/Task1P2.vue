<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Shutdown-Code eingeben</h2>
      <span class="role">P2</span>
    </header>

    <p class="hint">Frage den Master nach der Reihenfolge der Symbole.</p>

    <div class="slots">
      <div
        v-for="i in codeLength"
        :key="i"
        class="slot"
        :class="{ filled: eingabe[i - 1] }"
      >
        <SymbolIcon v-if="eingabe[i - 1]" :name="eingabe[i - 1]" :size="80" />
        <span v-else class="slot-num">{{ i }}</span>
      </div>
    </div>

    <div class="keys">
      <button
        v-for="s in tastaturSymbole"
        :key="s"
        class="key"
        :disabled="busy || eingabe.length >= codeLength"
        :aria-label="`Symbol: ${s}`"
        @click="tippen(s)"
      >
        <SymbolIcon :name="s" :size="64" />
      </button>
    </div>

    <div class="foot">
      <div class="actions">
        <button class="btn-side" :disabled="busy || !eingabe.length" @click="loeschen">
          Löschen
        </button>
        <button
          class="btn-action"
          :disabled="eingabe.length < codeLength || busy"
          @click="ausfuehren"
        >
          {{ busy ? 'Prüfen …' : 'Ausführen' }}
        </button>
      </div>
      <p v-if="fehler || serverError" class="msg-err">{{ fehler || serverError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import SymbolIcon from '../graphic-symbols/SymbolIcon.vue'
import { CODE_SYMBOLE } from '../graphic-symbols/Symbole.js'

const props = defineProps({
  codeLength: { type: Number, default: 4 },
  symbole:    { type: Array,  default: () => CODE_SYMBOLE },
  serverError: { type: String, default: '' },
  inputResultNonce: { type: Number, default: 0 },
})
const emit = defineEmits(['solved', 'failed'])

const eingabe = ref([])
const busy = ref(false)
const fehler = ref('')

const tastaturSymbole = computed(() => {
  if (props.symbole && props.symbole.length >= 12) return props.symbole
  return CODE_SYMBOLE
})

function freigebenNachFehler() {
  busy.value = false
  fehler.value = props.serverError || 'Falsche Eingabe'
  eingabe.value = []
}

// Server meldet falsch → Eingabe wieder freigeben (vorher blieb UI auf „Akzeptiert“)
watch(() => props.serverError, (e) => {
  if (e && busy.value) freigebenNachFehler()
})

watch(() => props.inputResultNonce, () => {
  if (busy.value && props.serverError) freigebenNachFehler()
})

function tippen(s) {
  if (busy.value || eingabe.value.length >= props.codeLength) return
  fehler.value = ''
  eingabe.value.push(s)
}

function loeschen() {
  if (busy.value || !eingabe.value.length) return
  eingabe.value.pop()
  fehler.value = ''
}

function ausfuehren() {
  if (busy.value || eingabe.value.length < props.codeLength) return
  busy.value = true
  fehler.value = ''
  // Nicht vorab als gelöst markieren — erst Server-Antwort (bei richtig wechselt der Task)
  emit('solved', { player: 'P2', code: [...eingabe.value] })
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
  margin: 0 0 20px 0;
}

.slots {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-bottom: 20px;
  flex-shrink: 0;
}

.slot {
  width: 110px;
  height: 110px;
  background: var(--bg-2);
  border: 2px dashed var(--border-2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.slot.filled {
  border-style: solid;
  border-color: var(--green-border);
}

.slot-num {
  font-family: var(--mono);
  font-size: 18px;
  color: var(--fg-3);
  letter-spacing: 0.1em;
}

.keys {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 12px;
  padding: 4px 0;
  min-height: 0;
}

.key {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
  cursor: pointer;
  min-height: 100px;
  padding: 8px;
  transition: background 0.15s, border-color 0.15s;
}

.key:hover:not(:disabled) {
  border-color: var(--green-border);
  background: var(--bg-1);
}

.key:active:not(:disabled) {
  background: var(--green-bg);
}

.key:disabled { opacity: 0.35; cursor: not-allowed; }

.foot {
  padding-top: 20px;
  margin-top: 16px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.actions {
  display: grid;
  grid-template-columns: 180px 360px;
  gap: 10px;
}

.btn-side {
  padding: 14px;
  background: transparent;
  color: var(--fg-2);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 13px;
  cursor: pointer;
  letter-spacing: 0.1em;
}

.btn-side:hover:not(:disabled) { color: var(--fg); border-color: var(--border-3); }
.btn-side:disabled { opacity: 0.35; cursor: not-allowed; }

.btn-action {
  padding: 14px;
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