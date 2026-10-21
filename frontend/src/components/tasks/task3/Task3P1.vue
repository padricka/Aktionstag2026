<!--
  Task3P1 — Vorderseite, Aufgabe 3 „Datenrettung" (view.type "rescue_terminal").

  Die Vorderseite hat die Code-Tabelle (8-stelliger Code → Buchstabe, frei erfunden) und
  das Backup-Terminal. Die Rückseite liest Codes vor, hier wird nur nachgeschlagen – nichts
  gerechnet. Kein Login. Das Wort geht als `solved` an PlayerScreen, geprüft wird im Backend.
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Backup-Terminal</h2>
      <span class="role">Vorderseite</span>
    </header>

    <p class="hint">
      Welche Tabelle der Rückseite gilt, sagt Regel ③. Die Rückseite liest dir die Codes vor –
      such jeden Code in deiner Code-Tabelle und tipp das Wort ein.
    </p>

    <div class="body">
      <div class="main-col">
        <section class="panel terminal">
          <span class="panel-label">Passwort der Backup-Platte ({{ wordLen }} Buchstaben)</span>
          <div class="foot">
            <input
              v-model="eingabe"
              class="input-big"
              :class="{ err: !!serverError }"
              placeholder="WORT"
              :maxlength="wordLen"
              :disabled="sending"
              @keyup.enter="absenden"
            />
            <button
              class="btn-action"
              :disabled="!eingabe.trim() || sending"
              @click="absenden"
            >
              {{ sending ? 'Prüfe …' : 'Daten retten' }}
            </button>
          </div>
          <p v-if="serverError" class="msg-err">{{ serverError }}</p>
        </section>

        <section class="panel">
          <span class="panel-label">Code-Tabelle · Code → Buchstabe</span>
          <div class="code-table">
            <div v-for="item in tabelle" :key="item.char" class="cell">
              <span class="cell-key">{{ item.char }}</span>
              <span class="cell-val">{{ item.code.slice(0, 4) }} {{ item.code.slice(4) }}</span>
            </div>
          </div>
        </section>
      </div>

      <aside v-if="view?.note" class="note-col">
        <span class="panel-label">Dein Teil der Anleitung</span>
        <TornNote :note="view.note" :seed="noteSeed" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import TornNote from '../../TornNote.vue'

const props = defineProps({
  view: { type: Object, default: null },
  serverError: { type: String, default: '' },
  // gleiche Aufgabe → gleiche Risskante
  noteSeed: { type: String, default: '' },
})
const emit = defineEmits(['solved'])

const eingabe = ref('')
const sending = ref(false)

const wordLen = computed(() => props.view?.word_len || 6)

// A–Z, damit man den Buchstaben schnell findet; daneben der Code (4 + 4 Ziffern, besser lesbar)
const tabelle = computed(() =>
  Object.entries(props.view?.code_table || {})
    .map(([char, code]) => ({ char, code }))
    .sort((a, b) => a.char.localeCompare(b.char)),
)

// Falsche Antwort: Backend meldet serverError, Eingabe leeren und wieder frei.
watch(
  () => props.serverError,
  (e) => {
    if (e && sending.value) {
      sending.value = false
      eingabe.value = ''
    }
  },
)

function absenden() {
  const versuch = eingabe.value.trim()
  if (!versuch || sending.value) return
  sending.value = true
  emit('solved', { target: 'rescue_word', answer: versuch })
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

.hint { font-size: 17px; line-height: 1.45; color: var(--fg); margin: 0 0 24px 0; }

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
  gap: 20px;
  min-width: 0;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 22px;
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

.foot {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.input-big {
  flex: 1;
  min-width: 180px;
  padding: 14px 18px;
  background: var(--bg);
  border: 1px solid var(--border-3);
  color: var(--green);
  font-family: var(--mono);
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.4em;
  text-transform: uppercase;
}

.input-big.err { border-color: var(--red); }
.input-big:disabled { opacity: 0.6; }

.btn-action {
  padding: 14px 24px;
  background: var(--green-bg);
  border: 1px solid var(--green-border);
  color: var(--green);
  font-family: var(--mono);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.1em;
  cursor: pointer;
}

.btn-action:disabled { opacity: 0.5; cursor: not-allowed; }

.msg-err { margin: 0; font-size: 13px; color: var(--red); }



.code-table {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(118px, 1fr));
  gap: 6px;
}

.cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 4px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
}

.cell-val { font-size: 15px; color: var(--green); letter-spacing: 0.08em; }
.cell-key { font-size: 20px; font-weight: 700; color: var(--fg); }

.note-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
}

@media (max-width: 1100px) {
  .body { grid-template-columns: minmax(0, 1fr); }
}
</style>
