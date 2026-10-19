<template>
  <div class="host">

    <GameOver
      v-if="istSpielVorbei && !istSieg"
      :result="gameOverResult"
      :score="gameOverScore"
      :survived-seconds="gameOverSurvived"
      :leaderboard="gameOverBoard"
    />

    <template v-else>

      <header class="host-top">
        <span class="host-brand">DRV-BOX · HOST</span>
        <span class="host-status">{{ statusLabel }}</span>
        <span class="host-session">{{ gameId ? gameId.toUpperCase() : '…' }}</span>
        <button class="exit-btn" @click="$emit('exit')">Verlassen</button>
      </header>

      <!-- LOBBY -->
      <section v-if="status !== 'running' && !istSieg" class="lobby">
        <h1 class="lobby-title">Bereit für den Start</h1>

        <div v-if="gameId" class="id-block">
          <span class="host-label">Sitzungs-ID — Spieler müssen genau diese eingeben</span>
          <div class="id-value">{{ gameId.toUpperCase() }}</div>
          <p class="lobby-sub">{{ wsHost }}</p>
        </div>
        <p v-else-if="bootError" class="lobby-error">{{ bootError }}</p>
        <p v-else class="lobby-sub">Sitzung wird erstellt …</p>

        <!-- DEV-Modus: zum Testen. Zeit steht, Fehler kosten nichts, Aufgaben überspringbar -->
        <div v-if="gameId" class="dev-block">
          <button
            class="dev-toggle"
            :class="{ on: devMode }"
            :aria-pressed="devMode ? 'true' : 'false'"
            @click="toggleDevMode"
          >
            DEV-Modus: {{ devMode ? 'AN' : 'AUS' }}
          </button>
          <span v-if="devMode" class="dev-note">Zeit steht · keine HP-Verluste · Aufgaben überspringbar</span>
        </div>
        <p v-if="devError" class="dev-error">{{ devError }}</p>

        <div class="slots">
          <div
            v-for="i in 3"
            :key="i"
            class="slot"
            :class="{ filled: playerList[i - 1] }"
          >
            <span class="slot-name">
              {{ playerList[i - 1] ? playerList[i - 1].name : 'wartet' }}
            </span>
            <span class="slot-role">
              {{ playerList[i - 1] && playerList[i - 1].role
                  ? roleLabel(playerList[i - 1].role)
                  : '–' }}
            </span>
          </div>
        </div>

        <p class="lobby-count">{{ playerList.length }} / 3</p>

        <p class="lobby-note">
          {{ readyToStart
              ? 'Alle Rollen besetzt — Spiel kann gestartet werden.'
              : 'Warte auf Spieler (gleiche ID) und Rollenwahl …' }}
        </p>
      </section>

      <!-- RUNNING -->
      <section v-else class="running">
        <div v-if="devMode && status === 'running'" class="dev-panel">
          <span class="dev-badge">DEV-MODUS · Zeit steht · keine HP-Verluste</span>
          <button class="dev-skip" :disabled="skipping" @click="skipTask">
            {{ skipping ? 'Überspringe …' : 'Aufgabe überspringen ⏭' }}
          </button>
          <span v-if="devError" class="dev-error">{{ devError }}</span>
        </div>

        <div class="time-block">
          <span class="host-label">Zeit</span>
          <div class="time-value" :class="{ critical: timeLeft <= 30 }">{{ zeit }}</div>
        </div>

        <div class="hp-block">
          <div class="hp-head">
            <span class="host-label">Server</span>
            <span class="hp-value">{{ hp }} / {{ maxHp }}</span>
          </div>
          <div class="hp-track">
            <div class="hp-fill" :style="{ width: hpPercent + '%' }"></div>
          </div>
        </div>

        <!-- Finale: Neustart-Code, füllt sich mit jeder gelösten Aufgabe -->
        <div class="finale">
          <span class="host-label">Neustart-Code</span>
          <VaultDoor mode="display" :digits="rebootDigits" :state="vaultState" />
          <p v-if="istSieg" class="finale-win">SERVER ONLINE · SIEG</p>
        </div>
      </section>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useGameSocket } from '../composables/useGameSocket.js'
import GameOver from './GameOver.vue'
import VaultDoor from './VaultDoor.vue'

defineEmits(['exit'])

const gameId = ref('')
const bootError = ref('')
const devMode = ref(false)
const devError = ref('')
const skipping = ref(false)
const status = ref('waiting')
const playerList = ref([])
const readyToStart = ref(false)
const maxHp = ref(300)   // bis zum ersten game_tick; danach max_health vom Backend
const hp = ref(300)
const timeLeft = ref(300)
const rebootDigits = ref([null, null, null])

const isGameOver = ref(false)
const gameOverResult = ref('meltdown')
const gameOverScore = ref(0)
const gameOverSurvived = ref(0)
const gameOverBoard = ref(null)   // Top 5 + eigener Platz aus game_over.leaderboard

// Spielende entscheidet allein das Backend (game_over / status), nicht hp oder Zeit hier.
const istSpielVorbei = computed(
  () => isGameOver.value || status.value === 'game_over' || status.value === 'won'
)

