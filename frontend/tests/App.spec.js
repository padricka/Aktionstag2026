/**
 * App.spec.js
 *
 * App.vue zeigt anfangs das Startmenü. Nach dem Start wird je nach Rolle
 * die Host-Ansicht (Beamer) oder die Spieler-Ansicht (Laptop) gerendert.
 * HostScreen/PlayerScreen/SettingsScreen werden gestubbt (kein Backend/Socket
 * im Test); StartMenu bleibt echt, damit der Klick-Flow getestet wird.
 */
// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '../src/App.vue'
import StartMenu from '../src/StartMenu.vue'

vi.mock('../src/composables/useGameSocket.js', () => import('./mocks/useGameSocket.js'))

const stubs = {
  HostScreen: { name: 'HostScreen', template: '<div class="host-screen"></div>' },
  PlayerScreen: { name: 'PlayerScreen', template: '<div class="player-screen"></div>' },
  SettingsScreen: { name: 'SettingsScreen', template: '<div class="settings-screen"></div>' },
}

describe('App.vue', () => {
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
})
