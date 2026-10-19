<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Alarm verifizieren</h2>
      <span class="role">Leitstand</span>
    </header>

    <p class="hint">
      Sag den anderen, an welcher Stelle die LED rot ist. Wie der Code entsteht, sagt Regel ② auf deinem
      Teil der Wartungsnotiz – die Aufkleber dazu kennt nur die Rückseite. Du tippst den Code.
    </p>

    <div v-if="!view" class="empty">Warte auf Task-Daten …</div>

    <div v-else class="body" :class="{ 'with-note': view.note }">
      <section class="panel">
        <span class="panel-label">LED-Leiste</span>
        <div class="led-row" :aria-label="`${slotCount} Stellen`">
          <div v-for="i in slotCount" :key="i" class="led-cell">
            <div
              class="led"
              :class="{ burning: i === burningSlot, blinking: i === burningSlot && blinkt }"
            />
            <span class="led-num">Stelle {{ i }}</span>
          </div>
        </div>
        <p class="led-mode">{{ blinkt ? 'Die LED blinkt' : 'Die LED leuchtet dauerhaft' }}</p>
      </section>

      <section class="panel">
        <span class="panel-label">Farbfolge laut Monitor</span>
        <p class="color-order">
          {{ colorOrderText }}
        </p>
      </section>

      <section class="panel terminal">
        <span class="panel-label">Shutdown-Terminal</span>

        <div v-if="pDone" class="done-badge">Code akzeptiert</div>

        <template v-else>
          <div class="slots">
            <div
              v-for="i in 4"
              :key="i"
              class="slot"
              :class="{ filled: eingabe[i - 1] }"
            >
              <SymbolIcon v-if="eingabe[i - 1]" :name="eingabe[i - 1]" :size="64" />
              <span v-else class="slot-num">{{ i }}</span>
            </div>
          </div>

          <div class="keys">
            <button
              v-for="s in tastatur"
              :key="s"
              class="key"
              :disabled="busy || eingabe.length >= 4"
              :aria-label="`Symbol: ${s}`"
              @click="tippen(s)"
            >
              <SymbolIcon :name="s" :size="48" />
            </button>
          </div>

          <div class="actions">
            <button class="btn-side" :disabled="busy || !eingabe.length" @click="loeschen">
              Löschen
            </button>
            <button
              class="btn-action"
              :disabled="eingabe.length < 4 || busy"
              @click="ausfuehren"
            >
              {{ busy ? 'Prüfen …' : 'Ausführen' }}
            </button>
          </div>
          <p v-if="fehler || serverError" class="msg-err">{{ fehler || serverError }}</p>
        </template>
      </section>

      <aside v-if="view.note" class="note-col">
        <span class="panel-label">Dein Teil der Wartungsnotiz</span>
        <TornNote :note="view.note" :seed="noteSeed" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import SymbolIcon from '../graphic-symbols/SymbolIcon.vue'
import TornNote from '../../TornNote.vue'

const props = defineProps({
  view: { type: Object, default: null },
  serverError: { type: String, default: '' },
  inputResultNonce: { type: Number, default: 0 },
  // gleiche Aufgabe → gleiche Risskante
  noteSeed: { type: String, default: '' },
})
const emit = defineEmits(['solved', 'failed'])

const eingabe = ref([])
const busy = ref(false)
const fehler = ref('')

const slotCount = computed(() => props.view?.slots || 4)
const burningSlot = computed(() => props.view?.burning_slot || null)
const blinkt = computed(() => props.view?.led === 'blinkt')
const colorOrder = computed(() => props.view?.color_order || [])
const pDone = computed(() => !!props.view?.p_done)
const colorOrderText = computed(() => colorOrder.value.join(' → '))
// Tastatur gehört zum Rätsel: kommt gemischt vom Backend (Code-Symbole + Ablenker)
const tastatur = computed(() => props.view?.keyboard || [])

function freigebenNachFehler() {
  busy.value = false
  fehler.value = props.serverError || 'Falsche Eingabe'
  eingabe.value = []
}

watch(() => props.serverError, (e) => {
  if (e && busy.value) freigebenNachFehler()
})

watch(() => props.inputResultNonce, () => {
  if (busy.value && props.serverError) freigebenNachFehler()
})

watch(pDone, (done) => {
  if (done) {
    busy.value = false
    fehler.value = ''
  }
})

