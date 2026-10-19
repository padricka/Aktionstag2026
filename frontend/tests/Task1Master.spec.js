/**
 * Task1Master — Leitstand, view.type alarm_leds (GAME_DESIGN / Escape Alarm).
 * LED-Leiste + Farbnotiz + Shutdown-Terminal (player_input shutdown_cmd).
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task1Master from '../src/components/tasks/task1/Task1Master.vue'

const stubs = {
  SymbolIcon: {
    name: 'SymbolIcon',
    template: '<span class="sym" :data-name="name" />',
    props: ['name', 'size', 'farbe'],
  },
}

const alarmView = {
  type: 'alarm_leds',
  slots: 4,
  burning_slot: 3,
  color_order: ['GELB', 'ROT', 'BLAU', 'GRÜN'],
  // Tastatur kommt vom Backend (gemischt pro Aufgabe)
  keyboard: ['herz', 'stern', 'plus', 'kreuz', 'ring', 'dreieck-runter',
    'blitz', 'sechseck', 'dreieck-runter-voll', 'pfeil', 'fuenfeck', 'dreieck-voll'],
  p_done: false,
}

describe('Task1Master.vue (alarm_leds)', () => {
  it('zeigt 4 LED-Steckplätze ohne Beschriftung; burning_slot blinkt', () => {
    const wrapper = mount(Task1Master, {
      props: { view: alarmView },
      global: { stubs },
    })

    const leds = wrapper.findAll('.led')
    expect(leds).toHaveLength(4)
    expect(leds[2].classes()).toContain('burning')
    expect(wrapper.find('.led-label').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('DEFEKT')
    expect(wrapper.text()).not.toContain('NETZWERK')
  })

  it('zeigt Wartungsnotiz mit color_order', () => {
    const wrapper = mount(Task1Master, {
      props: { view: alarmView },
      global: { stubs },
    })

    expect(wrapper.find('.color-order').text()).toMatch(/GELB/)
    expect(wrapper.find('.color-order').text()).toMatch(/ROT/)
    expect(wrapper.find('.color-order').text()).toMatch(/BLAU/)
    expect(wrapper.find('.color-order').text()).toMatch(/GRÜN/)
  })

  it('sendet shutdown_cmd als kommagetrennte Symbole über solved', async () => {
    const wrapper = mount(Task1Master, {
      props: { view: alarmView },
      global: { stubs },
    })

    const keys = wrapper.findAll('.key')
    expect(keys.length).toBeGreaterThanOrEqual(4)
    for (let i = 0; i < 4; i++) {
      await keys[i].trigger('click')
    }
    await wrapper.find('.btn-action').trigger('click')

    const solved = wrapper.emitted('solved')
    expect(solved).toHaveLength(1)
    expect(solved[0][0].code).toHaveLength(4)
    expect(solved[0][0].target).toBe('shutdown_cmd')
  })

  it('zeigt genau die Tastatur aus view.keyboard in dieser Reihenfolge', () => {
    const wrapper = mount(Task1Master, {
      props: { view: alarmView },
      global: { stubs },
    })

    const namen = wrapper.findAll('.key .sym').map((k) => k.attributes('data-name'))
    expect(namen).toEqual(alarmView.keyboard)
  })

  it('zeigt Erledigt-Zustand bei view.p_done', () => {
    const wrapper = mount(Task1Master, {
      props: { view: { ...alarmView, p_done: true } },
      global: { stubs },
    })

    expect(wrapper.find('.done-badge').exists()).toBe(true)
    expect(wrapper.find('.btn-action').exists()).toBe(false)
  })

  it('Rolle heißt Leitstand', () => {
    const wrapper = mount(Task1Master, {
      props: { view: alarmView },
      global: { stubs },
    })
    expect(wrapper.find('.role').text()).toBe('Leitstand')
  })
})
