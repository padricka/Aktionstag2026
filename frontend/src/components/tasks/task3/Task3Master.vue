<!--
  Task3Master — Leitstand, Aufgabe 3 „Datenrettung" (view.type "rescue_log").

  Der Leitstand hat das Log: Backup-Jobs (für die Rückseite) und den Schlüsselbund
  (Nr., Name, gültig/gesperrt). Die Nr. auf der Platte rechnet er nach Regel ② um.
  Keine Eingabe – hier wird nichts ausgewählt, das ist Teil des Rätsels.
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Datenrettung</h2>
      <span class="role">Leitstand</span>
    </header>

    <p class="hint">
      Lies der Rückseite die Backups vor. Auf der Platte steht eine 4-stellige Nr. – rechne sie
      mit Regel ② um. Welcher Schlüssel dazu gültig ist, siehst nur du im Schlüsselbund.
    </p>

    <div v-if="!view" class="empty">Warte auf Task-Daten …</div>

    <div v-else class="body">
      <div class="main-col">
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
              <tr><th>Nr.</th><th>Schlüssel</th><th>Status</th></tr>
            </thead>
            <tbody>
              <tr
                v-for="(s, i) in view.keys"
                :key="i"
                class="key-row"
                :class="{ 'is-bad': s.status !== 'gültig' }"
              >
                <td>{{ s.nr }}</td>
                <td class="bits">{{ s.name }}</td>
                <td class="status">{{ s.status }}</td>
              </tr>
            </tbody>
          </table>
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
import TornNote from '../../TornNote.vue'

defineProps({
  view: { type: Object, default: null },
  // gleiche Aufgabe → gleiche Risskante
  noteSeed: { type: String, default: '' },
})
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
