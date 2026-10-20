<!--
  IntroStory — Einsatzbesprechung am Beamer, bevor die Zeit läuft (Status "briefing").

  Szenen im Neon-Stil des Spiels (gleiche Bilder wie Startmenü/Rollen, NICHT die Sieg-/
  Niederlage-Bilder), dazu Sprechblasen mit der Story, die sich wie getippt aufbauen.
  Die letzte Szene ist ein kurzes Tutorial. Erst „Einsatz starten“ meldet start →
  HostScreen schickt start_game, das Spiel beginnt. Blättern: Knöpfe, Pfeiltasten, Enter.
-->
<template>
  <div class="intro" tabindex="-1" ref="root" @keydown="taste">
    <header class="intro-top">
      <span class="intro-brand">DRV-BOX · EINSATZBESPRECHUNG</span>
      <button v-if="!istLetzte" class="intro-skip" type="button" @click="springeZumTutorial">
        Intro überspringen ⏭
      </button>
    </header>

    <Transition name="szene" mode="out-in">
      <section :key="index" class="intro-scene" :class="`is-${slide.layout}`">
        <figure v-if="slide.image" class="intro-image">
          <img :src="slide.image" :alt="slide.alt" />
          <figcaption v-if="slide.caption" class="intro-caption">{{ slide.caption }}</figcaption>
        </figure>

        <div class="intro-talk">
          <div class="bubble" :class="`tail-${slide.tail || 'left'}`">
            <span class="bubble-speaker">{{ slide.speaker }}</span>
            <p class="bubble-text">{{ getippt }}<span v-if="tippt" class="bubble-cursor">▌</span></p>
            <!-- unsichtbarer Volltext hält die Größe fest, damit nichts springt -->
            <p class="bubble-text bubble-ghost" aria-hidden="true">{{ slide.text }}</p>
          </div>

          <ol v-if="slide.tutorial" class="tutorial">
            <li v-for="(t, i) in slide.tutorial" :key="i" :style="{ '--i': i }">
              <span class="tutorial-icon" aria-hidden="true">{{ t.icon }}</span>
              <span>{{ t.text }}</span>
            </li>
          </ol>
        </div>
      </section>
    </Transition>

    <footer class="intro-nav">
      <button class="intro-back" type="button" :disabled="index === 0" @click="zurueck">‹ Zurück</button>

      <div class="intro-dots" aria-hidden="true">
        <span
          v-for="(s, i) in SLIDES"
          :key="i"
          class="intro-dot"
          :class="{ 'is-active': i === index, 'is-done': i < index }"
        ></span>
      </div>

      <button v-if="!istLetzte" class="intro-next" type="button" @click="weiter">Weiter ›</button>
      <button v-else class="intro-start" type="button" :disabled="gestartet" @click="starten">
        {{ gestartet ? 'Startet …' : 'Einsatz starten ▶' }}
      </button>
    </footer>
  </div>
</template>

<script>
import startScreen from '../assets/start-screen2.jpg'
import hostRole from '../assets/host_role.png'
import clientRole from '../assets/client_role.png'
import masterRole from '../assets/master_role.png'
import playerRole from '../assets/player_role.png'

const KAISER = 'M. Kaiser · IT-Leitung (Funk)'

