/**
 * Task3P1 — Vorderseite, view.type rescue_terminal (GAME_DESIGN Aufgabe 3, leichte Fassung).
 * Code-Tabelle (8-stelliger Code → Buchstabe, frei erfunden), Teil 2/3 der Anleitung.
 * Kein Login mehr: das Terminal nimmt gleich das 6-Buchstaben-Wort (rescue_word).
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3P1 from '../src/components/tasks/task3/Task3P1.vue'

const codes = Object.fromEntries(
  Array.from({ length: 26 }, (_, i) => [String.fromCharCode(65 + i), (255 - i * 7).toString(2).padStart(8, '0')]),
)
const view = {
  type: 'rescue_terminal',
  code_table: codes,
  word_len: 6,
  note: { id: 'rescue', title: 'Datenrettung', part: 2, of: 3, torn: ['left'], lines: [{ row: 3, style: 'rule', text: '③ Im Schlüsselbund' }] },
}

const eingabe = (w) => w.find('input.input-big')
const knopf = (w) => w.find('button.btn-action')

describe('Task3P1.vue (rescue_terminal)', () => {
  it('zeigt die Code-Tabelle A–Z: Code und Buchstabe', () => {
    const w = mount(Task3P1, { props: { view } })
    const zellen = w.findAll('.cell')
    expect(zellen).toHaveLength(26)
    expect(zellen[0].text()).toContain('A')
    expect(zellen[0].text().replace(/\s/g, '')).toContain(codes.A)
    expect(zellen[25].text()).toContain('Z')
    expect(w.text()).not.toMatch(/ASCII/)
  })

  it('zeigt Teil 2 der Anleitung', () => {
    const w = mount(Task3P1, { props: { view } })
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 2 von 3: Datenrettung')
  })

  it('kein Login: gleich das Feld für das 6-Buchstaben-Wort', async () => {
    const w = mount(Task3P1, { props: { view } })
    expect(w.text()).not.toMatch(/BENUTZER|Anmelden/)
    expect(w.find('.terminal').text()).toContain('6 Buchstaben')
    expect(eingabe(w).attributes('maxlength')).toBe('6')
    await eingabe(w).setValue('renten')
    await knopf(w).trigger('click')
    expect(w.emitted('solved')[0][0]).toEqual({ target: 'rescue_word', answer: 'renten' })
    expect(knopf(w).attributes('disabled')).toBeDefined()
  })

  it('leere Eingabe schickt nichts', async () => {
    const w = mount(Task3P1, { props: { view } })
    await eingabe(w).setValue('   ')
    await knopf(w).trigger('click')
    expect(w.emitted('solved')).toBeUndefined()
  })

  it('nach falscher Antwort: Fehler zeigen, Eingabe leeren und wieder frei', async () => {
    const w = mount(Task3P1, { props: { view } })
    await eingabe(w).setValue('ANTRAG')
    await knopf(w).trigger('click')
    await w.setProps({ serverError: 'Falsche Eingabe' })

    expect(w.find('.msg-err').text()).toBe('Falsche Eingabe')
    expect(eingabe(w).element.value).toBe('')
    await eingabe(w).setValue('RENTEN')
    expect(knopf(w).attributes('disabled')).toBeUndefined()
  })
})