// Sieg: der Tresor bleibt sichtbar und öffnet sich, statt im Overlay zu verschwinden.
const istSieg = computed(() => status.value === 'won' && gameOverResult.value === 'victory')
const vaultState = computed(() => (istSieg.value ? 'open' : 'locked'))

const statusLabel = computed(() => {
  if (istSpielVorbei.value) return gameOverResult.value === 'victory' ? 'Sieg' : 'Niederlage'
  if (status.value === 'running') return 'Läuft'
  if (status.value === 'ready') return 'Bereit'
  return 'Wartet'
})

const hpPercent = computed(() => Math.max(0, Math.min(100, (hp.value / maxHp.value) * 100)))

const zeit = computed(() => {
  const t = Math.max(0, timeLeft.value)
  return `${String(Math.floor(t / 60)).padStart(2, '0')}:${String(t % 60).padStart(2, '0')}`
})

const wsHost = computed(() => `${location.hostname}:5173`)

function roleLabel(r) {
  if (r === 'MASTER') return 'Leitstand'
  if (r === 'FI-SI')  return 'Vorderseite'
  if (r === 'FI-AE')  return 'Rückseite'
  return r
}

const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
const httpProtocol = location.protocol === 'https:' ? 'https' : 'http'
const API_BASE = `${httpProtocol}://${location.hostname}:8000`

function handleMessage(msg) {
  const event = msg?.event || msg?.type
  const payload = msg?.payload || msg

  // Beamer mit vertippter ?game_id=…: keine ID anzeigen, die es nicht gibt.
  if (event === 'error' && payload.code === 'unknown_game') {
    bootError.value = `Sitzung „${gameId.value.toUpperCase()}" gibt es nicht. Seite ohne ?game_id= neu laden.`
    gameId.value = ''
    return
  }

  if (event === 'error' && payload.code === 'dev_denied') {
    devError.value = payload.message || 'DEV-Aktion abgelehnt'
    skipping.value = false
    setTimeout(() => { devError.value = '' }, 4000)
    return
  }

  if (event === 'lobby_update') {
    playerList.value = payload.players || []
    status.value = payload.status || 'waiting'
    readyToStart.value = !!payload.ready_to_start
    devMode.value = !!payload.dev_mode
    if (status.value === 'waiting' || status.value === 'ready') {
      hp.value = maxHp.value
      timeLeft.value = 300
      rebootDigits.value = [null, null, null]
      isGameOver.value = false
      gameOverResult.value = 'meltdown'
      gameOverScore.value = 0
      gameOverSurvived.value = 0
      gameOverBoard.value = null
    }
  }

  if (event === 'game_tick') {
    skipping.value = false
    if (typeof payload.health === 'number') hp.value = payload.health
    timeLeft.value = payload.time_left ?? timeLeft.value
    if (Array.isArray(payload.reboot_digits)) {
      rebootDigits.value = [0, 1, 2].map((i) => payload.reboot_digits[i] ?? null)
    }
    if (typeof payload.max_health === 'number') maxHp.value = payload.max_health
    if (status.value !== 'running' && status.value !== 'game_over' && status.value !== 'won') {
      status.value = 'running'
    }
  }

  if (event === 'game_over') {
    isGameOver.value = true
    gameOverResult.value = payload.result || 'meltdown'
    gameOverScore.value = payload.score || 0
    gameOverSurvived.value = payload.survived_seconds || 0
    gameOverBoard.value = payload.leaderboard || null
    status.value = gameOverResult.value === 'victory' ? 'won' : 'game_over'
  }
}

const { sendEvent, connect } = useGameSocket({ onMessage: handleMessage })

// DEV-Modus: Stand kommt immer vom Server (lobby_update), hier nur anfragen
function toggleDevMode() {
  devError.value = ''
  sendEvent('dev_mode', { enabled: !devMode.value })
}

function skipTask() {
  if (skipping.value) return
  skipping.value = true
  sendEvent('dev_skip_task', {})
  // Falls kein Tick kommt (z. B. Verbindung weg): nicht dauerhaft gesperrt
  setTimeout(() => { skipping.value = false }, 3000)
}

async function resolveGameId() {
  // Optional: ?game_id=xxxx — gleiche Sitzung wie create-game / force-start
  const fromQuery = new URLSearchParams(location.search).get('game_id')?.trim()
  if (fromQuery) return fromQuery.toLowerCase()

  const res = await fetch(`${API_BASE}/create-game/`)
  const data = await res.json()
  if (!res.ok || !data.game_id) throw new Error('create-game failed')
  return String(data.game_id).toLowerCase()
}

function connectAsHost(id) {
  gameId.value = id
  const url = `${protocol}://${location.hostname}:8000/ws/game/${id}/`
  connect(url, handleMessage, () => sendEvent('host_register', {}))
}

onMounted(async () => {
  try {
    const id = await resolveGameId()
    connectAsHost(id)
  } catch (err) {
    console.error(err)
    bootError.value = 'Sitzung konnte nicht erstellt werden. Backend erreichbar?'
  }
})
</script>

