<template>
  <div class="player">
    <!-- Verbindung weg: sichtbar machen, Wiederverbinden läuft im Hintergrund -->
    <Transition name="phase">
      <div v-if="verbindungWeg" class="conn-banner" role="alert">
        Verbindung verloren – verbinde neu …
      </div>
    </Transition>

    <!-- Verbinden → Rolle wählen → Warten → Spiel → Spielende blenden weich über (style.css: .phase-*) -->
    <Transition name="phase" mode="out-in">
      <GameOver
        v-if="istSpielVorbei"
        :result="gameOverResult"
        :score="gameOverScore"
        :survived-seconds="gameOverSurvived"
        :leaderboard="gameOverBoard"
        :show-restart="true"
        :show-exit="true"
        :restarting="restarting"
        @restart="handleRestart"
        @exit="$emit('exit')"
      />

      <!-- Phase 1: Verbinden -->
      <div v-else-if="!connected" class="phase-connect">
        <div class="connect-card">
          <h2 class="connect-title">Verbinden</h2>

          <label class="field">
            <span class="field-label">Sitzungs-ID</span>
            <input
              v-model="gameId"
              class="input"
              placeholder="a3k9"
              maxlength="8"
              @keyup.enter="handleJoin"
            />
          </label>

          <div class="connect-name">
            Angemeldet als <strong>{{ playerName || 'Agent' }}</strong>
          </div>

          <p v-if="joinError" class="join-error">{{ joinError }}</p>

          <button
            class="btn-main"
            :disabled="!gameId.trim() || joining"
            @click="handleJoin"
          >
            {{ joining ? 'Verbinde …' : 'Beitreten' }}
          </button>

          <button class="back-btn" @click="$emit('exit')">Zurück</button>
        </div>
      </div>

      <!-- Phase 2: Lobby mit Rollenwahl -->
      <div v-else-if="!myRole" class="phase-lobby">
        <header class="lobby-bar">
          <span class="bar-brand">DRV-BOX</span>
          <span class="bar-session">{{ gameId.toUpperCase() }}</span>
          <span class="bar-count">{{ lobbyPlayers.length }} / 3</span>
        </header>

        <main class="lobby-main">
          <h1 class="lobby-title">Rolle wählen</h1>
          <p class="lobby-sub">Jede Rolle einmal. Zusammen knacken — niemand hat die ganze Lösung.</p>

          <div class="role-cards">
            <button
              v-for="r in allRoles"
              :key="r"
              class="role-card"
              :class="{ taken: isTaken(r) }"
              :disabled="isTaken(r)"
              @click="pickRole(r)"
            >
              <span class="role-name">{{ roleLabel(r) }}</span>
              <span class="role-desc">{{ isTaken(r) ? 'belegt' : roleHint(r) }}</span>
            </button>
          </div>

          <p v-if="roleError" class="role-error">{{ roleError }}</p>
        </main>
      </div>

      <!-- Phase 3: Warten bis Spiel startet -->
      <div v-else-if="status !== 'running' && !siegPause" class="phase-wait">
        <header class="lobby-bar">
          <span class="bar-brand">DRV-BOX</span>
          <span class="bar-session">{{ gameId.toUpperCase() }}</span>
          <span class="bar-role">{{ roleLabel(myRole) }}</span>
          <span v-if="devMode" class="bar-dev">DEV · nicht gewertet</span>
        </header>

        <main class="wait-main">
          <h1 class="wait-title">Bereit für den Start</h1>
          <p class="wait-sub">{{ lobbyPlayers.length }} / 3 verbunden</p>

          <ul class="wait-list">
            <li v-for="p in lobbySortiert" :key="p.name" class="wait-item">
              <span class="wait-name">{{ p.name }}</span>
              <span class="wait-role">{{ p.role ? roleLabel(p.role) : '–' }}</span>
            </li>
            <li v-for="n in (3 - lobbyPlayers.length)" :key="'empty-' + n" class="wait-item empty">
              <span class="wait-name">wartet</span>
              <span class="wait-role">–</span>
            </li>
          </ul>

          <!-- Einsatzbesprechung am Beamer: gestartet wird dort -->
          <div v-if="status === 'briefing'" class="briefing-note">
            <span class="briefing-title">Einsatzbesprechung läuft</span>
            <span class="briefing-sub">Schaut auf den Beamer – gleich geht's los.</span>
            <!-- Der Beamer wartet auf der letzten Folie, bis alle drei „Bereit“ gedrückt haben -->
            <button class="ready-btn" :class="{ 'is-ready': meReady }" type="button" @click="toggleReady">
              {{ meReady ? '✓ Bereit – tippen zum Zurücknehmen' : 'Bereit' }}
            </button>
            <span class="briefing-count">{{ readyCount }}/3 bereit</span>
            <!-- Notfall: Beamer weg (Tab zu, abgestürzt) – nach 20 s auch ohne Besprechung starten -->
            <button v-if="notstartMoeglich" class="briefing-fallback" type="button" @click="startGame">
              Kein Beamer da? Ohne Einsatzbesprechung starten
            </button>
          </div>
          <button
            v-else
            class="start-btn"
            :disabled="!readyToStart || starting"
            @click="startGame"
          >
            {{ readyToStart
                ? (starting ? 'Starte …' : 'Runde starten')
                : `Warte auf Rollen (${rolesTaken.length} / 3)` }}
          </button>

          <p v-if="startError" class="wait-error">{{ startError }}</p>

          <button class="back-btn" @click="$emit('exit')">Verlassen</button>
        </main>
      </div>

      <!-- Phase 4: Spiel -->
      <div v-else class="phase-game">
        <header class="task-bar">
          <span class="bar-brand">DRV-BOX</span>
          <span class="bar-role">{{ roleLabel(myRole) }}</span>
          <span v-if="devMode" class="bar-dev" title="DEV-Modus: Zeit steht, Fehler kosten nichts">DEV · nicht gewertet</span>
          <span class="bar-stats">{{ hp }} HP · {{ zeit }}</span>
        </header>

        <main class="task-main" :class="{ 'with-kiste': kisteOffen }">
          <!-- von Aufgabe zu Aufgabe: alte gleitet weg, neue kommt herein (style.css: .task-*) -->
          <Transition name="task" mode="out-in">
            <component
              :is="currentTaskComponent"
              :key="currentTask"
              :role="normalizedRole"
              :task="task"
              :view="task?.view"
              :note-seed="task?.task_id || ''"
              :symbole="task1Switches"
              :code-length="task1CodeLength"
              :input-result-nonce="inputResultNonce"
              :server-error="lastError"
              :time-left="timeLeft"
              :victory="currentTask === 4 ? sieg : undefined"
              @solved="onTaskSolved"
              @eingabe="sendeEingabe"
              @task-failed="onTaskFailed"
              @failed="onTaskFailed"
            />
          </Transition>
        </main>

        <!-- Teilekiste nur beim Leitstand, links am Rand -->
        <Teilekiste v-if="myRole === 'MASTER'" v-model:open="kisteOffen" :teile="teile" />

        <!-- nach jeder Aufgabe: Fundort öffnet sich, Teil kommt in die Kiste -->
        <Transition name="phase">
          <Zwischenszene
            v-if="zwischenszene"
            :key="zwischenszene.key"
            :teil="zwischenszene.teil"
            :naechste="zwischenszene.naechste"
            :rolle="myRole"
            @fertig="zwischenszene = null"
          />
        </Transition>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useGameSocket } from '../composables/useGameSocket.js'
