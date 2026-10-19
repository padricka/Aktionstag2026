/**
 * Task2Master — Leitstand, view.type fire_log (GAME_DESIGN Aufgabe 2).
 * Brandmelde-Log (Uhrzeit, Quelle, Rack, [TEST]), Teil 1/3 des Löschplans,
 * Vier-Augen-Freigabe mit der Rückseite.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task2Master from '../src/components/tasks/task2/Task2Master.vue'

const note = { id: 'fire', title: 'Löschplan', part: 1, of: 3, torn: ['right'], lines: [{ row: 3, style: 'rule', text: '① Löschmittel je Brandgut:' }] }
const fireLog = {
  type: 'fire_log',
  log: [
    { time: '09:41', source: 'BMZ', rack: 'A-02', test: false },
    { time: '09:44', source: 'BMZ', rack: 'B-02', test: true },
    { time: '11:38', source: 'RM', rack: 'B-01', test: false },
    { time: '11:47', source: 'RM', rack: 'A-01', test: false },
  ],
  release: { armed: false, window: 3 },
  note,
}

describe('Task2Master.vue (fire_log)', () => {
  it('zeigt jede Logzeile mit Uhrzeit, Quelle und Rack, in Reihenfolge', () => {
    const w = mount(Task2Master, { props: { view: fireLog } })
    const zeilen = w.findAll('.log-row')
    expect(zeilen).toHaveLength(4)
    expect(zeilen[2].text()).toContain('11:38')
    expect(zeilen[2].text()).toContain('RM')
    expect(zeilen[2].text()).toContain('B-01')
  })

  it('markiert Probealarme mit [TEST]', () => {
    const w = mount(Task2Master, { props: { view: fireLog } })
    const zeilen = w.findAll('.log-row')
    expect(zeilen[1].text()).toContain('[TEST]')
    expect(zeilen[1].classes()).toContain('is-test')
    expect(zeilen[0].text()).not.toContain('[TEST]')
  })

  it('zeigt Teil 1 des Löschplans', () => {
    const w = mount(Task2Master, { props: { view: fireLog } })
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 1 von 3: Löschplan')
    expect(w.text()).toContain('① Löschmittel je Brandgut:')
  })

  it('Freigabe meldet target release, sobald scharf', async () => {
    const w = mount(Task2Master, { props: { view: { ...fireLog, release: { armed: true, window: 3 } } } })
    await w.find('button.release-btn').trigger('click')
    expect(w.emitted('solved')[0][0]).toEqual({ target: 'release' })
    expect(w.find('.release-status').text()).toContain('Rückseite')
  })

  it('Rolle heißt Leitstand', () => {
    const w = mount(Task2Master, { props: { view: fireLog } })
    expect(w.find('.role').text()).toBe('Leitstand')
  })
})
