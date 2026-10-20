<!--
  Teilekiste — nur beim Leitstand (GAME_DESIGN.md, „Fundorte und Teilekiste“).

  Zu: eine Kunststoffkiste liegt schräg und halb im Bild am linken Rand (der
  Taschenrechner liegt rechts), oben die Zahl der gefundenen Teile. Ein Klick zieht
  sie herein, die Aufgabe rückt zur Seite (v-model:open, wie beim Taschenrechner).
  Drei Fächer: Netzteil, Lüfter, Backup-Platte – gefunden mit Etikett, sonst nur der
  Umriss. Die Etiketten braucht das Team im Finale. Kommt ein Teil dazu, wackelt sie kurz.
-->
<template>
  <div class="kiste" :class="{ 'is-open': offen }">
    <section
      ref="panel"
      class="kiste-panel"
      :class="{ 'is-neu': neu }"
      tabindex="-1"
      aria-label="Teilekiste"
      @keydown.esc.prevent="schliessen"
    >
      <button
        v-if="!offen"
        class="kiste-handle"
        type="button"
        aria-expanded="false"
        aria-controls="kiste-body"
        :aria-label="`Teilekiste hervorziehen (${teile.length} von 3 Teilen)`"
        title="Teilekiste"
        @click="oeffnen"
      ></button>

      <div class="kiste-top">
        <span class="kiste-titel">TEILEKISTE</span>
        <span class="kiste-zahl">{{ teile.length }}/3</span>
      </div>

      <div id="kiste-body" class="kiste-body" :inert="offen ? null : true">
        <ul class="kiste-faecher">
          <li
            v-for="f in faecher"
            :key="f.id"
            class="kiste-fach"
            :class="{ 'is-da': f.teil }"
          >
            <TeilGrafik class="kiste-grafik" :teil="f.id" :leer="!f.teil" />
            <span class="kiste-name">{{ f.name }}</span>
            <span v-if="f.teil && f.teil.label" class="kiste-etikett">{{ f.teil.label }}</span>
            <span v-else-if="!f.teil" class="kiste-fehlt">noch nicht gefunden</span>
          </li>
        </ul>

        <button class="kiste-close" type="button" @click="schliessen">
          <span aria-hidden="true">‹</span> Wegschieben
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import TeilGrafik from './TeilGrafik.vue'
import { TEILE, TEIL_REIHENFOLGE } from '../utils/teile.js'

const props = defineProps({
  teile: { type: Array, default: () => [] },   // game_tick.parts
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['update:open'])

const offen = ref(props.open)
const panel = ref(null)
const neu = ref(false)
let neuTimer = null

watch(() => props.open, (v) => { offen.value = v })
watch(() => props.teile.length, (jetzt, vorher) => {
  if (jetzt > vorher) {
    neu.value = true
    clearTimeout(neuTimer)
    neuTimer = setTimeout(() => { neu.value = false }, 1200)
  }
})
onUnmounted(() => clearTimeout(neuTimer))

const faecher = computed(() =>
  TEIL_REIHENFOLGE.map((id) => ({
    id,
    name: TEILE[id].name,
    teil: props.teile.find((t) => t.id === id) || null,
  }))
)

async function oeffnen() {
  offen.value = true
  emit('update:open', true)
  await nextTick()
  panel.value?.focus({ preventScroll: true })
}

function schliessen() {
  offen.value = false
  emit('update:open', false)
}
</script>

<style scoped>
.kiste-panel {
  --kiste-ease: cubic-bezier(0.22, 1, 0.36, 1);
  position: fixed;
  left: 24px;
  bottom: 24px;
  z-index: 40;
  width: 260px;
  padding: 12px 14px 10px;
  box-sizing: border-box;
  border-radius: 10px 10px 14px 14px;
  /* graugrüne Kunststoffkiste mit Rippen */
  background:
    repeating-linear-gradient(90deg, transparent 0 22px, rgba(0, 0, 0, 0.12) 22px 25px),
    linear-gradient(170deg, #4d5b52 0%, #36423a 55%, #29332d 100%);
  box-shadow:
    6px 22px 34px rgba(0, 0, 0, 0.55),
    inset 0 2px 0 rgba(255, 255, 255, 0.12),
    inset 0 -5px 0 rgba(0, 0, 0, 0.4);
  outline: none;
  transform-origin: 0 100%;
  /* zu: halb über den linken Rand hinaus, schräg abgestellt */
  transform: translateX(-62%) translateY(14px) rotate(12deg);
  transition: transform 0.6s var(--kiste-ease), box-shadow 0.6s var(--kiste-ease);
}

.kiste:not(.is-open) .kiste-panel:hover {
  transform: translateX(-54%) translateY(8px) rotate(9deg);
}

.is-open .kiste-panel { transform: none; }

.kiste-panel.is-neu { animation: wackeln 0.6s ease-in-out 2; }

.kiste-handle {
  position: absolute;
  inset: 0;
  z-index: 2;
  border: none;
  border-radius: inherit;
  background: transparent;
  cursor: grab;
}
.kiste-handle:focus-visible { outline: 2px solid var(--green); outline-offset: 3px; }

.kiste-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.28);
  border-radius: 4px;
  font-family: var(--mono);
}
.kiste-titel { font-size: 11px; font-weight: 700; letter-spacing: 0.2em; color: #d7e2d9; }
.kiste-zahl {
  min-width: 34px;
  padding: 2px 6px;
  border-radius: 3px;
  background: #ffd23a;
  color: #1a1d22;
  font-size: 13px;
  font-weight: 700;
  text-align: center;
}

.kiste-body { display: flex; flex-direction: column; gap: 10px; }
.kiste-faecher { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }

.kiste-fach {
  display: grid;
  grid-template-columns: 76px 1fr;
  grid-template-rows: auto auto;
  column-gap: 10px;
  align-items: center;
  padding: 8px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.35);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.5);
  font-family: var(--mono);
}
.kiste-grafik { grid-row: span 2; }
.kiste-name { font-size: 13px; font-weight: 700; color: var(--fg-2); }
.kiste-fach.is-da .kiste-name { color: var(--fg); }
.kiste-etikett {
  justify-self: start;
  padding: 2px 6px;
  background: #f3eee1;
  color: #1a1d22;
  font-size: 12px;
  font-weight: 700;
  transform: rotate(-2deg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
.kiste-fehlt { font-size: 11px; color: var(--fg-3); }

.kiste-close {
  align-self: center;
  padding: 4px 10px;
  border: none;
  background: none;
  color: #b9c6bc;
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  cursor: pointer;
}
.kiste-close:hover { color: var(--green); }

@keyframes wackeln {
  0%, 100% { rotate: 0deg; }
  25% { rotate: -3deg; }
  75% { rotate: 3deg; }
}

/* Handy: liegt unten links, kommt von unten */
@media (max-width: 700px) {
  .kiste-panel {
    left: 12px;
    bottom: 12px;
    transform: translateY(66%) translateX(-10%) rotate(8deg) scale(0.85);
  }
  .kiste:not(.is-open) .kiste-panel:hover { transform: translateY(60%) translateX(-10%) rotate(6deg) scale(0.85); }
  .is-open .kiste-panel { transform: scale(0.85); }
}

@media (prefers-reduced-motion: reduce) {
  .kiste-panel { transition: none; }
  .kiste-panel.is-neu { animation: none; }
}
</style>
