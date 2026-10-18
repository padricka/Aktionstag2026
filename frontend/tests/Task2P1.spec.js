/**
 * Task2P1 — Vorderseite, view.type valve_panel.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task2P1 from '../src/components/tasks/task2/Task2P1.vue'

const valveView = {
  type: 'valve_panel',
  valves: ['V-31', 'V-32', 'V-33'],
  colors: ['ORANGE', 'RED', 'GREEN'],
  sequence_len: 3,
  step: 1,
  clue: { step: 1, valve: 'V-31', color: 'ORANGE' },
  last_fragment: null,
  p_done: false,
}

describe('Task2P1.vue (valve_panel)', () => {
  it('zeigt eigenen clue und Fortschritt aus view', () => {
    const wrapper = mount(Task2P1, { props: { view: valveView } })

    expect(wrapper.find('.clue').text()).toMatch(/Schritt 1/)
    expect(wrapper.find('.clue').text()).toMatch(/V-31/)
    expect(wrapper.find('.count').text()).toContain('1 / 3')
    expect(wrapper.find('.role').text()).toBe('Vorderseite')
  })

  it('emittiert valve_action über solved', async () => {
    const wrapper = mount(Task2P1, { props: { view: valveView } })

    await wrapper.find('select.valve').setValue('V-32')
    await wrapper.find('select.color').setValue('RED')
    await wrapper.find('.btn-action').trigger('click')

    expect(wrapper.emitted('solved')[0][0]).toEqual({ valve: 'V-32', color: 'RED' })
  })

  it('zeigt last_fragment nach p_done', () => {
    const wrapper = mount(Task2P1, {
      props: {
        view: {
          ...valveView,
          step: 3,
          p_done: true,
          last_fragment: { dots: 3, text: 'FIRE' },
        },
      },
    })

    expect(wrapper.find('.btn-action').exists()).toBe(false)
    expect(wrapper.find('.fragment-text').text()).toBe('FIRE')
    expect(wrapper.find('.fragment-dots').text()).toMatch(/●/)
  })
})
