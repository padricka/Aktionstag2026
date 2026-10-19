/**
 * Task2P1 — Vorderseite, view.type valve_panel.
 * Bedient über das Steuerpult (ControlDesk), siehe frontend/PANELS.md.
 *
 * Drehregler   role="slider" aria-label="Ventil"
 * Schieberegler role="slider" aria-label="Farbe"
 * Manometer    role="progressbar"
 * Auslöser     <button aria-label="Auslösen">
 * Wurzel       Klasse cd--<state>
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Task2P1 from '../src/components/tasks/task2/Task2P1.vue'

const valveView = {
  type: 'valve_panel',
  valves: ['V-31', 'V-32', 'V-33'],
  colors: ['ORANGE', 'RED', 'GREEN'],
  sequence_len: 3,
  step: 1,
  clue: { step: 1, valve: 'V-31', color: 'ORANGE' },
  last_fragment: null,
  p_done: false,
}

const pult = (w) => w.find('.cd')
const ventil = (w) => w.find('[role="slider"][aria-label="Ventil"]')
const farbe = (w) => w.find('[role="slider"][aria-label="Farbe"]')
const manometer = (w) => w.find('[role="progressbar"]')
const ausloeser = (w) => w.find('button[aria-label="Auslösen"]')

function mountTask(props = {}) {
  return mount(Task2P1, { props: { view: valveView, ...props } })
}

afterEach(() => {
  vi.useRealTimers()
})

describe('Task2P1.vue (valve_panel) — Steuerpult', () => {
  it('zeigt eigenen clue und Fortschritt aus view', () => {
    const wrapper = mountTask()

    expect(wrapper.find('.clue').text()).toMatch(/Schritt 1/)
    expect(wrapper.find('.clue').text()).toMatch(/V-31/)
    expect(wrapper.find('.role').text()).toBe('Vorderseite')
    expect(manometer(wrapper).attributes('aria-valuenow')).toBe('1')
    expect(manometer(wrapper).attributes('aria-valuemax')).toBe('3')
  })

  it('emittiert valve_action über solved', async () => {
    const wrapper = mountTask()

    await ventil(wrapper).trigger('keydown', { key: 'ArrowRight' })
    await farbe(wrapper).trigger('keydown', { key: 'ArrowRight' })
    await ausloeser(wrapper).trigger('click')

    expect(wrapper.emitted('solved')[0][0]).toEqual({ valve: 'V-32', color: 'RED' })
  })

  it('sperrt direkt nach dem Senden (checking), bis view.step steigt', async () => {
    const wrapper = mountTask()
    expect(pult(wrapper).classes()).toContain('cd--idle')

    await ausloeser(wrapper).trigger('click')
    expect(pult(wrapper).classes()).toContain('cd--checking')
    expect(ausloeser(wrapper).attributes('disabled')).toBeDefined()

    await ausloeser(wrapper).trigger('click')
    expect(wrapper.emitted('solved')).toHaveLength(1)

    await wrapper.setProps({ view: { ...valveView, step: 2 } })
    expect(pult(wrapper).classes()).toContain('cd--idle')
    expect(ausloeser(wrapper).attributes('disabled')).toBeUndefined()
  })

  it('zeigt serverError als error und ist nach 1200 ms wieder idle', async () => {
    vi.useFakeTimers()
    const wrapper = mountTask()

    await ausloeser(wrapper).trigger('click')
    await wrapper.setProps({ serverError: 'Falscher Schritt' })

    expect(pult(wrapper).classes()).toContain('cd--error')
    expect(wrapper.find('.msg-err').text()).toBe('Falscher Schritt')
    expect(ausloeser(wrapper).attributes('disabled')).toBeUndefined()

    vi.advanceTimersByTime(1199)
    await wrapper.vm.$nextTick()
    expect(pult(wrapper).classes()).toContain('cd--error')

    vi.advanceTimersByTime(1)
    await wrapper.vm.$nextTick()
    expect(pult(wrapper).classes()).toContain('cd--idle')
  })

  it('gibt nach error wieder frei und kann erneut senden', async () => {
    vi.useFakeTimers()
    const wrapper = mountTask()

    await ausloeser(wrapper).trigger('click')
    await wrapper.setProps({ serverError: 'Falscher Schritt' })
    vi.advanceTimersByTime(1200)
    await wrapper.vm.$nextTick()

    await ventil(wrapper).trigger('keydown', { key: 'ArrowRight' })
    await ausloeser(wrapper).trigger('click')

    expect(wrapper.emitted('solved')).toHaveLength(2)
    expect(wrapper.emitted('solved')[1][0]).toEqual({ valve: 'V-32', color: 'ORANGE' })
    expect(pult(wrapper).classes()).toContain('cd--checking')
  })

  it('zeigt nach p_done das letzte Fragment, Pult ist done', () => {
    const wrapper = mountTask({
      view: {
        ...valveView,
        step: 3,
        p_done: true,
        last_fragment: { dots: 3, text: 'FIRE' },
      },
    })

    expect(pult(wrapper).classes()).toContain('cd--done')
    expect(ausloeser(wrapper).attributes('disabled')).toBeDefined()
    expect(wrapper.find('.clue').exists()).toBe(true)
    expect(wrapper.find('.fragment-text').text()).toBe('FIRE')
    expect(wrapper.find('.fragment-dots').text()).toMatch(/●/)
  })
})
