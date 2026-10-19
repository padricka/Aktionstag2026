/**
 * Task3Master — Leitstand, view.type rescue_log (GAME_DESIGN Aufgabe 3).
 * Log mit Login-Name (Hex), Backup-Jobs und Schlüsselbund, Teil 1/3 der Anleitung.
 * Keine Eingabe – der Leitstand liest vor, rechnet um und entschlüsselt.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3Master from '../src/components/tasks/task3/Task3Master.vue'

const view = {
  type: 'rescue_log',
  login_hex: ['0x52', '0x45', '0x48', '0x41'],
  backups: [
    { date: '03.04.', serial: 'SN-9083', status: 'OK' },
    { date: '27.03.', serial: 'SN-4471', status: 'OK' },
    { date: '07.04.', serial: 'SN-2210', status: 'FEHLER' },
    { date: '22.03.', serial: 'SN-1356', status: 'OK' },
  ],
  keys: [
    { id: 2, key: '0101', status: 'abgelaufen' },
    { id: 6, key: '0111', status: 'REVOKED' },
    { id: 6, key: '0011', status: 'aktiv' },
    { id: 11, key: '1000', status: 'aktiv' },
  ],
  note: { id: 'rescue', title: 'Datenrettung', part: 1, of: 3, torn: ['right'], lines: [{ row: 3, style: 'rule', text: '④ Binär → Dezimal:' }] },
}

describe('Task3Master.vue (rescue_log)', () => {
  it('zeigt den Login-Namen nur als Hex-Codes', () => {
    const w = mount(Task3Master, { props: { view } })
    expect(w.findAll('.login-hex').map((h) => h.text())).toEqual(['0x52', '0x45', '0x48', '0x41'])
    expect(w.text()).not.toContain('REHA')
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

  it('listet den Schlüsselbund mit Key-ID, Schlüssel (binär) und Status', () => {
    const w = mount(Task3Master, { props: { view } })
    const keys = w.findAll('.key-row')
    expect(keys).toHaveLength(4)
    expect(keys[1].text()).toContain('6')
    expect(keys[1].text()).toContain('0111')
    expect(keys[1].text()).toContain('REVOKED')
    expect(w.find('.keyring').text()).not.toMatch(/k\s*=\s*\d/)
  })

  it('zeigt Teil 1 der Anleitung, hat keine Eingabe und heißt Leitstand', () => {
    const w = mount(Task3Master, { props: { view } })
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 1 von 3: Datenrettung')
    expect(w.find('input').exists()).toBe(false)
    expect(w.find('button').exists()).toBe(false)
    expect(w.find('.role').text()).toBe('Leitstand')
  })
})
