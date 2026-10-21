/**
 * Task2P1 — Vorderseite, view.type valve_panel (GAME_DESIGN Aufgabe 2).
 * Löscht über das Steuerpult (ControlDesk, frontend/PANELS.md): Drehregler = Rack,
 * Schieberegler = Löschmittel. Sieht, welches Rack unter Strom steht, und Teil 2/3
 * des Löschplans.
 *
 * Drehregler   role="slider" aria-label="Rack"
 * Schieberegler role="slider" aria-label="Löschmittel"
 * Manometer    role="progressbar"
 * Auslöser     <button aria-label="Auslösen">
 * Wurzel       Klasse cd--<state>
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Task2P1 from '../src/components/tasks/task2/Task2P1.vue'

const valveView = {
  type: 'valve_panel',
  racks: ['A-01', 'A-02', 'B-01', 'B-02'],
  agents: ['WASSER', 'SCHAUM', 'CO2', 'INERTGAS', 'ABSCHOTTEN'],
  power: { 'A-01': true, 'A-02': false, 'B-01': false, 'B-02': true },
  sequence_len: 3,
  step: 1,
  p_done: false,
  note: { id: 'fire', title: 'Löschplan', part: 2, of: 3, torn: ['left'], lines: [{ row: 3, style: 'rule', text: '② Gelöscht wird in der' }] },
}

const pult = (w) => w.find('.cd')
const rack = (w) => w.find('[role="slider"][aria-label="Schrank"]')
const mittel = (w) => w.find('[role="slider"][aria-label="Löschmittel"]')
const manometer = (w) => w.find('[role="progressbar"]')
const ausloeser = (w) => w.find('button[aria-label="Auslösen"]')

function mountTask(props = {}) {
  return mount(Task2P1, { props: { view: valveView, ...props } })
}

afterEach(() => {
  vi.useRealTimers()
})

describe('Task2P1.vue (valve_panel) — Steuerpult', () => {
  it('zeigt Racks, Löschmittel und Fortschritt aus view', () => {
    const w = mountTask()
    expect(w.find('.role').text()).toBe('Vorderseite')
    expect(rack(w).attributes('aria-valuetext')).toBe('A-01')
    expect(mittel(w).attributes('aria-valuetext')).toBe('WASSER')
    expect(manometer(w).attributes('aria-valuenow')).toBe('1')
    expect(manometer(w).attributes('aria-valuemax')).toBe('3')
  })

  it('zeigt, welches Rack unter Strom steht', () => {
    const w = mountTask()
    const racks = w.findAll('.power-item')
    expect(racks).toHaveLength(4)
    expect(racks[0].text()).toContain('A-01')
    expect(racks[0].classes()).toContain('is-on')
    expect(racks[1].classes()).not.toContain('is-on')
    expect(racks[0].text()).toMatch(/Strom an/i)
    expect(racks[1].text()).toMatch(/stromlos/i)
  })

  it('zeigt Teil 2 des Löschplans', () => {
    const w = mountTask()
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 2 von 3: Löschplan')
  })

  it('emittiert Rack und Löschmittel über solved', async () => {
    const w = mountTask()
    await rack(w).trigger('keydown', { key: 'ArrowRight' })
    await mittel(w).trigger('keydown', { key: 'ArrowRight' })
    await mittel(w).trigger('keydown', { key: 'ArrowRight' })
    await ausloeser(w).trigger('click')
    expect(w.emitted('solved')[0][0]).toEqual({ valve: 'A-02', color: 'CO2' })
  })

  it('sperrt direkt nach dem Senden (checking), bis view.step steigt', async () => {
    const w = mountTask()
    expect(pult(w).classes()).toContain('cd--idle')

    await ausloeser(w).trigger('click')
    expect(pult(w).classes()).toContain('cd--checking')
    await ausloeser(w).trigger('click')
    expect(w.emitted('solved')).toHaveLength(1)

    await w.setProps({ view: { ...valveView, step: 2 } })
    expect(pult(w).classes()).toContain('cd--idle')
  })

  it('zeigt serverError als error und ist nach 1200 ms wieder idle', async () => {
    vi.useFakeTimers()
    const w = mountTask()

    await ausloeser(w).trigger('click')
    await w.setProps({ serverError: 'Falsche Eingabe' })
    expect(pult(w).classes()).toContain('cd--error')
    expect(w.find('.msg-err').text()).toBe('Falsche Eingabe')

    vi.advanceTimersByTime(1200)
    await w.vm.$nextTick()
    expect(pult(w).classes()).toContain('cd--idle')
  })

  it('nach p_done ist das Pult fertig und verweist auf die Freigabe', () => {
    const w = mountTask({ view: { ...valveView, step: 3, p_done: true } })
    expect(pult(w).classes()).toContain('cd--done')
    expect(ausloeser(w).attributes('disabled')).toBeDefined()
    expect(w.find('.result').text()).toMatch(/Freigabe/)
  })
})

describe('Task2P1.vue — leichter (feat/leichter-loeschprotokoll)', () => {
  it('spricht von Schränken statt Racks', () => {
    const w = mount(Task2P1, { props: { view: valveView } })
    expect(w.text()).not.toMatch(/Rack/)
    expect(w.text()).toContain('Strom an den Schränken')
  })
})
