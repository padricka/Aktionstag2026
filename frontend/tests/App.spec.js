/**
 * App.vue zeigt anfangs das Startmenü. Nach dem Start wird je nach Rolle
 * die Host-Ansicht (Beamer) oder die Spieler-Ansicht (Laptop) gerendert.
 * HostScreen/PlayerScreen/SettingsScreen werden gestubbt (kein Backend/Socket
 * im Test); StartMenu bleibt echt, damit der Klick-Flow getestet wird.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import App from '../src/App.vue'
import StartMenu from '../src/StartMenu.vue'

vi.mock('../src/composables/useGameSocket.js', () => import('./mocks/useGameSocket.js'))

const stubs = {
  HostScreen: { name: 'HostScreen', template: '<div class="host-screen"></div>' },
  PlayerScreen: {
    name: 'PlayerScreen',
    props: ['playerName'],
    template: '<div class="player-screen">{{ playerName }}</div>',
  },
  SettingsScreen: {
    name: 'SettingsScreen',
    template: '<div class="settings-screen"><button class="fake-save" @click="$emit(\'save\')">save</button></div>',
  },
}

describe('App.vue', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
    document.documentElement.style.filter = ''
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockReturnValue({
        matches: true,
        addEventListener: () => {},
        removeEventListener: () => {},
      })
    )
  })

  afterEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
    vi.unstubAllGlobals()
  })

  it('zeigt anfangs das Startmenü', () => {
    const wrapper = mount(App, { global: { stubs } })

    expect(wrapper.findComponent(StartMenu).exists()).toBe(true)
    expect(wrapper.find('.title').text()).toBe('DRV-BOX')
    expect(wrapper.find('.btn-host').exists()).toBe(true)
  })

  it('zeigt nach host-Start die Host-Ansicht statt des Startmenüs', async () => {
    const wrapper = mount(App, { global: { stubs } })

    await wrapper.find('.btn-host').trigger('click')

    expect(wrapper.find('.host-screen').exists()).toBe(true)
    expect(wrapper.findComponent(StartMenu).exists()).toBe(false)
  })

  it('zeigt nach Spieler-Start die Player-Ansicht mit Namen', async () => {
    const wrapper = mount(App, { global: { stubs } })

    await wrapper.find('input').setValue('Patrick')
    await wrapper.find('.btn-primary').trigger('click')

    expect(wrapper.find('.player-screen').exists()).toBe(true)
    expect(wrapper.find('.player-screen').text()).toBe('Patrick')
    expect(wrapper.findComponent(StartMenu).exists()).toBe(false)
  })

  it('öffnet Einstellungen über dem Startmenü (Startmenü bleibt sichtbar)', async () => {
    const wrapper = mount(App, { global: { stubs } })

    await wrapper.find('.settings-link').trigger('click')

    expect(wrapper.find('.settings-overlay').exists()).toBe(true)
    expect(wrapper.find('.settings-screen').exists()).toBe(true)
    expect(wrapper.findComponent(StartMenu).exists()).toBe(true)
  })

  it('schließt Einstellungen nach save', async () => {
    const wrapper = mount(App, { global: { stubs } })

    await wrapper.find('.settings-link').trigger('click')
    await wrapper.find('.fake-save').trigger('click')

    expect(wrapper.find('.settings-overlay').exists()).toBe(false)
  })

  it('wendet gespeichertes Theme beim Mount an', async () => {
    localStorage.setItem(
      'drv_game_settings',
      JSON.stringify({ theme: 'light', brightness: 80, scanlinesEnabled: false })
    )

    mount(App, { global: { stubs } })
    await flushPromises()

    expect(document.documentElement.classList.contains('theme-light')).toBe(true)
    expect(document.documentElement.style.filter).toBe('brightness(80%)')
  })

  it('Leaderboard aus dem Hauptmenü öffnen und wieder zurück', async () => {
    const lbStub = {
      name: 'LeaderboardScreen',
      template: '<div class="leaderboard-screen"><button class="fake-back" @click="$emit(\'back\')">zurück</button></div>',
    }
    const wrapper = mount(App, { global: { stubs: { ...stubs, LeaderboardScreen: lbStub } } })

    await wrapper.find('.btn-leaderboard').trigger('click')
    expect(wrapper.find('.leaderboard-screen').exists()).toBe(true)
    expect(wrapper.findComponent(StartMenu).exists()).toBe(false)

    await wrapper.find('.fake-back').trigger('click')
    expect(wrapper.find('.leaderboard-screen').exists()).toBe(false)
    expect(wrapper.findComponent(StartMenu).exists()).toBe(true)
  })

  describe('Beamer neu laden (fix/verbindung)', () => {
    afterEach(() => window.history.replaceState(null, '', '/'))

    it('mit ?host=1&game_id=… in der Adresse geht es direkt zurück an den Beamer', async () => {
      window.history.replaceState(null, '', '/?host=1&game_id=abcd')
      const wrapper = mount(App, { global: { stubs } })
      await flushPromises()
      expect(wrapper.find('.host-screen').exists()).toBe(true)
      expect(wrapper.findComponent(StartMenu).exists()).toBe(false)
    })

    it('ohne host=1 bleibt es beim Startmenü (z. B. Spieler-Link)', async () => {
      window.history.replaceState(null, '', '/?game_id=abcd')
      const wrapper = mount(App, { global: { stubs } })
      await flushPromises()
      expect(wrapper.findComponent(StartMenu).exists()).toBe(true)
    })

    it('„Verlassen“ nimmt die Sitzung aus der Adresse', async () => {
      window.history.replaceState(null, '', '/?host=1&game_id=abcd')
      const hostStub = { name: 'HostScreen', template: '<div class="host-screen"><button class="fake-exit" @click="$emit(\'exit\')">x</button></div>' }
      const wrapper = mount(App, { global: { stubs: { ...stubs, HostScreen: hostStub } } })
      await flushPromises()
      await wrapper.find('.fake-exit').trigger('click')
      expect(window.location.search).toBe('')
    })
  })
})
