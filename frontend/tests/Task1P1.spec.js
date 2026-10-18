/**
 * Task1P1 — Vorderseite, view.type main_switches; Erledigt über view.p_done.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task1P1 from '../src/components/tasks/task1/Task1P1.vue'

const stubs = {
  SymbolIcon: { name: 'SymbolIcon', template: '<span class="sym" />', props: ['name', 'size', 'farbe'] },
}

describe('Task1P1.vue (main_switches)', () => {
  it('zeigt Schalter aus symbole und emittiert solved mit Symbol', async () => {
    const wrapper = mount(Task1P1, {
      props: {
        symbole: ['raute', 'dreieck', 'quadrat', 'kreis'],
        view: { type: 'main_switches', switches: ['raute', 'dreieck', 'quadrat', 'kreis'], p_done: false },
      },
      global: { stubs },
    })

    expect(wrapper.findAll('.symbol')).toHaveLength(4)
    await wrapper.findAll('.symbol')[2].trigger('click')
    await wrapper.find('.btn-action').trigger('click')

    expect(wrapper.emitted('solved')[0][0]).toEqual({ player: 'P1', value: 'quadrat' })
  })

  it('nutzt view.p_done als Erledigt (nicht nur lokaler State)', async () => {
    const wrapper = mount(Task1P1, {
      props: {
        symbole: ['raute', 'dreieck', 'quadrat', 'kreis'],
        view: { type: 'main_switches', p_done: true },
      },
      global: { stubs },
    })

    expect(wrapper.find('.btn-action').text()).toMatch(/Gesendet|Erledigt/)
    expect(wrapper.find('.btn-action').attributes('disabled')).toBeDefined()
    expect(wrapper.findAll('.symbol')[0].attributes('disabled')).toBeDefined()
  })

  it('gibt nach serverError wieder frei wenn nicht p_done', async () => {
    const wrapper = mount(Task1P1, {
      props: {
        symbole: ['raute', 'dreieck', 'quadrat', 'kreis'],
        view: { type: 'main_switches', p_done: false },
        serverError: '',
      },
      global: { stubs },
    })

    await wrapper.findAll('.symbol')[0].trigger('click')
    await wrapper.find('.btn-action').trigger('click')
    expect(wrapper.find('.btn-action').attributes('disabled')).toBeDefined()

    await wrapper.setProps({ serverError: 'Falsche Eingabe' })
    expect(wrapper.find('.btn-action').attributes('disabled')).toBeUndefined()
  })

  it('Rolle heißt Vorderseite', () => {
    const wrapper = mount(Task1P1, {
      props: { view: { type: 'main_switches', p_done: false } },
      global: { stubs },
    })
    expect(wrapper.find('.role').text()).toBe('Vorderseite')
  })
})