// Die Story. layout: wide = Bild über die ganze Breite, side = Bild links, Blase rechts.
export const SLIDES = [
  {
    image: startScreen,
    alt: 'Ein Techniker vor den Monitoren, daneben brennt ein Server-Rack',
    caption: 'DRV Schwaben · Rechenzentrum · Montag, 07:58 Uhr',
    layout: 'wide',
    speaker: KAISER,
    text: 'Alarm im Rechenzentrum! In Raum B-04 brennt ein Server-Rack – ausgerechnet das mit den Rentendaten.',
  },
  {
    image: hostRole,
    alt: 'Ein Monitor mit Countdown neben einem Server, der Funken sprüht',
    layout: 'side',
    speaker: KAISER,
    text: 'Uns bleiben nur ein paar Minuten, bis das System ganz ausfällt. Dann sind die Daten von Millionen Versicherten weg.',
  },
  {
    image: clientRole,
    alt: 'Drei Techniker: zwei an Laptops, einer mit einer Anleitung',
    layout: 'side',
    speaker: KAISER,
    text: 'Ihr drei seid das Notfall-Team: der Leitstand im Kontrollraum, einer vor dem Rack, einer dahinter. Jeder sieht nur seinen Teil – keiner hat die ganze Lösung.',
  },
  {
    image: masterRole,
    alt: 'Ein nachdenklicher Techniker mit Notizzetteln',
    layout: 'side',
    speaker: KAISER,
    text: 'Meine Wartungsnotizen liegen bei euch – leider zerrissen. Jeder hat ein Stück mit einer Regel. Lest sie euch gegenseitig vor!',
  },
  {
    image: playerRole,
    alt: 'Zwei Techniker streiten sich an ihren Laptops',
    layout: 'side',
    speaker: KAISER,
    text: 'Und ganz wichtig: Redet miteinander – nicht durcheinander! Jede falsche Eingabe kostet den Server Leben.',
  },
  {
    image: null,
    layout: 'tutorial',
    tail: 'none',
    speaker: 'So läuft der Einsatz',
    text: 'Kurz die Regeln – dann rettet den Server!',
    tutorial: [
      { icon: '①', text: 'Drei Aufgaben, dann das Finale. Jede gelöste Aufgabe verrät eine Ziffer des Neustart-Codes.' },
      { icon: '♥', text: 'Falsche Eingaben kosten Leben. Läuft die Zeit ab, ist der Server verloren.' },
      { icon: '✎', text: 'Eure Notizzettel erklären die Regeln – mit Rechenbeispielen. Rechts am Handy liegt ein Taschenrechner.' },
      { icon: '?', text: 'Hängt ihr fest? Hier am Beamer gibt es Hilfe-Zettel – jeder kostet 50 Punkte.' },
      { icon: '★', text: 'Je schneller und je weniger Hilfe, desto mehr Punkte.' },
    ],
  },
]
</script>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  // ms pro Zeichen in der Sprechblase (0 = sofort, z. B. in Tests)
  typeSpeed: { type: Number, default: 24 },
})
const emit = defineEmits(['start'])

const root = ref(null)
const index = ref(0)
const zeichen = ref(0)
const gestartet = ref(false)
let timer = null

const slide = computed(() => SLIDES[index.value])
const istLetzte = computed(() => index.value === SLIDES.length - 1)
const tippt = computed(() => zeichen.value < slide.value.text.length)
const getippt = computed(() => slide.value.text.slice(0, zeichen.value))

function stopp() {
  if (timer) { clearInterval(timer); timer = null }
}

function tippen() {
  stopp()
  if (!props.typeSpeed) { zeichen.value = slide.value.text.length; return }
  zeichen.value = 0
  timer = setInterval(() => {
    zeichen.value += 1
    if (!tippt.value) stopp()
  }, props.typeSpeed)
}

watch(index, tippen)
onMounted(() => { tippen(); root.value?.focus({ preventScroll: true }) })
onUnmounted(stopp)

// Erst fertig tippen lassen, dann weiterblättern
function weiter() {
  if (tippt.value) { stopp(); zeichen.value = slide.value.text.length; return }
  if (!istLetzte.value) index.value += 1
}

function zurueck() {
  if (index.value > 0) index.value -= 1
}

function springeZumTutorial() {
  index.value = SLIDES.length - 1
}

function starten() {
  if (gestartet.value) return
  gestartet.value = true
  emit('start')
}

function taste(e) {
  if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); weiter() }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); zurueck() }
  else if (e.key === 'Enter') { e.preventDefault(); istLetzte.value ? starten() : weiter() }
}
</script>

<style scoped>
.intro {
  --neon: #39ff5a;
  --neon-dim: rgba(57, 255, 90, 0.35);
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 24px 40px 28px;
  background: radial-gradient(ellipse at 50% 40%, #071a0c 0%, #020604 70%);
  color: var(--fg);
  outline: none;
  overflow: hidden;
}

.intro-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.intro-brand {
  font-family: var(--mono);
  font-size: 13px;
  letter-spacing: 0.25em;
  color: var(--neon);
  text-shadow: 0 0 10px var(--neon-dim);
}

.intro-skip {
  padding: 6px 12px;
  background: none;
  border: 1px solid var(--border-2);
  color: var(--fg-3);
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 0.1em;
  cursor: pointer;
}

.intro-skip:hover { color: var(--neon); border-color: var(--neon-dim); }

/* ------------------------------------------------------------------ Szene */
.intro-scene {
  flex: 1;
  min-height: 0;
  display: grid;
  gap: 32px;
  align-items: center;
}

.intro-scene.is-side { grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); }
.intro-scene.is-wide { grid-template-rows: minmax(0, 1fr) auto; justify-items: center; }
.intro-scene.is-tutorial { justify-items: center; align-content: center; }

