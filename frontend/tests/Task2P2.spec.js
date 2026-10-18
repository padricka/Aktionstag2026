/**
 * Task2P2 — Rückseite, view.type password_input.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task2P2 from '../src/components/tasks/task2/Task2P2.vue'

const pwView = {
  type: 'password_input',
  clue: { step: 3, valve: 'V-33', color: 'GREEN' },
  fragment: { dots: 2, text: 'BOX' },
  last_fragment: null,
  p_done: false,
}

describe('Task2P2.vue (password_input)', () => {
  it('zeigt clue und eigenes Fragment', () => {
    const wrapper = mount(Task2P2, { props: { view: pwView } })

    expect(wrapper.find('.clue').text()).toMatch(/Schritt 3/)
    expect(wrapper.find('.fragment-text').text()).toBe('BOX')
    expect(wrapper.find('.role').text()).toBe('Rückseite')
  })

  it('zeigt last_fragment wenn vorhanden; emittiert Passwort', async () => {
    const wrapper = mount(Task2P2, {
      props: {
        view: {
          ...pwView,
          last_fragment: { dots: 3, text: 'FIRE' },
        },
      },
    })

    expect(wrapper.text()).toContain('FIRE')
    await wrapper.find('.input-pw').setValue('SYSBOXFIRE')
    await wrapper.find('.btn-action').trigger('click')
    expect(wrapper.emitted('solved')[0][0]).toEqual({ password: 'SYSBOXFIRE' })
  })

  it('Erledigt über view.p_done', () => {
    const wrapper = mount(Task2P2, {
      props: { view: { ...pwView, p_done: true } },
    })
    expect(wrapper.find('.btn-action').text()).toMatch(/Akzeptiert|Erledigt/)
    expect(wrapper.find('.input-pw').attributes('disabled')).toBeDefined()
  })
})
