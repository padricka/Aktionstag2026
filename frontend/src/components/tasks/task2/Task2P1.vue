<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Löschanlage</h2>
      <span class="role">Vorderseite</span>
    </header>

    <p class="hint">
      Du löschst: Rack und Löschmittel wählen, auslösen. In welcher Reihenfolge, sagt Regel ② auf
      deinem Teil des Löschplans – das Log hat der Leitstand. Ob ein Rack unter Strom steht, siehst nur du.
    </p>

    <div class="body">
      <div class="main-col">
        <section class="desk">
          <ControlDesk
            :valves="racks"
            :colors="agents"
            :step="step"
            :sequence-len="sequenceLen"
            :state="panelState"
            valve-label="Rack"
            color-label="Löschmittel"
            @submit="ausloesen"
          />
        </section>

        <section class="power">
          <span class="panel-label">Strom an den Racks</span>
          <ul class="power-list">
            <li v-for="r in racks" :key="r" class="power-item" :class="{ 'is-on': power[r] }">
              <span class="power-led" aria-hidden="true"></span>
              <span class="power-rack">{{ r }}</span>
              <span class="power-text">{{ power[r] ? 'Strom an' : 'stromlos' }}</span>
            </li>
          </ul>
        </section>

        <div v-if="pDone" class="result">
          Alle Brände gelöscht. Jetzt müssen Leitstand und Rückseite gemeinsam die Freigabe drücken.
        </div>
      </div>

      <aside v-if="view?.note" class="note-col">
        <span class="panel-label">Dein Teil des Löschplans</span>
        <TornNote :note="view.note" :seed="noteSeed" />
      </aside>
    </div>

    <p v-if="serverError && panelState === 'error'" class="msg-err">{{ serverError }}</p>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import ControlDesk from '../../ControlDesk.vue'
import TornNote from '../../TornNote.vue'

const props = defineProps({
  view: { type: Object, default: null },
  serverError: { type: String, default: '' },
  // gleiche Aufgabe → gleiche Risskante
  noteSeed: { type: String, default: '' },
})

const emit = defineEmits(['solved'])

const FEHLER_MS = 1200

const lokalGesendet = ref(false)
const fehlerAktiv = ref(false)
let fehlerTimer = null

const racks = computed(() => props.view?.racks || [])
const agents = computed(() => props.view?.agents || [])
const power = computed(() => props.view?.power || {})
const sequenceLen = computed(() => props.view?.sequence_len ?? 3)
const step = computed(() => props.view?.step ?? 0)
const pDone = computed(() => !!props.view?.p_done)

// Panel ist reine Darstellung: "checking" hält es gesperrt, bis der Server antwortet.
const panelState = computed(() => {
  if (pDone.value) return 'done'
  if (fehlerAktiv.value) return 'error'
  if (lokalGesendet.value) return 'checking'
  return 'idle'
})

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

// "B-02:CO2" vom Steuerpult -> { valve: Rack, color: Löschmittel } (PlayerScreen baut valve_action)
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
  max-width: 1400px;
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
  grid-template-columns: minmax(0, 1fr) minmax(300px, 420px);
  gap: 24px;
  overflow: auto;
}

.main-col {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-width: 0;
}

.desk {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
}

.power {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 20px;
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

.power-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.power-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
}

.power-led {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--bg-3);
  border: 1px solid var(--border-3);
}

.power-item.is-on .power-led {
  background: var(--green);
  box-shadow: 0 0 10px var(--green);
}

.power-rack { font-size: 16px; font-weight: 700; color: var(--fg); }
.power-text { font-size: 12px; color: var(--fg-3); }
.power-item.is-on .power-text { color: var(--green); }

.result {
  padding: 16px 18px;
  background: var(--green-bg);
  border: 1px solid var(--green-border);
  color: var(--green);
  font-size: 14px;
  text-align: center;
}

.note-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
}

.msg-err {
  font-size: 12px;
  color: var(--red);
  margin: 10px 0 0 0;
  text-align: center;
  flex-shrink: 0;
}

@media (max-width: 1100px) {
  .body { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 600px) {
  .power-list { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
