<!--
  Task3P1 — Vorderseite, Aufgabe 3 „Datenrettung" (view.type "ascii_puzzle").

  Die Vorderseite sieht das Wort als ASCII-Zahlen und die Tabellenhälfte N–Z.
  Die Hälfte A–M sowie die oberen Stellenwerte (128/64/32/16) stehen nur beim
  Leitstand — deshalb ist die Lösung hier bewusst NICHT berechenbar:
  jede Eingabe geht als `solved` an PlayerScreen, geprüft wird im Backend.
  Erst `view.button_unlocked` schaltet den Sync-Knopf frei.
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">ASCII-Code entschlüsseln</h2>
      <span class="role">Vorderseite</span>
    </header>

    <p class="hint">
      Wandle die Zahlen in Buchstaben um und gib das Wort ein.
      Die Tabelle A–M und die oberen Stellenwerte stehen beim Leitstand.
    </p>

    <div class="body">
      <section class="col">
        <div class="codes">
          <div v-for="(code, i) in asciiCodes" :key="i" class="code">
            <span class="code-value">{{ code }}</span>
            <span class="code-label">Code {{ i + 1 }}</span>
          </div>
        </div>

        <section class="panel">
          <span class="panel-label">Deine Tabellenhälfte · N–Z</span>
          <div class="grid ascii-table">
            <div v-for="item in asciiHalf" :key="item.char" class="cell">
              <span class="cell-key">{{ item.char }}</span>
              <span class="cell-val">{{ item.dec }}</span>
            </div>
          </div>
        </section>

        <div class="foot">
          <input
            v-model="eingabe"
            class="input-big"
            :class="inputClass"
            placeholder="WORT"
            :disabled="sending || unlocked"
            @keyup.enter="absenden"
          />
          <button
            class="btn-action"
            :disabled="!eingabe.trim() || sending || unlocked"
            @click="absenden"
          >
            {{ unlocked ? 'Akzeptiert' : (sending ? 'Prüfe …' : 'Antwort prüfen') }}
          </button>
          <p v-if="serverError && !unlocked" class="msg-err">{{ serverError }}</p>
          <p v-if="unlocked" class="msg-ok">Wort akzeptiert – Sync-Knopf ist frei.</p>
        </div>
      </section>

      <aside class="col sync-col">
        <span class="panel-label">Gemeinsame Rettung</span>
        <SyncButton
          v-if="unlocked"
          :unlocked="true"
          :state="syncState"
          :window-ms="SYNC_WINDOW_MS"
          @press="drueckeSync"
        />
        <p v-else class="sync-locked">
          Der Sync-Knopf ist verplombt. Erst das Wort lösen – dann drücken beide
          Seiten innerhalb von 3 Sekunden.
        </p>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import SyncButton from '../../SyncButton.vue'
import { SYNC_WINDOW_MS, useSyncWindow } from '../../../composables/useSyncWindow.js'

const props = defineProps({
  asciiCodes: { type: Array, default: () => [83, 69, 82, 86] },
  view: { type: Object, default: null },
  serverError: { type: String, default: '' },
})
const emit = defineEmits(['solved'])

const eingabe = ref('')
const sending = ref(false)
const { state: syncState, begin: syncBegin } = useSyncWindow()

// Codiertes Wort: kommt fertig vom Server.
const asciiCodes = computed(() => props.view?.ascii_codes || props.asciiCodes)

// Eigene Tabellenhälfte (N–Z) aus dem view; nichts wird hier gerechnet.
const asciiHalf = computed(() =>
  Object.entries(props.view?.ascii_half || {})
    .map(([char, dec]) => ({ char, dec }))
    .sort((a, b) => a.dec - b.dec),
)

// Erst der Server schaltet frei.
const unlocked = computed(() => !!props.view?.button_unlocked)

const inputClass = computed(() => ({ err: !!props.serverError && !unlocked.value }))

// Falsche Antwort: Backend meldet serverError, Eingabe wieder frei.
watch(
  () => props.serverError,
  (e) => {
    if (e && sending.value) {
      sending.value = false
      eingabe.value = ''
    }
  },
)

watch(unlocked, (frei) => { if (frei) sending.value = false })

function absenden() {
  const versuch = eingabe.value.trim()
  if (!versuch || sending.value || unlocked.value) return
  // Keine Prüfung im Browser: jede Antwort geht zum Backend.
  sending.value = true
  emit('solved', { player: 'P1', answer: versuch })
}

function drueckeSync() {
  if (!unlocked.value) return
  if (!syncBegin()) return
  emit('solved', { target: 'sync_button' })
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

.hint { font-size: 13px; color: var(--fg-3); margin: 0 0 18px 0; }

.body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 420px);
  gap: 24px;
}

.col {
  display: flex;
  flex-direction: column;
  min-height: 0;
  gap: 16px;
}

.codes {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  gap: 12px;
  flex-shrink: 0;
}

.code {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 10px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
}

.code-value {
  font-family: var(--mono);
  font-size: 40px;
  font-weight: 700;
  color: var(--fg);
  letter-spacing: 0.05em;
  line-height: 1;
}

.code-label {
  font-size: 10px;
  color: var(--fg-3);
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
  min-height: 0;
  overflow-y: auto;
}

.panel-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.grid {
  display: grid;
  gap: 6px;
  align-content: start;
}

.ascii-table { grid-template-columns: repeat(4, 1fr); }

.cell {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
}

.cell-key { font-size: 15px; font-weight: 700; color: var(--fg); }
.cell-val { font-size: 14px; font-weight: 700; color: var(--green); }

.foot {
  padding-top: 16px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

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
.msg-ok { font-size: 12px; color: var(--green); margin: 0; letter-spacing: 0.05em; }

.sync-col {
  justify-content: center;
  overflow-y: auto;
  padding: 16px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
}

.sync-locked {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--fg-3);
  text-align: center;
  letter-spacing: 0.03em;
}

@media (max-width: 1100px) {
  .body { grid-template-columns: 1fr; overflow-y: auto; }
  .sync-col { justify-content: flex-start; }
  .code-value { font-size: 30px; }
}
</style>
