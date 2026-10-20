<!--
  IntroStory — Einsatzbesprechung am Beamer, bevor die Zeit läuft (Status "briefing").

  Szenen mit Sprechblasen, die sich wie getippt aufbauen; zum Schluss ein Tutorial mit
  einem echten Notizblatt und dem Taschenrechner. Erst „Einsatz starten“ meldet start →
  HostScreen schickt start_game, das Spiel beginnt. Blättern: Knöpfe, Pfeiltasten, Enter.

  Bilder: Szene 1 ist das Startbild. Szenen 2, 3 und 5 sind Ausschnitte daraus (Kamera-
  fahrt, Alarm-Licht, Beschriftungen), Szene 4 zeigt die echten Notizzettel. Liegen
  eigene Bilder in assets/intro/szene-2.jpg … szene-5.jpg, ersetzen sie die Ausschnitte
  automatisch (Prompts dafür: assets/intro/LIESMICH.md). Die Sieg-/Niederlage-Bilder
  kommen hier bewusst nicht vor.
-->
<template>
  <div class="intro" tabindex="-1" ref="root" @keydown="taste">
    <header class="intro-top">
      <span class="intro-brand">DRV-BOX · EINSATZBESPRECHUNG</span>
      <button v-if="!istLetzte && !outroAktiv" class="intro-skip" type="button" @click="springeZumTutorial">
        Intro überspringen ⏭
      </button>
    </header>

    <Transition name="szene" mode="out-in">
      <section :key="index" class="intro-scene" :class="`is-${slide.layout}`">
        <!-- Bild über die ganze Breite (Szene 1) -->
        <figure v-if="slide.visual === 'image'" class="intro-image">
          <img :src="slide.image" :alt="slide.alt" />
          <figcaption v-if="slide.caption" class="intro-caption">{{ slide.caption }}</figcaption>
        </figure>

        <!-- Ausschnitt mit Kamerafahrt (oder eigenes Bild) -->
        <figure v-else-if="slide.visual === 'scene'" class="intro-scene-frame" :class="{ 'is-alarm': slide.alarm }">
          <img :src="slide.image" :alt="slide.alt" :style="ausschnitt(slide)" :class="{ 'is-crop': slide.crop }" />
          <span v-if="slide.hud" class="scene-hud">{{ slide.hud }}</span>
          <span
            v-for="t in slide.tags || []"
            :key="t.text"
            class="scene-tag"
            :style="{ left: t.x, top: t.y }"
          >{{ t.text }}</span>
          <figcaption v-if="slide.caption" class="intro-caption">{{ slide.caption }}</figcaption>
        </figure>

        <!-- die echten Notizzettel-Stücke -->
        <div v-else-if="slide.visual === 'notes'" class="intro-notes">
          <div v-for="(n, i) in NOTIZ_STUECKE" :key="i" class="intro-note" :style="{ '--r': `${[-6, 3, -2][i]}deg` }">
            <TornNote :note="n" :seed="`intro-${i}`" />
          </div>
        </div>

        <!-- Tutorial: großes Beispiel-Notizblatt + Taschenrechner -->
        <div v-else-if="slide.visual === 'tutorial'" class="tutorial-visual">
          <div class="tutorial-note">
            <TornNote :note="BEISPIEL_NOTIZ" seed="intro-beispiel" />
          </div>
          <div class="calc-mini" aria-label="So sieht der Taschenrechner aus">
            <div class="calc-mini-top"><span>DRV·CALC</span><i></i></div>
            <div class="calc-mini-lcd"><small>64 + 2 + 1</small><b>67</b></div>
            <div class="calc-mini-keys">
              <span v-for="k in MINI_TASTEN" :key="k" :class="{ op: '÷×−+'.includes(k), eq: k === '=' }">{{ k }}</span>
            </div>
          </div>
        </div>

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

    <footer v-if="!outroAktiv" class="intro-nav">
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

    <!-- Übergang ins Spiel: Kamerafahrt aufs brennende Rack, Verbinden, 3 – 2 – 1 – LOS! -->
    <div v-if="outroAktiv" class="intro-outro" :style="{ '--outro-ms': `${outroSpeed * OUTRO.length}ms` }">
      <img class="outro-bild" :src="START_BILD" alt="" />
      <div class="outro-text">
        <p v-if="schritt === 0" class="outro-connect">Verbinde mit Rechenzentrum B-04<span class="outro-dots">…</span></p>
        <span v-else :key="schritt" class="outro-count" :class="{ 'is-los': schritt === OUTRO.length - 1 }">{{ OUTRO[schritt] }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import startScreen from '../assets/start-screen2.jpg'

const KAISER = 'M. Kaiser · IT-Leitung (Funk)'

// Eigene Szenenbilder (optional): assets/intro/szene-<n>.jpg|png|webp ersetzt den Ausschnitt
const EIGENE = import.meta.glob('../assets/intro/szene-*.{jpg,jpeg,png,webp}', { eager: true, import: 'default' })

function eigenesBild(n) {
  const key = Object.keys(EIGENE).find((k) => new RegExp(`/szene-${n}\\.`).test(k))
  return key ? EIGENE[key] : null
}

/** Szene n: eigenes Bild, sonst ein Ausschnitt des Startbilds (crop = Bildpunkt + Zoom). */
function szene(n, { crop, tags, ...rest }) {
  const eigen = eigenesBild(n)
  return {
    visual: 'scene',
    layout: 'side',
    image: eigen || startScreen,
    crop: eigen ? null : crop,
    tags: eigen ? [] : tags,
    ...rest,
  }
}

// Die Story. layout: wide = Bild über die ganze Breite, side = Bild links, Blase rechts.
export const SLIDES = [
  {
    visual: 'image',
    image: startScreen,
    alt: 'Ein Techniker vor den Monitoren, daneben brennt ein Server-Rack',
    caption: 'DRV Schwaben · Rechenzentrum · Montag, 07:58 Uhr',
    layout: 'wide',
    speaker: KAISER,
    text: 'Alarm im Rechenzentrum! In Raum B-04 brennt ein Server-Rack – ausgerechnet das mit den Rentendaten.',
  },
  szene(2, {
    alt: 'Nahaufnahme: das brennende Server-Rack, Alarmlicht',
    crop: { x: '90%', y: '35%', zoom: 1.9 },
    alarm: true,
    hud: '⚠ SYSTEMAUSFALL IN 09:00',
    speaker: KAISER,
    text: 'Uns bleiben nur ein paar Minuten, bis das System ganz ausfällt. Dann sind die Daten von Millionen Versicherten weg.',
  }),
  szene(3, {
    alt: 'Das Rechenzentrum: Kontrollplatz vor den Monitoren und das Server-Rack',
    crop: { x: '80%', y: '60%', zoom: 1.0 },
    tags: [
      { text: 'LEITSTAND', x: '30%', y: '18%' },
      { text: 'VORDERSEITE', x: '72%', y: '70%' },
      { text: 'RÜCKSEITE', x: '90%', y: '30%' },
    ],
    speaker: KAISER,
    text: 'Ihr drei seid das Notfall-Team: der Leitstand im Kontrollraum, einer vor dem Rack, einer dahinter. Jeder sieht nur seinen Teil – keiner hat die ganze Lösung.',
  }),
  {
    visual: 'notes',
    layout: 'side',
    speaker: KAISER,
    text: 'Meine Wartungsnotizen liegen bei euch – leider zerrissen. Jeder hat ein Stück mit einer Regel. Lest sie euch gegenseitig vor!',
  },
  szene(5, {
    alt: 'Nahaufnahme: der Techniker greift sich an den Kopf, Alarmlicht',
    crop: { x: '56%', y: '55%', zoom: 2.2 },
    alarm: true,
    speaker: KAISER,
    text: 'Und ganz wichtig: Redet miteinander – nicht durcheinander! Jede falsche Eingabe kostet den Server Leben.',
  }),
  {
    visual: 'tutorial',
    layout: 'tutorial',
    tail: 'none',
    speaker: 'So läuft der Einsatz',
    text: 'Kurz die Regeln – dann rettet den Server!',
    tutorial: [
      { icon: '①', text: 'Drei Aufgaben, dann das Finale. Jede gelöste Aufgabe verrät eine Ziffer des Neustart-Codes.' },
      { icon: '♥', text: 'Das Feuer frisst laufend Leben, falsche Eingaben noch mehr. Sind die Leben weg oder läuft die Zeit ab, ist der Server verloren.' },
      { icon: '✎', text: 'Eure Notizzettel (wie links) sagen, wie ihr vorgehen müsst: Die Nummern ①②③ geben die Reihenfolge vor, Rechenbeispiele stehen gleich dabei.' },
      { icon: '⌗', text: 'Rechts auf dem Handy liegt ein Taschenrechner – antippen, dann gleitet er herein.' },
      { icon: '★', text: 'Je schneller und je weniger Hilfe, desto mehr Punkte.' },
    ],
  },
]

const l = (row, style, text) => ({ row, style, text })

// Szene 4: die drei Stücke der Wartungsnotiz (wie in Aufgabe 1)
export const NOTIZ_STUECKE = [
  { id: 'intro-a', title: 'Wartungsnotiz', part: 1, of: 3, torn: ['right', 'bottom'], lines: [
    l(0, 'typed', 'WARTUNGSNOTIZ · TEIL 1/3'),
    l(2, 'rule', '② Code = die Farbfolge'),
    l(3, 'text', 'vom Monitor. Blinkt die LED:'),
    l(4, 'text', 'RÜCKWÄRTS eingeben!'),
  ] },
  { id: 'intro-b', title: 'Wartungsnotiz', part: 2, of: 3, torn: ['left', 'bottom'], lines: [
    l(0, 'stamp', 'NUR FÜR TECHNIKER'),
    l(1, 'typed', 'WARTUNGSNOTIZ · TEIL 2/3'),
    l(3, 'rule', '① NIE das Kabel am'),
    l(4, 'text', 'brennenden Platz kappen!'),
  ] },
  { id: 'intro-c', title: 'Wartungsnotiz', part: 3, of: 3, torn: ['top'], lines: [
    l(0, 'typed', 'WARTUNGSNOTIZ · TEIL 3/3'),
    l(2, 'rule', '③ Aufkleber zerkratzt?'),
    l(3, 'text', 'Dann gilt das Symbol vom'),
    l(4, 'text', 'Kabel am Brandplatz.'),
    l(6, 'sign', '– M. Kaiser, IT'),
  ] },
]

// Tutorial: ein Notizblatt in Originalgröße, mit nummerierten Schritten und Beispiel
export const BEISPIEL_NOTIZ = {
  id: 'intro-beispiel', title: 'Datenrettung', part: 3, of: 3, torn: ['top'], lines: [
    l(0, 'typed', 'DATENRETTUNG · TEIL 3/3'),
    l(2, 'rule', '① Richtige Backup-Platte: das'),
    l(3, 'text', 'NEUESTE Backup mit Status OK.'),
    l(4, 'text', 'Bsp: 03.04. neuer als 28.03.'),
    l(6, 'rule', '⑤ Schlüssel k: Die Key-ID steht'),
    l(7, 'text', 'im Paket-Kopf. Nimm den AKTIVEN.'),
    l(8, 'text', 'Bsp: ID 6 → „KEY-ID 6 · aktiv“'),
    l(10, 'sign', '– M. Kaiser, IT'),
  ],
}

const MINI_TASTEN = ['C', '⌫', '÷', '×', '7', '8', '9', '−', '4', '5', '6', '+', '1', '2', '3', '=']

// Übergang ins Spiel: ein Schritt je outroSpeed ms, danach start
const OUTRO = ['VERBINDE', '3', '2', '1', 'LOS!']
const START_BILD = startScreen
</script>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import TornNote from './TornNote.vue'

const props = defineProps({
  // ms pro Zeichen in der Sprechblase (0 = sofort, z. B. in Tests)
  typeSpeed: { type: Number, default: 24 },
  // ms je Schritt des Übergangs (Verbinden, 3, 2, 1, LOS!); 0 = sofort starten
  outroSpeed: { type: Number, default: 900 },
})
const emit = defineEmits(['start'])

const root = ref(null)
const index = ref(0)
const zeichen = ref(0)
const gestartet = ref(false)
const schritt = ref(-1)   // Übergang: -1 = noch nicht, 0 = Verbinden, 1–3 = Countdown, 4 = LOS!
const outroAktiv = computed(() => schritt.value >= 0)
let outroTimer = null
let timer = null

const slide = computed(() => SLIDES[index.value])
const istLetzte = computed(() => index.value === SLIDES.length - 1)
const tippt = computed(() => zeichen.value < slide.value.text.length)
const getippt = computed(() => slide.value.text.slice(0, zeichen.value))

function ausschnitt(s) {
  if (!s.crop) return {}
  return {
    objectPosition: `${s.crop.x} ${s.crop.y}`,
    transformOrigin: `${s.crop.x} ${s.crop.y}`,
    '--zoom': s.crop.zoom,
  }
}

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
onUnmounted(() => {
  stopp()
  if (outroTimer) clearInterval(outroTimer)
})

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
  if (!props.outroSpeed) { emit('start'); return }
  // erst der Übergang, dann startet das Spiel (die Zeit läuft also erst nach „LOS!“)
  schritt.value = 0
  outroTimer = setInterval(() => {
    schritt.value += 1
    if (schritt.value >= OUTRO.length) {
      clearInterval(outroTimer)
      outroTimer = null
      schritt.value = OUTRO.length - 1   // „LOS!“ bleibt stehen, bis das Spiel da ist
      emit('start')
    }
  }, props.outroSpeed)
}

