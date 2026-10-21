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
  setConnected,
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

// Aufgabe 3: Platte (Rückseite), Login und Wort (Vorderseite) melden über `solved`.
const datenrettungStub = {
  name: 'Task3Stub',
  template: `
    <div class="task3-stub">
      <button class="task3-answer" @click="$emit('solved', { target: 'rescue_word', answer: 'FALSCH' })">answer</button>
      <button class="task3-login" @click="$emit('solved', { target: 'terminal_login', answer: 'REHA' })">login</button>
      <button class="task3-disk" @click="$emit('solved', { target: 'mount_disk', value: 'SN-4471' })">disk</button>
    </div>
  `,
}

// Aufgabe 2: Löschen (Vorderseite) und Vier-Augen-Freigabe (Leitstand, Rückseite).
const loeschStub = {
  name: 'Task2Stub',
  template: `
    <div class="task2-stub">
      <button class="task2-loeschen" @click="$emit('solved', { valve: 'B-02', color: 'CO2' })">löschen</button>
      <button class="task2-freigabe" @click="$emit('solved', { target: 'release' })">freigabe</button>
    </div>
  `,
}

const stubs = {
  Task1P1: taskStub,
  Task1P2: taskStub,
  Task1Master: taskStub,
  Task2P1: loeschStub,
  Task2P2: loeschStub,
  Task2Master: loeschStub,
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
      { event: 'player_register', payload: { player_name: 'Patrick', client_id: expect.any(String) } },
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

  it('zeigt während der Einsatzbesprechung „schaut auf den Beamer“ statt des Start-Knopfs', async () => {
    const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
    simulateMessage({ event: 'lobby_update', payload: { players: [{ name: 'Patrick', role: 'MASTER' }], status: 'briefing', ready_to_start: true } })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.briefing-note').text()).toContain('Einsatzbesprechung')
    expect(wrapper.find('.start-btn').exists()).toBe(false)
  })

  describe('Wiedereinstieg nach Spielende (fix/wiedereinstieg)', () => {
    it('neu beigetreten nach einem Sieg: zeigt den Sieg mit den echten Punkten', async () => {
      const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
      await joinAs(wrapper)
      simulateMessage({ event: 'game_over', payload: { result: 'victory', score: 1425, survived_seconds: 240, leaderboard: null } })
      simulateMessage({ event: 'lobby_update', payload: { players: [], status: 'won', ready_to_start: true } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.end').classes()).toContain('is-win')
      expect(wrapper.text()).toContain('1425')
    })
  })

  describe('Einsatzbesprechung ohne Beamer (fix/beamer-anwesenheit)', () => {
    afterEach(() => vi.useRealTimers())

    async function imBriefing() {
      const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
      await joinAs(wrapper)
      simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
      vi.useFakeTimers()
      simulateMessage({ event: 'lobby_update', payload: { players: [{ name: 'Patrick', role: 'MASTER' }], status: 'briefing', ready_to_start: true } })
      await wrapper.vm.$nextTick()
      return wrapper
    }

    it('nach 20 s erscheint „Ohne Beamer starten“ (falls der Beamer weg ist)', async () => {
      const wrapper = await imBriefing()
      expect(wrapper.find('.briefing-fallback').exists()).toBe(false)
      vi.advanceTimersByTime(20000)
      await wrapper.vm.$nextTick()
      await wrapper.find('.briefing-fallback').trigger('click')
      expect(getSentEvents().at(-1)).toEqual({ event: 'start_game', payload: {} })
    })

    it('geht die Besprechung zu Ende (running), verschwindet der Knopf', async () => {
      const wrapper = await imBriefing()
      vi.advanceTimersByTime(20000)
      simulateMessage({ event: 'lobby_update', payload: { players: [{ name: 'Patrick', role: 'MASTER' }], status: 'waiting', ready_to_start: true } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.briefing-fallback').exists()).toBe(false)
    })
  })

  describe('Verbindung und Fehler (fix/verbindung)', () => {
    async function imSpiel() {
      const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
      await joinAs(wrapper)
      simulateMessage({ event: 'role_assigned', payload: { role: 'FI-SI' } })
      simulateMessage({ event: 'game_tick', payload: { health: 300, time_left: 280, tasks: [{ kind: 'data_rescue', view: { type: 'rescue_terminal' } }] } })
      await wrapper.vm.$nextTick()
      return wrapper
    }
    const fehlerDerAufgabe = (w) => w.find('.task3-stub').attributes('server-error')

    it('Verbindung weg: Banner und die Aufgabe wird freigegeben; wieder da: Banner weg', async () => {
      const wrapper = await imSpiel()
      expect(wrapper.find('.conn-banner').exists()).toBe(false)

      setConnected(false)
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.conn-banner').text()).toMatch(/Verbindung verloren/)
      expect(fehlerDerAufgabe(wrapper)).toMatch(/Verbindung unterbrochen/)

      setConnected(true)
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.conn-banner').exists()).toBe(false)
    })

    it.each([['error', /Nicht angekommen/], ['ignored', /Nicht angenommen/]])(
      'input_result %s gibt die Aufgabe frei (Meldung statt hängendem „Prüfe …“)',
      async (result, text) => {
        const wrapper = await imSpiel()
        simulateMessage({ event: 'input_result', payload: { result } })
        await wrapper.vm.$nextTick()
        expect(fehlerDerAufgabe(wrapper)).toMatch(text)
      },
    )

    it('abgelehnter Beitritt (register_denied) führt zurück zur ID-Eingabe, Meldung bleibt', async () => {
      const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
      await joinAs(wrapper)
      simulateMessage({ event: 'error', payload: { code: 'register_denied', message: 'Lobby ist bereits voll!' } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.phase-connect').exists()).toBe(true)
      expect(wrapper.text()).toContain('Lobby ist bereits voll!')
    })
  })

  describe('Bereit-Knopf in der Einsatzbesprechung', () => {
    async function imBriefing(players) {
      const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
      await joinAs(wrapper)
      simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
      simulateMessage({ event: 'lobby_update', payload: { players, status: 'briefing', ready_to_start: true } })
      await wrapper.vm.$nextTick()
      return wrapper
    }

    it('meldet „Bereit“ an den Server', async () => {
      const wrapper = await imBriefing([{ name: 'Patrick', role: 'MASTER', ready: false }])
      await wrapper.find('.ready-btn').trigger('click')
      expect(getSentEvents().at(-1)).toEqual({ event: 'player_ready', payload: { ready: true } })
    })

    it('zeigt nach dem Server-Update „bereit“ und nimmt es beim nächsten Klick zurück', async () => {
      const wrapper = await imBriefing([
        { name: 'Patrick', role: 'MASTER', ready: true },
        { name: 'Bene', role: 'FI-SI', ready: false },
      ])
      expect(wrapper.find('.ready-btn').classes()).toContain('is-ready')
      expect(wrapper.find('.briefing-note').text()).toContain('1/3')
      await wrapper.find('.ready-btn').trigger('click')
      expect(getSentEvents().at(-1)).toEqual({ event: 'player_ready', payload: { ready: false } })
    })

    it('gibt es nur in der Einsatzbesprechung', async () => {
      const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
      await joinAs(wrapper)
      simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
      simulateMessage({ event: 'lobby_update', payload: { players: [{ name: 'Patrick', role: 'MASTER' }], status: 'ready', ready_to_start: true } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.ready-btn').exists()).toBe(false)
    })
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

  async function inAufgabe3(rolle, type) {
    const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: rolle } })
    simulateMessage({
      event: 'game_tick',
      payload: { health: 240, time_left: 180, tasks: [{ kind: 'data_rescue', view: { type } }] },
    })
    await wrapper.vm.$nextTick()
    return wrapper
  }

  it('sendet in Aufgabe 3 das Wort der Vorderseite als rescue_word', async () => {
    const wrapper = await inAufgabe3('FI-SI', 'rescue_terminal')
    await wrapper.find('.task3-answer').trigger('click')
    expect(getSentEvents().at(-1)).toEqual({
      event: 'player_input',
      payload: { action_type: 'text_input', target: 'rescue_word', value: 'FALSCH' },
    })
  })

  it('sendet in Aufgabe 3 den Login der Vorderseite als terminal_login', async () => {
    const wrapper = await inAufgabe3('FI-SI', 'rescue_terminal')
    await wrapper.find('.task3-login').trigger('click')
    expect(getSentEvents().at(-1)).toEqual({
      event: 'player_input',
      payload: { action_type: 'text_input', target: 'terminal_login', value: 'REHA' },
    })
  })

  it('sendet in Aufgabe 3 die Platte der Rückseite als mount_disk', async () => {
    const wrapper = await inAufgabe3('FI-AE', 'packet_dump')
    await wrapper.find('.task3-disk').trigger('click')
    expect(getSentEvents().at(-1)).toEqual({
      event: 'player_input',
      payload: { action_type: 'button_press', target: 'mount_disk', value: 'SN-4471' },
    })
  })

  it.each([['MASTER', 'rescue_log', '.task3-answer'], ['MASTER', 'rescue_log', '.task3-disk'], ['FI-AE', 'packet_dump', '.task3-answer']])(
    'in Aufgabe 3 sendet %s über %s/%s nichts',
    async (rolle, type, knopf) => {
      const wrapper = await inAufgabe3(rolle, type)
      const vorher = getSentEvents().length
      await wrapper.find(knopf).trigger('click')
      expect(getSentEvents()).toHaveLength(vorher)
    },
  )

  async function inAufgabe2(rolle, type) {
    const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: rolle } })
    simulateMessage({
      event: 'game_tick',
      payload: { health: 240, time_left: 180, tasks: [{ kind: 'fire_protocol', view: { type } }] },
    })
    await wrapper.vm.$nextTick()
    return wrapper
  }

  it('sendet in Aufgabe 2 das Löschen der Vorderseite als valve_action RACK:MITTEL', async () => {
    const wrapper = await inAufgabe2('FI-SI', 'valve_panel')
    await wrapper.find('.task2-loeschen').trigger('click')
    expect(getSentEvents().at(-1)).toEqual({
      event: 'player_input',
      payload: { action_type: 'button_press', target: 'valve_action', value: 'B-02:CO2' },
    })
  })

  it.each([['MASTER', 'fire_log'], ['FI-AE', 'rack_rear']])(
    'sendet in Aufgabe 2 die Freigabe von %s als button_press release',
    async (rolle, type) => {
      const wrapper = await inAufgabe2(rolle, type)
      await wrapper.find('.task2-freigabe').trigger('click')
      expect(getSentEvents().at(-1)).toEqual({
        event: 'player_input',
        payload: { action_type: 'button_press', target: 'release', value: 'press' },
      })
    },
  )

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

  it('Warteliste in fester Rollen-Reihenfolge (Leitstand zuerst)', async () => {
    const wrapper = mount(PlayerScreen, { props: { playerName: 'Bene' }, global: { stubs } })
    await joinAs(wrapper)
    simulateMessage({ event: 'role_assigned', payload: { role: 'FI-SI' } })
    simulateMessage({ event: 'lobby_update', payload: {
      players: [{ name: 'Bene', role: 'FI-SI' }, { name: 'Anna', role: 'MASTER' }],
      roles_taken: ['FI-SI', 'MASTER'], status: 'waiting', ready_to_start: false,
    } })
    await wrapper.vm.$nextTick()
    const namen = wrapper.findAll('.wait-item .wait-name').map((n) => n.text())
    expect(namen).toEqual(['Anna', 'Bene', 'wartet'])
  })

  describe('Fundorte und Teilekiste (feat/fundorte)', () => {
    const NETZTEIL = { id: 'psu', name: 'Netzteil', fundort: 'schrank', label: '230 V' }

    async function imSpiel(rolle, teile = []) {
      const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
      await joinAs(wrapper)
      simulateMessage({ event: 'role_assigned', payload: { role: rolle } })
      simulateMessage({ event: 'lobby_update', payload: { players: [{ name: 'Patrick', role: rolle }], status: 'running', ready_to_start: true } })
      simulateMessage({ event: 'game_tick', payload: { health: 300, time_left: 500, tasks: [{ task_id: 't1', kind: 'alarm', view: {} }], parts: teile } })
      await wrapper.vm.$nextTick()
      return wrapper
    }

    it('neues Teil gefunden: Zwischenszene mit Fundort und nächster Aufgabe', async () => {
      const wrapper = await imSpiel('FI-SI')
      expect(wrapper.find('.zwischenszene').exists()).toBe(false)
      simulateMessage({ event: 'game_tick', payload: { health: 300, time_left: 499, tasks: [{ task_id: 't2', kind: 'fire_protocol', view: {} }], parts: [NETZTEIL] } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.zwischenszene .fundort--schrank').exists()).toBe(true)

      wrapper.findComponent({ name: 'Zwischenszene' }).vm.$emit('fertig')
      await wrapper.vm.$nextTick()
      await flushPromises()
      expect(wrapper.findComponent({ name: 'Zwischenszene' }).exists()).toBe(false)
    })

    it('wer später dazukommt, sieht keine Zwischenszene für alte Teile', async () => {
      const wrapper = await imSpiel('FI-SI', [NETZTEIL])
      expect(wrapper.find('.zwischenszene').exists()).toBe(false)
    })

    it('nur der Leitstand hat die Teilekiste', async () => {
      expect((await imSpiel('MASTER', [NETZTEIL])).find('.kiste').exists()).toBe(true)
      resetGameSocketMock()
      expect((await imSpiel('FI-AE', [NETZTEIL])).find('.kiste').exists()).toBe(false)
    })
  })

  describe('Kleinkram (fix/kleinkram)', () => {
    afterEach(() => {
      vi.useRealTimers()
      sessionStorage.clear()
    })

    const kennung = () => getSentEvents().filter((e) => e.event === 'player_register').at(-1).payload.client_id

    it('schickt eine Tab-Kennung mit, die ein Neuladen übersteht (gleicher Name auf zwei Geräten wird erkannt)', async () => {
      const erster = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
      await joinAs(erster)
      const id = kennung()
      expect(id).toMatch(/\S{8,}/)
      erster.unmount()

      resetGameSocketMock()   // „F5“: neue Komponente, gleicher Tab
      const nachReload = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
      await joinAs(nachReload)
      expect(kennung()).toBe(id)
    })

    it('Sieg im Finale: erst geht der Tresor auf, dann kommt das Ergebnis', async () => {
      const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
      await joinAs(wrapper)
      simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
      simulateMessage({ event: 'lobby_update', payload: { players: [{ name: 'Patrick', role: 'MASTER' }], status: 'running', ready_to_start: true } })
      simulateMessage({ event: 'game_tick', payload: { health: 300, time_left: 100, tasks: [{ task_id: 't4', kind: 'reboot', view: {} }] } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.reboot-stub').exists()).toBe(true)

      vi.useFakeTimers()
      simulateMessage({ event: 'game_over', payload: { result: 'victory', score: 900, survived_seconds: 200 } })
      simulateMessage({ event: 'lobby_update', payload: { players: [{ name: 'Patrick', role: 'MASTER' }], status: 'won', ready_to_start: true } })
      await wrapper.vm.$nextTick()
      // Tresor bleibt sichtbar und bekommt victory = true
      expect(wrapper.find('.reboot-stub').exists()).toBe(true)
      expect(wrapper.findComponent({ name: 'Task4RebootStub' }).attributes('victory')).toBe('true')
      expect(wrapper.find('.end').exists()).toBe(false)

      vi.advanceTimersByTime(2500)
      await wrapper.vm.$nextTick()
      await flushPromises()
      expect(wrapper.find('.end').exists()).toBe(true)
      expect(wrapper.find('.end-status').text()).toBe('Mission erfüllt')
    })

    it('Niederlage im Finale: Ergebnis sofort', async () => {
      const wrapper = mount(PlayerScreen, { props: { playerName: 'Patrick' }, global: { stubs } })
      await joinAs(wrapper)
      simulateMessage({ event: 'role_assigned', payload: { role: 'MASTER' } })
      simulateMessage({ event: 'lobby_update', payload: { players: [{ name: 'Patrick', role: 'MASTER' }], status: 'running', ready_to_start: true } })
      simulateMessage({ event: 'game_tick', payload: { health: 300, time_left: 1, tasks: [{ task_id: 't4', kind: 'reboot', view: {} }] } })
      simulateMessage({ event: 'game_over', payload: { result: 'meltdown', score: 0, survived_seconds: 300 } })
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.end').exists()).toBe(true)
    })
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
