/**
 * Task3Master — Leitstand, view.type rescue_key (GAME_DESIGN Aufgabe 3).
 * Sieht den Schlüssel k als 4 Bit und Teil 1/3 der Anleitung (Binär → Dezimal).
 * Keine Eingabe.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3Master from '../src/components/tasks/task3/Task3Master.vue'

const view = {
  type: 'rescue_key',
  key: '0101',
  note: { id: 'rescue', title: 'Datenrettung', part: 1, of: 3, torn: ['right'], lines: [{ row: 3, style: 'rule', text: '② Binär → Dezimal:' }] },
}

describe('Task3Master.vue (rescue_key)', () => {
  it('zeigt den Schlüssel Bit für Bit mit den Stellenwerten 8 4 2 1', () => {
    const w = mount(Task3Master, { props: { view } })
    expect(w.findAll('.key-bit').map((b) => b.text())).toEqual(['0', '1', '0', '1'])
    expect(w.findAll('.key-place').map((p) => p.text())).toEqual(['8', '4', '2', '1'])
  })

  it('verrät den Dezimalwert des Schlüssels nicht', () => {
    const w = mount(Task3Master, { props: { view } })
    expect(w.find('.key').text()).not.toContain('5')
  })

  it('zeigt Teil 1 der Datenrettungs-Anleitung', () => {
    const w = mount(Task3Master, { props: { view } })
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 1 von 3: Datenrettung')
  })

  it('hat keine Eingabe und heißt Leitstand', () => {
    const w = mount(Task3Master, { props: { view } })
    expect(w.find('input').exists()).toBe(false)
    expect(w.find('button').exists()).toBe(false)
    expect(w.find('.role').text()).toBe('Leitstand')
  })
})
