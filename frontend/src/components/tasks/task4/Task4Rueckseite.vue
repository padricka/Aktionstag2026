<!--
  Finale · Rückseite (view.type "repair_back"): zwei Netzteilschächte mit Sicherung
  (ok / durchgebrannt) und das Schild, auf welcher Seite der Warmgang ist (die Vorderseite
  braucht es für den Lüfter). Netzteil antippen, Spannung einstellen, in den Schacht.
  Zuletzt Schlüssel „Strom“ – er kommt als erster.
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Finale · Server reparieren</h2>
      <span class="role">Rückseite</span>
    </header>

    <p class="hint">
      Sag der Vorderseite, auf welcher Seite der Warmgang ist (Schild). Das Netzteil kommt zuletzt –
      stell vorher die Spannung vom Etikett ein (Teilekiste beim Leitstand).
    </p>

    <div v-if="!view" class="empty">Warte auf Task-Daten …</div>

    <div v-else class="body">
      <div class="main-col">
        <!-- was falsch war (vom Server), oben gut sichtbar -->
        <p v-if="serverError" class="msg-err" role="alert">{{ serverError }}</p>
        <section class="panel">
          <span class="panel-label">In deiner Hand</span>
          <div v-if="hand.length" class="hand">
            <div v-for="t in hand" :key="t.id" class="hand-item">
              <button
                class="hand-teil"
                :class="{ 'is-gewaehlt': gewaehlt === t.id }"
                :data-teil="t.id"
                type="button"
                @click="waehlen(t.id)"
              >
                <TeilGrafik :teil="t.id" />
                <span>{{ t.name }}</span>
              </button>
              <button class="zurueck" :data-teil="t.id" type="button" @click="zurueck(t.id)">zurückgeben</button>
            </div>
          </div>
          <p v-else class="hand-leer">Noch nichts – der Leitstand verteilt die Teile.</p>

          <div v-if="gewaehlt === 'psu'" class="spannung">
            <span>Spannungsschalter am Netzteil:</span>
            <button class="spannung-115" :class="{ 'is-an': volt === '115' }" type="button" @click="volt = '115'">115 V</button>
            <button class="spannung-230" :class="{ 'is-an': volt === '230' }" type="button" @click="volt = '230'">230 V</button>
          </div>
        </section>

        <section class="panel">
          <span class="panel-label">Serverschrank · Rückseite</span>
          <div class="rack-rahmen">
            <div class="gang-schild is-warm">
              WARMGANG {{ warmgang === 'links' ? '← LINKS' : 'RECHTS →' }}
              <small>von vorne gesehen · Schild an der Rückwand</small>
            </div>

            <div class="rack-zeile-titel">NETZTEILE</div>
            <div class="nt-schaechte">
              <button
                v-for="s in view.psu_bays"
                :key="s.nr"
                class="nt-schacht"
                :class="{ 'is-ziel': gewaehlt === 'psu', 'is-eingebaut': eingebautIn(s) }"
                :data-sicherung="s.sicherung"
                type="button"
                @click="schachtGewaehlt(s)"
              >
                <span class="nt-nr">PSU-Schacht {{ s.nr }}</span>
                <span class="nt-oeffnung">
                  <TeilGrafik v-if="eingebautIn(s)" teil="psu" />
                </span>
                <span class="sicherung">
                  <i></i>
                  <small>{{ s.sicherung === 'ok' ? 'Sicherung ok' : 'Sicherung durch' }}</small>
                </span>
              </button>
            </div>
          </div>
        </section>

        <section class="panel">
          <span class="panel-label">Hochfahren</span>
          <div class="schluessel-reihe">
            <SchluesselSchalter
              label="Strom"
              :bereit="view.phase === 'start'"
              :gedreht="(view.keys || []).includes('strom')"
              @drehen="emit('eingabe', { target: 'key', value: 'strom' })"
            />
            <p class="schluessel-stand">
              {{ view.phase === 'start' ? `Schlüssel gedreht: ${(view.keys || []).length}/3` : 'Erst alle Teile einbauen.' }}
            </p>
          </div>
        </section>

      </div>

      <aside v-if="view.note" class="note-col">
        <span class="panel-label">Dein Teil der Einbauanleitung</span>
        <TornNote :note="view.note" :seed="noteSeed" />
      </aside>
    </div>

    <div v-if="victory" class="sieg">SERVER FÄHRT HOCH …</div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import TornNote from '../../TornNote.vue'
