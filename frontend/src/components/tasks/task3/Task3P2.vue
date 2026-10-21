<!--
  Task3P2 — Rückseite, Aufgabe 3 „Datenrettung" (view.type "packet_dump").

  Erst die richtige Backup-Platte einlegen (Datum und Status stehen im Log des
  Leitstands), dann erscheinen die Nr. der Platte (4-stellig binär) und zwei Tabellen mit
  je 6 Codes, überschrieben mit einem Schlüssel-Namen. Hier wird nichts gerechnet oder geprüft.
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Backup-Platten</h2>
      <span class="role">Rückseite</span>
    </header>

    <p class="hint">
      <template v-if="!mounted">
        Lege die richtige Backup-Platte ein – welche, sagt Regel ① auf deinem Teil der Anleitung.
        Datum und Status der Backups stehen im Log des Leitstands.
      </template>
      <template v-else>
        Sag dem Leitstand die Nr. der Platte. Welche Tabelle gilt, weiß die Vorderseite (③) –
        lies ihr dann die 6 Codes vor (Regel ④), nicht rechnen.
      </template>
    </p>

    <div class="body">
      <div class="main-col">
        <section v-if="!mounted" class="panel">
          <span class="panel-label">Laufwerksschacht · Platte einlegen</span>
          <div class="disks">
            <button
              v-for="sn in disks"
              :key="sn"
              class="disk"
              type="button"
              :disabled="sending"
              @click="einlegen(sn)"
            >
              <span class="disk-led" aria-hidden="true"></span>
              <span class="disk-sn">{{ sn }}</span>
              <span class="disk-label">BACKUP</span>
            </button>
          </div>
          <p v-if="serverError" class="msg-err">{{ serverError }}</p>
        </section>

        <section v-else class="panel">
          <span class="panel-label">Backup-Platte · Datentabellen</span>
          <div class="key-nr">
            Auf der Platte steht die Nr. <strong>{{ view.key_id }}</strong>
          </div>
          <!-- zwei Tabellen, je mit dem Namen eines Schlüssels – welche gilt, sagt Regel ③ -->
          <div class="code-tables">
            <div v-for="t in tables" :key="t.name" class="code-table">
              <span class="code-table-name">Tabelle {{ t.name }}</span>
              <ol class="code-rows">
                <li v-for="(c, i) in t.rows" :key="i" class="code-row">
                  <span class="row-nr">{{ i + 1 }}</span>
                  <span class="code">{{ c.slice(0, 4) }} {{ c.slice(4) }}</span>
                </li>
              </ol>
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

const sending = ref(false)

const disks = computed(() => props.view?.disks || [])
const mounted = computed(() => !!props.view?.mounted)
const tables = computed(() => props.view?.tables || [])

// Antwort vom Server: falsche Platte → wieder frei, richtige → Tabellen erscheinen
watch(() => props.serverError, (e) => { if (e) sending.value = false })
watch(mounted, () => { sending.value = false })

function einlegen(sn) {
  if (sending.value || mounted.value) return
  sending.value = true
  emit('solved', { target: 'mount_disk', value: sn })
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

.disks {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.disk {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  padding: 18px 16px;
  background: linear-gradient(180deg, var(--bg-3), var(--bg-1));
  border: 1px solid var(--border-3);
  color: var(--fg);
  font-family: var(--mono);
  cursor: pointer;
  text-align: left;
}

.disk:hover:not(:disabled) { border-color: var(--green-border); }
.disk:disabled { opacity: 0.5; cursor: wait; }

.disk-led {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--fg-4);
}

.disk-sn { font-size: 22px; font-weight: 700; letter-spacing: 0.06em; }
.disk-label { font-size: 11px; color: var(--fg-3); letter-spacing: 0.2em; }

.msg-err { margin: 0; font-size: 13px; color: var(--red); }

.key-nr {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg);
  border: 1px solid var(--amber-border);
  font-family: var(--mono);
  font-size: 15px;
  color: var(--fg-2);
}
.key-nr strong { font-size: 24px; color: var(--amber); }

.code-tables {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}
.code-table {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 16px;
  background: var(--bg);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
}
.code-table-name { font-size: 18px; font-weight: 700; color: var(--amber); letter-spacing: 0.08em; }
.code-rows { list-style: none; margin: 0; padding: 0; }
.code-row { display: flex; align-items: baseline; gap: 14px; padding: 6px 0; }
.code-row + .code-row { border-top: 1px dashed var(--border-2); }
.row-nr { font-size: 13px; color: var(--fg-3); min-width: 16px; }
.code { font-size: 26px; font-weight: 700; color: var(--green); letter-spacing: 0.12em; }

.note-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
}

@media (max-width: 1100px) {
  .body { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 600px) {
  .code { font-size: 20px; }
}
</style>