.intro-image {
  margin: 0;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.intro-image img {
  max-width: 100%;
  max-height: 100%;
  min-height: 0;
  object-fit: contain;
  /* schwarzer Bildhintergrund verschmilzt mit dem Beamer-Hintergrund (kein Kasten) */
  mix-blend-mode: screen;

}

.is-wide .intro-image img { max-height: 58vh; }

.intro-caption {
  font-family: var(--mono);
  font-size: 14px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--neon);
  opacity: 0.85;
}

.intro-talk {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 960px;
  width: 100%;
}

/* ------------------------------------------------------------ Sprechblase (Comic) */
.bubble {
  position: relative;
  display: grid;
  padding: 20px 26px 22px;
  background: #f4fff5;
  color: #0b1a0e;
  border: 3px solid var(--neon);
  border-radius: 22px;
  box-shadow: 0 0 0 4px rgba(57, 255, 90, 0.12), 0 0 30px rgba(57, 255, 90, 0.25);
  animation: plopp 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Text und unsichtbarer Volltext liegen übereinander (gleiche Zelle) */
.bubble-text,
.bubble-ghost { grid-area: 2 / 1; }
.bubble-speaker { grid-area: 1 / 1; }

.bubble::after {
  content: '';
  position: absolute;
  width: 26px;
  height: 26px;
  background: #f4fff5;
  border: 3px solid var(--neon);
  border-top: none;
  border-right: none;
}

.bubble.tail-left::after { left: -15px; top: 38px; transform: rotate(45deg) skew(10deg, 10deg); }
.is-wide .bubble.tail-left::after { left: 60px; top: -15px; transform: rotate(135deg); }
.bubble.tail-none::after { display: none; }

.bubble-speaker {
  margin-bottom: 8px;
  font-family: var(--mono);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #1f7a33;
}

.bubble-text {
  margin: 0;
  font-family: 'Caveat', 'Segoe Print', 'Bradley Hand', cursive;
  font-size: clamp(26px, 2.5vw, 40px);
  line-height: 1.25;
}

.bubble-ghost { visibility: hidden; }
.bubble-cursor { animation: blink 0.8s steps(1) infinite; }

@keyframes plopp {
  from { transform: scale(0.85) translateY(10px); opacity: 0; }
  to { transform: none; opacity: 1; }
}

@keyframes blink { 50% { opacity: 0; } }

/* ----------------------------------------------------------------- Tutorial */
.tutorial {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tutorial li {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  border: 1px solid var(--neon-dim);
  background: rgba(57, 255, 90, 0.05);
  font-size: clamp(18px, 1.6vw, 26px);
  line-height: 1.35;
  animation: rein 0.4s ease-out both;
  animation-delay: calc(var(--i) * 0.12s + 0.2s);
}

.tutorial-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border: 2px solid var(--neon);
  border-radius: 50%;
  color: var(--neon);
  font-weight: 700;
  font-size: 20px;
  text-shadow: 0 0 8px var(--neon-dim);
}

@keyframes rein {
  from { transform: translateX(-16px); opacity: 0; }
  to { transform: none; opacity: 1; }
}

/* --------------------------------------------------------------- Navigation */
.intro-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.intro-back,
.intro-next,
.intro-start {
  min-width: 170px;
  padding: 14px 22px;
  font-family: var(--mono);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.08em;
  cursor: pointer;
}

.intro-back {
  background: none;
  border: 1px solid var(--border-2);
  color: var(--fg-3);
}

.intro-back:disabled { visibility: hidden; }

.intro-next {
  background: rgba(57, 255, 90, 0.1);
  border: 1px solid var(--neon);
  color: var(--neon);
}

.intro-start {
  background: var(--neon);
  border: none;
  color: #031006;
  box-shadow: 0 0 24px var(--neon-dim);
  animation: puls 1.6s ease-in-out infinite;
}

.intro-start:disabled { animation: none; opacity: 0.6; cursor: wait; }

@keyframes puls { 50% { box-shadow: 0 0 40px rgba(57, 255, 90, 0.6); } }

.intro-dots { display: flex; gap: 10px; }

.intro-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--neon-dim);
}

.intro-dot.is-done { background: var(--neon-dim); }
.intro-dot.is-active { background: var(--neon); border-color: var(--neon); box-shadow: 0 0 10px var(--neon); }

/* Szenenwechsel */
.szene-enter-active, .szene-leave-active { transition: opacity 0.35s, transform 0.35s; }
.szene-enter-from { opacity: 0; transform: translateX(30px); }
.szene-leave-to { opacity: 0; transform: translateX(-30px); }

@media (max-width: 900px) {
  .intro { padding: 16px; }
  .intro-scene.is-side { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  .bubble, .tutorial li, .intro-start { animation: none; }
  .szene-enter-active, .szene-leave-active { transition: none; }
}
</style>
