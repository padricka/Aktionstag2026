/**
 * Task3Master — Leitstand, view.type rescue_log (GAME_DESIGN Aufgabe 3, leichte Fassung).
 * Backup-Jobs und Schlüsselbund (Nr., Name, gültig/gesperrt – zwei gültige), Teil 1/3 der
 * Anleitung. Keine Eingabe, keine Zugangsdaten mehr – der Leitstand liest vor und rechnet die Nr. um.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3Master from '../src/components/tasks/task3/Task3Master.vue'

const view = {
  type: 'rescue_log',
  backups: [
    { date: '03.04.', serial: 'SN-9083', status: 'OK' },
    { date: '27.03.', serial: 'SN-4471', status: 'OK' },
    { date: '07.04.', serial: 'SN-2210', status: 'FEHLER' },
    { date: '22.03.', serial: 'SN-1356', status: 'OK' },
  ],
  keys: [
    { nr: 2, name: 'KILO', status: 'gesperrt' },
    { nr: 6, name: 'DELTA', status: 'gültig' },
    { nr: 9, name: 'ECHO', status: 'gültig' },
    { nr: 13, name: 'BRAVO', status: 'gesperrt' },
  ],
  note: { id: 'rescue', title: 'Datenrettung', part: 1, of: 3, torn: ['right'], lines: [{ row: 3, style: 'rule', text: '② Auf der Platte steht eine Nr.' }] },
}

describe('Task3Master.vue (rescue_log)', () => {
  it('hat keine Zugangsdaten mehr', () => {
    const w = mount(Task3Master, { props: { view } })
    expect(w.find('.login').exists()).toBe(false)
    expect(w.text()).not.toMatch(/Zugangsdaten|0x/)
  })

  it('listet die Backup-Jobs mit Datum, Platte und Status', () => {
    const w = mount(Task3Master, { props: { view } })
    const jobs = w.findAll('.backup-row')
    expect(jobs).toHaveLength(4)
    expect(jobs[2].text()).toContain('07.04.')
    expect(jobs[2].text()).toContain('SN-2210')
    expect(jobs[2].text()).toContain('FEHLER')
    expect(jobs[2].classes()).toContain('is-bad')
  })

  it('listet den Schlüsselbund mit Nr., Name und gültig/gesperrt', () => {
    const w = mount(Task3Master, { props: { view } })
    const keys = w.findAll('.key-row')
    expect(keys).toHaveLength(4)
    expect(keys[1].text()).toContain('6')
    expect(keys[1].text()).toContain('DELTA')
    expect(keys[1].text()).toContain('gültig')
    expect(keys[1].classes()).not.toContain('is-bad')
    expect(keys[0].classes()).toContain('is-bad')
    expect(w.find('.keyring').text()).not.toMatch(/Key-ID|binär|REVOKED/)
  })

  it('zeigt Teil 1 der Anleitung, hat keine Eingabe und heißt Leitstand', () => {
    const w = mount(Task3Master, { props: { view } })
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 1 von 3: Datenrettung')
    expect(w.find('input').exists()).toBe(false)
    expect(w.find('button').exists()).toBe(false)
    expect(w.find('.role').text()).toBe('Leitstand')
  })
})
