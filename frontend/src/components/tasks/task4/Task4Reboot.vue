<!--
  Task4Reboot — Finale „Neustart" (view.type "reboot").

  Jede Rolle sieht genau eine Ziffer des Neustart-Codes und sagt sie dem Leitstand.
  Nur der Leitstand hat das Terminal (view.terminal) und gibt den Code ein.

  Die Komponente prüft nichts selbst: VaultDoor meldet den eingestellten Code,
  die Task reicht ihn als `solved` an PlayerScreen weiter (target "reboot_code").
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Neustart</h2>
      <span class="role">{{ rollenName }}</span>
    </header>

    <div class="body" :class="{ 'body--terminal': terminal }">
      <section class="digit-panel">
        <span class="panel-label">Deine Ziffer</span>
        <div class="digit" aria-live="polite">{{ ziffer }}</div>
        <p class="digit-hint">Deine Ziffer – sag sie dem Leitstand</p>
      </section>

      <section v-if="terminal" class="terminal-panel">
        <span class="panel-label">Neustart-Terminal</span>

        <VaultDoor mode="input" :state="vaultState" @unlock="onUnlock" />

        <p class="order-hint">Ziffern in Aufgabenreihenfolge: Alarm – Löschprotokoll – Datenrettung</p>
        <p v-if="state === 'error'" class="msg-err">{{ serverError || 'Falscher Code' }}</p>
      </section>

      <section v-else class="wait-panel">
        <span class="panel-label">Terminal</span>
        <p class="wait-hint">Der Leitstand tippt den Code ein …</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import VaultDoor from '../../VaultDoor.vue'

const props = defineProps({
  view: { type: Object, default: null },
  role: { type: String, default: '' },
  serverError: { type: String, default: '' },
  inputResultNonce: { type: Number, default: 0 },
  victory: { type: Boolean, default: false },
})
const emit = defineEmits(['solved'])

const state = ref('locked')
let fehlerTimer = null

const terminal = computed(() => !!props.view?.terminal)
const ziffer = computed(() => {
  const d = props.view?.digit
  return d === null || d === undefined ? '–' : String(d)
})

const rollenName = computed(() => {
  if (props.role === 'MASTER') return 'Leitstand'
  if (props.role === 'P1') return 'Vorderseite'
  if (props.role === 'P2') return 'Rückseite'
  return terminal.value ? 'Leitstand' : ''
})

// Der Tresor zeigt den Sieg, sobald das Spiel gewonnen ist.
const vaultState = computed(() => (props.victory ? 'open' : state.value))

function fehlerZeigen(text) {
  state.value = 'error'
  clearTimeout(fehlerTimer)
  // Kurz rot zeigen, dann wieder Eingabe freigeben.
  fehlerTimer = setTimeout(() => {
    if (state.value === 'error') state.value = 'locked'
  }, 900)
}

watch(
  () => props.serverError,
  (e) => {
    if (e && state.value === 'checking') fehlerZeigen(e)
  },
)

watch(
  () => props.victory,
  (sieg) => {
    if (sieg) {
      clearTimeout(fehlerTimer)
      state.value = 'open'
    }
  },
)

onBeforeUnmount(() => clearTimeout(fehlerTimer))

function onUnlock(code) {
  if (state.value === 'checking' || state.value === 'open') return
  clearTimeout(fehlerTimer)
  state.value = 'checking'
  emit('solved', { player: 'MASTER', value: code })
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
  margin-bottom: 18px;
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

.body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: stretch;
}

.digit-panel,
.terminal-panel,
.wait-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 24px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
  min-height: 0;
}

.panel-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.digit {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--mono);
  font-size: 180px;
  line-height: 1;
  font-weight: 700;
  color: var(--green);
  text-shadow: 0 0 48px rgba(0, 255, 102, 0.35);
  font-variant-numeric: tabular-nums;
}

.digit-hint {
  margin: 0;
  font-family: var(--mono);
  font-size: 14px;
  color: var(--fg-2);
  text-align: center;
  letter-spacing: 0.05em;
}

.terminal-panel { overflow-y: auto; }

.order-hint {
  margin: 0;
  font-family: var(--mono);
  font-size: 13px;
  color: var(--fg-2);
  letter-spacing: 0.05em;
}

.wait-panel { justify-content: center; align-items: center; }

.wait-hint {
  margin: 0;
  font-family: var(--mono);
  font-size: 15px;
  color: var(--fg-3);
  text-align: center;
  letter-spacing: 0.05em;
}

.msg-err {
  margin: 0;
  font-family: var(--mono);
  font-size: 12px;
  color: var(--red);
}

@media (max-width: 900px) {
  .body { grid-template-columns: 1fr; }
  .digit { font-size: 120px; }
}
</style>
