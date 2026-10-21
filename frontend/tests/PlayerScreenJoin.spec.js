/**
 * PlayerScreen — Beitreten mit einer Sitzungs-ID, die es nicht gibt.
 * Der Server schickt error { code: "unknown_game" } und schließt die Verbindung.
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

async function joinAs(wrapper, id) {
  await wrapper.find('.input').setValue(id)
  await wrapper.find('.btn-main').trigger('click')
  await flushPromises()
}

describe('PlayerScreen.vue — unbekannte Sitzungs-ID', () => {
  beforeEach(() => {
    resetGameSocketMock()
    vi.useFakeTimers()
    vi.stubGlobal('location', { protocol: 'http:', hostname: 'localhost' })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('bleibt in der Verbinden-Phase und zeigt einen Hinweis', async () => {
    const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' } })
    await joinAs(wrapper, 'abxy')

    simulateMessage({
      event: 'error',
      payload: { message: 'Unbekannte Sitzungs-ID', code: 'unknown_game' },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.phase-connect').exists()).toBe(true)
    expect(wrapper.find('.phase-lobby').exists()).toBe(false)
    expect(wrapper.find('.join-error').text()).toContain('ABXY')
  })

  it('der Hinweis bleibt stehen, bis neu verbunden wird', async () => {
    const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' } })
    await joinAs(wrapper, 'abxy')
    simulateMessage({ event: 'error', payload: { message: 'x', code: 'unknown_game' } })
    await wrapper.vm.$nextTick()

    vi.advanceTimersByTime(5000)
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.join-error').exists()).toBe(true)

    // Zweiter Versuch mit richtiger ID
    await joinAs(wrapper, 'abcd')
    expect(wrapper.find('.join-error').exists()).toBe(false)
    expect(getConnectCalls().at(-1).url).toContain('/ws/game/abcd/')
    expect(getSentEvents().at(-1)).toEqual({
      event: 'player_register',
      payload: { player_name: 'Patrick', client_id: expect.any(String) },
    })
  })

  it('andere Fehler werfen nicht aus der Lobby', async () => {
    const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' } })
    await joinAs(wrapper, 'abcd')
    simulateMessage({ event: 'error', payload: { message: 'Lobby ist bereits voll!' } })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.phase-lobby').exists()).toBe(true)
  })
})
