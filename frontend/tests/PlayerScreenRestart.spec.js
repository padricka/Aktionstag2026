/**
 * PlayerScreen — Neustart nach Spielende.
 * reset_game löscht im Backend alle Spieler (lobby_update mit players: []).
 * Wer angemeldet war, soll sich dann selbst wieder anmelden, statt bei der
 * ID-Eingabe zu landen oder ohne Anmeldung in der Rollenwahl zu hängen.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import PlayerScreen from '../src/components/PlayerScreen.vue'
import {
  simulateMessage,
  resetGameSocketMock,
  getSentEvents,
  getConnectCalls,
} from './mocks/useGameSocket.js'

vi.mock('../src/composables/useGameSocket.js', () => import('./mocks/useGameSocket.js'))

const NAME = 'Patrick'
const taskStub = { name: 'TaskStub', template: '<div class="task-stub" />' }
const stubs = Object.fromEntries(
  ['Task1P1', 'Task1P2', 'Task1Master', 'Task2P1', 'Task2P2', 'Task2Master',
    'Task3P1', 'Task3P2', 'Task3Master', 'Task4Reboot'].map((n) => [n, taskStub]),
)

function lobby(players, status = 'waiting') {
  simulateMessage({
    event: 'lobby_update',
    payload: { players, status, ready_to_start: false, roles_taken: players.map((p) => p.role).filter(Boolean) },
  })
}

const registrierungen = () => getSentEvents().filter((e) => e.event === 'player_register').length

/** Beitreten, Rolle haben, Runde verloren → GameOver-Bildschirm. */
async function nachSpielende() {
  const wrapper = mount(PlayerScreen, { props: { playerName: NAME }, global: { stubs } })
  await wrapper.find('.input').setValue('abcd')
  await wrapper.find('.btn-main').trigger('click')
  await flushPromises()
  lobby([{ name: NAME, role: null }])
  simulateMessage({ event: 'role_assigned', payload: { role: 'FI-SI' } })
  lobby([{ name: NAME, role: 'FI-SI' }, { name: 'B', role: 'MASTER' }, { name: 'C', role: 'FI-AE' }], 'running')
  simulateMessage({ event: 'game_over', payload: { result: 'meltdown', score: 0, survived_seconds: 99 } })
  await wrapper.vm.$nextTick()
  expect(wrapper.find('.restart-btn').exists()).toBe(true)
  return wrapper
}

