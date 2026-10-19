/**
 * Task3P1 — Vorderseite, view.type rescue_terminal (GAME_DESIGN Aufgabe 3).
 * Sieht die ASCII-Tabelle A–Z und Teil 2/3 der Anleitung, tippt das gerettete Wort.
 * Keine Prüfung im Browser – jede Eingabe geht als `solved` an PlayerScreen.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3P1 from '../src/components/tasks/task3/Task3P1.vue'

const tabelle = Object.fromEntries(Array.from({ length: 26 }, (_, i) => [String.fromCharCode(65 + i), 65 + i]))
const view = {
  type: 'rescue_terminal',
  ascii_table: tabelle,
  word_len: 5,
  note: { id: 'rescue', title: 'Datenrettung', part: 2, of: 3, torn: ['left'], lines: [{ row: 3, style: 'rule', text: '① Erst prüfen' }] },
}

const eingabe = (w) => w.find('input.input-big')
const knopf = (w) => w.find('button.btn-action')

describe('Task3P1.vue (rescue_terminal)', () => {
  it('zeigt die ganze ASCII-Tabelle A–Z, sortiert nach Zahl', () => {
    const w = mount(Task3P1, { props: { view } })
    const zellen = w.findAll('.cell')
    expect(zellen).toHaveLength(26)
    expect(zellen[0].text()).toContain('A')
    expect(zellen[0].text()).toContain('65')
    expect(zellen[25].text()).toContain('Z')
    expect(zellen[25].text()).toContain('90')
  })

  it('zeigt Teil 2 der Anleitung', () => {
    const w = mount(Task3P1, { props: { view } })
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 2 von 3: Datenrettung')
  })

  it('nennt die Wortlänge, nicht das Wort', () => {
    const w = mount(Task3P1, { props: { view } })
    expect(eingabe(w).attributes('maxlength')).toBe('5')
    expect(w.text()).toContain('5 Buchstaben')
  })

  it('schickt das Wort ans Backend und sperrt bis zur Antwort', async () => {
    const w = mount(Task3P1, { props: { view } })
    await eingabe(w).setValue('rente')
    await knopf(w).trigger('click')
    expect(w.emitted('solved')[0][0]).toEqual({ answer: 'rente' })
    expect(knopf(w).attributes('disabled')).toBeDefined()
    expect(knopf(w).text()).toContain('Prüfe')
  })

  it('leere Eingabe schickt nichts', async () => {
    const w = mount(Task3P1, { props: { view } })
    await eingabe(w).setValue('   ')
    await knopf(w).trigger('click')
    expect(w.emitted('solved')).toBeUndefined()
  })

  it('nach falscher Antwort: Fehler zeigen, Eingabe leeren und wieder frei', async () => {
    const w = mount(Task3P1, { props: { view } })
    await eingabe(w).setValue('RENTO')
    await knopf(w).trigger('click')
    await w.setProps({ serverError: 'Falsche Eingabe' })

    expect(w.find('.msg-err').text()).toBe('Falsche Eingabe')
    expect(eingabe(w).element.value).toBe('')
    await eingabe(w).setValue('RENTE')
    expect(knopf(w).attributes('disabled')).toBeUndefined()
  })
})
