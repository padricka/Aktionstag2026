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
      <section class="desk">
        <ControlDesk
          :valves="valves"
          :colors="colors"
          :step="step"
          :sequence-len="sequenceLen"
          :state="panelState"
          @submit="ausloesen"
        />
      </section>

      <aside class="side">
        <span class="panel-label">Dein Notizzettel</span>
        <div class="clue">
          <span>Schritt {{ clue.step }}</span>
          <strong>{{ clue.valve }} · {{ clue.color }}</strong>
        </div>

        <div v-if="pDone" class="result">
          <span class="panel-label">Letztes Passwort-Fragment</span>
          <span class="fragment-dots">{{ dotsLabel(lastFragment?.dots) }}</span>
          <p class="fragment-text">{{ lastFragment?.text || '–' }}</p>
          <p class="result-hint">Der Rückseite mitteilen (Punkte = Reihenfolge).</p>
        </div>
      </aside>
    </div>

    <p v-if="serverError && panelState === 'error'" class="msg-err">{{ serverError }}</p>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import ControlDesk from '../../ControlDesk.vue'

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
})

const emit = defineEmits(['solved'])

const FEHLER_MS = 1200

const lokalGesendet = ref(false)
const fehlerAktiv = ref(false)
let fehlerTimer = null

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

// Panel ist reine Darstellung: "checking" hält es gesperrt, bis der Server antwortet.
const panelState = computed(() => {
  if (pDone.value) return 'done'
  if (fehlerAktiv.value) return 'error'
  if (lokalGesendet.value) return 'checking'
  return 'idle'
})

function dotsLabel(n) {
  const count = Math.max(0, Number(n) || 0)
  return '●'.repeat(count) || '–'
}

function fehlerZeigen() {
  fehlerAktiv.value = true
  if (fehlerTimer) clearTimeout(fehlerTimer)
  fehlerTimer = setTimeout(() => {
    fehlerAktiv.value = false
    fehlerTimer = null
  }, FEHLER_MS)
}

function fehlerBeenden() {
  if (fehlerTimer) { clearTimeout(fehlerTimer); fehlerTimer = null }
  fehlerAktiv.value = false
}

watch(() => props.serverError, (e) => {
  if (e && !pDone.value) {
    lokalGesendet.value = false
    fehlerZeigen()
  }
})

// Nächster Schritt vom Server = die Prüfung ist durch, wieder freigeben.
watch(step, () => { lokalGesendet.value = false })

watch(pDone, (done) => {
  if (done) {
    lokalGesendet.value = true
    fehlerBeenden()
  }
})

onUnmounted(() => {
  if (fehlerTimer) { clearTimeout(fehlerTimer); fehlerTimer = null }
})

// "V-32:RED" vom Steuerpult -> { valve, color } wie bisher.
function ausloesen(wert) {
  const [valve, color] = String(wert || '').split(':')
  if (!valve || !color || pDone.value || lokalGesendet.value) return
  fehlerBeenden()
  lokalGesendet.value = true
  emit('solved', { valve, color })
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
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 20px;
  align-items: center;
  overflow: auto;
}

.desk {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  padding: 8px 0;
}

.side {
  display: flex;
  flex-direction: column;
  gap: 14px;
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

.result {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px;
  background: var(--green-bg);
  border: 1px solid var(--green-border);
}

.fragment-dots {
  font-size: 20px;
  letter-spacing: 0.2em;
  color: var(--amber, #ffb830);
}

.fragment-text {
  font-family: var(--mono);
  font-size: 34px;
  font-weight: 700;
  color: var(--green);
  margin: 0;
  letter-spacing: 0.12em;
}

.result-hint { font-size: 12px; color: var(--fg-3); margin: 0; text-align: center; }

.msg-err {
  font-size: 12px;
  color: var(--red);
  margin: 10px 0 0 0;
  text-align: center;
  flex-shrink: 0;
}

@media (max-width: 860px) {
  .body {
    grid-template-columns: minmax(0, 1fr);
    align-items: start;
  }
}
</style>