import GameOver from './GameOver.vue'
import Teilekiste from './Teilekiste.vue'
import Zwischenszene from './Zwischenszene.vue'

import Task1P1 from './tasks/task1/Task1P1.vue'
import Task1P2 from './tasks/task1/Task1P2.vue'
import Task1Master from './tasks/task1/Task1Master.vue'
import Task2P1 from './tasks/task2/Task2P1.vue'
import Task2P2 from './tasks/task2/Task2P2.vue'
import Task2Master from './tasks/task2/Task2Master.vue'
import Task3P1 from './tasks/task3/Task3P1.vue'
import Task3P2 from './tasks/task3/Task3P2.vue'
import Task3Master from './tasks/task3/Task3Master.vue'
import Task4Leitstand from './tasks/task4/Task4Leitstand.vue'
import Task4Vorderseite from './tasks/task4/Task4Vorderseite.vue'
import Task4Rueckseite from './tasks/task4/Task4Rueckseite.vue'

const props = defineProps({
  playerName: { type: String, default: '' }
})
defineEmits(['exit'])

const WS_BASE = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.hostname}:8000/ws/game/`
const DEFAULT_MAX_HP = 300   // nur bis zum ersten game_tick; danach gilt max_health vom Backend
const ALL_ROLES = ['MASTER', 'FI-SI', 'FI-AE']

const gameId = ref('')      // so wie eingetippt (Anzeige)
const joinedId = ref('')    // bereinigt (trim, klein) – damit wird verbunden, auch beim Neustart
const connected = ref(false)
const joining = ref(false)
const registered = ref(false)   // true, sobald ich in einem lobby_update auftauche
const joinError = ref('')
const myRole = ref(null)
const lobbyPlayers = ref([])
const rolesTaken = ref([])
const status = ref('waiting')
const maxHp = ref(DEFAULT_MAX_HP)
const hp = ref(DEFAULT_MAX_HP)
const START_ZEIT = 540   // bis zum ersten game_tick (Backend: DEFAULT_TIME)
const timeLeft = ref(START_ZEIT)
const task = ref(null)
const currentTask = ref(1)
const isGameOver = ref(false)
const gameOverResult = ref('meltdown')
const gameOverScore = ref(0)
const gameOverSurvived = ref(0)
const gameOverBoard = ref(null)   // Top 5 + eigener Platz aus game_over.leaderboard
const devMode = ref(false)        // vom Beamer gesetzt; DEV-Runden zählen nicht fürs Leaderboard
const lastError = ref('')
const roleError = ref('')

const readyToStart = ref(false)
const meReady = computed(() => lobbyPlayers.value.some(
  (p) => p.name === (props.playerName || 'Agent') && p.ready
))
const readyCount = computed(() => lobbyPlayers.value.filter((p) => p.ready).length)
const starting = ref(false)
const startError = ref('')

const restarting = ref(false)
const kisteOffen = ref(false)       // Teilekiste (Leitstand) offen → Aufgabe rückt zur Seite
const teile = ref([])               // gefundene Teile (game_tick.parts)
const zwischenszene = ref(null)     // { teil, naechste, key } solange die Szene läuft
let teileBekannt = false            // erst ab dem zweiten Tick: Wiedereinstieg zeigt keine alte Szene
const inputResultNonce = ref(0)   // ← wird bei jedem Server-input_result inkrementiert

const allRoles = ALL_ROLES
// Warteliste in Rollen-Reihenfolge (Leitstand, Vorderseite, Rückseite), ohne Rolle zuletzt
const lobbySortiert = computed(() => {
  const rang = (p) => (p.role ? ALL_ROLES.indexOf(p.role) : ALL_ROLES.length)
  return [...lobbyPlayers.value].sort((a, b) => rang(a) - rang(b))
})

const normalizedRole = computed(() => {
  if (myRole.value === 'FI-SI') return 'P1'
  if (myRole.value === 'FI-AE') return 'P2'
  return myRole.value
})

const currentTaskComponent = computed(() => {
  if (!myRole.value) return null
  if (myRole.value === 'MASTER') {
    const masterMap = { 1: Task1Master, 2: Task2Master, 3: Task3Master, 4: Task4Leitstand }
    return masterMap[currentTask.value] || null
  }
  // Finale (Reparatur): jede Rolle hat ihre eigene Ansicht
  const playerMap = {
    '1-P1': Task1P1, '1-P2': Task1P2,
    '2-P1': Task2P1, '2-P2': Task2P2,
    '3-P1': Task3P1, '3-P2': Task3P2,
    '4-P1': Task4Vorderseite, '4-P2': Task4Rueckseite,
  }
  return playerMap[`${currentTask.value}-${normalizedRole.value}`] || null
})

const task1Switches   = computed(() => task.value?.view?.switches || ['raute', 'dreieck', 'quadrat', 'kreis'])
const task1CodeLength = computed(() => task.value?.view?.code_length || 4)

// Sieg im Finale: erst sieht man den Tresor aufgehen, dann kommt das Ergebnis
const SIEG_PAUSE_MS = 1800
const siegPause = ref(false)
let siegTimer = null

const istSpielVorbei = computed(
  () => !siegPause.value && (isGameOver.value || status.value === 'game_over' || status.value === 'won')
)

// Sieg: der Tresor im Finale öffnet sich (Task4Reboot wertet das aus).
const sieg = computed(() => isGameOver.value && gameOverResult.value === 'victory')

const zeit = computed(() => {
  const t = Math.max(0, timeLeft.value)
  return `${String(Math.floor(t / 60)).padStart(2, '0')}:${String(t % 60).padStart(2, '0')}`
})

// Kennung dieses Browser-Tabs: übersteht F5 (sessionStorage), ein zweites Gerät hat eine
// andere. Damit lehnt der Server in der Lobby einen zweiten Spieler mit gleichem Namen ab.
function tabKennung() {
  const neu = () => globalThis.crypto?.randomUUID?.()
    || `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`
  try {
    let id = sessionStorage.getItem('drv_client_id')
    if (!id) {
      id = neu()
      sessionStorage.setItem('drv_client_id', id)
    }
    return id
  } catch {
    return neu()
  }
}
const clientId = tabKennung()

function anmelden() {
  sendEvent('player_register', { player_name: props.playerName || 'Agent', client_id: clientId })
}

function roleLabel(r) {
  if (r === 'MASTER') return 'Leitstand'
  if (r === 'FI-SI')  return 'Vorderseite'
  if (r === 'FI-AE')  return 'Rückseite'
  return r
}

function roleHint(r) {
  if (r === 'MASTER') return 'Kontrollraum · Monitore'
  if (r === 'FI-SI')  return 'Vor dem Serverschrank'
  if (r === 'FI-AE')  return 'Hinter dem Serverschrank'
  return ''
}

function isTaken(r) {
  return rolesTaken.value.includes(r)
}

watch(currentTask, () => { lastError.value = '' })

// Welche Aufgabe läuft, sagt das Backend (task.kind). Hier nur: kind → Komponente.
const TASK_NUMBER = { alarm: 1, fire_protocol: 2, data_rescue: 3, repair: 4 }

function taskNumber(t) {
  return TASK_NUMBER[t?.kind] ?? taskNumberFromView(t?.view?.type)
}

// Übergang: ältere Payloads/Test-Fixtures ohne kind. Entfernen, sobald alle Ticks kind haben.
function taskNumberFromView(viewType) {
  switch (viewType) {
    case 'alarm_leds':
    case 'alarm_source':
    case 'main_switches':
    case 'code_stickers':
    case 'shutdown_terminal': return 1
    case 'fire_log':
    case 'fire_protocol':
    case 'valve_panel':
    case 'rack_rear':         return 2
    case 'rescue_log':
    case 'rescue_terminal':
    case 'packet_dump':
    case 'task3_master':
    case 'task3_p1':
    case 'task3_p2':          return 3
    case 'repair_console':
    case 'repair_front':
    case 'repair_back':       return 4
    default:                  return null
  }
}

const handleServerMessage = (msg) => {
  const event = msg?.event || msg?.type
  const payload = msg?.payload || msg

  // Vertippte Sitzungs-ID: Server schließt die Verbindung → zurück zur Eingabe.
  // Der Hinweis bleibt stehen, bis der nächste Versuch startet.
  if (event === 'error' && payload.code === 'unknown_game') {
    disconnect()
    connected.value = false
    joining.value = false
    joinError.value = `Sitzung „${gameId.value.trim().toUpperCase()}" gibt es nicht. Bitte die ID vom Beamer prüfen.`
    return
  }

  // Beitritt abgelehnt (Spiel läuft schon, Lobby voll, Name vergeben): zurück zur Eingabe,
  // die Meldung bleibt stehen – sonst landet man in einer Sackgasse bei „Rolle wählen“
  if (event === 'error' && payload.code === 'register_denied') {
    disconnect()
    connected.value = false
    registered.value = false
    joining.value = false
    joinError.value = payload.message || 'Beitritt nicht möglich'
    return
  }

  if (event === 'lobby_update') {
    const newPlayers = payload.players ?? []
    const stillInLobby = newPlayers.some(p => p.name === (props.playerName || 'Agent'))
    const lobbyOpen = payload.status === 'waiting' || payload.status === 'ready'

    if (stillInLobby) {
      registered.value = true
    } else if (connected.value && registered.value && lobbyOpen) {
      // Neustart (reset_game) löscht alle Spieler. Statt zurück zur ID-Eingabe:
      // Runde zurücksetzen und automatisch wieder anmelden. Wer selbst Neustart
      // gedrückt hat, meldet sich in handleRestart über die neue Verbindung an.
      registered.value = false
      resetRound()
      if (!restarting.value) {
        anmelden()
      }
    }

    lobbyPlayers.value = newPlayers
    rolesTaken.value = payload.roles_taken ?? []
    status.value = payload.status ?? status.value
    readyToStart.value = !!payload.ready_to_start
    devMode.value = !!payload.dev_mode

    if (status.value === 'waiting' || status.value === 'ready') {
      if (!isGameOver.value) {
        hp.value = maxHp.value
        timeLeft.value = START_ZEIT
        lastError.value = ''
      }
    }
  }

  if (event === 'role_assigned') {
    myRole.value = payload.role
    roleError.value = ''
  }

  if (event === 'game_tick') {
    if (Array.isArray(payload.parts)) {
      if (teileBekannt && payload.parts.length > teile.value.length) {
        zwischenszene.value = { teil: payload.parts.at(-1), naechste: payload.parts.length + 1, key: payload.parts.length }
      }
      teile.value = payload.parts
      teileBekannt = true
    }
    if (typeof payload.health === 'number') hp.value = payload.health
    timeLeft.value = payload.time_left ?? timeLeft.value
    task.value = payload.tasks?.[0] ?? task.value

    const n = taskNumber(task.value)
    if (n && n !== currentTask.value) {
      currentTask.value = n
      lastError.value = ''
    }

    if (typeof payload.max_health === 'number') maxHp.value = payload.max_health

    if (status.value !== 'running' && status.value !== 'game_over' && status.value !== 'won') {
      status.value = 'running'
    }
    // Spielende entscheidet allein das Backend (game_over), nicht hp <= 0 hier.
  }

  if (event === 'input_result') {
    // Fehler zuerst setzen, dann Nonce — Tasks können beides auswerten.
    // Auch "error"/"ignored" melden, sonst bleibt der Knopf der Aufgabe auf „Prüfe …“ stehen.
    if (payload.result === 'wrong') {
      // was falsch war, sagt der Server (z. B. „Stromschlag!“), sonst allgemein
      lastError.value = payload.message || 'Falsche Eingabe'
      if (typeof payload.health === 'number') hp.value = payload.health
    } else if (payload.result === 'error') {
      lastError.value = 'Nicht angekommen – bitte erneut versuchen'
    } else if (payload.result === 'ignored') {
      lastError.value = 'Nicht angenommen – bitte erneut versuchen'
    } else {
      lastError.value = ''
    }
    inputResultNonce.value++
  }

  if (event === 'game_over') {
    const imFinale = !isGameOver.value && currentTask.value === 4 && !!task.value
    if (payload.result === 'victory' && imFinale) {
      siegPause.value = true
      siegTimer = setTimeout(() => { siegPause.value = false; siegTimer = null }, SIEG_PAUSE_MS)
    }
    isGameOver.value = true
    gameOverResult.value = payload.result || 'meltdown'
    gameOverScore.value = payload.score || 0
    gameOverSurvived.value = payload.survived_seconds || 0
    gameOverBoard.value = payload.leaderboard || null
    status.value = gameOverResult.value === 'victory' ? 'won' : 'game_over'
  }

  if (event === 'error') {
    const m = payload.message || 'Fehler'
    joinError.value = m
    roleError.value = m
    startError.value = m
    setTimeout(() => {
      joinError.value = ''
      roleError.value = ''
      startError.value = ''
    }, 2500)
  }
}

