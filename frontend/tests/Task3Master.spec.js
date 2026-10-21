/**
 * Task3Master — Leitstand, view.type rescue_log (GAME_DESIGN Aufgabe 3, leichte Fassung).
 * Log mit Login-Name (Hex), Backup-Jobs und Schlüsselbund (Nr., k, gültig/gesperrt),
 * Teil 1/3 der Anleitung. Einzige Eingabe: k eintragen (set_key) – danach sehen es alle.
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
    { nr: 2, k: 5, status: 'gesperrt' },
    { nr: 6, k: 7, status: 'gesperrt' },
    { nr: 6, k: 3, status: 'gültig' },
    { nr: 8, k: 8, status: 'gültig' },
  ],
  key: null,
  note: { id: 'rescue', title: 'Datenrettung', part: 1, of: 3, torn: ['right'], lines: [{ row: 3, style: 'rule', text: '⑤ Schlüssel k' }] },
}

const feld = (w) => w.find('input.key-input')
const knopf = (w) => w.find('button.key-btn')

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

  it('listet den Schlüsselbund mit Nr., k als normale Zahl und gültig/gesperrt', () => {
    const w = mount(Task3Master, { props: { view } })
    const keys = w.findAll('.key-row')
    expect(keys).toHaveLength(4)
    expect(keys[1].text()).toContain('6')
    expect(keys[1].text()).toContain('7')
    expect(keys[1].text()).toContain('gesperrt')
    expect(keys[1].classes()).toContain('is-bad')
    expect(keys[2].classes()).not.toContain('is-bad')
    expect(w.find('.keyring').text()).not.toMatch(/Key-ID|binär|REVOKED/)
  })

  it('k eintragen meldet set_key und wartet auf den Server', async () => {
    const w = mount(Task3Master, { props: { view } })
    await feld(w).setValue(' 3 ')
    await knopf(w).trigger('click')
    expect(w.emitted('solved')[0][0]).toEqual({ target: 'set_key', value: '3' })
    expect(knopf(w).attributes('disabled')).toBeDefined()
  })

  it('falsches k: Fehler zeigen und wieder frei', async () => {
    const w = mount(Task3Master, { props: { view } })
    await feld(w).setValue('7')
    await knopf(w).trigger('click')
    await w.setProps({ serverError: 'Falsche Eingabe' })
    expect(w.find('.msg-err').text()).toBe('Falsche Eingabe')
    await feld(w).setValue('3')
    expect(knopf(w).attributes('disabled')).toBeUndefined()
  })

  it('eingetragenes k steht groß da, das Feld ist weg', () => {
    const w = mount(Task3Master, { props: { view: { ...view, key: 3 } } })
    expect(w.find('.key-set').text()).toContain('k = 3')
    expect(feld(w).exists()).toBe(false)
  })

  it('zeigt Teil 1 der Anleitung und heißt Leitstand', () => {
    const w = mount(Task3Master, { props: { view } })
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 1 von 3: Datenrettung')
    expect(w.find('.role').text()).toBe('Leitstand')
  })
})