function taste(e) {
  if (outroAktiv.value) return
  if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); weiter() }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); zurueck() }
  else if (e.key === 'Enter') { e.preventDefault(); istLetzte.value ? starten() : weiter() }
}
</script>

<style scoped>
.intro {
  position: relative;
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
  gap: 36px;
  align-items: center;
}

.intro-scene.is-side { grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); }
.intro-scene.is-wide { grid-template-rows: minmax(0, 1fr) auto; justify-items: center; }
.intro-scene.is-tutorial { grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr); }

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

/* Ausschnitt mit Kamerafahrt: wie ein Kamerabild aus dem Rechenzentrum */
.intro-scene-frame {
  position: relative;
  margin: 0;
  width: 100%;
  aspect-ratio: 16 / 10;
  max-height: 100%;
  overflow: hidden;
  border: 1px solid var(--neon-dim);
  border-radius: 6px;
  box-shadow: 0 0 40px rgba(57, 255, 90, 0.12), inset 0 0 80px rgba(0, 0, 0, 0.8);
  background: #000;
}

.intro-scene-frame img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.intro-scene-frame img.is-crop {
  transform: scale(var(--zoom, 1));
  animation: kamerafahrt 14s ease-in-out infinite alternate;
}

@keyframes kamerafahrt {
  from { transform: scale(var(--zoom, 1)); }
  to { transform: scale(calc(var(--zoom, 1) * 1.1)); }
}

