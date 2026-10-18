<template>
  <div class="app">

    <!-- Startmenü -->
    <StartMenu
      v-if="!gestartet"
      @spiel-starten="onStart"
      @open-settings="showStartMenuSettings = true"
    />

    <!-- Host (Beamer) -->
    <HostScreen
      v-else-if="role === 'host'"
      @exit="zurueck"
    />

    <!-- Spieler / Master (Laptop) -->
    <PlayerScreen
      v-else
      :player-name="playerName"
      @exit="zurueck"
    />

    <!-- Einstellungen über dem Startmenü (nicht v-else — sonst verschwindet der Menüpunkt) -->
    <div v-if="showStartMenuSettings" class="settings-overlay">
      <div class="settings-modal-wrapper">
        <button class="close-btn" @click="showStartMenuSettings = false">
          Schließen
        </button>
        <SettingsScreen @save="showStartMenuSettings = false" />
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import StartMenu from './StartMenu.vue'
import HostScreen from './components/HostScreen.vue'
import PlayerScreen from './components/PlayerScreen.vue'
import SettingsScreen from './components/SettingsScreen.vue'

const gestartet = ref(false)
const role = ref(null)
const playerName = ref('')
const showStartMenuSettings = ref(false)

function onStart(daten) {
  gestartet.value = true
  role.value = daten?.role ?? 'player'
  playerName.value = daten?.name ?? ''
}

function zurueck() {
  gestartet.value = false
  role.value = null
  playerName.value = ''
}
</script>

<style scoped>
.app {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}

.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 10, 8, 0.92);
  display: flex;
  justify-content: center;
  padding: 48px 24px;
  z-index: 100;
  overflow-y: auto;
}

.settings-modal-wrapper {
  position: relative;
  width: 100%;
  max-width: 640px;
}

.close-btn {
  background: transparent;
  border: 1px solid #ff0055;
  color: #ff0055;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.85rem;
  margin-bottom: 1rem;
  display: block;
  margin-left: auto;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #ff0055;
  color: #fff;
}
</style>