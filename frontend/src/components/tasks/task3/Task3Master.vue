<!--
  Task3Master — Leitstand, Aufgabe 3 „Datenrettung" (view.type "rescue_log").

  Der Leitstand hat das Log: Login-Name in Hex (für die Vorderseite), Backup-Jobs
  (für die Rückseite) und den Schlüsselbund. Einzige Eingabe: k eintragen (set_key),
  danach sehen es alle. Umgerechnet wird hier nichts – das ist Teil des Rätsels.
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Datenrettung</h2>
      <span class="role">Leitstand</span>
    </header>

    <p class="hint">
      Lies den anderen dein Log vor: Login für die Vorderseite, Backups für die Rückseite.
      Die Schlüssel-Nr. steht auf der Platte der Rückseite – such den gültigen Schlüssel (⑤) und trag k ein.
    </p>

    <div v-if="!view" class="empty">Warte auf Task-Daten …</div>

    <div v-else class="body">
      <div class="main-col">
        <section class="panel">
          <span class="panel-label">Zugangsdaten Backup-Terminal</span>
          <div class="login">
            <span class="login-label">BENUTZER</span>
            <span v-for="(h, i) in view.login_hex" :key="i" class="login-hex">{{ h }}</span>
          </div>
        </section>

        <section class="panel">
          <span class="panel-label">Backup-Jobs</span>
          <table class="log-table">
            <thead>
              <tr><th>Datum</th><th>Platte</th><th>Status</th></tr>
            </thead>
            <tbody>
              <tr
                v-for="b in view.backups"
                :key="b.serial"
                class="backup-row"
                :class="{ 'is-bad': b.status !== 'OK' }"
              >
                <td>{{ b.date }}</td>
                <td>{{ b.serial }}</td>
                <td class="status">{{ b.status }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="panel keyring">
          <span class="panel-label">Schlüsselbund</span>
          <table class="log-table">
            <thead>
              <tr><th>Nr.</th><th>Schlüssel k</th><th>Status</th></tr>
            </thead>
            <tbody>
              <tr
                v-for="(s, i) in view.keys"
                :key="i"
                class="key-row"
                :class="{ 'is-bad': s.status !== 'gültig' }"
              >
                <td>{{ s.nr }}</td>
                <td class="bits">{{ s.k }}</td>
                <td class="status">{{ s.status }}</td>
              </tr>
            </tbody>
          </table>

          <!-- k eintragen (Regel ⑤): danach sehen es alle -->
          <p v-if="view.key" class="key-set">Schlüssel eingetragen · k = {{ view.key }}</p>
          <div v-else class="key-form">
            <label class="key-label" for="k-eingabe">k eintragen</label>
            <input
              id="k-eingabe"
              v-model="kEingabe"
              class="key-input"
              inputmode="numeric"
              maxlength="1"
              placeholder="k"
              :disabled="sending"
              @keyup.enter="eintragen"
            />
            <button class="key-btn" type="button" :disabled="!kEingabe.trim() || sending" @click="eintragen">
              {{ sending ? 'Prüfe …' : 'Eintragen' }}
            </button>
          </div>
          <p v-if="serverError && !view.key" class="msg-err">{{ serverError }}</p>
        </section>
      </div>

      <aside v-if="view.note" class="note-col">
        <span class="panel-label">Dein Teil der Anleitung</span>
        <TornNote :note="view.note" :seed="noteSeed" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import TornNote from '../../TornNote.vue'

const props = defineProps({
  view: { type: Object, default: null },
  serverError: { type: String, default: '' },
  // gleiche Aufgabe → gleiche Risskante
  noteSeed: { type: String, default: '' },
})
const emit = defineEmits(['solved'])

const kEingabe = ref('')
const sending = ref(false)

// Antwort vom Server: falsches k → wieder frei; richtiges → view.key ist gesetzt
watch(() => props.serverError, (e) => { if (e) { sending.value = false; kEingabe.value = '' } })
watch(() => props.view?.key, () => { sending.value = false })

function eintragen() {
  const k = kEingabe.value.trim()
  if (!k || sending.value) return
  sending.value = true
  emit('solved', { target: 'set_key', value: k })
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
  grid-template-columns: minmax(0, 1fr) minmax(300px, 420px);
  gap: 24px;
  overflow: auto;
}

.main-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 22px;
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

.login {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 14px;
  padding: 14px 18px;
  background: var(--bg);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
}

.login-label { font-size: 13px; color: var(--fg-3); letter-spacing: 0.15em; }
.login-hex { font-size: 26px; font-weight: 700; color: var(--green); letter-spacing: 0.05em; }

.log-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 16px;
}

.log-table th {
  padding: 8px 14px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: var(--fg-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--border-2);
}

.log-table td {
  padding: 8px 14px;
  color: var(--fg);
  border-top: 1px dashed var(--border-2);
}

.log-table .bits { letter-spacing: 0.2em; color: var(--green); font-weight: 700; }
.log-table .status { font-weight: 700; color: var(--green); }
.log-table .is-bad .status { color: var(--red); }

.key-form { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; }
.key-label { font-size: 13px; color: var(--fg-2); letter-spacing: 0.1em; text-transform: uppercase; }
.key-input {
  width: 72px;
  padding: 10px 12px;
  background: var(--bg);
  border: 1px solid var(--border-3);
  color: var(--green);
  font-family: var(--mono);
  font-size: 26px;
  text-align: center;
}
.key-btn {
  padding: 12px 20px;
  background: var(--green-bg);
  border: 1px solid var(--green-border);
  color: var(--green);
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.1em;
  cursor: pointer;
}
.key-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.key-set { margin: 0; font-family: var(--mono); font-size: 22px; font-weight: 700; color: var(--green); }
.msg-err { margin: 0; font-size: 13px; color: var(--red); }

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