/* Vignette + Scanlines, damit es wie eine Überwachungskamera wirkt */
.intro-scene-frame::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse at center, transparent 55%, rgba(0, 0, 0, 0.7) 100%),
    repeating-linear-gradient(to bottom, rgba(0, 0, 0, 0.18) 0 2px, transparent 2px 4px);
}

/* Alarm: rotes Pulsieren über der Szene */
.intro-scene-frame.is-alarm::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background: radial-gradient(ellipse at 70% 30%, rgba(255, 40, 40, 0.35), transparent 70%);
  animation: alarm 1.4s ease-in-out infinite;
}

@keyframes alarm { 50% { opacity: 0.15; } }

.scene-hud {
  position: absolute;
  z-index: 2;
  left: 18px;
  top: 16px;
  padding: 6px 12px;
  border: 1px solid rgba(255, 80, 80, 0.8);
  background: rgba(40, 0, 0, 0.6);
  color: #ff6b6b;
  font-family: var(--mono);
  font-size: clamp(14px, 1.3vw, 20px);
  font-weight: 700;
  letter-spacing: 0.15em;
  animation: alarm 1.4s ease-in-out infinite;
}

.scene-tag {
  position: absolute;
  z-index: 2;
  transform: translate(-50%, -50%);
  padding: 5px 12px;
  border: 1px solid var(--neon);
  background: rgba(0, 20, 6, 0.75);
  color: var(--neon);
  font-family: var(--mono);
  font-size: clamp(12px, 1.1vw, 17px);
  font-weight: 700;
  letter-spacing: 0.18em;
  box-shadow: 0 0 14px var(--neon-dim);
  animation: tag-rein 0.5s ease-out both;
}