const { connect, sendEvent, disconnect, isConnected } = useGameSocket({
  url: WS_BASE,
  onMessage: handleServerMessage,
})

// Verbindung weg (WLAN, Server-Neustart): Banner zeigen und gesperrte Aufgaben freigeben.
// Das Wiederverbinden macht useGameSocket selbst, die Anmeldung läuft dann über onOpen neu.
const verbindungWeg = computed(() => connected.value && !isConnected.value)
watch(verbindungWeg, (weg) => {
  if (weg) lastError.value = 'Verbindung unterbrochen – bitte nochmal versuchen'
})

// Einsatzbesprechung: Fällt der Beamer weg, startet der Server auch ohne ihn (siehe
// fix/beamer-anwesenheit). Damit die Handys nicht festhängen, nach 20 s ein Notfall-Knopf.
const BRIEFING_NOTSTART_MS = 20000
const notstartMoeglich = ref(false)
let notstartTimer = null
watch(status, (s) => {
  if (notstartTimer) { clearTimeout(notstartTimer); notstartTimer = null }
  notstartMoeglich.value = false
  if (s === 'briefing') {
    notstartTimer = setTimeout(() => { notstartMoeglich.value = true }, BRIEFING_NOTSTART_MS)
  }
})

let restartTimer = null
let joinTimer = null
onUnmounted(() => {
  if (restartTimer) clearTimeout(restartTimer)
  if (joinTimer) clearTimeout(joinTimer)
  if (notstartTimer) clearTimeout(notstartTimer)
  if (siegTimer) clearTimeout(siegTimer)
})

