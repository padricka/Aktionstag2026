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
            type="button"
            class="btn"
            :class="{ active: settings.theme === 'dark' }"
            @click="setTheme('dark')"
          >
            Dark
          </button>
          <button
            type="button"
            class="btn"
            :class="{ active: settings.theme === 'light' }"
            @click="setTheme('light')"
          >
            Light
          </button>
          <button
            type="button"
            class="btn"
            :class="{ active: settings.theme === 'girl' }"
            @click="setTheme('girl')"
          >
            Girl
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
          class="slider"
          @input="applyBrightness"
        />
      </div>

      <div class="setting">
        <div class="setting-info">
          <span class="setting-name">Scanlines</span>
          <span class="setting-value mono">{{ settings.scanlinesEnabled ? 'an' : 'aus' }}</span>
        </div>
        <button
          type="button"
          class="btn"
          :class="{ active: settings.scanlinesEnabled }"
          @click="toggleScanlines"
        >
          {{ settings.scanlinesEnabled ? 'Deaktivieren' : 'Aktivieren' }}
        </button>
      </div>
    </section>

    <section class="settings-section audio-stub">
      <h2 class="label">Audio</h2>
      <p class="stub-note">Noch nicht verdrahtet — Werte werden gespeichert, ändern aber noch keinen Sound.</p>

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
          type="button"
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
          type="button"
          class="btn"
          :class="{ active: settings.sfxEnabled }"
          @click="settings.sfxEnabled = !settings.sfxEnabled"
        >
          {{ settings.sfxEnabled ? 'Deaktivieren' : 'Aktivieren' }}
        </button>
      </div>
    </section>

    <footer class="settings-actions">
      <button type="button" class="btn" @click="resetToDefaults">Zurücksetzen</button>
      <button type="button" class="btn btn-primary" @click="saveAndClose">Speichern</button>
    </footer>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'

const emit = defineEmits(['save'])

const DEFAULT_SETTINGS = {
  theme: 'dark',
  brightness: 100,
  scanlinesEnabled: false,
  masterVolume: 80,
  musicEnabled: true,
  musicVolume: 60,
  sfxEnabled: true,
}

const settings = reactive({ ...DEFAULT_SETTINGS })

onMounted(() => {
  const saved = localStorage.getItem('drv_game_settings')
  if (saved) {
    try {
      Object.assign(settings, { ...DEFAULT_SETTINGS, ...JSON.parse(saved) })
      if ((settings.theme === 'girl' || settings.theme === 'light') && settings.scanlinesEnabled) {
        settings.scanlinesEnabled = false
        localStorage.setItem('drv_game_settings', JSON.stringify({ ...settings }))
      }
    } catch (e) { /* ignore */ }
  }
  applyAll()
})

function applyTheme() {
  const root = document.documentElement
  root.classList.remove('theme-light', 'theme-girl', 'theme-dark')
  root.classList.add(`theme-${settings.theme || 'dark'}`)
}

function applyBrightness() {
  document.documentElement.style.filter = `brightness(${settings.brightness}%)`
}

function applyScanlines() {
  document.documentElement.classList.toggle('scanlines', !!settings.scanlinesEnabled)
}

function applyAll() {
  applyTheme()
  applyBrightness()
  applyScanlines()
}

function setTheme(theme) {
  settings.theme = theme
  // Girl/Light + dichte Scanlines = unlesbar — beim Wechsel aus
  if ((theme === 'girl' || theme === 'light') && settings.scanlinesEnabled) {
    settings.scanlinesEnabled = false
    applyScanlines()
  }
  applyTheme()
}

function toggleScanlines() {
  settings.scanlinesEnabled = !settings.scanlinesEnabled
  applyScanlines()
}

function saveAndClose() {
  localStorage.setItem('drv_game_settings', JSON.stringify({ ...settings }))
  applyAll()
  emit('save')
}

function resetToDefaults() {
  Object.assign(settings, DEFAULT_SETTINGS)
  localStorage.setItem('drv_game_settings', JSON.stringify(DEFAULT_SETTINGS))
  applyAll()
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
  color: var(--fg-2);
}

.settings-section {
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--border);
}

.settings-section:last-of-type { border-bottom: none; }

.settings-section h2 {
  margin: 0 0 var(--space-3) 0;
}

.stub-note {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--amber);
  margin: 0 0 var(--space-3) 0;
  letter-spacing: 0.02em;
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

.theme-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
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

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border);
  margin-top: var(--space-3);
}
</style>