.scene-tag:nth-of-type(2) { animation-delay: 0.4s; }
.scene-tag:nth-of-type(3) { animation-delay: 0.8s; }

@keyframes tag-rein { from { opacity: 0; transform: translate(-50%, -30%); } }

.intro-scene-frame .intro-caption {
  position: absolute;
  z-index: 2;
  left: 18px;
  bottom: 14px;
}

/* Szene 4: die echten Zettel auf dem Tisch */
.intro-notes {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px 24px;
  align-items: start;
  padding: 10px;
}

.intro-note { transform: rotate(var(--r)); animation: zettel 0.6s ease-out both; }
.intro-note:nth-child(2) { margin-top: 60px; animation-delay: 0.2s; }
.intro-note:nth-child(3) { grid-column: 1 / -1; justify-self: center; width: 60%; margin-top: -20px; animation-delay: 0.4s; }

@keyframes zettel { from { opacity: 0; transform: translateY(-30px) rotate(calc(var(--r) * 3)); } }

/* --------------------------------------------------- Tutorial: Notizblatt + Rechner */
.tutorial-visual {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
  height: 100%;
}

.tutorial-note {
  width: min(100%, 470px);
  transform: rotate(-2deg);
}

.calc-mini {
  position: absolute;
  right: 0;
  bottom: 4%;
  width: 200px;
  padding: 10px;
  border-radius: 12px;
  background: linear-gradient(160deg, #3a3f48 0%, #262a31 55%, #1d2026 100%);
  box-shadow: -6px 16px 26px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.12);
  transform: rotate(8deg);
}

