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
      <h2>Sync-Knopf · Aufgabe 3 Vorder- und Rückseite</h2>
      <p class="hint">
        Klappe öffnen, dann drücken. Der Partner drückt in dieser Vorschau nach 1,6 s mit —
        „Partner verpasst" zeigt den Fehlerfall (Ring rot, danach wieder bereit).
      </p>
      <SyncButton :unlocked="syncFrei" :state="syncState" @press="drueckeSync" />
      <div class="actions">
        <button @click="syncFrei = !syncFrei">{{ syncFrei ? 'Verplomben' : 'Freischalten' }}</button>
        <button @click="partnerVerpasst">Partner verpasst</button>
        <button @click="zuruecksetzen">Zurücksetzen</button>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import WirePanel from '../components/WirePanel.vue'
import SyncButton from '../components/SyncButton.vue'

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

// --- Sync-Knopf: simuliert Backend + Partner ---
const syncFrei = ref(true)
const syncState = ref('idle')
let syncTimer = null

function drueckeSync() {
  syncState.value = 'waiting'
  clearTimeout(syncTimer)
  syncTimer = setTimeout(() => (syncState.value = 'synced'), 1600)
}

function partnerVerpasst() {
  clearTimeout(syncTimer)
  syncState.value = 'error'
  syncTimer = setTimeout(() => (syncState.value = 'idle'), 1400)
}

function zuruecksetzen() {
  clearTimeout(syncTimer)
  syncState.value = 'idle'
}

onBeforeUnmount(() => clearTimeout(syncTimer))
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
