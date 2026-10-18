<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Freigabe-Passwort</h2>
      <span class="role">Rückseite</span>
    </header>

    <p class="hint">
      Teile eure Fragmente und sortiert nach Punkten (● → ●●●). Das letzte Fragment erscheint erst nach dem Fluten.
    </p>

    <div class="grid">
      <section class="panel">
        <span class="panel-label">Dein Aufkleber · Sequenz</span>
        <div class="clue">
          <span>Schritt {{ clue.step }}</span>
          <strong>{{ clue.valve }} · {{ clue.color }}</strong>
        </div>
      </section>

      <section class="panel">
        <span class="panel-label">Dein Fragment</span>
        <div class="fragment">
          <span class="fragment-dots">{{ dotsLabel(fragment.dots) }}</span>
          <span class="fragment-text">{{ fragment.text }}</span>
        </div>
      </section>

      <section class="panel" :class="{ missing: !lastFragment }">
        <span class="panel-label">Letztes Fragment</span>
        <div class="fragment">
          <template v-if="lastFragment">
            <span class="fragment-dots">{{ dotsLabel(lastFragment.dots) }}</span>
            <span class="fragment-text">{{ lastFragment.text }}</span>
          </template>
          <span v-else class="waiting">wartet auf Fluten …</span>
        </div>
      </section>
    </div>

    <div class="foot">
      <input
        v-model="enteredPassword"
        class="input-pw"
        placeholder="FRAGMENTE ZUSAMMEN"
        :disabled="pDone"
        @keyup.enter="verifyPassword"
      />
      <button
        class="btn-action"
        :disabled="!enteredPassword.trim() || pDone"
        @click="verifyPassword"
      >
        {{ pDone ? 'Akzeptiert' : 'Passwort bestätigen' }}
      </button>
      <p v-if="serverError && !pDone" class="msg-err">{{ serverError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  view: { type: Object, default: null },
  fragments: { type: Array, default: () => [] },
  lastFragment: { type: [Object, String], default: null },
  p2Done: { type: Boolean, default: false },
  serverError: { type: String, default: '' },
})

const emit = defineEmits(['solved'])
const enteredPassword = ref('')

const clue = computed(() => props.view?.clue || { step: '–', valve: '–', color: '–' })
const fragment = computed(() => props.view?.fragment || { dots: 0, text: '–' })
const pDone = computed(() => !!(props.view?.p_done ?? props.p2Done))
const lastFragment = computed(() => {
  const lf = props.view?.last_fragment ?? props.lastFragment
  if (!lf) return null
  if (typeof lf === 'string') return { dots: 0, text: lf }
  return lf
})

function dotsLabel(n) {
  const count = Math.max(0, Number(n) || 0)
  return '●'.repeat(count) || '–'
}

watch(pDone, (v) => { if (!v) enteredPassword.value = '' })
watch(() => props.serverError, (e) => { if (e) enteredPassword.value = '' })

function verifyPassword() {
  if (!enteredPassword.value.trim() || pDone.value) return
  emit('solved', { password: enteredPassword.value.trim() })
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

.hint { font-size: 13px; color: var(--fg-3); margin: 0 0 20px 0; }

.grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
}

.panel.missing { border-style: dashed; opacity: 0.7; }

.panel-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.clue {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 14px;
  color: var(--fg-2);
  flex: 1;
  justify-content: center;
}

.clue strong {
  font-size: 20px;
  color: var(--fg);
}

.fragment {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
}

.fragment-dots {
  font-size: 20px;
  letter-spacing: 0.2em;
  color: var(--amber, #ffb830);
}

.fragment-text {
  font-family: var(--mono);
  font-size: 32px;
  font-weight: 700;
  color: var(--green);
  letter-spacing: 0.1em;
}

.waiting {
  font-family: var(--mono);
  color: var(--fg-3);
  font-size: 14px;
}

.foot {
  padding-top: 20px;
  margin-top: 20px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.input-pw {
  width: 100%;
  max-width: 480px;
  padding: 14px;
  background: var(--bg);
  color: var(--fg);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 20px;
  text-align: center;
  letter-spacing: 0.15em;
  font-weight: 700;
  outline: none;
}

.input-pw:focus { border-color: var(--green-border); }

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

.btn-action:disabled { opacity: 0.35; cursor: not-allowed; }

.msg-err { font-size: 12px; color: var(--red); margin: 0; }
</style>
