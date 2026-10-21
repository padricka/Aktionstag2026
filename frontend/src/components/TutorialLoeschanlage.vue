<!--
  TutorialLoeschanlage — kurze Vorführung vor Aufgabe 2 (feat/tutorial-loeschanlage),
  läuft in der Zwischenszene nach der Titelkarte. Fünf Schritte, je `dauer / 5`:
    ① Schrank wählen · ② Löschmittel wählen · ③ AUSLÖSEN → gelöscht
    So NICHT: Wasser auf einen Schrank unter Strom → Stromschlag, −30 Leben
    ④ Freigabe: Leitstand + Rückseite gleichzeitig
  Nur Anzeige, keine Eingaben. Uhr und Feuer stehen solange (PAUSE_NACH im Backend).
-->
<template>
  <div class="tut-loesch" :class="[`is-schritt-${schritt}`, { 'is-gross': gross }]">
    <p class="tut-kopf">So funktioniert die Löschanlage</p>

    <div class="tut-pult" :class="{ 'is-fehler': fehler, 'is-ok': geloescht }">
      <div v-if="schritt < 4" class="tut-regler">
        <div class="tut-feld">
          <span class="tut-label">Schrank</span>
          <span class="tut-knopf" :style="{ '--dreh': schritt === 1 || schritt === 2 ? '120deg' : '0deg' }"><i></i></span>
          <span class="tut-wert">{{ fehler ? 'A-01' : schritt >= 1 ? 'B-01' : 'A-01' }}</span>
          <span v-if="fehler" class="tut-strom">⚡ Strom an</span>
        </div>
        <div class="tut-feld">
          <span class="tut-label">Löschmittel</span>
          <span class="tut-schiene"><i :style="{ left: fehler ? '0%' : schritt >= 2 ? '50%' : '0%' }"></i></span>
          <span class="tut-wert">{{ fehler ? 'WASSER' : schritt >= 2 ? 'CO2' : 'WASSER' }}</span>
        </div>
        <button class="tut-ausloesen" :class="{ 'is-gedrueckt': schritt >= 2 }" type="button" tabindex="-1" aria-hidden="true">
          AUSLÖSEN
        </button>
      </div>

      <div v-else class="tut-freigabe">
        <div class="tut-person">
          <span class="tut-frei-knopf is-gedrueckt">FREIGABE</span>
          <span>Leitstand</span>
        </div>
        <span class="tut-zaehlen">3 · 2 · 1</span>
        <div class="tut-person">
          <span class="tut-frei-knopf is-gedrueckt">FREIGABE</span>
          <span>Rückseite</span>
        </div>
      </div>

      <p v-if="geloescht" class="tut-meldung tut-meldung--ok">✓ Schrank B-01 gelöscht</p>
      <p v-if="fehler" class="tut-meldung tut-meldung--fehler">⚡ Stromschlag! −30 Leben</p>
    </div>

    <p class="tut-schritt" aria-live="polite">{{ TEXTE[schritt] }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'

const props = defineProps({
  dauer: { type: Number, required: true },   // ms für alle fünf Schritte
  gross: { type: Boolean, default: false },
})

const TEXTE = [
  '① Den Schrank wählen, der brennt (Drehregler).',
  '② Das passende Löschmittel wählen (Schieberegler).',
  '③ AUSLÖSEN drücken – der Brand ist gelöscht. Dann der nächste Schrank.',
  'So NICHT: falsches Löschmittel, z. B. Wasser auf einen Schrank unter Strom → −30 Leben!',
  '④ Zum Schluss: Leitstand + Rückseite drücken FREIGABE GLEICHZEITIG (max. 3 s).',
]

const schritt = ref(0)
const geloescht = computed(() => schritt.value === 2)
const fehler = computed(() => schritt.value === 3)
let timer = null

onMounted(() => {
  timer = setInterval(() => {
    if (schritt.value < TEXTE.length - 1) schritt.value += 1
  }, props.dauer / TEXTE.length)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.tut-loesch {
  --tut-s: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: calc(16px * var(--tut-s));
  max-width: calc(560px * var(--tut-s));
}
.is-gross { --tut-s: 1.8; }

.tut-kopf {
  margin: 0;
  font-size: calc(13px * var(--tut-s));
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--amber);
}

.tut-pult {
  position: relative;
  width: 100%;
  padding: calc(18px * var(--tut-s));
  background: linear-gradient(160deg, #2c3138, #16191d);
  border: 2px solid #0c0e11;
  border-radius: 8px;
  transition: box-shadow 0.3s ease;
}
.tut-pult.is-ok { box-shadow: 0 0 0 3px var(--green), 0 0 24px rgba(0, 255, 102, 0.35); }
.tut-pult.is-fehler { box-shadow: 0 0 0 3px var(--red), 0 0 24px rgba(255, 58, 77, 0.5); animation: tut-wackeln 0.4s ease 2; }

.tut-regler {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  align-items: center;
  gap: calc(18px * var(--tut-s));
}

.tut-feld { display: flex; flex-direction: column; align-items: center; gap: calc(8px * var(--tut-s)); }
.tut-label { font-size: calc(12px * var(--tut-s)); letter-spacing: 0.12em; text-transform: uppercase; color: var(--fg-2); }
.tut-wert { font-size: calc(18px * var(--tut-s)); font-weight: 700; color: var(--fg); }
.tut-strom { font-size: calc(12px * var(--tut-s)); color: var(--amber); font-weight: 700; }

.tut-knopf {
  position: relative;
  width: calc(56px * var(--tut-s));
  height: calc(56px * var(--tut-s));
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #5a626d, #20242a);
  border: 2px solid #0a0b0d;
  transform: rotate(var(--dreh));
  transition: transform 0.8s cubic-bezier(0.22, 1, 0.36, 1);
}
.tut-knopf i {
  position: absolute;
  left: 50%;
  top: 6%;
  width: 4px;
  height: 38%;
  margin-left: -2px;
  background: var(--amber);
  border-radius: 2px;
}

.tut-schiene {
  position: relative;
  width: calc(110px * var(--tut-s));
  height: calc(10px * var(--tut-s));
  background: #0c0e11;
  border-radius: 5px;
}
.tut-schiene i {
  position: absolute;
  top: 50%;
  width: calc(22px * var(--tut-s));
  height: calc(28px * var(--tut-s));
  margin-top: calc(-14px * var(--tut-s));
  background: linear-gradient(#cfd5dc, #7d8590);
  border-radius: 4px;
  transition: left 0.8s cubic-bezier(0.22, 1, 0.36, 1);
}

.tut-ausloesen,
.tut-frei-knopf {
  padding: calc(12px * var(--tut-s)) calc(16px * var(--tut-s));
  font-family: inherit;
  font-size: calc(14px * var(--tut-s));
  font-weight: 700;
  letter-spacing: 0.1em;
  color: #fff;
  background: #b3261e;
  border: 2px solid #5c0f0a;
  border-radius: 6px;
  box-shadow: 0 5px 0 #5c0f0a;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.is-gedrueckt { transform: translateY(4px); box-shadow: 0 1px 0 #5c0f0a; }
.tut-ausloesen { pointer-events: none; }

.tut-freigabe {
  display: flex;
  align-items: center;
  justify-content: space-around;
  gap: calc(12px * var(--tut-s));
}
.tut-person { display: flex; flex-direction: column; align-items: center; gap: calc(8px * var(--tut-s)); font-size: calc(14px * var(--tut-s)); color: var(--fg-2); }
.tut-frei-knopf { background: #1f7a3a; border-color: #0d3a1b; box-shadow: 0 1px 0 #0d3a1b; }
.tut-zaehlen { font-size: calc(22px * var(--tut-s)); font-weight: 700; color: var(--amber); }

.tut-meldung {
  margin: calc(12px * var(--tut-s)) 0 0;
  font-size: calc(16px * var(--tut-s));
  font-weight: 700;
}
.tut-meldung--ok { color: var(--green); }
.tut-meldung--fehler { color: var(--red); }

.tut-schritt {
  margin: 0;
  min-height: 2.6em;
  font-size: calc(16px * var(--tut-s));
  line-height: 1.3;
  color: var(--fg);
}

@keyframes tut-wackeln {
  25% { transform: translateX(-6px); }
  75% { transform: translateX(6px); }
}

@media (max-width: 420px) {
  .tut-regler { grid-template-columns: 1fr 1fr; }
  .tut-ausloesen { grid-column: 1 / -1; }
}

@media (prefers-reduced-motion: reduce) {
  .tut-knopf, .tut-schiene i { transition: none; }
  .tut-pult.is-fehler { animation: none; }
}
</style>
