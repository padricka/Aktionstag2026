/**
 * PlayerScreen — Spielregeln liegen im Backend.
 * - Welche Aufgabe läuft, sagt task.kind (nicht aus view.type erraten).
 * - Max-HP kommt aus game_tick.max_health.
 * - Spielende nur durch game_over vom Server, nicht weil lokal hp <= 0 ist.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import PlayerScreen from '../src/components/PlayerScreen.vue'
import { simulateMessage, resetGameSocketMock } from './mocks/useGameSocket.js'

vi.mock('../src/composables/useGameSocket.js', () => import('./mocks/useGameSocket.js'))

const stub = (name) => ({ name, template: `<div class="stub-${name}" />` })
const stubs = Object.fromEntries(
  ['Task1P1', 'Task1P2', 'Task1Master', 'Task2P1', 'Task2P2', 'Task2Master',
    'Task3P1', 'Task3P2', 'Task3Master', 'Task4Reboot'].map((n) => [n, stub(n)]),
)

async function imSpiel(role = 'FI-SI') {
  const wrapper = mount(PlayerScreen, { props: { playerName: 'Ben' }, global: { stubs } })
  await wrapper.find('.input').setValue('abcd')
  await wrapper.find('.btn-main').trigger('click')
  await flushPromises()
  simulateMessage({ event: 'lobby_update', payload: { players: [{ name: 'Ben', role }], status: 'running' } })
  simulateMessage({ event: 'role_assigned', payload: { role } })
  await wrapper.vm.$nextTick()
  return wrapper
}

function tick(payload) {
  simulateMessage({
    event: 'game_tick',
    payload: { health: 300, max_health: 300, time_left: 300, reboot_digits: [null, null, null], ...payload },
  })
}

describe('PlayerScreen.vue — Zustand kommt vom Backend', () => {
  beforeEach(() => {
    resetGameSocketMock()
    vi.stubGlobal('location', { protocol: 'http:', hostname: 'localhost' })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('wählt die Aufgabe über task.kind, auch bei unbekanntem view.type', async () => {
    const wrapper = await imSpiel('FI-SI')
    tick({ tasks: [{ task_id: 't-2', kind: 'fire_protocol', view: { type: 'ganz_neu' } }] })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.stub-Task2P1').exists()).toBe(true)
  })

  it('zeigt Game Over erst mit game_over, nicht schon bei 0 HP im Tick', async () => {
    const wrapper = await imSpiel()
    tick({ health: 0, tasks: [{ task_id: 't-1', kind: 'alarm', view: { type: 'main_switches' } }] })
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.end').exists()).toBe(false)

    simulateMessage({ event: 'game_over', payload: { result: 'meltdown', score: 0, survived_seconds: 9 } })
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.end').exists()).toBe(true)
  })

  it('eine falsche Eingabe mit 0 HP beendet das Spiel nicht selbst', async () => {
    const wrapper = await imSpiel()
    tick({ tasks: [{ task_id: 't-1', kind: 'alarm', view: { type: 'main_switches' } }] })
    simulateMessage({ event: 'input_result', payload: { result: 'wrong', health: 0 } })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.end').exists()).toBe(false)
  })
})
