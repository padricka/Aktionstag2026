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
})
