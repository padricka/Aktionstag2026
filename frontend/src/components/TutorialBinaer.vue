<!--
  TutorialBinaer — kurze Vorführung vor Aufgabe 3 (feat/tutorial-binaer), läuft in der
  Zwischenszene nach der Titelkarte. Sieben Bilder, je `dauer / 7`:
    4 Ziffern: Werte darüber · Einsen leuchten · 8 + 4 + 1 = 13
    8 Ziffern: genauso · Einsen leuchten · 64 + 16 + 4 + 1 = 85 · 85 → U (ASCII-Tabelle)
  Nur Anzeige, keine Eingaben. Uhr und Feuer stehen solange (PAUSE_NACH im Backend).
-->
<template>
  <div class="tut-binaer" :class="{ 'is-gross': gross }">
    <p class="tut-kopf">So rechnet man eine Datenzeile aus</p>

    <div class="tb-tafel" :style="{ '--spalten': beispiel.werte.length }">
      <span v-for="w in beispiel.werte" :key="`w${w}`" class="tb-wert" :class="{ 'is-an': leuchten && eins(w) }">{{ w }}</span>
      <span
        v-for="(z, i) in beispiel.ziffern"
        :key="`z${i}`"
        class="tb-ziffer"
        :class="{ 'is-eins': leuchten && z === '1' }"
      >{{ z }}</span>
    </div>

    <p class="tb-summe" :class="{ 'is-da': summe }">{{ summe ? summenText : ' ' }}</p>
    <p class="tb-ascii" :class="{ 'is-da': schritt === 6 }">{{ schritt === 6 ? '85 → in der ASCII-Tabelle: U' : ' ' }}</p>

    <p class="tut-schritt" aria-live="polite">{{ TEXTE[schritt] }}</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  dauer: { type: Number, required: true },   // ms für alle sieben Bilder
  gross: { type: Boolean, default: false },
})

const KLEIN = { werte: [8, 4, 2, 1], ziffern: '1101'.split('') }
const GROSS = { werte: [128, 64, 32, 16, 8, 4, 2, 1], ziffern: '01010101'.split('') }
const TEXTE = [
  'Über jeder Ziffer steht ein Wert.',
  'Nur die Werte über einer 1 zählen.',
  'Diese Werte zusammenzählen – fertig ist die Zahl.',
  'Mit 8 Ziffern geht es genauso.',
  'Wieder: nur die Werte über einer 1.',
  'Zusammenzählen …',
  '… und die Zahl in der ASCII-Tabelle nachschlagen.',
]

const schritt = ref(0)
const beispiel = computed(() => (schritt.value < 3 ? KLEIN : GROSS))
const leuchten = computed(() => schritt.value % 3 !== 0 || schritt.value === 6)
const summe = computed(() => [2, 5, 6].includes(schritt.value))
const summenText = computed(() => {
  const b = beispiel.value
  const werte = b.werte.filter((_, i) => b.ziffern[i] === '1')
  return `${werte.join(' + ')} = ${werte.reduce((a, w) => a + w, 0)}`
})
const eins = (w) => beispiel.value.ziffern[beispiel.value.werte.indexOf(w)] === '1'

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
  max-width: calc(560px * var(--tut-s));
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
  grid-template-columns: repeat(var(--spalten), minmax(0, 1fr));
  gap: calc(4px * var(--tut-s)) calc(6px * var(--tut-s));
  width: 100%;
  padding: calc(14px * var(--tut-s));
  background: var(--bg);
  border: 1px solid var(--border-2);
  text-align: center;
}

.tb-wert {
  padding-bottom: calc(6px * var(--tut-s));
  border-bottom: 2px solid var(--border-3);
  font-size: calc(16px * var(--tut-s));
  font-weight: 700;
  color: var(--fg-3);
  transition: color 0.3s ease;
}
.tb-wert.is-an { color: var(--amber); }

.tb-ziffer {
  font-size: calc(34px * var(--tut-s));
  font-weight: 700;
  color: var(--fg-3);
  transition: color 0.3s ease, text-shadow 0.3s ease;
}
.tb-ziffer.is-eins { color: var(--green); text-shadow: 0 0 12px rgba(0, 255, 102, 0.45); }

.tb-summe,
.tb-ascii {
  margin: 0;
  min-height: 1.3em;
  font-size: calc(26px * var(--tut-s));
  font-weight: 700;
  color: var(--green);
  opacity: 0;
  transform: translateY(6px);
  transition: opacity 0.4s ease, transform 0.4s ease;
}
.tb-ascii { font-size: calc(20px * var(--tut-s)); color: var(--fg); }
.is-da { opacity: 1; transform: none; }

.tut-schritt {
  margin: 0;
  min-height: 1.4em;
  font-size: calc(16px * var(--tut-s));
  color: var(--fg);
}

@media (prefers-reduced-motion: reduce) {
  .tb-wert, .tb-ziffer, .tb-summe, .tb-ascii { transition: none; }
}
</style>
