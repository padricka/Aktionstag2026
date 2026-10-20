<!--
  BrennenderServer — der Beamer zeigt das brennende Server-Rack (statt des Tresors).

  Feuer nach Leben: Stufe 1 (über 2/3), 2 (über 1/3), 3 (darunter); dazu wächst es
  stufenlos über die CSS-Variable --feuer. Ein Fehler (Leben fallen um 40 und mehr auf
  einmal) lässt es kurz auflodern – das Feuer selbst frisst nur 1 Leben alle 3 s.
  Rechts die drei Teile fürs Finale: Umriss, bis sie gefunden sind (game_tick.parts).
  Sieg: Flammen und Rauch verschwinden, die LEDs werden grün, „SERVER ONLINE“.
  Alles SVG/CSS, keine Bilder.
-->
<template>
  <div
    class="brennender-server"
    :class="[`bs--stufe-${stufe}`, { 'is-geloescht': sieg, 'is-auflodern': auflodern }]"
    :style="{ '--feuer': feuer.toFixed(2) }"
  >
    <div class="bs-buehne" aria-hidden="true">
      <div class="bs-glut"></div>

      <div class="bs-rauch">
        <i v-for="n in 7" :key="n" :style="{ '--n': n }"></i>
      </div>

      <div class="bs-rack">
        <div class="bs-rack-kopf">RZ B-04 · RACK 07 · RENTE</div>
        <div v-for="n in 9" :key="n" class="bs-einschub" :style="{ '--d': n }">
          <span class="bs-led"></span><span class="bs-led"></span>
          <span class="bs-schlitz"></span>
          <span class="bs-schlitz bs-schlitz--kurz"></span>
        </div>
        <div class="bs-rack-fuss"></div>
      </div>

      <div class="bs-flammen">
        <i v-for="n in 11" :key="n" class="bs-flamme" :style="{ '--n': n }"></i>
      </div>
      <div class="bs-funken">
        <i v-for="n in 8" :key="n" :style="{ '--n': n }"></i>
      </div>

      <p v-if="sieg" class="bs-online">SERVER ONLINE</p>
    </div>

    <ul class="bs-teile" aria-label="Teile für die Reparatur">
      <li v-for="f in faecher" :key="f.id" class="bs-teil" :class="{ 'is-da': f.teil }">
        <TeilGrafik :teil="f.id" :leer="!f.teil" :dreht="sieg && f.id === 'fan'" />
        <span>{{ f.name }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import TeilGrafik from './TeilGrafik.vue'
import { TEILE, TEIL_REIHENFOLGE } from '../utils/teile.js'

const props = defineProps({
  hp: { type: Number, required: true },
  maxHp: { type: Number, default: 300 },
  teile: { type: Array, default: () => [] },   // game_tick.parts
  sieg: { type: Boolean, default: false },
})

const AUFLODERN_AB = 40   // so viel auf einmal = Fehler (das Feuer allein nimmt 1)

const anteil = computed(() => Math.max(0, Math.min(1, props.hp / (props.maxHp || 1))))
const stufe = computed(() => (anteil.value > 0.66 ? 1 : anteil.value > 0.33 ? 2 : 3))
const feuer = computed(() => 0.45 + (1 - anteil.value) * 0.8)

const faecher = computed(() =>
  TEIL_REIHENFOLGE.map((id) => ({
    id,
    name: TEILE[id].name,
    teil: props.teile.find((t) => t.id === id) || null,
  }))
)

const auflodern = ref(false)
let lodernTimer = null
watch(() => props.hp, (jetzt, vorher) => {
  if (vorher - jetzt >= AUFLODERN_AB) {
    auflodern.value = true
    clearTimeout(lodernTimer)
    lodernTimer = setTimeout(() => { auflodern.value = false }, 1200)
  }
})
onUnmounted(() => clearTimeout(lodernTimer))
</script>

<style scoped>
.brennender-server {
  --feuer: 0.5;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: clamp(16px, 4vw, 56px);
  width: 100%;
  max-width: 980px;
  margin-inline: auto;
}

/* ------------------------------------------------------------------ Bühne */
.bs-buehne {
  position: relative;
  width: clamp(180px, 22vw, 300px);
  padding-top: calc(70px + var(--feuer) * 60px);   /* Platz für Flammen und Rauch */
}

.bs-glut {
  position: absolute;
  left: -40%;
  right: -40%;
  top: 0;
  bottom: -10%;
  background: radial-gradient(ellipse at 50% 40%, rgba(255, 120, 30, calc(0.12 + var(--feuer) * 0.28)), transparent 65%);
  transition: opacity 1.2s ease;
  pointer-events: none;
}

/* Rack */
.bs-rack {
  position: relative;
  z-index: 1;
  padding: 10px 12px 8px;
  background: linear-gradient(90deg, #15181c, #23272e 12%, #1b1f24 88%, #101215);
  border: 3px solid #2b3038;
  border-radius: 4px 4px 2px 2px;
  box-shadow: 0 18px 30px rgba(0, 0, 0, 0.6), inset 0 0 0 2px #0b0d10;
}
.bs-rack-kopf {
  margin-bottom: 8px;
  padding: 3px 6px;
  background: #0b0d10;
  color: #7d8590;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.15em;
  text-align: center;
}
.bs-einschub {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 18px;
  margin-bottom: 5px;
  padding: 0 8px;
  background: linear-gradient(180deg, #2f343c, #1f2329);
  border: 1px solid #0f1114;
  /* Hitze: die oberen Einschübe glühen an */
  box-shadow: inset 0 0 calc((10 - var(--d)) * var(--feuer) * 1.6px) rgba(255, 110, 30, 0.55);
}
.bs-led {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--red);
  box-shadow: 0 0 6px var(--red);
  animation: led-blinken calc(0.5s + var(--d) * 0.07s) steps(2) infinite;
}
.bs-led + .bs-led { background: var(--amber); box-shadow: 0 0 6px var(--amber); animation-delay: 0.2s; }
.bs-schlitz { flex: 1; height: 4px; background: #0d0f12; border-radius: 2px; }
.bs-schlitz--kurz { flex: 0 0 22%; }
.bs-rack-fuss { height: 10px; margin: 6px -12px -8px; background: #0b0d10; }

/* Flammen: Tropfenformen über dem Rack und an den Seiten */
.bs-flammen {
  position: absolute;
  z-index: 2;
  left: -6%;
  right: -6%;
  top: calc(30px + var(--feuer) * 40px);
  height: 40%;
  pointer-events: none;
  transition: opacity 1.2s ease, transform 1.2s ease;
  transform-origin: 50% 100%;
}
.bs-flamme {
  position: absolute;
  bottom: 60%;
  left: calc((var(--n) - 1) * 9%);
  width: calc(22px + var(--feuer) * 30px);
  height: calc(22px + var(--feuer) * 30px);
  border-radius: 50% 0 50% 50%;
  background: radial-gradient(circle at 60% 40%, #fff3b0 0%, #ffd23a 22%, #ff8a1f 52%, rgba(214, 48, 20, 0.85) 75%, transparent 78%);
  filter: blur(0.6px) drop-shadow(0 0 10px rgba(255, 120, 30, 0.8));
  transform-origin: 50% 100%;
  animation: flackern calc(0.7s + var(--n) * 0.06s) ease-in-out infinite alternate;
  mix-blend-mode: screen;
}
/* heller Kern in jeder Flamme */
.bs-flamme::after {
  content: '';
  position: absolute;
  inset: 34% 26% 8% 30%;
  border-radius: inherit;
  background: radial-gradient(circle at 60% 40%, #fffbe6 0%, #ffe27a 55%, transparent 72%);
}
.bs-flamme:nth-child(even) { bottom: 52%; animation-delay: -0.3s; width: calc(16px + var(--feuer) * 24px); height: calc(16px + var(--feuer) * 24px); }
/* Seitenflammen, die am Rack herunterkriechen */
.bs-flamme:nth-child(10) { left: 2%; bottom: -35%; }
.bs-flamme:nth-child(11) { left: 88%; bottom: -20%; }

/* Stufe 1: nur oben in der Mitte · Stufe 2: ganze Oberkante · Stufe 3: auch an den Seiten */
.bs--stufe-1 .bs-flamme:nth-child(-n + 3),
.bs--stufe-1 .bs-flamme:nth-child(n + 9) { display: none; }
.bs--stufe-2 .bs-flamme:nth-child(n + 10) { display: none; }

/* Rauch */
.bs-rauch {
  position: absolute;
  z-index: 0;
  left: 10%;
  right: 10%;
  top: 0;
  height: 60%;
  pointer-events: none;
  transition: opacity 1.5s ease;
}
.bs-rauch i {
  position: absolute;
  bottom: 0;
  left: calc(var(--n) * 11%);
  width: calc(40px + var(--feuer) * 50px);
  height: calc(40px + var(--feuer) * 50px);
  border-radius: 50%;
  background: radial-gradient(circle, rgba(150, 155, 160, calc(0.3 + var(--feuer) * 0.3)), transparent 70%);
  filter: blur(4px);
  animation: aufsteigen calc(3s + var(--n) * 0.4s) linear infinite;
  animation-delay: calc(var(--n) * -0.55s);
}

/* Funken */
.bs-funken {
  position: absolute;
  z-index: 3;
  left: 0;
  right: 0;
  top: 20%;
  height: 40%;
  pointer-events: none;
  transition: opacity 1s ease;
}
.bs-funken i {
  position: absolute;
  bottom: 0;
  left: calc(8% + var(--n) * 10%);
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #ffd23a;
  box-shadow: 0 0 6px #ff8a1f;
  animation: funke calc(1.2s + var(--n) * 0.15s) ease-out infinite;
  animation-delay: calc(var(--n) * -0.37s);
  opacity: calc(var(--feuer) - 0.3);
}

/* Fehler: Feuer lodert kurz auf */
.is-auflodern .bs-flammen { animation: auflodern 1.2s ease-out; }
.is-auflodern .bs-glut { animation: glut-blitz 1.2s ease-out; }

/* Sieg: Feuer aus, LEDs grün */
.is-geloescht .bs-flammen { opacity: 0; transform: scaleY(0.1); }
.is-geloescht .bs-rauch,
.is-geloescht .bs-funken,
.is-geloescht .bs-glut { opacity: 0; }
.is-geloescht .bs-einschub { box-shadow: none; transition: box-shadow 1.5s ease; }
.is-geloescht .bs-led {
  animation: led-gruen 0.3s calc(1s + var(--d) * 0.12s) forwards;
}

.bs-online {
  position: absolute;
  z-index: 4;
  left: 50%;
  top: 34%;
  margin: 0;
  transform: translateX(-50%);
  white-space: nowrap;
  padding: 6px 14px;
  background: rgba(5, 8, 6, 0.85);
  border: 1px solid var(--green-border);
  color: var(--green);
  font-family: var(--mono);
  font-size: clamp(16px, 2vw, 26px);
  letter-spacing: 0.2em;
  text-shadow: 0 0 12px rgba(0, 255, 102, 0.6);
  opacity: 0;
  animation: rein 0.6s ease 2.2s forwards;
}

/* ------------------------------------------------------------------ Teile */
.bs-teile {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
  width: clamp(120px, 12vw, 170px);
}
.bs-teil {
  display: grid;
  gap: 4px;
  justify-items: center;
  padding: 8px;
  border: 1px dashed var(--border-2);
  background: var(--bg-1);
  font-family: var(--mono);
  font-size: 12px;
  color: var(--fg-3);
  transition: border-color 0.6s ease, color 0.6s ease;
}
.bs-teil.is-da {
  border-style: solid;
  border-color: var(--green-border);
  color: var(--fg);
  animation: teil-rein 0.8s cubic-bezier(0.22, 1, 0.36, 1);
}
.bs-teil :deep(.teil) { width: 80%; }

/* ------------------------------------------------------------------ Animationen */
@keyframes flackern {
  0% { transform: rotate(-45deg) scale(1) translateY(0); opacity: 0.9; }
  50% { transform: rotate(-41deg) scale(1.12, 1.25) translateY(-3px); opacity: 1; }
  100% { transform: rotate(-48deg) scale(0.92, 1.05) translateY(-1px); opacity: 0.85; }
}
@keyframes aufsteigen {
  from { transform: translateY(0) scale(0.6); opacity: 0; }
  20% { opacity: 1; }
  to { transform: translateY(-160%) scale(1.6); opacity: 0; }
}
@keyframes funke {
  from { transform: translate(0, 0); opacity: 1; }
  to { transform: translate(calc((var(--n) - 4) * 6px), -90px); opacity: 0; }
}
@keyframes led-blinken { 50% { opacity: 0.25; } }
@keyframes led-gruen { to { background: var(--green); box-shadow: 0 0 6px var(--green); opacity: 1; } }
@keyframes auflodern {
  0% { transform: scale(1); }
  25% { transform: scale(1.45, 1.7); filter: brightness(1.4); }
  100% { transform: scale(1); }
}
@keyframes glut-blitz { 25% { opacity: 1; filter: brightness(1.8); } }
@keyframes rein { to { opacity: 1; } }
@keyframes teil-rein {
  from { transform: scale(0.7); box-shadow: 0 0 0 rgba(0, 255, 102, 0); }
  50% { box-shadow: 0 0 24px rgba(0, 255, 102, 0.5); }
  to { transform: none; }
}

@media (prefers-reduced-motion: reduce) {
  .bs-flamme, .bs-rauch i, .bs-funken i, .bs-led { animation: none; }
}
</style>