describe('PlayerScreen.vue — Neustart', () => {
  beforeEach(() => {
    resetGameSocketMock()
    vi.useFakeTimers()
    vi.stubGlobal('location', { protocol: 'http:', hostname: 'localhost' })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('Mitspieler kommt nach fremdem Neustart ohne neue ID-Eingabe zurück in die Rollenwahl', async () => {
    const wrapper = await nachSpielende()
    const vorher = registrierungen()

    lobby([])   // ein anderer hat Neustart gedrückt
    await wrapper.vm.$nextTick()

    expect(registrierungen()).toBe(vorher + 1)
    expect(wrapper.find('.restart-btn').exists()).toBe(false)
    expect(wrapper.find('.phase-connect').exists()).toBe(false)
    expect(wrapper.find('.phase-lobby').exists()).toBe(true)
  })

  it('meldet sich erneut an, wenn ein zweiter Neustart die frische Anmeldung löscht', async () => {
    const wrapper = await nachSpielende()
    lobby([])
    lobby([{ name: NAME, role: null }])
    const vorher = registrierungen()

    lobby([])   // zweiter, fast gleichzeitiger Neustart
    await wrapper.vm.$nextTick()

    expect(registrierungen()).toBe(vorher + 1)
    expect(wrapper.find('.phase-lobby').exists()).toBe(true)
  })

  it('meldet sich nicht doppelt an, bevor die erste Anmeldung bestätigt ist', async () => {
    const wrapper = mount(PlayerScreen, { props: { playerName: NAME }, global: { stubs } })
    await wrapper.find('.input').setValue('abcd')
    await wrapper.find('.btn-main').trigger('click')
    await flushPromises()

    lobby([])   // lobby_update direkt nach dem Verbinden, vor der eigenen Anmeldung
    await wrapper.vm.$nextTick()

    expect(registrierungen()).toBe(1)
  })

  it('meldet sich während einer laufenden Runde nicht neu an', async () => {
    await nachSpielende()
    const vorher = registrierungen()

    lobby([{ name: 'B', role: 'MASTER' }], 'running')

    expect(registrierungen()).toBe(vorher)
  })

  it('wer selbst Neustart drückt, meldet sich genau einmal über die neue Verbindung an', async () => {
    const wrapper = await nachSpielende()
    const vorher = registrierungen()

    await wrapper.find('.restart-btn').trigger('click')
    expect(getSentEvents().at(-1)).toEqual({ event: 'reset_game', payload: {} })
    lobby([])   // eigener Reset kommt noch auf der alten Verbindung an
    vi.advanceTimersByTime(300)
    await wrapper.vm.$nextTick()

    expect(registrierungen()).toBe(vorher + 1)
    expect(wrapper.find('.phase-lobby').exists()).toBe(true)
  })

  it('„Spiel beenden“ im Spielende führt zurück zum Hauptmenü', async () => {
    const wrapper = await nachSpielende()
    await wrapper.find('.end-card .end-exit').trigger('click')
    expect(wrapper.emitted('exit')).toHaveLength(1)
  })

  it('verbindet sich nach Neustart mit derselben bereinigten ID wie beim Beitreten', async () => {
    // Der Beamer zeigt die ID groß; Spieler tippen sie oft genau so (ggf. mit Leerzeichen)
    const wrapper = mount(PlayerScreen, { props: { playerName: NAME }, global: { stubs } })
    await wrapper.find('.input').setValue(' XVK2 ')
    await wrapper.find('.btn-main').trigger('click')
    await flushPromises()
    lobby([{ name: NAME, role: 'FI-SI' }], 'running')
    simulateMessage({ event: 'role_assigned', payload: { role: 'FI-SI' } })
    simulateMessage({ event: 'game_over', payload: { result: 'meltdown', score: 0, survived_seconds: 9 } })
    await wrapper.vm.$nextTick()

    await wrapper.find('.restart-btn').trigger('click')
    vi.advanceTimersByTime(300)

    const urls = getConnectCalls().map((c) => c.url)
    expect(urls).toHaveLength(2)
    expect(urls[1]).toBe(urls[0])
    expect(urls[1]).toMatch(/\/ws\/game\/xvk2\/$/)
  })
})

describe('PlayerScreen.vue — Leaderboard im Spielende', () => {
  beforeEach(() => {
    resetGameSocketMock()
    vi.stubGlobal('location', { protocol: 'http:', hostname: 'localhost' })
  })
  afterEach(() => vi.unstubAllGlobals())

  it('reicht die Top 5 aus game_over an die Punkte-Karte weiter', async () => {
    const wrapper = mount(PlayerScreen, { props: { playerName: NAME }, global: { stubs } })
    await wrapper.find('.input').setValue('abcd')
    await wrapper.find('.btn-main').trigger('click')
    await flushPromises()
    simulateMessage({
      event: 'game_over',
      payload: {
        result: 'victory', score: 50, survived_seconds: 9,
        leaderboard: { rank: 1, total: 1, top: [{ rank: 1, score: 50, players: [NAME, 'B', 'C'] }] },
      },
    })
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.end-board li.is-own').text()).toContain('50')
  })
})

describe('PlayerScreen.vue — DEV-Modus sichtbar', () => {
  beforeEach(() => {
    resetGameSocketMock()
    vi.stubGlobal('location', { protocol: 'http:', hostname: 'localhost' })
  })
  afterEach(() => vi.unstubAllGlobals())

  async function imSpiel(devMode) {
    const wrapper = mount(PlayerScreen, { props: { playerName: NAME }, global: { stubs } })
    await wrapper.find('.input').setValue('abcd')
    await wrapper.find('.btn-main').trigger('click')
    await flushPromises()
    simulateMessage({ event: 'lobby_update', payload: { players: [{ name: NAME, role: 'FI-SI' }], status: 'running', dev_mode: devMode } })
    simulateMessage({ event: 'role_assigned', payload: { role: 'FI-SI' } })
    simulateMessage({ event: 'game_tick', payload: { health: 300, time_left: 300, tasks: [] } })
    await wrapper.vm.$nextTick()
    return wrapper
  }

  it('zeigt im DEV-Modus während der Runde „DEV · nicht gewertet“', async () => {
    const wrapper = await imSpiel(true)
    expect(wrapper.find('.task-bar .bar-dev').text()).toContain('nicht gewertet')
  })

  it('ohne DEV-Modus kein Schild', async () => {
    const wrapper = await imSpiel(false)
    expect(wrapper.find('.bar-dev').exists()).toBe(false)
  })
})