<style scoped>
.host {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 32px 48px;
  overflow: hidden;
}

.host-top {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
  font-family: var(--mono);
  font-size: 13px;
}

.host-brand {
  color: var(--green);
  font-weight: 700;
  letter-spacing: 0.15em;
}

.host-status { color: var(--fg-2); }

.host-session {
  margin-left: auto;
  color: var(--fg-3);
  letter-spacing: 0.15em;
}

.exit-btn {
  background: none;
  border: 1px solid var(--border-2);
  color: var(--fg-3);
  font-family: var(--mono);
  font-size: 11px;
  padding: 5px 10px;
  cursor: pointer;
  letter-spacing: 0.1em;
}

.exit-btn:hover {
  color: var(--red);
  border-color: var(--red);
}

/* Lobby */
.lobby {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
  text-align: center;
  min-height: 0;
}

.lobby-title {
  font-family: var(--mono);
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0;
  color: var(--fg);
}

.id-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin: 8px 0 4px;
}

.id-value {
  font-family: var(--mono);
  font-size: 96px;
  font-weight: 700;
  letter-spacing: 0.2em;
  line-height: 1;
  color: var(--green);
  text-transform: uppercase;
}

.lobby-sub {
  font-family: var(--mono);
  font-size: 15px;
  color: var(--fg-2);
  margin: 0;
  letter-spacing: 0.05em;
}

.lobby-error {
  font-family: var(--mono);
  font-size: 14px;
  color: var(--red);
  margin: 0;
}

/* DEV-Modus (Bernstein = bewusst anders als das Spiel-Grün) */
.dev-block {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.dev-toggle,
.dev-skip {
  background: none;
  border: 1px dashed var(--border-2);
  color: var(--fg-3);
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 0.12em;
  padding: 6px 12px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}

.dev-toggle:hover,
.dev-toggle.on {
  color: var(--amber);
  border-color: var(--amber-border);
  border-style: solid;
  background: var(--amber-bg);
}

.dev-note,
.dev-badge {
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 0.08em;
  color: var(--amber);
}

.dev-error {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--red);
  margin: 0;
}

.dev-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  padding: 10px 16px;
  border: 1px solid var(--amber-border);
  background: var(--amber-bg);
}

.dev-skip {
  color: var(--amber);
  border: 1px solid var(--amber);
  font-size: 14px;
  padding: 8px 16px;
}

.dev-skip:hover:not(:disabled) { background: var(--amber-bg); }
.dev-skip:disabled { opacity: 0.4; cursor: wait; }

.slots {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  width: 100%;
  max-width: 900px;
  margin-top: 12px;
}

.slot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 20px;
  background: var(--bg-1);
  border: 1px dashed var(--border-2);
  font-family: var(--mono);
  font-size: 15px;
  color: var(--fg-3);
  transition: color 0.15s, border-color 0.15s;
}

.slot.filled {
  color: var(--fg);
  border-style: solid;
  border-color: var(--green-border);
}

.slot-name { font-weight: 600; }

.slot-role {
  font-size: 12px;
  letter-spacing: 0.1em;
  color: var(--green);
}

.lobby-count {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--fg-3);
  margin: 0;
  letter-spacing: 0.15em;
}

.lobby-note {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--fg-2);
  margin: 8px 0 0 0;
  letter-spacing: 0.05em;
}

/* Running */
.running {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  justify-items: center;
  align-items: center;
  gap: 18px;
  overflow: hidden;
}

.time-block { text-align: center; }

.host-label {
  display: block;
  font-family: var(--mono);
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--fg-3);
  margin-bottom: 16px;
}

.time-value {
  font-family: var(--mono);
  font-size: clamp(72px, 20vh, 220px);
  font-weight: 500;
  letter-spacing: -0.05em;
  line-height: 0.9;
  color: var(--fg);
  font-variant-numeric: tabular-nums;
}

.time-value.critical { color: var(--red); }

.hp-block { max-width: 1000px; width: 100%; }

.hp-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 12px;
}

.hp-head .host-label { margin-bottom: 0; }

.hp-value {
  font-family: var(--mono);
  font-size: 24px;
  font-weight: 600;
  color: var(--fg);
}

.hp-track {
  height: 28px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  overflow: hidden;
}

.hp-fill {
  height: 100%;
  background: var(--green);
  transition: width 0.3s;
}

/* Finale — Neustart-Code, gut sichtbar für den ganzen Raum */
.finale {
  width: 100%;
  max-width: min(640px, 58vh);
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.finale .host-label { margin-bottom: 8px; }

.finale-win {
  margin: 12px 0 0 0;
  font-family: var(--mono);
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.2em;
  color: var(--green);
  text-shadow: 0 0 24px rgba(0, 255, 102, 0.45);
}

@media (max-width: 900px) {
  .host { padding: 20px; }
  .lobby-title { font-size: 28px; }
  .id-value { font-size: 56px; letter-spacing: 0.12em; }
  .time-value { font-size: 120px; }
  .slots { grid-template-columns: 1fr; }
  .finale { max-width: 420px; }
  .finale-win { font-size: 20px; }
}
</style>