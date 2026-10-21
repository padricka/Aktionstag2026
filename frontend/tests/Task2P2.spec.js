/**
 * Task2P2 — Rückseite, view.type rack_rear (GAME_DESIGN Aufgabe 2).
 * Brandgut hinter jedem Rack, Teil 3/3 des Löschplans, Freigabe mit dem Leitstand.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task2P2 from '../src/components/tasks/task2/Task2P2.vue'

const rearView = {
  type: 'rack_rear',
  rear: [
    { rack: 'A-01', material: 'PAPIER', label: 'Papierarchiv' },
    { rack: 'A-02', material: 'AKKU', label: 'USV-Akku (Lithium)' },
    { rack: 'B-01', material: 'SERVER', label: 'Server' },
    { rack: 'B-02', material: 'KABEL', label: 'Kabelbaum' },
  ],
  release: { armed: false, window: 3 },
  note: { id: 'fire', title: 'Löschplan', part: 3, of: 3, torn: ['top'], lines: [{ row: 2, style: 'rule', text: '③ Uhrzeiten im Log' }] },
}

describe('Task2P2.vue (rack_rear)', () => {
  it('zeigt das Brandgut hinter jedem Rack', () => {
    const w = mount(Task2P2, { props: { view: rearView } })
    const racks = w.findAll('.rear-item')
    expect(racks).toHaveLength(4)
    expect(racks[1].text()).toContain('A-02')
    expect(racks[1].text()).toContain('USV-Akku (Lithium)')
    expect(w.find('.role').text()).toBe('Rückseite')
  })

  it('zeigt Teil 3 des Löschplans', () => {
    const w = mount(Task2P2, { props: { view: rearView } })
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 3 von 3: Löschplan')
  })

  it('Freigabe gesperrt bis gelöscht, dann target release', async () => {
    const w = mount(Task2P2, { props: { view: rearView } })
    expect(w.find('button.release-btn').attributes('disabled')).toBeDefined()

    await w.setProps({ view: { ...rearView, release: { armed: true, window: 3 } } })
    await w.find('button.release-btn').trigger('click')
    expect(w.emitted('solved')[0][0]).toEqual({ target: 'release' })
    expect(w.find('.release-status').text()).toContain('Leitstand')
  })
})

describe('Task2P2.vue — leichter (feat/leichter-loeschprotokoll)', () => {
  it('spricht von Schränken statt Racks', () => {
    const w = mount(Task2P2, { props: { view: rearView } })
    expect(w.text()).not.toMatch(/Rack/)
    expect(w.find('.title').text()).toBe('Schrank-Rückseite')
  })
})
