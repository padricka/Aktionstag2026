<!--
  Nur für die Entwicklung: Vorschau des Tresors ohne Backend.
  Aufruf mit laufendem Vite-Dev-Server: http://localhost:5173/vault-demo.html
  Wird von `vite build` nicht mitgebaut (eigener Einstieg, nicht in index.html).
-->
<template>
  <main class="demo theme-dark">
    <header>
      <h1>Tresor-Vorschau</h1>
      <p>Lösungscode dieser Vorschau: <b>{{ CODE.join('') }}</b></p>
    </header>

    <section>
      <h2>Beamer (zeigt gefundene Ziffern)</h2>
      <VaultDoor mode="display" :digits="gefunden" :state="beamerState" />
      <div class="actions">
        <button @click="ziffer()" :disabled="gefunden.every((d) => d !== null)">Aufgabe gelöst → Ziffer finden</button>
        <button @click="reset()">Zurücksetzen</button>
      </div>
    </section>

    <section>
      <h2>Leitstand (Code eingeben)</h2>
      <VaultDoor mode="input" :state="inputState" @unlock="pruefe" />
      <p class="hint">Räder: oben/unten klicken, Mausrad oder Pfeiltasten. Dann „Öffnen".</p>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import VaultDoor from '../components/VaultDoor.vue'

const CODE = [4, 7, 2]
const gefunden = ref([null, null, null])
const beamerState = ref('locked')
const inputState = ref('locked')

function ziffer() {
  const i = gefunden.value.findIndex((d) => d === null)
  if (i >= 0) gefunden.value = gefunden.value.map((d, j) => (j === i ? CODE[i] : d))
}

function reset() {
  gefunden.value = [null, null, null]
  beamerState.value = 'locked'
  inputState.value = 'locked'
}

function pruefe(code) {
  inputState.value = 'checking'
  setTimeout(() => {
    const ok = code === CODE.join('')
    inputState.value = ok ? 'open' : 'error'
    if (ok) beamerState.value = 'open'
    else setTimeout(() => (inputState.value = 'locked'), 900)
  }, 1100)
}
</script>

<style>
body { margin: 0; background: #070a08; }
.demo {
  min-height: 100vh; padding: 24px 16px 48px; box-sizing: border-box;
  display: grid; gap: 40px; justify-items: center;
  color: #e0ebe4; font-family: 'Share Tech Mono', ui-monospace, monospace;
}
.demo header { text-align: center; }
.demo h1 { margin: 0 0 6px; color: #00ff66; letter-spacing: 3px; }
.demo h2 { font-size: 15px; color: #a3b5a9; letter-spacing: 2px; text-align: center; }
.demo section { width: min(640px, 100%); }
.demo .actions { display: flex; gap: 12px; justify-content: center; margin-top: 16px; flex-wrap: wrap; }
.demo button {
  font: inherit; padding: 8px 14px; cursor: pointer;
  color: #00ff66; background: #0f1611; border: 1px solid rgba(0, 255, 102, .35);
}
.demo button:disabled { opacity: .4; cursor: default; }
.demo .hint { text-align: center; color: #5a9a73; font-size: 13px; }
</style>
