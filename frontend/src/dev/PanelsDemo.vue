<!--
  Nur für die Entwicklung: Vorschau der Effekt-Panels ohne Backend.
  Aufruf mit laufendem Vite-Dev-Server: http://localhost:5173/panels-demo.html
  Wird von `vite build` nicht mitgebaut (eigener Einstieg, nicht in index.html).
  Neue Panels bekommen hier eine eigene <section>.
-->
<template>
  <main class="demo">
    <header>
      <h1>Panel-Vorschau</h1>
    </header>

    <section>
      <h2>Kabelpanel · Aufgabe 1 Vorderseite</h2>
      <p class="hint">Richtiges Kabel in dieser Vorschau: <b>{{ WIRES[RICHTIG] }}</b> (Steckplatz {{ RICHTIG + 1 }})</p>
      <WirePanel :wires="WIRES" :state="wireState" :seconds="sekunden" @cut="pruefeKabel" />
      <div class="actions"><button @click="wireState = 'armed'; sekunden = 95">Zurücksetzen</button></div>
    </section>

    <section>
      <h2>Steuerpult · Aufgabe 2 Vorderseite</h2>
      <p v-if="deskState !== 'done'" class="hint">
        Erwartet in dieser Vorschau: <b>{{ SEQUENZ[deskStep] }}</b>
        (Schritt {{ deskStep + 1 }} von {{ SEQUENZ.length }}) — falsch auslösen zeigt den Fehlerfall.
      </p>
      <p v-else class="hint">Alle {{ SEQUENZ.length }} Schritte geflutet — „Zurücksetzen" startet neu.</p>
      <ControlDesk
        :valves="VALVES"
        :colors="COLORS"
        :step="deskStep"
        :sequence-len="SEQUENZ.length"
        :state="deskState"
        @submit="pruefeSchritt"
      />
      <div class="actions"><button @click="deskZuruecksetzen">Zurücksetzen</button></div>
    </section>
  </main>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import WirePanel from '../components/WirePanel.vue'
import ControlDesk from '../components/ControlDesk.vue'

const WIRES = ['raute', 'dreieck', 'quadrat', 'kreis']
const RICHTIG = 2
const wireState = ref('armed')
const sekunden = ref(95)
setInterval(() => { if (wireState.value !== "defused" && sekunden.value > 0) sekunden.value -= 1 }, 1000)

function pruefeKabel({ index }) {
  wireState.value = 'checking'
  setTimeout(() => {
    wireState.value = index === RICHTIG ? 'defused' : 'error'
    if (index !== RICHTIG) setTimeout(() => (wireState.value = 'armed'), 1200)
  }, 900)
}

// --- Steuerpult: simuliert Backend (Prüfung + Fortschritt) ---
const VALVES = ['V-31', 'V-32', 'V-33']
const COLORS = ['ORANGE', 'RED', 'GREEN']
const SEQUENZ = ['V-32:RED', 'V-31:ORANGE', 'V-33:GREEN']
const deskStep = ref(0)
const deskState = ref('idle')
let deskTimer = null

function pruefeSchritt(wert) {
  deskState.value = 'checking'
  clearTimeout(deskTimer)
  deskTimer = setTimeout(() => {
    if (wert !== SEQUENZ[deskStep.value]) {
      deskState.value = 'error'
      deskTimer = setTimeout(() => (deskState.value = 'idle'), 1300)
      return
    }
    deskStep.value += 1
    deskState.value = deskStep.value >= SEQUENZ.length ? 'done' : 'idle'
  }, 700)
}

function deskZuruecksetzen() {
  clearTimeout(deskTimer)
  deskStep.value = 0
  deskState.value = 'idle'
}

onBeforeUnmount(() => clearTimeout(deskTimer))
</script>

<style>
body { margin: 0; background: #070a08; }
.demo {
  min-height: 100vh; padding: 24px 16px 48px; box-sizing: border-box;
  display: grid; gap: 40px; justify-items: center; align-content: start;
  color: #e0ebe4; font-family: 'Share Tech Mono', ui-monospace, monospace;
}
.demo header { text-align: center; }
.demo h1 { margin: 0; color: #00ff66; letter-spacing: 3px; }
.demo h2 { font-size: 15px; color: #a3b5a9; letter-spacing: 2px; text-align: center; }
.demo section { width: min(640px, 100%); }
.demo .hint { text-align: center; color: #5a9a73; font-size: 13px; }
.demo .actions { display: flex; gap: 12px; justify-content: center; margin-top: 16px; }
.demo .actions button {
  font: inherit; padding: 8px 14px; cursor: pointer;
  color: #00ff66; background: #0f1611; border: 1px solid rgba(0, 255, 102, .35);
}
</style>
