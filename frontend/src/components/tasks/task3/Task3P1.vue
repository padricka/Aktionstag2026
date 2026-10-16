<template>
  <div class="task">
    <header class="head">
      <h2 class="title">ASCII-Code entschlüsseln</h2>
      <span class="role">P1</span>
    </header>

    <p class="hint">Wandle die Zahlen in Buchstaben um und gib das Wort ein.</p>

    <div class="codes">
      <div v-for="(code, i) in asciiCodes" :key="i" class="code">
        <span class="code-value">{{ code }}</span>
        <span class="code-label">Code {{ i + 1 }}</span>
      </div>
    </div>

    <div class="foot">
      <input
        v-model="eingabe"
        class="input-big"
        :class="inputClass"
        placeholder="WORT"
        :disabled="isSolved"
        @keyup.enter="absenden"
      />
      <button
        class="btn-action"
        :disabled="!eingabe.trim() || isSolved"
        @click="absenden"
      >
        {{ isSolved ? 'Akzeptiert' : 'Antwort prüfen' }}
      </button>
      <p v-if="ergebnis === 'wrong'" class="msg-err">Falsche Antwort</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  asciiCodes: { type: Array, default: () => [83, 69, 82, 86] }
})
const emit = defineEmits(['solved', 'failed'])

const eingabe = ref('')
const ergebnis = ref(null)
const isSolved = ref(false)

const zielWort = computed(() =>
  props.asciiCodes.map(c => String.fromCharCode(c)).join('').toUpperCase()
)

const inputClass = computed(() => ({
  err: ergebnis.value === 'wrong',
  ok:  ergebnis.value === 'correct',
}))

function absenden() {
  if (!eingabe.value.trim() || isSolved.value) return
  const versuch = eingabe.value.trim().toUpperCase()
  if (versuch === zielWort.value) {
    ergebnis.value = 'correct'
    isSolved.value = true
    emit('solved', { player: 'P1', answer: versuch })
  } else {
    ergebnis.value = 'wrong'
    emit('failed', { player: 'P1', answer: versuch })
    setTimeout(() => { ergebnis.value = null; eingabe.value = '' }, 1500)
  }
}
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

.codes {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  gap: 14px;
  padding: 8px 0;
}

.code {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 20px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
}

.code-value {
  font-family: var(--mono);
  font-size: 56px;
  font-weight: 700;
  color: var(--fg);
  letter-spacing: 0.05em;
  line-height: 1;
}

.code-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.foot {
  padding-top: 20px;
  margin-top: 20px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

/* Schmaler als vorher: 480px statt 720px */
.input-big {
  width: 100%;
  max-width: 480px;
  padding: 14px;
  background: var(--bg);
  color: var(--fg);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 22px;
  text-align: center;
  letter-spacing: 0.3em;
  font-weight: 700;
  outline: none;
}

.input-big:focus { border-color: var(--green-border); }
.input-big.err { border-color: var(--red); color: var(--red); }
.input-big.ok  { border-color: var(--green-border); color: var(--green); }

.btn-action {
  padding: 14px 56px;
  background: var(--green);
  color: #050a08;
  border: none;
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.15em;
  cursor: pointer;
}

.btn-action:hover:not(:disabled) { background: #4dff8f; }
.btn-action:disabled { opacity: 0.35; cursor: not-allowed; }

.msg-err { font-size: 12px; color: var(--red); margin: 0; }
</style>