<!--
  TutorialBinaer — kurze Vorführung vor Aufgabe 3 (feat/tutorial-binaer), läuft in der
  Zwischenszene nach der Titelkarte. Fünf Bilder, je `dauer / 5`:
    Nr. auf der Platte: 8 4 2 1 über 0110 · Einsen leuchten · 4 + 2 = 6
    Die langen Codes NICHT rechnen · in der Code-Tabelle nachschlagen → R
  Nur Anzeige, keine Eingaben. Uhr und Feuer stehen solange (PAUSE_NACH im Backend).
-->
<template>
  <div class="tut-binaer" :class="{ 'is-gross': gross }">
    <p class="tut-kopf">{{ schritt < 3 ? 'Die Nr. auf der Platte ausrechnen' : 'Die Codes nur nachschlagen' }}</p>

    <template v-if="schritt < 3">
      <div class="tb-tafel">
        <span v-for="(w, i) in WERTE" :key="`w${w}`" class="tb-wert" :class="{ 'is-an': schritt > 0 && NR[i] === '1' }">{{ w }}</span>
        <span
          v-for="(z, i) in NR"
          :key="`z${i}`"
          class="tb-ziffer"
          :class="{ 'is-eins': schritt > 0 && z === '1' }"
        >{{ z }}</span>
      </div>
      <p class="tb-summe" :class="{ 'is-da': schritt === 2 }">{{ schritt === 2 ? '4 + 2 = 6' : ' ' }}</p>
    </template>

    <template v-else>
      <p class="tb-code">{{ CODE }}</p>
      <div class="tb-tabelle" :class="{ 'is-da': schritt === 4 }">
        <span
          v-for="e in TABELLE"
          :key="e.b"
          class="tb-eintrag"
          :class="{ 'is-treffer': schritt === 4 && e.c === CODE }"
        ><b>{{ e.b }}</b> {{ e.c }}</span>
      </div>
    </template>

    <p class="tut-schritt" aria-live="polite">{{ TEXTE[schritt] }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  dauer: { type: Number, required: true },   // ms für alle fünf Bilder
  gross: { type: Boolean, default: false },
})

const WERTE = [8, 4, 2, 1]
const NR = '0110'.split('')
const CODE = '0100 1101'                     // wie das Beispiel auf dem Zettel der Rückseite
const TABELLE = [
  { b: 'P', c: '1110 0010' },
  { b: 'Q', c: '0011 1000' },
  { b: 'R', c: '0100 1101' },
  { b: 'S', c: '1001 0110' },
]
const TEXTE = [
  'Über den 4 Ziffern stehen die Werte 8 + 4 + 2 + 1.',
  'Nur die Werte über einer 1 zählen.',
  'Zusammenzählen – die Platte hat Nr. 6.',
  'Die langen Codes mit 8 Ziffern NICHT rechnen!',
  'Einfach in der Code-Tabelle suchen – fertig ist der Buchstabe.',
]

const schritt = ref(0)
let timer = null
onMounted(() => {
  timer = setInterval(() => {
    if (schritt.value < TEXTE.length - 1) schritt.value += 1
  }, props.dauer / TEXTE.length)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.tut-binaer {
  --tut-s: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: calc(14px * var(--tut-s));
  max-width: calc(520px * var(--tut-s));
  width: 100%;
}
.is-gross { --tut-s: 1.8; }

.tut-kopf {
  margin: 0;
  font-size: calc(13px * var(--tut-s));
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--amber);
}

.tb-tafel {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: calc(4px * var(--tut-s)) calc(10px * var(--tut-s));
  width: 70%;
  padding: calc(14px * var(--tut-s));
  background: var(--bg);
  border: 1px solid var(--border-2);
  text-align: center;
}

.tb-wert {
  padding-bottom: calc(6px * var(--tut-s));
  border-bottom: 2px solid var(--border-3);
  font-size: calc(18px * var(--tut-s));
  font-weight: 700;
  color: var(--fg-3);
  transition: color 0.3s ease;
}
.tb-wert.is-an { color: var(--amber); }

.tb-ziffer {
  font-size: calc(36px * var(--tut-s));
  font-weight: 700;
  color: var(--fg-3);
  transition: color 0.3s ease, text-shadow 0.3s ease;
}
.tb-ziffer.is-eins { color: var(--green); text-shadow: 0 0 12px rgba(0, 255, 102, 0.45); }

.tb-summe {
  margin: 0;
  min-height: 1.3em;
  font-size: calc(28px * var(--tut-s));
  font-weight: 700;
  color: var(--green);
  opacity: 0;
  transform: translateY(6px);
  transition: opacity 0.4s ease, transform 0.4s ease;
}

.tb-code {
  margin: 0;
  padding: calc(8px * var(--tut-s)) calc(16px * var(--tut-s));
  font-size: calc(30px * var(--tut-s));
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--green);
  background: var(--bg);
  border: 1px solid var(--border-2);
}

.tb-tabelle {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: calc(6px * var(--tut-s));
  width: 100%;
  opacity: 0;
  transition: opacity 0.4s ease;
}
.tb-eintrag {
  padding: calc(6px * var(--tut-s)) calc(10px * var(--tut-s));
  font-size: calc(16px * var(--tut-s));
  color: var(--fg-2);
  background: var(--bg);
  border: 1px solid var(--border-2);
  transition: border-color 0.3s ease, color 0.3s ease;
}
.tb-eintrag b { margin-right: 8px; color: var(--fg); }
.tb-eintrag.is-treffer { border-color: var(--green); color: var(--green); box-shadow: 0 0 12px rgba(0, 255, 102, 0.35); }

.is-da { opacity: 1; transform: none; }

.tut-schritt {
  margin: 0;
  min-height: 1.4em;
  font-size: calc(16px * var(--tut-s));
  color: var(--fg);
}

@media (prefers-reduced-motion: reduce) {
  .tb-wert, .tb-ziffer, .tb-summe, .tb-tabelle, .tb-eintrag { transition: none; }
}
</style>