.calc-mini-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-family: var(--mono);
  font-size: 8px;
  letter-spacing: 0.15em;
  color: #c9ced6;
}

.calc-mini-top i { width: 36px; height: 7px; background: #3b2e22; border-radius: 2px; }

.calc-mini-lcd {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding: 4px 7px;
  margin-bottom: 7px;
  border-radius: 4px;
  background: linear-gradient(180deg, #b7c6a0, #a6b78e);
  color: #1c2818;
  font-family: var(--mono);
}

.calc-mini-lcd small { font-size: 11px; opacity: 0.75; }
.calc-mini-lcd b { font-size: 24px; }

.calc-mini-keys {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
}

.calc-mini-keys span {
  display: grid;
  place-items: center;
  height: 24px;
  border-radius: 4px;
  background: linear-gradient(180deg, #4a505a, #353a42);
  box-shadow: 0 2px 0 #15171b;
  color: #eef1f5;
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 700;
}

.calc-mini-keys span.op { background: linear-gradient(180deg, #6a5a3a, #4f4329); color: #ffd27a; }
.calc-mini-keys span.eq { background: linear-gradient(180deg, #2f7a4f, #1f5a39); }

/* ------------------------------------------------------------ Sprechblase (Comic) */
.intro-talk {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 960px;
  width: 100%;
}

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
  gap: 10px;
}

.tutorial li {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border: 1px solid var(--neon-dim);
  background: rgba(57, 255, 90, 0.05);
  font-size: clamp(17px, 1.45vw, 24px);
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

/* ------------------------------------------------- Übergang ins Spiel (Outro) */
.intro-outro {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: grid;
  place-items: center;
  overflow: hidden;
  background: #000;
  animation: outro-rein 0.4s ease-out both;
}

/* Kamera fährt aufs brennende Rack zu und wird dabei dunkler */
.outro-bild {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform-origin: 86% 42%;
  animation: outro-zoom var(--outro-ms, 4500ms) cubic-bezier(0.5, 0, 0.75, 0) forwards;
}

.intro-outro::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at center, rgba(0, 0, 0, 0.35), rgba(0, 0, 0, 0.9) 75%),
    repeating-linear-gradient(to bottom, rgba(0, 0, 0, 0.25) 0 2px, transparent 2px 4px);
}

.outro-text {
  position: relative;
  z-index: 1;
  text-align: center;
}

.outro-connect {
  margin: 0;
  font-family: var(--mono);
  font-size: clamp(22px, 2.4vw, 40px);
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--neon);
  text-shadow: 0 0 18px var(--neon-dim);
}

.outro-dots { animation: blink 0.6s steps(1) infinite; }

.outro-count {
  display: block;
  font-family: var(--mono);
  font-size: clamp(140px, 22vw, 320px);
  font-weight: 700;
  line-height: 1;
  color: var(--neon);
  text-shadow: 0 0 40px var(--neon), 0 0 120px rgba(57, 255, 90, 0.5);
  animation: zahl 0.9s cubic-bezier(0.2, 0.9, 0.3, 1) both;
}

.outro-count.is-los {
  font-size: clamp(120px, 18vw, 260px);
  color: #fff;
  text-shadow: 0 0 30px var(--neon), 0 0 90px var(--neon);
  animation: los 0.9s ease-out both;
}

@keyframes outro-rein { from { opacity: 0; } }
@keyframes outro-zoom {
  from { transform: scale(1); filter: brightness(1); }
  to { transform: scale(3.4); filter: brightness(0.35); }
}
@keyframes zahl {
  from { transform: scale(1.8); opacity: 0; }
  25% { opacity: 1; }
  to { transform: scale(0.9); opacity: 0.85; }
}
@keyframes los {
  from { transform: scale(0.6); opacity: 0; }
  30% { transform: scale(1.1); opacity: 1; }
  to { transform: scale(1.4); opacity: 0; }
}

@media (max-width: 900px) {
  .intro { padding: 16px; }
  .intro-scene.is-side, .intro-scene.is-tutorial { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  .bubble, .tutorial li, .intro-start, .intro-note, .scene-tag,
  .intro-scene-frame img.is-crop, .intro-scene-frame.is-alarm::before, .scene-hud,
  .outro-bild, .outro-count, .intro-outro { animation: none; }
  .szene-enter-active, .szene-leave-active { transition: none; }
}
</style>
