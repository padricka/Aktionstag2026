/**
 * HostScreen.spec.js
 *
 * Die Komponente zeigt anfangs die Lobby (3 Slots) und nach einem
 * `game_over`-Socket-Event das Game-Over-Overlay.
 *
 * - useGameSocket ist gemockt (tests/mocks/useGameSocket.js) → kein echtes Socket.
 * - fetch wird gestubbt, da onMounted ein `create-game` holt (kein Backend im Test).
 */
// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import HostScreen from '../src/components/HostScreen.vue'
import {
  simulateMessage,
  resetGameSocketMock,
  getSentEvents,
} from './mocks/useGameSocket.js'

vi.mock('../src/composables/useGameSocket.js', () => import('./mocks/useGameSocket.js'))

describe('HostScreen.vue (mit Fake-WebSocket)', () => {
  beforeEach(() => {
    resetGameSocketMock()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ game_id: 'test' }) })
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('zeigt anfangs die Lobby mit 3 Slots und die Sitzungs-ID', async () => {
    const wrapper = mount(HostScreen)
    await new Promise((r) => setTimeout(r, 10))

    expect(wrapper.find('.lobby').exists()).toBe(true)
    expect(wrapper.find('.lobby-title').text()).toBe('Bereit für den Start')
    expect(wrapper.find('.id-value').text()).toBe('TEST')
    expect(wrapper.findAll('.slot')).toHaveLength(3)
    expect(wrapper.find('.host-top').exists()).toBe(true)
  })

  it('sendet host_register nach create-game', async () => {
    mount(HostScreen)
    await new Promise((r) => setTimeout(r, 10))

    expect(getSentEvents()).toContainEqual({ event: 'host_register', payload: {} })
  })

  it('füllt Lobby-Slots aus lobby_update', async () => {
    const wrapper = mount(HostScreen)
    await new Promise((r) => setTimeout(r, 10))

    simulateMessage({
      event: 'lobby_update',
      payload: {
        players: [
          { name: 'A', role: 'MASTER' },
          { name: 'B', role: 'FI-SI' },
        ],
        roles_taken: ['MASTER', 'FI-SI'],
        status: 'waiting',
      },
    })
    await wrapper.vm.$nextTick()

    const slots = wrapper.findAll('.slot')
    expect(slots[0].text()).toContain('A')
    expect(slots[1].text()).toContain('B')
    expect(slots[2].text()).toContain('wartet')
  })

  it('wechselt bei game_tick in die Lauf-Ansicht mit HP/Zeit', async () => {
    const wrapper = mount(HostScreen)
    await new Promise((r) => setTimeout(r, 10))

    simulateMessage({
      event: 'game_tick',
      payload: { health: 240, time_left: 290, tasks: [] },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.running').exists()).toBe(true)
    expect(wrapper.find('.lobby').exists()).toBe(false)
    expect(wrapper.find('.hp-value').text()).toContain('240')
  })

  it('zeigt nach game_over das Game-Over-Overlay und verbirgt Lobby/Counter', async () => {
    const wrapper = mount(HostScreen)
    await new Promise((r) => setTimeout(r, 10))

    simulateMessage({
      type: 'game_over',
      payload: { result: 'meltdown', score: 42, survived_seconds: 123 },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.end').exists()).toBe(true)
    expect(wrapper.find('.end-card').exists()).toBe(true)
    expect(wrapper.find('.lobby').exists()).toBe(false)
    expect(wrapper.find('.host-top').exists()).toBe(false)
  })

  it('zeigt die gefundenen Ziffern aus reboot_digits auf dem Beamer', async () => {
    const wrapper = mount(HostScreen)
    await new Promise((r) => setTimeout(r, 10))

    simulateMessage({
      event: 'game_tick',
      payload: { health: 240, time_left: 290, tasks: [], reboot_digits: [4, 7, null] },
    })
    await wrapper.vm.$nextTick()

    const raeder = wrapper.findAll('[role="spinbutton"]')
    expect(raeder.map((r) => r.attributes('aria-valuenow'))).toEqual(['4', '7', undefined])
    expect(wrapper.find('.vd-panel__status').text()).toBe('GESPERRT · 2/3')
  })

  it('zeigt bei Sieg den offenen Tresor statt des Game-Over-Overlays', async () => {
    const wrapper = mount(HostScreen)
    await new Promise((r) => setTimeout(r, 10))

    simulateMessage({
      event: 'game_tick',
      payload: { health: 240, time_left: 290, tasks: [], reboot_digits: [4, 7, 2] },
    })
    simulateMessage({
      event: 'game_over',
      payload: { result: 'victory', score: 60, survived_seconds: 200 },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.vault').classes()).toContain('vault--open')
    expect(wrapper.find('.end').exists()).toBe(false)
    expect(wrapper.find('.finale-win').exists()).toBe(true)
  })

  describe('Hilfe-Notizen am Beamer', () => {
    async function imSpiel(hints) {
      const wrapper = mount(HostScreen)
      await new Promise((r) => setTimeout(r, 10))
      simulateMessage({ event: 'game_tick', payload: { health: 300, time_left: 280, tasks: [], hints } })
      await wrapper.vm.$nextTick()
      return wrapper
    }

    it('zeigt die Hilfe-Notizen der laufenden Aufgabe und öffnet die nächste per open_hint', async () => {
      const wrapper = await imSpiel({ total: 4, opened: [], cost: 50 })
      expect(wrapper.find('.hint-board').exists()).toBe(true)
      await wrapper.find('button.hint-open').trigger('click')
      expect(getSentEvents().at(-1)).toEqual({ event: 'open_hint', payload: {} })

      simulateMessage({ event: 'game_tick', payload: { health: 300, time_left: 279, tasks: [], hints: { total: 4, opened: ['Lest euch eure Teile vor.'], cost: 50 } } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.hint-note').text()).toContain('Lest euch eure Teile vor.')
    })

    it('ohne Hilfen (z. B. Finale) kein Hilfe-Bereich', async () => {
      const wrapper = await imSpiel({ total: 0, opened: [], cost: 50 })
      expect(wrapper.find('.hint-board').exists()).toBe(false)
    })

    it('zeigt eine Ablehnung des Servers (hint_denied)', async () => {
      const wrapper = await imSpiel({ total: 4, opened: [], cost: 50 })
      simulateMessage({ event: 'error', payload: { code: 'hint_denied', message: 'Alle Hilfen sind schon offen' } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.hint-error').text()).toBe('Alle Hilfen sind schon offen')
    })
  })

  describe('Neustart vom Beamer', () => {
    async function nachNiederlage() {
      const wrapper = mount(HostScreen)
      await new Promise((r) => setTimeout(r, 10))
      simulateMessage({ event: 'game_tick', payload: { health: 10, time_left: 100, tasks: [] } })
      simulateMessage({ event: 'game_over', payload: { result: 'meltdown', score: 42, survived_seconds: 123 } })
      await wrapper.vm.$nextTick()
      return wrapper
    }

    it('nach einer Niederlage startet der Host neu: reset_game, dann wieder Lobby', async () => {
      const wrapper = await nachNiederlage()
      await wrapper.find('.restart-btn').trigger('click')

      expect(getSentEvents().at(-1)).toEqual({ event: 'reset_game', payload: {} })
      expect(wrapper.find('.restart-btn').text()).toContain('Neustart …')

      simulateMessage({ event: 'lobby_update', payload: { players: [], status: 'waiting' } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.end').exists()).toBe(false)
      expect(wrapper.find('.lobby').exists()).toBe(true)
      expect(wrapper.find('.id-value').text()).toBe('TEST')     // gleiche Sitzung
    })

    it('nach einer Niederlage führt „Spiel beenden“ ins Hauptmenü', async () => {
      const wrapper = await nachNiederlage()
      await wrapper.find('.end-exit').trigger('click')
      expect(wrapper.emitted('exit')).toHaveLength(1)
    })

    it('nach einem Sieg gibt es neben dem offenen Tresor eine neue Runde', async () => {
      const wrapper = mount(HostScreen)
      await new Promise((r) => setTimeout(r, 10))
      simulateMessage({ event: 'game_over', payload: { result: 'victory', score: 60, survived_seconds: 200 } })
      await wrapper.vm.$nextTick()

      await wrapper.find('.host-restart').trigger('click')
      expect(getSentEvents().at(-1)).toEqual({ event: 'reset_game', payload: {} })
    })
  })

  it('zeigt einen Fehler statt der ID, wenn die Sitzung unbekannt ist (?game_id=…)', async () => {
    const wrapper = mount(HostScreen)
    await new Promise((r) => setTimeout(r, 10))

    simulateMessage({
      event: 'error',
      payload: { message: 'Unbekannte Sitzungs-ID', code: 'unknown_game' },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.id-value').exists()).toBe(false)
    expect(wrapper.find('.lobby-error').text()).toContain('TEST')
  })

  describe('Zustand kommt vom Backend', () => {
    async function laufend() {
      const wrapper = mount(HostScreen)
      await new Promise((r) => setTimeout(r, 10))
      simulateMessage({
        event: 'lobby_update',
        payload: { players: [], status: 'running', ready_to_start: true },
      })
      return wrapper
    }

    it('nimmt die maximalen HP aus game_tick.max_health', async () => {
      const wrapper = await laufend()
      simulateMessage({ event: 'game_tick', payload: { health: 250, max_health: 500, time_left: 100, tasks: [] } })
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.hp-value').text()).toBe('250 / 500')
      expect(wrapper.find('.hp-fill').attributes('style')).toContain('width: 50%')
    })

    it('zeigt Game Over erst mit game_over, nicht schon bei 0 HP oder 0 Sekunden', async () => {
      const wrapper = await laufend()
      simulateMessage({ event: 'game_tick', payload: { health: 0, max_health: 300, time_left: 0, tasks: [] } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.end').exists()).toBe(false)

      simulateMessage({ event: 'game_over', payload: { result: 'meltdown', score: 0, survived_seconds: 300 } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.end').exists()).toBe(true)
    })
  })

  describe('DEV-Modus', () => {
    async function laufendesSpiel(devMode) {
      const wrapper = mount(HostScreen)
      await new Promise((r) => setTimeout(r, 10))
      simulateMessage({
        event: 'lobby_update',
        payload: { players: [], status: 'running', ready_to_start: true, dev_mode: devMode },
      })
      simulateMessage({ event: 'game_tick', payload: { health: 300, time_left: 300, tasks: [] } })
      await wrapper.vm.$nextTick()
      return wrapper
    }

    it('zeigt in der Lobby neben der Sitzungs-ID einen Schalter, anfangs AUS', async () => {
      const wrapper = mount(HostScreen)
      await new Promise((r) => setTimeout(r, 10))

      const toggle = wrapper.find('.lobby .dev-toggle')
      expect(toggle.exists()).toBe(true)
      expect(toggle.text()).toContain('AUS')
      expect(toggle.attributes('aria-pressed')).toBe('false')
    })

    it('schaltet über den Server um und zeigt den Stand aus lobby_update', async () => {
      const wrapper = mount(HostScreen)
      await new Promise((r) => setTimeout(r, 10))

      await wrapper.find('.dev-toggle').trigger('click')
      expect(getSentEvents().at(-1)).toEqual({ event: 'dev_mode', payload: { enabled: true } })

      simulateMessage({
        event: 'lobby_update',
        payload: { players: [], status: 'waiting', ready_to_start: false, dev_mode: true },
      })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.dev-toggle').text()).toContain('AN')
      expect(wrapper.find('.dev-toggle').attributes('aria-pressed')).toBe('true')

      await wrapper.find('.dev-toggle').trigger('click')
      expect(getSentEvents().at(-1)).toEqual({ event: 'dev_mode', payload: { enabled: false } })
    })

    it('sagt in Lobby und Spiel dazu, dass DEV-Runden nicht gewertet werden', async () => {
      const wrapper = mount(HostScreen)
      await new Promise((r) => setTimeout(r, 10))
      simulateMessage({
        event: 'lobby_update',
        payload: { players: [], status: 'waiting', ready_to_start: false, dev_mode: true },
      })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.dev-note').text()).toContain('nicht gewertet')

      const laufend = await laufendesSpiel(true)
      expect(laufend.find('.dev-badge').text()).toContain('nicht gewertet')
    })

    it('ohne DEV-Modus gibt es im Spiel keinen Überspringen-Button', async () => {
      const wrapper = await laufendesSpiel(false)
      expect(wrapper.find('.running').exists()).toBe(true)
      expect(wrapper.find('.dev-skip').exists()).toBe(false)
      expect(wrapper.find('.dev-badge').exists()).toBe(false)
    })

    it('mit DEV-Modus überspringt der Host die Aufgabe für alle', async () => {
      const wrapper = await laufendesSpiel(true)
      expect(wrapper.find('.dev-badge').exists()).toBe(true)

      await wrapper.find('.dev-skip').trigger('click')
      expect(getSentEvents().at(-1)).toEqual({ event: 'dev_skip_task', payload: {} })
      // bis zur nächsten Aufgabe gesperrt (kein Doppelsprung)
      expect(wrapper.find('.dev-skip').attributes('disabled')).toBeDefined()

      simulateMessage({ event: 'game_tick', payload: { health: 300, time_left: 300, tasks: [] } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.dev-skip').attributes('disabled')).toBeUndefined()
    })

    it('zeigt eine Ablehnung des Servers an', async () => {
      const wrapper = mount(HostScreen)
      await new Promise((r) => setTimeout(r, 10))

      simulateMessage({
        event: 'error',
        payload: { message: 'DEV-Modus nur vor dem Start umschaltbar', code: 'dev_denied' },
      })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.dev-error').text()).toContain('nur vor dem Start')
    })
  })
})