function handleJoin() {
  const id = gameId.value.trim().toLowerCase()
  if (!id || joining.value) return
  joinedId.value = id

  joining.value = true
  joinError.value = ''

  connect(`${WS_BASE}${id}/`, handleServerMessage, () => {
    connected.value = true
    joining.value = false
    anmelden()
  })

  joinTimer = setTimeout(() => {
    if (joining.value) {
      joining.value = false
      disconnect()   // sonst versucht useGameSocket es endlos weiter
      joinError.value = 'Verbindung fehlgeschlagen'
    }
  }, 4000)
}

function pickRole(r) {
  if (isTaken(r)) return
  roleError.value = ''
  sendEvent('choose_role', { role: r })
}

function toggleReady() {
  sendEvent('player_ready', { ready: !meReady.value })
}

function startGame() {
  if (!readyToStart.value || starting.value) return
  starting.value = true
  startError.value = ''
  sendEvent('start_game', {})
  setTimeout(() => { starting.value = false }, 3000)
}

function handleRestart() {
  if (restarting.value) return
  restarting.value = true

  sendEvent('reset_game', {})

  restartTimer = setTimeout(() => {
    disconnect()
    resetRound()

    connect(`${WS_BASE}${joinedId.value}/`, handleServerMessage, () => {
      connected.value = true
      anmelden()
      restarting.value = false
    })
  }, 300)
}