import TeilGrafik from '../../TeilGrafik.vue'
import SchluesselSchalter from './SchluesselSchalter.vue'

const props = defineProps({
  view: { type: Object, default: null },
  noteSeed: { type: String, default: '' },
  serverError: { type: String, default: '' },
  victory: { type: Boolean, default: false },
})
const emit = defineEmits(['eingabe'])

const gewaehlt = ref(null)
const volt = ref('115')
const hand = computed(() => props.view?.hand || [])
const warmgang = computed(() => props.view?.warmgang || '')

watch(hand, (h) => {
  if (gewaehlt.value && !h.some((t) => t.id === gewaehlt.value)) gewaehlt.value = null
})

// eingebaut: im Schacht mit heiler Sicherung (nur dort lässt der Server es zu)
const eingebautIn = (s) => !!props.view?.installed?.psu && s.sicherung === 'ok'

function waehlen(id) {
  gewaehlt.value = gewaehlt.value === id ? null : id
}

function zurueck(id) {
  emit('eingabe', { target: 'return', value: id })
}

function schachtGewaehlt(s) {
  if (gewaehlt.value !== 'psu') return
  emit('eingabe', { target: 'install_psu', value: `${s.nr}:${volt.value}` })
}
</script>

<style scoped src="./finale.css"></style>
<style scoped>
.spannung { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-family: var(--mono); font-size: 13px; color: var(--fg-2); }
.spannung button {
  padding: 6px 14px;
  background: #1a1d22;
  border: 1px solid var(--border-3);
  color: var(--fg-2);
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}
.spannung button.is-an { border-color: #e6c229; color: #ffd23a; background: rgba(230, 194, 41, 0.12); }

.rack-rahmen {
  display: grid;
  gap: 12px;
  padding: 14px 16px;
  background: linear-gradient(90deg, #101215, #1b1f24 10%, #23272e 90%, #15181c);
  border: 3px solid #2b3038;
  box-shadow: inset 0 0 0 2px #0b0d10;
}
.rack-zeile-titel { font-family: var(--mono); font-size: 10px; letter-spacing: 0.2em; color: #7d8590; }

.gang-schild {
  justify-self: center;
  display: grid;
  justify-items: center;
  gap: 2px;
  padding: 8px 22px;
  font-family: var(--mono);
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.2em;
  color: #fff;
  border: 2px solid rgba(255, 255, 255, 0.6);
}
.gang-schild small { font-size: 10px; letter-spacing: 0.1em; font-weight: 400; opacity: 0.8; }
.gang-schild.is-warm { background: #a8322b; }

.nt-schaechte { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.nt-schacht {
  display: grid;
  gap: 8px;
  padding: 10px;
  background: #0b0d10;
  border: 1px solid #2b3038;
  color: #c9ced6;
  font-family: var(--mono);
  cursor: pointer;
}
.nt-nr { font-size: 13px; font-weight: 700; text-align: left; }
.nt-oeffnung { display: grid; place-items: center; height: 70px; background: #050607; border: 1px dashed #2b3038; }
.nt-oeffnung :deep(.teil) { height: 64px; width: auto; }
.nt-schacht.is-ziel { border-color: var(--green-border); }
.nt-schacht.is-ziel:hover { border-color: var(--green); }
.nt-schacht.is-eingebaut { border-color: var(--green-border); }

/* Sicherung: Glasröhrchen mit Draht – durchgebrannt ist er gerissen und das Glas schwarz */
.sicherung { display: flex; align-items: center; gap: 8px; font-size: 11px; color: var(--fg-2); }
.sicherung i {
  position: relative;
  width: 42px;
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(90deg, #8a929c 0 18%, rgba(220, 230, 240, 0.25) 18% 82%, #8a929c 82%);
  border: 1px solid #5d646e;
}
.sicherung i::after {
  content: '';
  position: absolute;
  left: 18%;
  right: 18%;
  top: 50%;
  height: 1.5px;
  background: #d8c27f;
}
.nt-schacht[data-sicherung='durch'] .sicherung i {
  background: linear-gradient(90deg, #8a929c 0 18%, #1a1a1a 18% 82%, #8a929c 82%);
}
.nt-schacht[data-sicherung='durch'] .sicherung i::after { right: 55%; background: #5a4a2a; }
.nt-schacht[data-sicherung='durch'] .sicherung small { color: var(--red-2); }
</style>
