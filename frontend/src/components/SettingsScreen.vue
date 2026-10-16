<template>
  <div class="settings panel">
    <header class="settings-head">
      <h1>Einstellungen</h1>
      <p class="muted">Darstellung und Audio</p>
    </header>

    <section class="settings-section">
      <h2 class="label">Darstellung</h2>

      <div class="setting">
        <div class="setting-info">
          <span class="setting-name">Thema</span>
        </div>
        <div class="theme-actions">
          <button
            class="btn"
            :class="{ active: settings.theme === 'dark' }"
            @click="settings.theme = 'dark'; applyTheme()"
          >
            Dark Mode
          </button>
          <button
            class="btn"
            :class="{ active: settings.theme === 'light' }"
            @click="settings.theme = 'light'; applyTheme()"
          >
            Light Mode
          </button>
          <button
            class="btn"
            :class="{ active: settings.theme === 'girl' }"
            @click="settings.theme = 'girl'; applyTheme()"
          >
            Girl Mode
          </button>
        </div>
      </div>

      <div class="setting">
        <div class="setting-info">
          <span class="setting-name">Helligkeit</span>
          <span class="setting-value mono">{{ settings.brightness }} %</span>
        </div>
        <input
          type="range" min="25" max="100"
          v-model.number="settings.brightness"
          @input="applyBrightness"
          class="slider"
        />
      </div>

      <div class="setting">
        <div class="setting-info">
          <span class="setting-name">Scanlines</span>
          <span class="setting-value mono">{{ settings.scanlinesEnabled ? 'an' : 'aus' }}</span>
        </div>
        <button
          class="btn"
          :class="{ active: settings.scanlinesEnabled }"
          @click="settings.scanlinesEnabled = !settings.scanlinesEnabled"
        >
          {{ settings.scanlinesEnabled ? 'Deaktivieren' : 'Aktivieren' }}
        </button>
      </div>
    </section>

    <section class="settings-section">
      <h2 class="label">Audio</h2>

      <div class="setting">
        <div class="setting-info">
          <span class="setting-name">Lautstärke</span>
          <span class="setting-value mono">{{ settings.masterVolume }} %</span>
        </div>
        <input
          type="range" min="0" max="100"
          v-model.number="settings.masterVolume"
          class="slider"
        />
      </div>

      <div class="setting">
        <div class="setting-info">
          <span class="setting-name">Hintergrundmusik</span>
          <span class="setting-value mono">{{ settings.musicEnabled ? 'an' : 'aus' }}</span>
        </div>
        <button
          class="btn"
          :class="{ active: settings.musicEnabled }"
          @click="settings.musicEnabled = !settings.musicEnabled"
        >
          {{ settings.musicEnabled ? 'Deaktivieren' : 'Aktivieren' }}
        </button>
      </div>

      <div v-if="settings.musicEnabled" class="setting">
        <div class="setting-info">
          <span class="setting-name">Musiklautstärke</span>
          <span class="setting-value mono">{{ settings.musicVolume }} %</span>
        </div>
        <input
          type="range" min="0" max="100"
          v-model.number="settings.musicVolume"
          class="slider"
        />
      </div>

      <div class="setting">
        <div class="setting-info">
          <span class="setting-name">Soundeffekte</span>
          <span class="setting-value mono">{{ settings.sfxEnabled ? 'an' : 'aus' }}</span>
        </div>
        <button
          class="btn"
          :class="{ active: settings.sfxEnabled }"
          @click="settings.sfxEnabled = !settings.sfxEnabled"
        >
          {{ settings.sfxEnabled ? 'Deaktivieren' : 'Aktivieren' }}
        </button>
      </div>
    </section>

    <footer class="settings-actions">
      <button class="btn" @click="resetToDefaults">Zurücksetzen</button>
      <button class="btn btn-primary" @click="saveAndClose">Speichern</button>
    </footer>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'

const emit = defineEmits(['save'])

const DEFAULT_SETTINGS = {
  brightness: 100,
  scanlinesEnabled: true,
  masterVolume: 80,
  musicEnabled: true,
  musicVolume: 60,
  sfxEnabled: true,
  theme: 'dark'
}

const settings = reactive({ ...DEFAULT_SETTINGS })

onMounted(() => {
  const saved = localStorage.getItem('drv_game_settings')
  if (saved) {
    try { Object.assign(settings, JSON.parse(saved)) } catch (e) { /* ignore */ }
  }
  applyBrightness()
  applyTheme()
})

function applyBrightness() {
  document.documentElement.style.filter = `brightness(${settings.brightness}%)`
}

function applyTheme() {
  document.documentElement.classList.remove('theme-light', 'theme-girl', 'theme-dark')
  if (settings.theme === 'light') {
    document.documentElement.classList.add('theme-light')
  } else if (settings.theme === 'girl') {
    document.documentElement.classList.add('theme-girl')
  } else {
    document.documentElement.classList.add('theme-dark')
  }
}

function saveAndClose() {
  localStorage.setItem('drv_game_settings', JSON.stringify(settings))
  applyBrightness()
  applyTheme()
  emit('save')
}

function resetToDefaults() {
  Object.assign(settings, DEFAULT_SETTINGS)
  localStorage.setItem('drv_game_settings', JSON.stringify(DEFAULT_SETTINGS))
  applyBrightness()
  applyTheme()
}
</script>

<style scoped>
.settings {
  padding: var(--space-5);
  color: var(--fg);
}

.settings-head {
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--space-3);
}

.settings-head h1 {
  font-family: var(--sans);
  font-size: var(--text-lg);
  font-weight: 700;
  margin: 0 0 4px 0;
}

.settings-head p {
  font-size: var(--text-sm);
  margin: 0;
}

.settings-section {
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--border);
}

.settings-section:last-of-type { border-bottom: none; }

.settings-section h2 {
  margin: 0 0 var(--space-3) 0;
}

.setting {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-2) 0;
}

.setting-info {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.setting-name {
  font-family: var(--sans);
  font-size: var(--text-sm);
  color: var(--fg);
}

.setting-value {
  font-size: var(--text-xs);
  color: var(--fg-3);
}

.slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 4px;
  background: var(--bg-3);
  border-radius: 2px;
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  background: var(--green);
  border-radius: 50%;
  cursor: pointer;
}

.slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  background: var(--green);
  border: none;
  border-radius: 50%;
  cursor: pointer;
}

.btn.active {
  border-color: var(--green-border);
  color: var(--green);
  background: var(--green-bg);
}

.theme-actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border);
  margin-top: var(--space-3);
}
</style>