<!--
  Task3P1 — Vorderseite, Aufgabe 3 „Datenrettung" (view.type "rescue_terminal").

  Die Vorderseite hat die ASCII-Tabelle und das Backup-Terminal: erst Login
  (Name steht in Hex im Log des Leitstands), dann das gerettete Wort. Hier wird
  nichts gerechnet oder geprüft: jede Eingabe geht als `solved` an PlayerScreen.
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Backup-Terminal</h2>
      <span class="role">Vorderseite</span>
    </header>

    <p class="hint">
      Das Terminal ist gesperrt. Den Benutzernamen hat der Leitstand – aber in Hex (Regel ②).
      Welche Pakete heil sind, sagt Regel ③ – die Pakete hat die Rückseite. Die ASCII-Tabelle brauchen alle.
    </p>

    <div class="body">
      <div class="main-col">
        <section class="panel terminal" :class="{ 'is-locked': !loggedIn }">
          <span class="panel-label">
            {{ loggedIn ? `Angemeldet · Passwort der Backup-Platte (${wordLen} Buchstaben)` : `Gesperrt · BENUTZER (${loginLen} Buchstaben)` }}
          </span>
          <div class="foot">
            <input
              :key="loggedIn ? 'wort' : 'login'"
              v-model="eingabe"
              class="input-big"
              :class="{ err: !!serverError }"
              :placeholder="loggedIn ? 'WORT' : 'BENUTZER'"
              :maxlength="loggedIn ? wordLen : loginLen"
              :disabled="sending"
              @keyup.enter="absenden"
            />
            <button
              class="btn-action"
              :disabled="!eingabe.trim() || sending"
              @click="absenden"
            >
              {{ sending ? 'Prüfe …' : (loggedIn ? 'Daten retten' : 'Anmelden') }}
            </button>
          </div>
          <p v-if="serverError" class="msg-err">{{ serverError }}</p>
        </section>

        <section class="panel">
          <span class="panel-label">ASCII-Tabelle · Zahl → Buchstabe</span>
          <div class="ascii-table">
            <div v-for="item in tabelle" :key="item.char" class="cell">
              <span class="cell-val">{{ item.dec }}</span>
              <span class="cell-key">{{ item.char }}</span>
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

const wordLen = computed(() => props.view?.word_len || 5)
const loginLen = computed(() => props.view?.login_len || 4)
const loggedIn = computed(() => !!props.view?.logged_in)

// Login geschafft: Feld für das Wort ist frei
watch(loggedIn, (ja) => {
  if (ja) {
    sending.value = false
    eingabe.value = ''
  }
})

const tabelle = computed(() =>
  Object.entries(props.view?.ascii_table || {})
    .map(([char, dec]) => ({ char, dec }))
    .sort((a, b) => a.dec - b.dec),
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
  emit('solved', { target: loggedIn.value ? 'rescue_word' : 'terminal_login', answer: versuch })
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

.terminal.is-locked { border-color: var(--amber-border); }
.terminal.is-locked .panel-label { color: var(--amber); }

.ascii-table {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(62px, 1fr));
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

.cell-val { font-size: 13px; color: var(--fg-3); }
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
