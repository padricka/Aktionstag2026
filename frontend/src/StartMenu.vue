<template>
  <div class="start">
    <div class="hero">
      <img src="./assets/start-screen2.jpg" alt="" />
    </div>

    <div class="overlay">
      <div class="top">
        <button type="button" class="settings-link" @click="openSettings">
          Einstellungen
        </button>
      </div>

      <div class="content">
        <h1 class="title">DRV-BOX</h1>
        <p class="sub">Rettet den Server!</p>

        <div class="form">
          <label class="field">
            <span class="label">Dein Name</span>
            <input
              v-model="name"
              class="input"
              placeholder="z.B. Patrick"
              maxlength="20"
              @keyup.enter="starten('player')"
            />
          </label>

          <div class="actions">
            <button
              class="btn btn-primary"
              :disabled="!name.trim()"
              @click="starten('player')"
            >
              Als Spieler
            </button>
            <button class="btn-host" @click="starten('host')">
              Als Host
            </button>
          </div>
        </div>
      </div>

      <div class="bottom">
        <span class="version">v1.0</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const name = ref('')
const emit = defineEmits(['spiel-starten', 'open-settings'])

function starten(role) {
  if (role === 'player' && !name.value.trim()) return
  emit('spiel-starten', { name: name.value.trim(), role })
}

function openSettings() {
  emit('open-settings')
}
</script>

<style scoped>
.start {
  position: relative;
  height: 100dvh;
  width: 100vw;
  overflow: hidden;
  background: var(--bg);
}

.hero {
  position: absolute;
  inset: 0;
}

.hero img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.5;
  filter: brightness(0.8);
}

.overlay {
  position: relative;
  z-index: 2;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 40px 60px;
  background: linear-gradient(
    180deg,
    rgba(10, 15, 12, 0.75) 0%,
    rgba(10, 15, 12, 0.4) 40%,
    rgba(10, 15, 12, 0.92) 100%
  );
}

.top {
  display: flex;
  justify-content: flex-end;
}

.settings-link {
  background: rgba(5, 10, 8, 0.75);
  border: 1px solid var(--green-border);
  color: var(--green);
  font-family: var(--mono);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 10px 14px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.settings-link:hover {
  background: var(--green-bg);
  border-color: var(--green);
  color: #fff;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  max-width: 720px;
}

.title {
  font-family: var(--mono);
  font-size: 72px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  line-height: 0.95;
  letter-spacing: -0.03em;
}

.sub {
  font-family: var(--sans);
  font-size: 20px;
  color: var(--green);
  margin: 0 0 28px 0;
  letter-spacing: 0.02em;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 420px;
}

/* ---- HIER WAR DER FEHLENDE BLOCK ---- */
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.label {
  font-family: var(--sans);
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.input {
  width: 100%;
  padding: 12px 14px;
  background: var(--bg);
  color: var(--fg);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 15px;
  outline: none;
}

.input:focus { border-color: var(--green-border); }

.actions {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 8px;
}

.btn-primary {
  padding: 14px;
  background: var(--green);
  color: #050a08;
  border: none;
  font-family: var(--mono);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 0.1em;
  transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) { background: #4dff8f; }
.btn-primary:disabled { opacity: 0.35; cursor: not-allowed; }

.btn-host {
  padding: 14px;
  background: transparent;
  color: var(--fg-2);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 0.1em;
}

.btn-host:hover {
  color: var(--green);
  border-color: var(--green-border);
}

.bottom {
  display: flex;
  justify-content: flex-start;
}

.version {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.1em;
}

@media (max-width: 800px) {
  .title { font-size: 48px; }
  .sub { font-size: 16px; }
  .overlay { padding: 24px; }
}
</style>