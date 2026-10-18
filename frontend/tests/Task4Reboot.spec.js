/**
 * Task4Reboot — Finale, view.type "reboot".
 *
 * Jede Rolle sieht genau eine Ziffer des Neustart-Codes; nur der Leitstand
 * (terminal: true) hat das Eingabeterminal. Der Code wird als `solved`
 * weitergereicht — die Komponente prüft ihn nicht selbst.
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Task4Reboot from '../src/components/tasks/task4/Task4Reboot.vue'

const rebootView = (over = {}) => ({ type: 'reboot', digit: 7, terminal: false, ...over })

const raeder = (w) => w.findAll('[role="spinbutton"]')

async function codeEinstellen(w, [a, b, c]) {
  const [r1, r2, r3] = raeder(w)
  for (let i = 0; i < a; i++) await r1.trigger('keydown', { key: 'ArrowUp' })
  for (let i = 0; i < b; i++) await r2.trigger('keydown', { key: 'ArrowUp' })
  for (let i = 0; i < c; i++) await r3.trigger('keydown', { key: 'ArrowUp' })
}

afterEach(() => {
  vi.useRealTimers()
})

describe('Task4Reboot.vue (reboot)', () => {
  it('zeigt die eigene Ziffer groß und den Hinweis für alle Rollen', () => {
    const w = mount(Task4Reboot, { props: { view: rebootView({ digit: 4 }) } })

    expect(w.find('.title').text()).toBe('Neustart')
    expect(w.find('.digit').text()).toBe('4')
    expect(w.text()).toContain('Deine Ziffer – sag sie dem Leitstand')
  })

  it('zeigt ohne terminal kein Eingabeterminal', () => {
    const w = mount(Task4Reboot, { props: { view: rebootView({ terminal: false }) } })

    expect(w.find('.vault').exists()).toBe(false)
    expect(w.find('.vd-panel__unlock').exists()).toBe(false)
    expect(w.text()).not.toContain('Aufgabenreihenfolge')
  })

  it('zeigt beim Leitstand (terminal) das Terminal und die Reihenfolge der Ziffern', () => {
    const w = mount(Task4Reboot, { props: { view: rebootView({ terminal: true }) } })

    expect(w.find('.vault').exists()).toBe(true)
    expect(raeder(w)).toHaveLength(3)
    expect(w.find('.vd-panel__unlock').exists()).toBe(true)
    expect(w.text()).toContain('Ziffern in Aufgabenreihenfolge: Alarm – Löschprotokoll – Datenrettung')
  })

  it('sendet den Code als solved und geht in den Zustand checking', async () => {
    const w = mount(Task4Reboot, { props: { view: rebootView({ terminal: true }) } })

    await codeEinstellen(w, [4, 7, 2])
    await w.find('.vd-panel__unlock').trigger('click')

    expect(w.emitted('solved')).toEqual([[{ player: 'MASTER', value: '472' }]])
    expect(w.find('.vault').classes()).toContain('vault--checking')
  })

  it('zeigt serverError als error und fällt nach 900 ms auf locked zurück', async () => {
    vi.useFakeTimers()
    const w = mount(Task4Reboot, { props: { view: rebootView({ terminal: true }) } })

    await w.find('.vd-panel__unlock').trigger('click')
    await w.setProps({ serverError: 'Falsche Eingabe' })

    expect(w.find('.vault').classes()).toContain('vault--error')

    vi.advanceTimersByTime(900)
    await w.vm.$nextTick()

    expect(w.find('.vault').classes()).toContain('vault--locked')
  })

  it('öffnet den Tresor bei Sieg', async () => {
    const w = mount(Task4Reboot, { props: { view: rebootView({ terminal: true }) } })

    await w.setProps({ victory: true })

    expect(w.find('.vault').classes()).toContain('vault--open')
  })
})
