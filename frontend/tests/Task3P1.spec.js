/**
 * Task3P1 — Vorderseite, view.type rescue_terminal (GAME_DESIGN Aufgabe 3).
 * ASCII-Tabelle A–Z, Teil 2/3 der Anleitung. Terminal: erst Login (terminal_login),
 * dann das gerettete Wort (rescue_word). Keine Prüfung im Browser.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3P1 from '../src/components/tasks/task3/Task3P1.vue'

const tabelle = Object.fromEntries(Array.from({ length: 26 }, (_, i) => [String.fromCharCode(65 + i), 65 + i]))
const view = {
  type: 'rescue_terminal',
  ascii_table: tabelle,
  login_len: 4,
  logged_in: false,
  word_len: 5,
  note: { id: 'rescue', title: 'Datenrettung', part: 2, of: 3, torn: ['left'], lines: [{ row: 3, style: 'rule', text: '② Login-Name steht in HEX:' }] },
}

const eingabe = (w) => w.find('input.input-big')
const knopf = (w) => w.find('button.btn-action')

describe('Task3P1.vue (rescue_terminal)', () => {
  it('zeigt die ganze ASCII-Tabelle A–Z, sortiert nach Zahl', () => {
    const w = mount(Task3P1, { props: { view } })
    const zellen = w.findAll('.cell')
    expect(zellen).toHaveLength(26)
    expect(zellen[0].text()).toContain('65')
    expect(zellen[0].text()).toContain('A')
    expect(zellen[25].text()).toContain('Z')
  })

  it('zeigt Teil 2 der Anleitung', () => {
    const w = mount(Task3P1, { props: { view } })
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 2 von 3: Datenrettung')
  })

  it('ist erst gesperrt: Login mit Benutzername (Länge aus view)', async () => {
    const w = mount(Task3P1, { props: { view } })
    expect(w.find('.terminal').text()).toMatch(/BENUTZER/)
    expect(eingabe(w).attributes('maxlength')).toBe('4')
    await eingabe(w).setValue('reha')
    await knopf(w).trigger('click')
    expect(w.emitted('solved')[0][0]).toEqual({ target: 'terminal_login', answer: 'reha' })
    expect(knopf(w).attributes('disabled')).toBeDefined()
  })

  it('nach dem Login: Feld für das gerettete Wort', async () => {
    const w = mount(Task3P1, { props: { view } })
    await w.setProps({ view: { ...view, logged_in: true } })
    expect(w.find('.terminal').text()).toContain('5 Buchstaben')
    expect(eingabe(w).attributes('maxlength')).toBe('5')
    expect(eingabe(w).attributes('disabled')).toBeUndefined()
    await eingabe(w).setValue('rente')
    await knopf(w).trigger('click')
    expect(w.emitted('solved')[0][0]).toEqual({ target: 'rescue_word', answer: 'rente' })
  })

  it('leere Eingabe schickt nichts', async () => {
    const w = mount(Task3P1, { props: { view } })
    await eingabe(w).setValue('   ')
    await knopf(w).trigger('click')
    expect(w.emitted('solved')).toBeUndefined()
  })

  it('nach falscher Antwort: Fehler zeigen, Eingabe leeren und wieder frei', async () => {
    const w = mount(Task3P1, { props: { view } })
    await eingabe(w).setValue('ADMIN')
    await knopf(w).trigger('click')
    await w.setProps({ serverError: 'Falsche Eingabe' })

    expect(w.find('.msg-err').text()).toBe('Falsche Eingabe')
    expect(eingabe(w).element.value).toBe('')
    await eingabe(w).setValue('REHA')
    expect(knopf(w).attributes('disabled')).toBeUndefined()
  })
})

describe('Task3P1.vue — leichter (feat/leichter-datenrettung)', () => {
  it('nach dem Login: Alphabet-Leiste zum Zurückschieben', async () => {
    const w = mount(Task3P1, { props: { view: { ...view, logged_in: true } } })
    const buchstaben = w.findAll('.alphabet .abc')
    expect(buchstaben).toHaveLength(26)
    expect(buchstaben[0].text()).toBe('A')
    expect(buchstaben[25].text()).toBe('Z')
  })

  it('zeigt k, sobald der Leitstand es eingetragen hat', async () => {
    const w = mount(Task3P1, { props: { view: { ...view, logged_in: true } } })
    expect(w.find('.key-badge').exists()).toBe(false)
    await w.setProps({ view: { ...view, logged_in: true, key: 3 } })
    expect(w.find('.key-badge').text()).toContain('k = 3')
    expect(w.find('.alphabet').text()).toMatch(/3 Schritte/)
  })

  it('spricht nicht mehr von Paketen', () => {
    const w = mount(Task3P1, { props: { view } })
    expect(w.text()).not.toMatch(/Paket/)
  })
})
