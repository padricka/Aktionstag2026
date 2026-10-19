<!--
  Task3P2 — Rückseite, Aufgabe 3 „Datenrettung" (view.type "packet_dump").

  Erst die richtige Backup-Platte einlegen (Datum und Status stehen im Log des
  Leitstands), dann erscheinen die Datenpakete (8 Bit, das erste ist das Prüfbit)
  und die Key-ID im Paket-Kopf. Hier wird nichts gezählt, umgerechnet oder geprüft.
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
        Lies den anderen die Pakete und die Key-ID vor. Welcher Schlüssel gilt, sagt Regel ⑤ –
        den Schlüsselbund hat der Leitstand.
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
          <span class="panel-label">Speicherauszug · P = Prüfbit</span>
          <div class="key-id">
            Paket-Kopf · KEY-ID <strong>{{ view.key_id }}</strong>
          </div>
          <ol class="packets">
            <li v-for="(p, i) in packets" :key="i" class="packet">
              <span class="packet-nr">Paket {{ i + 1 }}</span>
              <span class="packet-bits">
                <span class="packet-p" title="Prüfbit">{{ p[0] }}</span>
                <span class="packet-data">{{ gruppiert(p.slice(1)) }}</span>
              </span>
            </li>
          </ol>
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
const packets = computed(() => props.view?.packets || [])

// Antwort vom Server: falsche Platte → wieder frei, richtige → Pakete erscheinen
watch(() => props.serverError, (e) => { if (e) sending.value = false })
watch(mounted, () => { sending.value = false })

function einlegen(sn) {
  if (sending.value || mounted.value) return
  sending.value = true
  emit('solved', { target: 'mount_disk', value: sn })
}

// 7 Datenbits lesbarer: 3 + 4 (passt zu 64 32 16 | 8 4 2 1)
function gruppiert(bits) {
  return `${bits.slice(0, 3)} ${bits.slice(3)}`
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

.key-id {
  padding: 12px 16px;
  background: var(--bg);
  border: 1px solid var(--amber-border);
  font-family: var(--mono);
  font-size: 15px;
  color: var(--fg-2);
  letter-spacing: 0.1em;
}

.key-id strong { font-size: 26px; color: var(--amber); margin-left: 8px; letter-spacing: 0.2em; }

.packets {
  list-style: none;
  margin: 0;
  padding: 10px 0;
  background: var(--bg);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
}

.packet {
  display: flex;
  align-items: baseline;
  gap: 24px;
  padding: 10px 20px;
}

.packet + .packet { border-top: 1px dashed var(--border-2); }

.packet-nr { font-size: 13px; color: var(--fg-3); min-width: 70px; }

.packet-bits {
  display: flex;
  align-items: baseline;
  gap: 14px;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.18em;
}

.packet-p {
  color: var(--amber);
  padding-right: 14px;
  border-right: 2px solid var(--border-3);
}

.packet-data { color: var(--green); white-space: pre; }

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
  .packet-bits { font-size: 22px; }
}
</style>