function tippen(s) {
  if (pDone.value || busy.value || eingabe.value.length >= 4) return
  fehler.value = ''
  eingabe.value.push(s)
}

function loeschen() {
  if (pDone.value || busy.value || !eingabe.value.length) return
  eingabe.value.pop()
  fehler.value = ''
}

function ausfuehren() {
  if (pDone.value || busy.value || eingabe.value.length < 4) return
  busy.value = true
  fehler.value = ''
  emit('solved', {
    target: 'shutdown_cmd',
    code: [...eingabe.value],
  })
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
  font-size: 17px;
  line-height: 1.45;
  color: var(--fg);
  margin: 0 0 20px 0;
}

.empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fg-3);
}

.body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto 1fr;
  gap: 20px;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
}

.panel.terminal {
  grid-column: 1 / -1;
}

.panel-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.led-row {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 12px 0;
}

.led-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.led-num {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--fg-2);
}

.led {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--bg-3);
  border: 2px solid var(--border-3);
  box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.35);
}

:global(html.theme-girl) .led:not(.burning),
:global(html.theme-light) .led:not(.burning) {
  background: #fff;
  border-color: var(--fg-2);
  box-shadow: inset 0 0 0 8px var(--bg-3);
}

.led.burning {
  background: var(--red);
  border-color: var(--red);
  box-shadow: 0 0 16px rgba(255, 58, 77, 0.55);
}

/* Blinken ist Teil des Rätsels (Regel ② der Notiz): deutlich an/aus, kein Pulsieren */
.led.burning.blinking {
  animation: led-blink 0.9s steps(1) infinite;
}

@keyframes led-blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0.15; }
}

.led-mode {
  margin: 0;
  text-align: center;
  font-family: var(--mono);
  font-size: 13px;
  letter-spacing: 0.08em;
  color: var(--fg-2);
}

/* Mit Zettel: rechts eine eigene Spalte, wie bei Vorder- und Rückseite */
.body.with-note {
  grid-template-columns: 1fr 1fr minmax(300px, 400px);
}

.body.with-note .panel.terminal {
  grid-column: 1 / 3;
}

.note-col {
  grid-column: 3;
  grid-row: 1 / span 2;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
}

@media (max-width: 1100px) {
  .body.with-note { grid-template-columns: 1fr 1fr; }
  .body.with-note .panel.terminal { grid-column: 1 / -1; }
  .note-col { grid-column: 1 / -1; grid-row: auto; }
}

.color-order {
  font-family: var(--mono);
  font-size: 18px;
  font-weight: 700;
  color: var(--fg);
  letter-spacing: 0.08em;
  margin: 0;
  text-align: center;
}

.done-badge {
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--green);
  letter-spacing: 0.12em;
  text-align: center;
  padding: 24px;
  border: 1px solid var(--green-border);
  background: var(--green-bg);
}

.slots {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.slot {
  width: 88px;
  height: 88px;
  background: var(--bg-1);
  border: 2px dashed var(--border-2);
  color: var(--fg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.slot.filled {
  border-style: solid;
  border-color: var(--green-border);
}

.slot-num {
  font-family: var(--mono);
  color: var(--fg-3);
}

.keys {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
}

.key {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 72px;
  background: var(--bg-1);
  color: var(--fg);
  border: 1px solid var(--border-2);
  cursor: pointer;
}

.key:hover:not(:disabled) {
  border-color: var(--green-border);
}

.key:disabled { opacity: 0.35; cursor: not-allowed; }

.actions {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 10px;
  max-width: 520px;
  margin: 0 auto;
}

.btn-side {
  padding: 12px;
  background: transparent;
  color: var(--fg-2);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  cursor: pointer;
}

.btn-side:disabled { opacity: 0.35; cursor: not-allowed; }

.btn-action {
  padding: 12px;
  background: var(--green);
  color: var(--bg);
  border: none;
  font-family: var(--mono);
  font-weight: 700;
  letter-spacing: 0.12em;
  cursor: pointer;
}

.btn-action:disabled { opacity: 0.35; cursor: not-allowed; }

.msg-err {
  font-size: 12px;
  color: var(--red);
  text-align: center;
  margin: 0;
}

@media (prefers-reduced-motion: reduce) {
  /* ohne Animation trägt die Beschriftung .led-mode die Information */
  .led.burning.blinking { animation: none; }
}
</style>
