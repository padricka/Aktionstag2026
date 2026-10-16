<template>
  <div class="app">

    <!-- OVERLAY / MODAL SETTINGS -->
    <div v-if="showStartMenuSettings" class="settings-overlay">
      <div class="settings-modal-wrapper">
        <button class="close-btn" @click="showStartMenuSettings = false">
          [ X ] CLOSE_SETTINGS
        </button>
        <SettingsScreen @save="showStartMenuSettings = false" />
      </div>
    </div>

    <!-- Startmenü -->
    <StartMenu
      v-else-if="!gestartet"
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

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import StartMenu from './StartMenu.vue'
import HostScreen from './components/HostScreen.vue'
import PlayerScreen from './components/PlayerScreen.vue'
import SettingsScreen from './components/SettingsScreen.vue'

const gestartet = ref(false)
const role = ref(null)
const playerName = ref('')
const showStartMenuSettings = ref(false)

// Init Theme on Load (in case settings screen isn't opened first)
onMounted(() => {
  const saved = localStorage.getItem('drv_game_settings')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      if (parsed.theme) {
        document.documentElement.classList.remove('theme-light', 'theme-girl', 'theme-dark')
        document.documentElement.classList.add(`theme-${parsed.theme}`)
      }
    } catch (e) { /* ignore */ }
  }

  // Sparkle Mouse Trail Logic
  window.addEventListener('mousemove', handleMouseMove)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
})

let lastSparkleTime = 0
function handleMouseMove(e) {
  // Only apply sparkle effect in Girl Mode
  if (!document.documentElement.classList.contains('theme-girl')) return

  const now = Date.now()
  // Limit creation rate to ~20 sparkles per second (50ms interval)
  if (now - lastSparkleTime < 50) return
  lastSparkleTime = now

  const sparkle = document.createElement('div')
  sparkle.className = 'sparkle'
  sparkle.style.left = `${e.clientX}px`
  sparkle.style.top = `${e.clientY}px`

  // Randomize scale/rotation slightly for better effect
  const scale = 0.5 + Math.random() * 1.0
  const rotation = Math.random() * 360
  sparkle.style.transform = `translate(-50%, -50%) scale(${scale}) rotate(${rotation}deg)`

  document.body.appendChild(sparkle)

  // Remove the element after animation completes (600ms)
  setTimeout(() => {
    if (document.body.contains(sparkle)) {
      document.body.removeChild(sparkle)
    }
  }, 600)
}

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