/** Alles, was zu einer Runde gehört, auf Anfang (Rolle wird neu gewählt). */
function resetRound() {
  teile.value = []
  teileBekannt = false
  zwischenszene.value = null
  kisteOffen.value = false
  if (siegTimer) { clearTimeout(siegTimer); siegTimer = null }
  siegPause.value = false
  isGameOver.value = false
  gameOverResult.value = 'meltdown'
  gameOverScore.value = 0
  gameOverSurvived.value = 0
  gameOverBoard.value = null
  myRole.value = null
  task.value = null
  currentTask.value = 1
  hp.value = maxHp.value
  timeLeft.value = START_ZEIT
  lastError.value = ''
  inputResultNonce.value = 0
}

function onTaskFailed() {
  sendEvent('player_input', { action_type: 'button_press', target: 'penalty', value: 'wrong' })
}

// Finale: die Ansichten melden jede Handlung direkt (Teil geben, Wartung, Einbau, Schlüssel)
function sendeEingabe({ target, value }) {
  lastError.value = ''
  sendEvent('player_input', { action_type: 'button_press', target, value: String(value) })
}

function onTaskSolved(data) {
  let payloadData = {}

  if (!myRole.value) return

  if (currentTask.value === 1) {
    // Escape Alarm: Leitstand tippt shutdown_cmd, Vorderseite main_switch, Rückseite nur Anzeige
    if (myRole.value === 'MASTER' || data?.target === 'shutdown_cmd') {
      const codeStr = Array.isArray(data?.code) ? data.code.join(',') : (data?.code || data?.value || '')
      payloadData = { action_type: 'text_input', target: 'shutdown_cmd', value: codeStr }
    } else if (normalizedRole.value === 'P1') {
      payloadData = { action_type: 'button_press', target: 'main_switch', value: data?.value || '' }
    }
  } else if (currentTask.value === 2) {
    // Löschprotokoll: Vorderseite löscht (RACK:MITTEL), Leitstand + Rückseite geben gemeinsam frei
    if (data?.target === 'release') {
      payloadData = { action_type: 'button_press', target: 'release', value: 'press' }
    } else if (normalizedRole.value === 'P1') {
      payloadData = { action_type: 'button_press', target: 'valve_action',
                      value: `${data?.valve || ''}:${data?.color || ''}` }
    }
  } else if (currentTask.value === 3) {
    // Datenrettung: Rückseite legt die Platte ein, Vorderseite tippt das Wort.
    // Geprüft wird alles im Backend.
    if (data?.target === 'mount_disk' && normalizedRole.value === 'P2') {
      payloadData = { action_type: 'button_press', target: 'mount_disk', value: data?.value || '' }
    } else if (normalizedRole.value === 'P1') {
      payloadData = { action_type: 'text_input', target: 'rescue_word', value: data?.answer || '' }
    }
  }

  lastError.value = ''
  if (payloadData.target) sendEvent('player_input', payloadData)
}
</script>

