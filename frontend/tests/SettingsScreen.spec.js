/**
 * SettingsScreen — Themes, Helligkeit, Scanlines, localStorage.
 * Audio-Schalter speichern nur Werte (Stub).
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SettingsScreen from '../src/components/SettingsScreen.vue'

describe('SettingsScreen.vue', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
    document.documentElement.style.filter = ''
  })

  afterEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
    document.documentElement.style.filter = ''
  })

  it('setzt Dark als Default und speichert Theme Girl', async () => {
    const wrapper = mount(SettingsScreen)
    await flushPromises()

    expect(document.documentElement.classList.contains('theme-dark')).toBe(true)

    const buttons = wrapper.findAll('.theme-actions .btn')
    const girlBtn = buttons.find((b) => b.text() === 'Girl')
    await girlBtn.trigger('click')

    expect(document.documentElement.classList.contains('theme-girl')).toBe(true)

    await wrapper.find('.btn-primary').trigger('click')

    const saved = JSON.parse(localStorage.getItem('drv_game_settings'))
    expect(saved.theme).toBe('girl')
    expect(wrapper.emitted('save')).toHaveLength(1)
  })

  it('wendet Helligkeit sofort an', async () => {
    const wrapper = mount(SettingsScreen)
    await flushPromises()

    const slider = wrapper.find('input.slider')
    await slider.setValue(50)
    await slider.trigger('input')

    expect(document.documentElement.style.filter).toBe('brightness(50%)')
  })

  it('schaltet Scanlines an und speichert das', async () => {
    const wrapper = mount(SettingsScreen)
    await flushPromises()

    const scanBtn = wrapper.findAll('button.btn').find((b) => b.text() === 'Aktivieren')
    await scanBtn.trigger('click')

    expect(document.documentElement.classList.contains('scanlines')).toBe(true)

    await wrapper.find('.btn-primary').trigger('click')
    const saved = JSON.parse(localStorage.getItem('drv_game_settings'))
    expect(saved.scanlinesEnabled).toBe(true)
  })

  it('deaktiviert Scanlines beim Wechsel zu Girl (Lesbarkeit)', async () => {
    localStorage.setItem(
      'drv_game_settings',
      JSON.stringify({ theme: 'dark', scanlinesEnabled: true, brightness: 100 })
    )

    const wrapper = mount(SettingsScreen)
    await flushPromises()

    // noch Dark + Scanlines aus Save
    expect(document.documentElement.classList.contains('scanlines')).toBe(true)

    const girlBtn = wrapper.findAll('.theme-actions .btn').find((b) => b.text() === 'Girl')
    await girlBtn.trigger('click')

    expect(document.documentElement.classList.contains('theme-girl')).toBe(true)
    expect(document.documentElement.classList.contains('scanlines')).toBe(false)
  })

  it('bereinigt alte Saves: Girl + Scanlines → Scanlines aus', async () => {
    localStorage.setItem(
      'drv_game_settings',
      JSON.stringify({ theme: 'girl', scanlinesEnabled: true, brightness: 100 })
    )

    mount(SettingsScreen)
    await flushPromises()

    expect(document.documentElement.classList.contains('theme-girl')).toBe(true)
    expect(document.documentElement.classList.contains('scanlines')).toBe(false)
    const saved = JSON.parse(localStorage.getItem('drv_game_settings'))
    expect(saved.scanlinesEnabled).toBe(false)
  })

  it('Zurücksetzen stellt Defaults wieder her', async () => {
    localStorage.setItem(
      'drv_game_settings',
      JSON.stringify({ theme: 'girl', brightness: 40, scanlinesEnabled: false })
    )

    const wrapper = mount(SettingsScreen)
    await flushPromises()

    await wrapper.findAll('button.btn').find((b) => b.text() === 'Zurücksetzen').trigger('click')

    const saved = JSON.parse(localStorage.getItem('drv_game_settings'))
    expect(saved.theme).toBe('dark')
    expect(saved.brightness).toBe(100)
    expect(document.documentElement.classList.contains('theme-dark')).toBe(true)
  })

  it('zeigt Audio-Stub-Hinweis', async () => {
    const wrapper = mount(SettingsScreen)
    await flushPromises()
    expect(wrapper.text()).toContain('Noch nicht verdrahtet')
  })
})
