<!--
  Task3P2 — Rückseite, Aufgabe 3 „Datenrettung" (view.type "packet_dump").

  Die Rückseite sieht die Datenpakete (8 Bit, das erste ist das Prüfbit). Hier wird
  nichts gezählt oder umgerechnet – die Regeln stehen auf den Anleitungs-Teilen.
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Datenpakete</h2>
      <span class="role">Rückseite</span>
    </header>

    <p class="hint">
      Lies den anderen die Pakete vor. Einer davon ist beschädigt. Aus den Zahlen werden mit
      Regel ③ Buchstaben, mit Regel ④ wird das Wort entschlüsselt – den Schlüssel k hat der Leitstand.
    </p>

    <div class="body">
      <section class="panel">
        <span class="panel-label">Speicherauszug · P = Prüfbit</span>
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

      <aside v-if="view?.note" class="note-col">
        <span class="panel-label">Dein Teil der Anleitung</span>
        <TornNote :note="view.note" :seed="noteSeed" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import TornNote from '../../TornNote.vue'

const props = defineProps({
  view: { type: Object, default: null },
  // gleiche Aufgabe → gleiche Risskante
  noteSeed: { type: String, default: '' },
})

const packets = computed(() => props.view?.packets || [])

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

.panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 22px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
  align-self: start;
}

.panel-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

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
