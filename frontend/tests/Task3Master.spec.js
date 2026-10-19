/**
 * Task3Master — Leitstand, Aufgabe 3 „Datenrettung" (view.type "ascii_binary_tables").
 *
 * Der Leitstand hat keine Eingabe. Er zeigt seine Tabellenhälfte A–M, die
 * oberen Stellenwerte 128/64/32/16 und ob P1/P2 ihren Knopf freigeschaltet haben.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3Master from '../src/components/tasks/task3/Task3Master.vue'

const masterView = {
  type: 'ascii_binary_tables',
  ascii_half: { A: 65, B: 66, C: 67, D: 68, E: 69, F: 70, G: 71, H: 72, I: 73, J: 74, K: 75, L: 76, M: 77 },
  place_values: [128, 64, 32, 16],
  p1_status: 'GESPERRT',
  p2_status: 'GESPERRT',
}

describe('Task3Master.vue (ascii_binary_tables)', () => {
  it('zeigt die Tabelle A–M vollständig und sortiert', () => {
    const w = mount(Task3Master, { props: { view: masterView } })

    const buchstaben = w.findAll('.cell-key').map((el) => el.text())
    expect(buchstaben).toHaveLength(13)
    expect(buchstaben[0]).toBe('A')
    expect(buchstaben[12]).toBe('M')
    expect(w.findAll('.cell-val').map((el) => el.text())[0]).toBe('65')
    expect(w.findAll('.cell-val').map((el) => el.text()).at(-1)).toBe('77')
  })

  it('zeigt die oberen Stellenwerte 128/64/32/16 gross', () => {
    const w = mount(Task3Master, { props: { view: masterView } })

    expect(w.findAll('.place-value').map((el) => el.text())).toEqual(['128', '64', '32', '16'])
    expect(w.find('.role').text()).toBe('Leitstand')
  })

  it('zeigt den Status beider Seiten', () => {
    const w = mount(Task3Master, { props: { view: masterView } })

    const zeilen = w.findAll('.status-row').map((el) => el.text())
    expect(zeilen[0]).toContain('Vorderseite')
    expect(zeilen[0]).toContain('GESPERRT')
    expect(zeilen[1]).toContain('Rückseite')
    expect(w.find('.status-hint').exists()).toBe(false)
  })

  it('meldet, wenn beide Knöpfe frei sind', () => {
    const w = mount(Task3Master, {
      props: { view: { ...masterView, p1_status: 'FREIGESCHALTET', p2_status: 'FREIGESCHALTET' } },
    })

    expect(w.findAll('.status-value').map((el) => el.text())).toEqual([
      'FREIGESCHALTET',
      'FREIGESCHALTET',
    ])
    expect(w.find('.status-hint').text()).toMatch(/3 Sekunden/)
  })

  it('erklärt, dass die Tabellenhälfte sein Beitrag fürs Team ist', () => {
    const w = mount(Task3Master, { props: { view: masterView } })

    const hint = w.find('.hint').text()
    expect(hint).toContain('Vorderseite')
    expect(hint).toContain('Rückseite')
    expect(hint).toContain('N–Z')
  })

  it('ordnet die oberen Stellenwerte den ersten vier Spalten der Rückseite zu', () => {
    const w = mount(Task3Master, { props: { view: masterView } })

    const spalten = w.findAll('.bits-head .bit-cell').map((el) => el.text())
    expect(spalten).toEqual(['128', '64', '32', '16', '·', '·', '·', '·'])
    expect(w.find('.bits-note').text()).toMatch(/ersten vier Spalten/)
    expect(w.find('.bits-note').text()).toMatch(/Rückseite/)
  })
})
