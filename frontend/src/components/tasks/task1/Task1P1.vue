<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Hauptschalter</h2>
      <span class="role">Vorderseite</span>
    </header>

    <p class="hint">
      Frag den Leitstand, welcher Steckplatz brennt – kapp das Kabel mit diesem Symbol.
    </p>

    <div class="body">
      <WirePanel
        :wires="wires"
        :seconds="timeLeft"
        :state="panelState"
        @cut="kappen"
      />
    </div>

    <p v-if="serverError && panelState === 'error'" class="msg-err">{{ serverError }}</p>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import WirePanel from '../../WirePanel.vue'

const props = defineProps({
  symbole: { type: Array, default: () => ['raute', 'dreieck', 'quadrat', 'kreis'] },
  view: { type: Object, default: null },
  serverError: { type: String, default: '' },
  timeLeft: { type: Number, default: null },
})
const emit = defineEmits(['solved', 'failed'])

const FEHLER_MS = 1200

const lokalGesendet = ref(false)
const fehlerAktiv = ref(false)
let fehlerTimer = null

const wires = computed(() => props.view?.switches || props.symbole)
const pDone = computed(() => !!props.view?.p_done)

// Panel ist reine Darstellung: "checking" hält es gesperrt, bis der Server antwortet.
const panelState = computed(() => {
  if (pDone.value) return 'defused'
  if (fehlerAktiv.value) return 'error'
  if (lokalGesendet.value) return 'checking'
  return 'armed'
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

watch(pDone, (done) => {
  if (done) {
    lokalGesendet.value = true
    fehlerBeenden()
  }
})

onUnmounted(fehlerBeenden)

function kappen({ symbol }) {
  if (pDone.value || lokalGesendet.value) return
  lokalGesendet.value = true
  fehlerBeenden()
  emit('solved', { player: 'P1', value: symbol })
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

.body {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 0;
  overflow: auto;
}

.msg-err {
  font-size: 12px;
  color: var(--red);
  margin: 10px 0 0 0;
  text-align: center;
  flex-shrink: 0;
}
</style>
