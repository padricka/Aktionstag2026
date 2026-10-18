<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Ventilpanel</h2>
      <span class="role">Vorderseite</span>
    </header>

    <p class="hint">
      Alle drei haben je einen Schritt — flutet in der Reihenfolge Schritt 1 → 2 → 3.
    </p>

    <div class="body">
      <aside class="side">
        <span class="panel-label">Fortschritt</span>
        <div class="pips">
          <span
            v-for="i in sequenceLen"
            :key="i"
            class="pip"
            :class="{ done: (i - 1) < step, current: (i - 1) === step && !pDone }"
          />
        </div>
        <span class="count">{{ step }} / {{ sequenceLen }}</span>

        <span class="panel-label">Dein Notizzettel</span>
        <div class="clue">
          <span>Schritt {{ clue.step }}</span>
          <strong>{{ clue.valve }} · {{ clue.color }}</strong>
        </div>
      </aside>

      <section class="panel">
        <template v-if="!pDone">
          <span class="panel-label">Nächster Schritt</span>
          <div class="inputs">
            <label class="field">
              <span class="field-label">Ventil</span>
              <select v-model="selectedValve" class="select valve" :disabled="busy">
                <option disabled value="">– wählen –</option>
                <option v-for="v in valves" :key="v" :value="v">{{ v }}</option>
              </select>
            </label>
            <label class="field">
              <span class="field-label">Farbe</span>
              <select v-model="selectedColor" class="select color" :disabled="busy">
                <option disabled value="">– wählen –</option>
                <option v-for="c in colors" :key="c" :value="c">{{ c }}</option>
              </select>
            </label>
          </div>
        </template>

        <div v-else class="result">
          <span class="panel-label">Letztes Passwort-Fragment</span>
          <span class="fragment-dots">{{ dotsLabel(lastFragment?.dots) }}</span>
          <p class="fragment-text">{{ lastFragment?.text || '–' }}</p>
          <p class="result-hint">Der Rückseite mitteilen (Punkte = Reihenfolge).</p>
        </div>
      </section>
    </div>

    <div class="foot">
      <button
        v-if="!pDone"
        class="btn-action"
        :disabled="!selectedValve || !selectedColor || busy"
        @click="submitStep"
      >
        {{ busy ? 'Sende …' : `Schritt ${step + 1} ausführen` }}
      </button>
      <p v-if="serverError && !pDone" class="msg-err">{{ serverError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'

const props = defineProps({
  view: { type: Object, default: null },
  // Legacy-Props (PlayerScreen) — view hat Vorrang
  valves: { type: Array, default: () => ['V-31', 'V-32', 'V-33'] },
  colors: { type: Array, default: () => ['ORANGE', 'RED', 'GREEN'] },
  sequenceLen: { type: Number, default: 3 },
  step: { type: Number, default: 0 },
  lastFragment: { type: [Object, String], default: null },
  p1Done: { type: Boolean, default: false },
  serverError: { type: String, default: '' },
  inputResultNonce: { type: Number, default: 0 },
})

const emit = defineEmits(['solved'])

const selectedValve = ref('')
const selectedColor = ref('')
const busy = ref(false)
let busyTimer = null

const valves = computed(() => props.view?.valves || props.valves)
const colors = computed(() => props.view?.colors || props.colors)
const sequenceLen = computed(() => props.view?.sequence_len ?? props.sequenceLen)
const step = computed(() => props.view?.step ?? props.step)
const clue = computed(() => props.view?.clue || { step: '–', valve: '–', color: '–' })
const pDone = computed(() => !!(props.view?.p_done ?? props.p1Done))
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

function releaseBusy() {
  busy.value = false
  if (busyTimer) { clearTimeout(busyTimer); busyTimer = null }
}

watch(() => props.inputResultNonce, () => releaseBusy())
watch(step, () => {
  selectedValve.value = ''
  selectedColor.value = ''
  releaseBusy()
})
watch(pDone, () => releaseBusy())
onUnmounted(() => { if (busyTimer) clearTimeout(busyTimer) })

function submitStep() {
  if (!selectedValve.value || !selectedColor.value || busy.value || pDone.value) return
  busy.value = true
  emit('solved', { valve: selectedValve.value, color: selectedColor.value })
  if (busyTimer) clearTimeout(busyTimer)
  busyTimer = setTimeout(() => { busy.value = false }, 2000)
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

.body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
}

.side, .panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 24px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
}

.panel { justify-content: center; }

.panel-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.pips { display: flex; gap: 10px; }

.pip {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid var(--border-3);
}

.pip.done { background: var(--green); border-color: var(--green); }
.pip.current { border-color: var(--green); box-shadow: 0 0 0 5px var(--green-bg); }

.count {
  font-family: var(--mono);
  font-size: 26px;
  font-weight: 700;
  color: var(--fg);
  letter-spacing: 0.1em;
}

.clue {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 14px;
  color: var(--fg-2);
}

.clue strong {
  font-size: 18px;
  color: var(--fg);
  letter-spacing: 0.06em;
}

.inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  max-width: 560px;
}

.field { display: flex; flex-direction: column; gap: 6px; }

.field-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.select {
  padding: 14px;
  background: var(--bg);
  color: var(--fg);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 16px;
  cursor: pointer;
  outline: none;
}

.select:focus { border-color: var(--green-border); }

.result {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  background: var(--green-bg);
  border: 1px solid var(--green-border);
  max-width: 400px;
  margin: 0 auto;
}

.fragment-dots {
  font-size: 20px;
  letter-spacing: 0.2em;
  color: var(--amber, #ffb830);
}

.fragment-text {
  font-family: var(--mono);
  font-size: 40px;
  font-weight: 700;
  color: var(--green);
  margin: 0;
  letter-spacing: 0.12em;
}

.result-hint { font-size: 12px; color: var(--fg-3); margin: 0; }

.foot {
  padding-top: 20px;
  margin-top: 20px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

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