<style scoped>
/* Verbindung verloren: oben über allem, bis die Verbindung wieder steht */
.conn-banner {
  position: fixed;
  top: 12px;
  left: 0;
  right: 0;
  width: fit-content;
  margin: 0 auto;
  z-index: 200;
  padding: 10px 20px;
  border: 1px solid var(--red-border, #ff3a4d);
  background: rgba(40, 0, 0, 0.92);
  color: #ff8a8a;
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.08em;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  animation: conn-puls 1.2s ease-in-out infinite;
}

@keyframes conn-puls { 50% { border-color: #ff8a8a; } }

/* Spielphase: Kopfleiste + Aufgabe, als ein Block für den Übergang */
.phase-game {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.player {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Phase 1: Verbinden */
.phase-connect {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.connect-card {
  width: 100%;
  max-width: 400px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  padding: 36px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.connect-title {
  font-family: var(--mono);
  font-size: 20px;
  font-weight: 700;
  color: var(--fg);
  margin: 0 0 8px 0;
  letter-spacing: 0.05em;
}

.field { display: flex; flex-direction: column; gap: 6px; }

.field-label {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.input {
  width: 100%;
  padding: 14px 16px;
  background: var(--bg);
  color: var(--fg);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 16px;
  outline: none;
  text-align: center;
  letter-spacing: 0.15em;
}

.input:focus { border-color: var(--green-border); }

.connect-name {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--fg-3);
  text-align: center;
}

.connect-name strong { color: var(--green); font-weight: 600; }

.join-error {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--red);
  text-align: center;
  margin: 0;
}

.btn-main {
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

.btn-main:hover:not(:disabled) { background: #4dff8f; }
.btn-main:disabled { opacity: 0.35; cursor: not-allowed; }

.back-btn {
  background: none;
  border: none;
  color: var(--fg-3);
  font-family: var(--mono);
  font-size: 12px;
  cursor: pointer;
  padding: 4px;
  align-self: center;
  letter-spacing: 0.05em;
}

.back-btn:hover { color: var(--fg-2); }

/* Bar (Lobby / Task) */
.lobby-bar,
.task-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 24px;
  border-bottom: 1px solid var(--border);
  font-family: var(--mono);
  font-size: 13px;
}

.bar-brand { font-weight: 700; color: var(--green); letter-spacing: 0.15em; }
.bar-session,
.bar-role { color: var(--fg-2); letter-spacing: 0.1em; }
.bar-count,
.bar-stats { margin-left: auto; color: var(--fg-3); letter-spacing: 0.05em; }

/* Bernstein wie am Beamer: DEV-Runden zählen nicht */
.bar-dev {
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--amber);
  background: var(--amber-bg);
  border: 1px solid var(--amber-border);
}

/* Phase 2: Rollenwahl */
.phase-lobby {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.lobby-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 40px;
  gap: 12px;
}

.lobby-title {
  font-family: var(--mono);
  font-size: 40px;
  font-weight: 700;
  color: var(--fg);
  margin: 0;
  letter-spacing: -0.01em;
}

.lobby-sub {
  font-family: var(--mono);
  font-size: 14px;
  color: var(--fg-3);
  margin: 0 0 20px 0;
  letter-spacing: 0.05em;
}

.role-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  width: 100%;
  max-width: 900px;
}

.role-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 28px 22px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  color: var(--fg);
  font-family: var(--mono);
  cursor: pointer;
  text-align: left;
  min-height: 160px;
  transition: border-color 0.15s, background 0.15s;
}

.role-card:hover:not(:disabled) {
  border-color: var(--green-border);
  background: var(--bg-2);
}

.role-card.taken { opacity: 0.4; cursor: not-allowed; }

.role-name {
  font-size: 22px;
  font-weight: 700;
  color: var(--green);
  letter-spacing: 0.05em;
  margin-top: auto;
}

.role-desc {
  font-size: 12px;
  color: var(--fg-3);
  letter-spacing: 0.05em;
}

.role-error {
  margin-top: 16px;
  font-family: var(--mono);
  font-size: 13px;
  color: var(--red);
  padding: 10px 16px;
  border: 1px solid var(--red);
  background: rgba(255, 58, 77, 0.08);
  letter-spacing: 0.05em;
}

/* Phase 3: Warten */
.phase-wait {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.wait-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 32px 40px;
}

.wait-title {
  font-family: var(--mono);
  font-size: 32px;
  font-weight: 700;
  color: var(--fg);
  margin: 0;
}

.wait-sub {
  font-family: var(--mono);
  font-size: 14px;
  color: var(--fg-3);
  margin: 0;
  letter-spacing: 0.1em;
}

.wait-list {
  list-style: none;
  padding: 0;
  margin: 12px 0 20px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  max-width: 420px;
}

.wait-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  font-family: var(--mono);
  font-size: 14px;
}

.wait-item.empty {
  opacity: 0.5;
  border-style: dashed;
}

.wait-name { color: var(--fg); }

.wait-role {
  color: var(--green);
  font-size: 12px;
  letter-spacing: 0.1em;
}

.briefing-note {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 18px 28px;
  border: 1px solid var(--green-border);
  background: var(--green-bg);
  text-align: center;
  animation: briefing-puls 1.6s ease-in-out infinite;
}

.briefing-title { font-family: var(--mono); font-size: 16px; font-weight: 700; letter-spacing: 0.12em; color: var(--green); }
.briefing-sub { font-size: 14px; color: var(--fg-2); }
.briefing-count { font-family: var(--mono); font-size: 13px; letter-spacing: 0.1em; color: var(--fg-3); }
.ready-btn {
  margin-top: 10px;
  min-height: 52px;
  width: 100%;
  font-family: var(--mono);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.12em;
  background: transparent;
  color: var(--green);
  border: 2px solid var(--green);
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}
.ready-btn:hover { background: rgba(0, 255, 140, 0.12); }
.ready-btn.is-ready { background: var(--green); color: var(--bg); }

.briefing-fallback {
  margin-top: 10px;
  padding: 8px 14px;
  background: none;
  border: 1px solid var(--border-2);
  color: var(--fg-3);
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 0.06em;
  cursor: pointer;
}

.briefing-fallback:hover { color: var(--green); border-color: var(--green-border); }

@keyframes briefing-puls { 50% { border-color: var(--green); } }

@media (prefers-reduced-motion: reduce) {
  .briefing-note { animation: none; }
}

.start-btn {
  margin-top: 16px;
  padding: 16px 64px;
  background: var(--green);
  color: #050a08;
  border: none;
  font-family: var(--mono);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.15em;
  cursor: pointer;
  transition: background 0.15s;
}

.start-btn:hover:not(:disabled) { background: #4dff8f; }

.start-btn:disabled {
  background: var(--bg-2);
  color: var(--fg-3);
  cursor: not-allowed;
}

.wait-error {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--red);
  margin: 8px 0 0 0;
  letter-spacing: 0.05em;
}

.task-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
}

/* Platz für die offene Teilekiste (links, auf dem Handy unten), damit
   die Zahlen der Aufgabe sichtbar bleiben */
.task-main { transition: padding 0.6s cubic-bezier(0.22, 1, 0.36, 1); }
.task-main.with-kiste { padding-left: 300px; }

@media (max-width: 700px) {
  .task-main.with-kiste { padding-left: 16px; padding-bottom: 420px; overflow-y: auto; }
}

@media (max-width: 900px) {
  .role-cards { grid-template-columns: 1fr; }
  .lobby-title { font-size: 28px; }
}
</style>
