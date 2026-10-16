<template>
  <div class="master-container">
    <!-- AUTHENTIFIZIERUNG (JOIN SECTION) -->
    <div v-if="!hasJoined" class="auth-section">
      <h3 class="section-title">// MASTER_AUTHENTICATION</h3>
      <p class="section-subtitle">Game ID zur Überwachung eingeben:</p>

      <button
        class="btn-connect"
        :disabled="!gameId.trim()"
        @click="handleJoin"
      >
        Verbinden
      </button>
    </div>

    <template v-else>
      <header class="master-bar">
        <span class="master-role">Master</span>
        <span class="master-session">{{ gameId.toUpperCase() }}</span>
      </header>

      <nav v-if="currentTab === 'init'" class="tabs">
        <button
          v-for="n in [1, 2, 3]"
          :key="n"
          class="tab"
          :class="{ active: aufgabe === n }"
          @click="aufgabe = n"
        >
          Aufgabe {{ n }}
        </button>
      </nav>

      <main class="master-main">
        <div v-if="currentTab === 'init'" class="master-content">
          <Task1Master v-if="aufgabe === 1" :view="views[1]" />
          <Task2Master v-else-if="aufgabe === 2" :view="views[2]" />
          <Task3Master v-else-if="aufgabe === 3" :view="views[3]" />
        </div>

        <div v-else class="manual">
          <div class="manual-item">
            <h3>Aufgabe 1</h3>
            <p>P1 wählt das Symbol der defekten Komponente. P2 gibt den Code in der Reihenfolge ein.</p>
          </div>
          <div class="manual-item">
            <h3>Aufgabe 2</h3>
            <p>P1 führt die Ventil-Sequenz aus. Danach nennt P1 den letzten Passwort-Teil. P2 setzt das Passwort in der Reihenfolge zusammen.</p>
          </div>
          <div class="manual-item">
            <h3>Aufgabe 3</h3>
            <p>P1 entschlüsselt ASCII, P2 entschlüsselt Binär. Antworten in die Konsole eingeben.</p>
          </div>
        </div>
      </main>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useGameSocket } from '../composables/useGameSocket.js'
import Task1Master from './tasks/task1/Task1Master.vue'
import Task2Master from './tasks/task2/Task2Master.vue'
import Task3Master from './tasks/task3/Task3Master.vue'
import GameOver from './GameOver.vue'

defineProps({ currentTab: { type: String, default: 'init' } })

const WS_BASE = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.hostname}:8000/ws/game/`

const aufgabe = ref(1)
const spielVorbei = ref(false)
const gameOverResult = ref('meltdown')
const gameOverScore = ref(0)
const gameOverSurvived = ref(0)
const gameId = ref('')
const hasJoined = ref(false)
const views = ref({ 1: null, 2: null, 3: null })
let lastViewTask = null

function taskNumberFromView(t) {
  if (t === 'alarm_source')  return 1
  if (t === 'fire_protocol') return 2
  if (t === 'task3_master')  return 3
  return null
}

function handleServerMessage(msg) {
  const event = msg?.event || msg?.type
  const payload = msg?.payload || msg

  if (event === 'game_tick') {
    if (payload.health <= 0 || payload.time_left <= 0) spielVorbei.value = true
    const task = payload.tasks?.[0]
    const view = task?.view
    if (view) {
      const n = taskNumberFromView(view.type)
      if (n) {
        views.value = { ...views.value, [n]: view }
        if (n !== lastViewTask) {
          lastViewTask = n
          aufgabe.value = n
        }
      }
    }
  }

  if (event === 'game_over') {
    spielVorbei.value = true
    gameOverResult.value = payload.result || 'meltdown'
    gameOverScore.value = payload.score || 0
    gameOverSurvived.value = payload.survived_seconds || 0
  }

  if (event === 'lobby_update' && payload.status !== 'running') {
    spielVorbei.value = false
    views.value = { 1: null, 2: null, 3: null }
    lastViewTask = null
  }
}

const { connect, sendEvent } = useGameSocket({
  url: WS_BASE,
  onMessage: handleServerMessage
})

function handleJoin() {
  const id = gameId.value.trim().toLowerCase()
  if (!id || hasJoined.value) return
  hasJoined.value = true
  connect(`${WS_BASE}${id}/`, handleServerMessage, () => {
    sendEvent('player_register', { player_name: 'MASTER' })
  })
}
</script>

<style scoped>
.master-container {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.auth-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.section-title {
  font-family: var(--mono);
  font-size: 18px;
  font-weight: 700;
  color: var(--fg);
  margin: 0 0 8px 0;
}

.section-subtitle {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--fg-3);
  margin: 0 0 20px 0;
}

.btn-connect {
  padding: 14px 48px;
  background: var(--green);
  color: #050a08;
  border: none;
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 0.1em;
}

.btn-connect:hover:not(:disabled) { background: #4dff8f; }
.btn-connect:disabled { opacity: 0.35; cursor: not-allowed; }

.master-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid var(--border);
  font-family: var(--mono);
  font-size: 12px;
}

.master-role {
  color: var(--green);
  font-weight: 700;
  letter-spacing: 0.15em;
}

.master-session {
  color: var(--fg-3);
  letter-spacing: 0.15em;
}

.tabs {
  flex-shrink: 0;
  display: flex;
  gap: 0;
  padding: 0 24px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
}

.tab {
  padding: 14px 20px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--fg-3);
  font-family: var(--mono);
  font-size: 13px;
  cursor: pointer;
  margin-bottom: -1px;
  letter-spacing: 0.05em;
  transition: color 0.15s, border-color 0.15s;
}

.tab:hover { color: var(--fg-2); }

.tab.active {
  color: var(--green);
  border-bottom-color: var(--green);
}

.master-main {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 24px;
}

.master-content {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.manual {
  max-width: 640px;
  display: flex;
  flex-direction: column;
}

.manual-item {
  padding: 20px 0;
  border-bottom: 1px solid var(--border);
}

.manual-item:last-child { border-bottom: none; }

.manual-item h3 {
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  margin: 0 0 6px 0;
  color: var(--green);
  letter-spacing: 0.05em;
}

.manual-item p {
  font-family: var(--mono);
  font-size: 13px;
  margin: 0;
  color: var(--fg-2);
  line-height: 1.6;
}
</style>