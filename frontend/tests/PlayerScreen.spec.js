/**
 * PlayerScreen — Join → Lobby → Rollenwahl → Tick / Game Over.
 * useGameSocket gemockt; Task-Komponenten gestubbt.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import PlayerScreen from '../src/components/PlayerScreen.vue'
import {
  simulateMessage,
  resetGameSocketMock,
  getSentEvents,
} from './mocks/useGameSocket.js'

vi.mock('../src/composables/useGameSocket.js', () => import('./mocks/useGameSocket.js'))

const taskStub = {
  name: 'TaskStub',
  template: `
    <div class="task-stub">
      <button
        class="task-stub-solved"
        @click="$emit('solved', { target: 'shutdown_cmd', code: ['stern', 'kreuz', 'plus', 'herz'] })"
      >solved</button>
    </div>
  `,
}

const rebootStub = {
  name: 'Task4RebootStub',
  template: `
    <div class="reboot-stub">
      <button class="reboot-stub-solved" @click="$emit('solved', { player: 'MASTER', value: '472' })">solved</button>
    </div>
  `,
}

// Aufgabe 3: Antwort und Sync-Knopf melden beide über `solved`.
const datenrettungStub = {
  name: 'Task3Stub',
  template: `
    <div class="task3-stub">
      <button class="task3-answer" @click="$emit('solved', { player: 'P1', answer: 'FALSCH' })">answer</button>
      <button class="task3-sync" @click="$emit('solved', { target: 'sync_button' })">sync</button>
    </div>
  `,
}

const stubs = {
  Task1P1: taskStub,
  Task1P2: taskStub,
  Task1Master: taskStub,
  Task2P1: taskStub,
  Task2P2: taskStub,
  Task2Master: taskStub,
  Task3P1: datenrettungStub,
  Task3P2: datenrettungStub,
  Task3Master: datenrettungStub,
  Task4Reboot: rebootStub,
}

async function joinAs(wrapper, id = 'abcd') {
  await wrapper.find('.input').setValue(id)
  await wrapper.find('.btn-main').trigger('click')
  await flushPromises()
}

describe('PlayerScreen.vue', () => {
  beforeEach(() => {
    resetGameSocketMock()
    vi.stubGlobal('location', {
      protocol: 'http:',
      hostname: 'localhost',
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('zeigt Verbinden-Phase mit Spielernamen', () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })

    expect(wrapper.find('.phase-connect').exists()).toBe(true)
    expect(wrapper.text()).toContain('Patrick')
    expect(wrapper.find('.btn-main').attributes('disabled')).toBeDefined()
  })

  it('sendet player_register nach Beitreten', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })

    await joinAs(wrapper, 'ensp')

    expect(wrapper.find('.phase-lobby').exists()).toBe(true)
    expect(getSentEvents()).toEqual([
      { event: 'player_register', payload: { player_name: 'Patrick' } },
    ])
  })

  it('sendet choose_role bei Rollenwahl', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)

    const masterCard = wrapper.findAll('.role-card').find((b) => b.text().includes('Leitstand'))
    await masterCard.trigger('click')

    expect(getSentEvents().at(-1)).toEqual({
      event: 'choose_role',
      payload: { role: 'MASTER' },
    })
  })

  it('wechselt nach role_assigned in die Warte-Phase', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)

    simulateMessage({
      event: 'role_assigned',
      payload: { role: 'FI-SI' },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.phase-wait').exists()).toBe(true)
    expect(wrapper.text()).toContain('Vorderseite')
  })

  it('zeigt Anzeigenamen Leitstand / Vorderseite / Rückseite (IDs unverändert)', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)

    const text = wrapper.find('.phase-lobby').text()
    expect(text).toContain('Leitstand')
    expect(text).toContain('Vorderseite')
    expect(text).toContain('Rückseite')
    expect(text).not.toContain('Spieler 1')
  })

  it('sendet shutdown_cmd von MASTER (Leitstand) bei Task 1', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
    simulateMessage({
      event: 'game_tick',
      payload: {
        health: 280,
        time_left: 290,
        tasks: [{
          view: {
            type: 'alarm_leds',
            slots: 4,
            burning_slot: 2,
            color_order: ['ROT', 'GELB', 'GRÜN', 'BLAU'],
            p_done: false,
          },
        }],
      },
    })
    await wrapper.vm.$nextTick()

    await wrapper.find('.task-stub-solved').trigger('click')

    expect(getSentEvents().at(-1)).toEqual({
      event: 'player_input',
      payload: {
        action_type: 'text_input',
        target: 'shutdown_cmd',
        value: 'stern,kreuz,plus,herz',
      },
    })
  })

  it('deaktiviert belegte Rollen aus lobby_update', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)

    simulateMessage({
      event: 'lobby_update',
      payload: {
        players: [{ name: 'Anna', role: 'MASTER' }],
        roles_taken: ['MASTER'],
        status: 'waiting',
        ready_to_start: false,
      },
    })
    await wrapper.vm.$nextTick()

    const masterCard = wrapper.findAll('.role-card').find((b) => b.text().includes('Leitstand'))
    expect(masterCard.attributes('disabled')).toBeDefined()
    expect(masterCard.classes()).toContain('taken')
  })

  it('sendet start_game wenn ready_to_start', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)

    simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
    simulateMessage({
      event: 'lobby_update',
      payload: {
        players: [
          { name: 'Patrick', role: 'MASTER' },
          { name: 'A', role: 'FI-SI' },
          { name: 'B', role: 'FI-AE' },
        ],
        roles_taken: ['MASTER', 'FI-SI', 'FI-AE'],
        status: 'waiting',
        ready_to_start: true,
      },
    })
    await wrapper.vm.$nextTick()

    await wrapper.find('.start-btn').trigger('click')
    expect(getSentEvents().at(-1)).toEqual({ event: 'start_game', payload: {} })
  })

  it('zeigt Task-UI und HP nach game_tick', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'FI-AE' } })
    simulateMessage({
      event: 'game_tick',
      payload: {
        health: 250,
        time_left: 280,
        tasks: [{ view: { type: 'shutdown_terminal', code_length: 4 } }],
      },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.task-bar').exists()).toBe(true)
    expect(wrapper.find('.task-stub').exists()).toBe(true)
    expect(wrapper.find('.bar-stats').text()).toContain('250 HP')
  })

  it('hat im Spiel einen Taschenrechner; offen rückt die Aufgabe zur Seite', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
    simulateMessage({ event: 'game_tick', payload: { health: 250, time_left: 280, tasks: [{ kind: 'alarm', view: {} }] } })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.task-main').classes()).not.toContain('with-calc')
    await wrapper.find('button.calc-handle').trigger('click')
    expect(wrapper.find('.calc-panel').exists()).toBe(true)
    expect(wrapper.find('.task-main').classes()).toContain('with-calc')
    expect(wrapper.find('.task-stub').exists()).toBe(true)      // Aufgabe bleibt sichtbar
  })

  it('zeigt den Taschenrechner noch nicht in der Lobby', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)
    expect(wrapper.find('button.calc-handle').exists()).toBe(false)
  })

  it('sendet beim Finale (Aufgabe 4) reboot_code vom Leitstand', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
    simulateMessage({
      event: 'game_tick',
      payload: {
        health: 240,
        time_left: 200,
        reboot_digits: [4, 7, 2],
        tasks: [{ view: { type: 'reboot', digit: 7, terminal: true } }],
      },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.reboot-stub').exists()).toBe(true)
    await wrapper.find('.reboot-stub-solved').trigger('click')

    expect(getSentEvents().at(-1)).toEqual({
      event: 'player_input',
      payload: { action_type: 'text_input', target: 'reboot_code', value: '472' },
    })
  })

  it('sendet in Aufgabe 3 die ascii_answer der Vorderseite', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'FI-SI' } })
    simulateMessage({
      event: 'game_tick',
      payload: {
        health: 240,
        time_left: 180,
        tasks: [{
          view: {
            type: 'ascii_puzzle',
            ascii_codes: [83, 69, 82, 86, 69, 82],
            ascii_half: { N: 78, Z: 90 },
            button_unlocked: false,
          },
        }],
      },
    })
    await wrapper.vm.$nextTick()

    await wrapper.find('.task3-answer').trigger('click')

    expect(getSentEvents().at(-1)).toEqual({
      event: 'player_input',
      payload: { action_type: 'text_input', target: 'ascii_answer', value: 'FALSCH' },
    })
  })

  it('sendet in Aufgabe 3 die binary_answer der Rückseite', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'FI-AE' } })
    simulateMessage({
      event: 'game_tick',
      payload: {
        health: 240,
        time_left: 180,
        tasks: [{
          view: {
            type: 'binary_puzzle',
            binary_codes: ['01001000'],
            place_values: [8, 4, 2, 1],
            button_unlocked: false,
          },
        }],
      },
    })
    await wrapper.vm.$nextTick()

    await wrapper.find('.task3-answer').trigger('click')

    expect(getSentEvents().at(-1)).toEqual({
      event: 'player_input',
      payload: { action_type: 'text_input', target: 'binary_answer', value: 'FALSCH' },
    })
  })

  it('sendet den Sync-Knopf aus Aufgabe 3 als button_press', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'FI-SI' } })
    simulateMessage({
      event: 'game_tick',
      payload: {
        health: 240,
        time_left: 180,
        tasks: [{
          view: {
            type: 'ascii_puzzle',
            ascii_codes: [83, 69, 82, 86, 69, 82],
            ascii_half: { N: 78, Z: 90 },
            button_unlocked: true,
          },
        }],
      },
    })
    await wrapper.vm.$nextTick()

    await wrapper.find('.task3-sync').trigger('click')

    expect(getSentEvents().at(-1)).toEqual({
      event: 'player_input',
      payload: { action_type: 'button_press', target: 'sync_button', value: 'press' },
    })
  })

  it('zeigt das Finale auch der Vorderseite, ohne reboot_code zu senden', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'FI-SI' } })
    simulateMessage({
      event: 'game_tick',
      payload: {
        health: 240,
        time_left: 200,
        reboot_digits: [4, null, null],
        tasks: [{ view: { type: 'reboot', digit: 3, terminal: false } }],
      },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.reboot-stub').exists()).toBe(true)
    await wrapper.find('.reboot-stub-solved').trigger('click')

    expect(getSentEvents().some((e) => e.payload?.target === 'reboot_code')).toBe(false)
  })

  it('zeigt GameOver nach game_over', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
    simulateMessage({
      event: 'game_over',
      payload: { result: 'meltdown', score: 7, survived_seconds: 11 },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.end').exists()).toBe(true)
    expect(wrapper.find('.end-score').text()).toBe('7')
  })

  it('akzeptiert auch type statt event (Übergang)', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
    simulateMessage({
      type: 'game_over',
      payload: { result: 'victory', score: 99, survived_seconds: 1 },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.end-status').text()).toBe('Mission erfüllt')
  })

  it('emittiert exit bei Zurück', async () => {
    const wrapper = mount(PlayerScreen, {
      props: { playerName: 'Patrick' },
      global: { stubs },
    })
    await wrapper.find('.back-btn').trigger('click')
    expect(wrapper.emitted('exit')).toHaveLength(1)
  })
})
