<!--
  TutorialLoeschanlage — kurze Vorführung vor Aufgabe 2 (feat/tutorial-loeschanlage),
  läuft in der Zwischenszene nach der Titelkarte. Gezeigt wird das ECHTE Steuerpult der
  Vorderseite (ControlDesk) und die echten Freigabe-Knöpfe (ReleaseButton), nur nicht
  bedienbar (inert). Fünf Schritte, je `dauer / 5`:
    ① Schrank wählen · ② Löschmittel wählen · ③ AUSLÖSEN → Manometer steigt
    So NICHT: Wasser auf einen Schrank unter Strom → STÖRUNG, −30 Leben
    ④ Freigabe: Leitstand + Rückseite gleichzeitig
  Uhr und Feuer stehen solange (PAUSE_NACH im Backend).
-->
<template>
  <div class="tut-loesch" :class="{ 'is-gross': gross }" inert>
    <p class="tut-kopf">So funktioniert die Löschanlage</p>

    <div v-if="schritt < 4" class="tut-geraet">
      <p class="tut-strom" :class="{ 'is-da': schritt === 3 }">⚡ Schrank A-01 steht unter Strom</p>
      <ControlDesk
        :valves="SCHRAENKE"
        :colors="MITTEL"
        valve-label="Schrank"
        color-label="Löschmittel"
        :step="fortschritt"
        :sequence-len="3"
        :state="schritt === 3 ? 'error' : 'idle'"
        :valve-index="schrank"
        :color-index="mittel"
      />
      <p v-if="schritt === 2" class="tut-meldung tut-meldung--ok">✓ Schrank B-01 gelöscht</p>
      <p v-else-if="schritt === 3" class="tut-meldung tut-meldung--fehler">⚡ Stromschlag! −30 Leben</p>
    </div>

    <div v-else class="tut-freigabe">
      <div class="tut-person">
        <ReleaseButton :armed="true" :window="3" partner="Rückseite" />
        <span>Leitstand</span>
      </div>
      <span class="tut-zaehlen">3 · 2 · 1</span>
      <div class="tut-person">
        <ReleaseButton :armed="true" :window="3" partner="Leitstand" />
        <span>Rückseite</span>
      </div>
    </div>

    <p class="tut-schritt" aria-live="polite">{{ TEXTE[schritt] }}</p>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import ControlDesk from './ControlDesk.vue'
import ReleaseButton from './tasks/task2/ReleaseButton.vue'

const props = defineProps({
  dauer: { type: Number, required: true },   // ms für alle fünf Schritte
  gross: { type: Boolean, default: false },
})

// wie im Spiel (FireProtocolTask): vier Schränke, fünf Löschmittel
const SCHRAENKE = ['A-01', 'A-02', 'B-01', 'B-02']
const MITTEL = ['WASSER', 'SCHAUM', 'CO2', 'INERTGAS', 'ABSCHOTTEN']
const TEXTE = [
  '① Den Schrank wählen, der brennt (Drehregler).',
  '② Das passende Löschmittel wählen (Schieberegler).',
  '③ AUSLÖSEN drücken – der Brand ist gelöscht. Dann der nächste Schrank.',
  'So NICHT: falsches Löschmittel, z. B. Wasser auf einen Schrank unter Strom → −30 Leben!',
  '④ Zum Schluss: Leitstand + Rückseite drücken FREIGABE GLEICHZEITIG (max. 3 s).',
]
const BEWEGUNG_MS = 600   // kurz warten, dann dreht/schiebt sich der Regler – man sieht die Bewegung

const schritt = ref(0)
const schrank = ref(0)
const mittel = ref(0)
const fortschritt = ref(0)
const timer = []

watch(schritt, (s) => {
  if (s === 1) timer.push(setTimeout(() => { mittel.value = 2 }, BEWEGUNG_MS))          // CO2
  if (s === 2) timer.push(setTimeout(() => { fortschritt.value = 1 }, BEWEGUNG_MS / 2))
  if (s === 3) { schrank.value = 0; mittel.value = 0 }                                   // A-01 + WASSER
})

onMounted(() => {
  timer.push(setTimeout(() => { schrank.value = 2 }, BEWEGUNG_MS))                       // B-01
  timer.push(setInterval(() => {
    if (schritt.value < TEXTE.length - 1) schritt.value += 1
  }, props.dauer / TEXTE.length))
})
onUnmounted(() => timer.forEach((t) => { clearTimeout(t); clearInterval(t) }))
</script>

<style scoped>
.tut-loesch {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  width: min(640px, 100%);
  pointer-events: none;
}
/* Beamer: dasselbe Gerät, nur größer */
.is-gross { zoom: 1.5; }

.tut-kopf {
  margin: 0;
  font-size: 13px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--amber);
}

.tut-geraet { display: flex; flex-direction: column; align-items: center; gap: 8px; width: 100%; }

.tut-strom {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--amber);
  visibility: hidden;
}
.tut-strom.is-da { visibility: visible; }

.tut-freigabe {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: center;
  gap: 16px;
  width: 100%;
}
.tut-person { flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; align-items: center; gap: 8px; font-size: 15px; color: var(--fg-2); }
.tut-zaehlen { font-size: 24px; font-weight: 700; color: var(--amber); }

.tut-meldung { margin: 0; font-size: 18px; font-weight: 700; }
.tut-meldung--ok { color: var(--green); }
.tut-meldung--fehler { color: var(--red); }

.tut-schritt {
  margin: 0;
  min-height: 2.6em;
  font-size: 16px;
  line-height: 1.3;
  color: var(--fg);
}
</style>
