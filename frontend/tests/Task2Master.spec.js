/**
 * Task2Master — Leitstand, view.type fire_log (GAME_DESIGN Aufgabe 2).
 * Ein Sequenz-Schritt + ein Passwort-Fragment mit Punkten. Keine Eingabe.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task2Master from '../src/components/tasks/task2/Task2Master.vue'

const fireLog = {
  type: 'fire_log',
  clue: { step: 2, valve: 'V-32', color: 'RED' },
  fragment: { dots: 1, text: 'SYS' },
}

describe('Task2Master.vue (fire_log)', () => {
  it('zeigt genau einen Sequenz-Hinweis (clue)', () => {
    const wrapper = mount(Task2Master, { props: { view: fireLog } })

    expect(wrapper.find('.clue').exists()).toBe(true)
    expect(wrapper.text()).toContain('Schritt 2')
    expect(wrapper.text()).toContain('V-32')
    expect(wrapper.text()).toContain('RED')
    // Keine komplette Sequenz mehr
    expect(wrapper.find('.seq-item').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('password_preview')
  })

  it('zeigt Passwort-Fragment mit Punkt-Markierung', () => {
    const wrapper = mount(Task2Master, { props: { view: fireLog } })

    expect(wrapper.find('.fragment-text').text()).toBe('SYS')
    expect(wrapper.find('.fragment-dots').text()).toMatch(/●/)
  })

  it('hat keine Eingabe-Controls', () => {
    const wrapper = mount(Task2Master, { props: { view: fireLog } })
    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.find('input').exists()).toBe(false)
  })

  it('Rolle heißt Leitstand', () => {
    const wrapper = mount(Task2Master, { props: { view: fireLog } })
    expect(wrapper.find('.role').text()).toBe('Leitstand')
  })
})
