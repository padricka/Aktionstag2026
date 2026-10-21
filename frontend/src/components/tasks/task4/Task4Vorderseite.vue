<!--
  Finale · Vorderseite (view.type "repair_front"): vier Plattenschächte mit LED
  (grün = belegt, rot = defekt, aus = leer) und die Lüfterwand mit einer Lücke.
  Teil in der Hand antippen, dann den Platz – der Lüfter bekommt vorher seine Richtung.
  Teile, die vorne nicht passen, gehen zurück an den Leitstand. Zuletzt Schlüssel „Kühlung“.
-->
<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Finale · Server reparieren</h2>
      <span class="role">Vorderseite</span>
    </header>

    <p class="hint">
      Der Leitstand gibt dir Teile. Tipp ein Teil an, dann den Platz im Rack. Vorher muss der
      Leitstand den Platz auf Wartung schalten – sonst gibt es einen Stromschlag.
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

          <div v-if="gewaehlt === 'fan'" class="richtung">
            <span>Pfeil am Lüfter zeigt nach:</span>
            <button class="richtung-vorne" :class="{ 'is-an': richtung === 'vorne' }" type="button" @click="richtung = 'vorne'">
              ↙ vorne (zu dir)
            </button>
            <button class="richtung-hinten" :class="{ 'is-an': richtung === 'hinten' }" type="button" @click="richtung = 'hinten'">
              ↗ hinten (ins Rack)
            </button>
          </div>
        </section>

        <section class="panel rack-vorne">
          <span class="panel-label">Rack · Vorderseite</span>

          <div class="rack-rahmen">
            <div class="rack-zeile-titel">FESTPLATTEN</div>
            <div class="schaechte">
              <button
                v-for="s in view.bays"
                :key="s.nr"
                class="schacht"
                :class="{ 'is-ziel': gewaehlt === 'disk' && s.led === 'aus' }"
                :data-led="s.led"
                type="button"
                @click="schachtGewaehlt(s)"
              >
                <span class="schacht-nr">{{ s.nr }}</span>
                <span class="schacht-front">
                  <i v-if="s.led !== 'aus'" class="schacht-griff"></i>
                </span>
                <span class="schacht-led"></span>
              </button>
            </div>

            <div class="rack-zeile-titel">LÜFTER</div>
            <div class="luefterwand">
              <button
                v-for="l in view.fan_slots"
                :key="l.nr"
                class="luefter-platz"
                :class="{ 'is-luecke': !l.belegt, 'is-ziel': gewaehlt === 'fan' && !l.belegt }"
                type="button"
                @click="luefterGewaehlt(l)"
              >
                <TeilGrafik v-if="l.belegt" teil="fan" dreht />
                <span v-else class="luecke">Platz {{ l.nr }} · leer</span>
                <span class="luefter-nr">{{ l.nr }}</span>
              </button>
            </div>
          </div>
        </section>

        <section class="panel">
          <span class="panel-label">Hochfahren</span>
          <div class="schluessel-reihe">
            <SchluesselSchalter
              label="Kühlung"
              :bereit="view.phase === 'start'"
              :gedreht="(view.keys || []).includes('kuehlung')"
              @drehen="emit('eingabe', { target: 'key', value: 'kuehlung' })"
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

const gewaehlt = ref(null)      // Teil in der Hand, das gerade eingebaut werden soll
const richtung = ref('vorne')   // Pfeil am Lüfter
const hand = computed(() => props.view?.hand || [])

// Teil weg (eingebaut oder zurück): Auswahl aufheben
watch(hand, (h) => {
  if (gewaehlt.value && !h.some((t) => t.id === gewaehlt.value)) gewaehlt.value = null
})

function waehlen(id) {
  gewaehlt.value = gewaehlt.value === id ? null : id
}

function zurueck(id) {
  emit('eingabe', { target: 'return', value: id })
}

function schachtGewaehlt(s) {
  if (gewaehlt.value !== 'disk') return
  emit('eingabe', { target: 'install_disk', value: String(s.nr) })
}

function luefterGewaehlt(l) {
  if (gewaehlt.value !== 'fan' || l.belegt) return
  emit('eingabe', { target: 'install_fan', value: `${l.nr}:${richtung.value}` })
}
</script>

<style scoped src="./finale.css"></style>
<style scoped>
.richtung { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-family: var(--mono); font-size: 13px; color: var(--fg-2); }
.richtung button {
  padding: 6px 12px;
  background: var(--bg);
  border: 1px solid var(--border-3);
  color: var(--fg-2);
  font-family: var(--mono);
  font-size: 13px;
  cursor: pointer;
}
.richtung button.is-an { border-color: var(--green); color: var(--green); background: var(--green-bg); }

/* Rack-Front */
.rack-rahmen {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  background: linear-gradient(90deg, #15181c, #23272e 10%, #1b1f24 90%, #101215);
  border: 3px solid #2b3038;
  box-shadow: inset 0 0 0 2px #0b0d10;
}
.rack-zeile-titel { font-family: var(--mono); font-size: 10px; letter-spacing: 0.2em; color: #7d8590; }

.schaechte { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.schacht {
  position: relative;
  display: grid;
  grid-template-columns: 22px 1fr 14px;
  align-items: center;
  gap: 6px;
  height: 46px;
  padding: 0 8px;
  background: #0b0d10;
  border: 1px solid #2b3038;
  cursor: pointer;
}
.schacht-nr { font-family: var(--mono); font-size: 16px; font-weight: 700; color: #c9ced6; }
.schacht-front { height: 30px; background: #050607; border-radius: 2px; display: grid; place-items: center; }
.schacht[data-led='gruen'] .schacht-front,
.schacht[data-led='rot'] .schacht-front { background: linear-gradient(180deg, #4a505a, #2f343c); }
.schacht-griff { width: 60%; height: 5px; background: #15181c; border-radius: 3px; }
.schacht-led { width: 10px; height: 10px; border-radius: 50%; background: #1d2228; }
.schacht[data-led='gruen'] .schacht-led { background: var(--green); box-shadow: 0 0 8px var(--green); }
.schacht[data-led='rot'] .schacht-led { background: var(--red); box-shadow: 0 0 8px var(--red); animation: blinken 0.8s steps(2) infinite; }
.schacht.is-ziel { border-color: var(--green-border); box-shadow: 0 0 0 1px var(--green-bg); }
.schacht.is-ziel:hover { border-color: var(--green); }

.luefterwand { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.luefter-platz {
  position: relative;
  display: grid;
  place-items: center;
  aspect-ratio: 1.3;
  padding: 6px;
  background: #0b0d10;
  border: 1px solid #2b3038;
  cursor: default;
}
.luefter-platz :deep(.teil) { width: 90%; }
.luefter-platz.is-luecke { cursor: pointer; border-style: dashed; }
.luefter-platz.is-ziel { border-color: var(--green); box-shadow: 0 0 14px rgba(0, 255, 102, 0.2); }
.luecke { font-family: var(--mono); font-size: 12px; color: var(--fg-3); }
.luefter-nr {
  position: absolute;
  left: 6px;
  top: 4px;
  font-family: var(--mono);
  font-size: 12px;
  font-weight: 700;
  color: #9aa3ae;
}

@keyframes blinken { 50% { opacity: 0.3; } }
@media (max-width: 700px) {
  .schaechte { grid-template-columns: repeat(2, 1fr); }
}
</style>
