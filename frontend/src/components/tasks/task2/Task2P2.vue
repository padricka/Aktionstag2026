<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Freigabe-Passwort setzen</h2>
      <span class="role">P2</span>
    </header>

    <p class="hint">Frage den Master, in welcher Reihenfolge die Teile zusammengesetzt werden.</p>

    <div class="frags">
      <div
        v-for="(frag, i) in sichtbareTeile"
        :key="i"
        class="frag"
        :class="{ missing: !frag }"
      >
        <span class="frag-idx">Teil #{{ i }}</span>
        <span class="frag-value">{{ frag || '—' }}</span>
        <span class="frag-state">{{ frag ? 'verfügbar' : 'wartet' }}</span>
      </div>
    </div>

    <div class="foot">
      <input
        v-model="enteredPassword"
        class="input-pw"
        placeholder="TEIL-TEIL-TEIL"
        :disabled="p2Done"
        @keyup.enter="verifyPassword"
      />
      <button
        class="btn-action"
        :disabled="!enteredPassword.trim() || p2Done"
        @click="verifyPassword"
      >
        {{ p2Done ? 'Akzeptiert' : 'Passwort bestätigen' }}
      </button>
      <p v-if="serverError" class="msg-err">{{ serverError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  fragments:    { type: Array,  default: () => [] },
  lastFragment: { type: String, default: null },
  p2Done:       { type: Boolean, default: false },
  serverError:  { type: String, default: '' },
})

const emit = defineEmits(['solved'])

const enteredPassword = ref('')

const sichtbareTeile = computed(() => {
  const out = [...props.fragments]
  out[2] = props.lastFragment || null
  return out
})

watch(() => props.p2Done, (v) => { if (!v) enteredPassword.value = '' })

// Nach falscher Eingabe: Server-Fehler → Feld leeren, Retry erlauben
watch(() => props.serverError, (e) => {
  if (e) enteredPassword.value = ''
})

function verifyPassword() {
  if (!enteredPassword.value.trim() || props.p2Done) return
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

.frags {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  padding: 8px 0;
}

.frag {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 28px 20px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
}

.frag.missing { border-style: dashed; opacity: 0.55; }

.frag-idx {
  font-size: 12px;
  color: var(--fg-3);
  letter-spacing: 0.2em;
  text-transform: uppercase;
  font-weight: 600;
}

.frag-value {
  font-family: var(--mono);
  font-size: 44px;
  font-weight: 700;
  color: var(--fg);
  letter-spacing: 0.1em;
  line-height: 1;
}

.frag.missing .frag-value {
  font-size: 28px;
  color: var(--fg-3);
  font-weight: 400;
}

.frag-state {
  font-size: 11px;
  color: var(--green);
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.frag.missing .frag-state { color: var(--fg-3); }

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
  letter-spacing: 0.25em;
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

.btn-action:hover:not(:disabled) { background: #4dff8f; }
.btn-action:disabled { opacity: 0.35; cursor: not-allowed; }

.msg-err { font-size: 12px; color: var(--red); margin: 0; }
</style>