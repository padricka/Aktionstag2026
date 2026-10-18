/**
 * Task1P1 — Vorderseite, view.type main_switches; bedient über das Kabelpanel.
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Task1P1 from '../src/components/tasks/task1/Task1P1.vue'

const stubs = {
  SymbolIcon: { name: 'SymbolIcon', template: '<span class="sym" />', props: ['name', 'size', 'farbe'] },
}

const WIRES = ['raute', 'dreieck', 'quadrat', 'kreis']

const kabel = (w) => w.findAll('.wp-wire')
const knopf = (w) => w.find('.wp__cut')
const panel = (w) => w.find('.wp')

function mountTask(props = {}) {
  return mount(Task1P1, {
    props: {
      symbole: WIRES,
      view: { type: 'main_switches', switches: WIRES, p_done: false },
      ...props,
    },
    global: { stubs },
  })
}

afterEach(() => {
  vi.useRealTimers()
})

describe('Task1P1.vue (main_switches) — Kabelpanel', () => {
  it('zeigt ein Kabel pro Steckplatz und emittiert solved mit Symbol', async () => {
    const wrapper = mountTask()

    expect(kabel(wrapper)).toHaveLength(4)
    await kabel(wrapper)[2].trigger('click')
    await knopf(wrapper).trigger('click')

    expect(wrapper.emitted('solved')[0][0]).toEqual({ player: 'P1', value: 'quadrat' })
  })

  it('nutzt symbole als Fallback, wenn view keine switches liefert', async () => {
    const wrapper = mountTask({ view: { type: 'main_switches', p_done: false } })

    expect(kabel(wrapper)).toHaveLength(4)
    await kabel(wrapper)[0].trigger('click')
    await knopf(wrapper).trigger('click')

    expect(wrapper.emitted('solved')[0][0]).toEqual({ player: 'P1', value: 'raute' })
  })

  it('nutzt view.p_done als Erledigt (nicht nur lokaler State)', async () => {
    const wrapper = mountTask({ view: { type: 'main_switches', p_done: true } })

    expect(panel(wrapper).classes()).toContain('wp--defused')
    expect(knopf(wrapper).text()).toBe('ENTSCHÄRFT')
    expect(knopf(wrapper).attributes('disabled')).toBeDefined()

    await kabel(wrapper)[0].trigger('click')
    expect(kabel(wrapper)[0].classes()).not.toContain('is-selected')
    expect(wrapper.findAll('.is-cut')).toHaveLength(0)
    expect(wrapper.emitted('solved')).toBeUndefined()
  })

  it('sperrt direkt nach dem Senden (checking) und sendet nur einmal', async () => {
    const wrapper = mountTask()

    await kabel(wrapper)[1].trigger('click')
    await knopf(wrapper).trigger('click')
    expect(panel(wrapper).classes()).toContain('wp--checking')

    await kabel(wrapper)[3].trigger('click')
    await knopf(wrapper).trigger('click')
    expect(wrapper.emitted('solved')).toHaveLength(1)
  })

  it('zeigt serverError als error und ist nach 1200 ms wieder armed', async () => {
    vi.useFakeTimers()
    const wrapper = mountTask()

    await kabel(wrapper)[0].trigger('click')
    await knopf(wrapper).trigger('click')

    await wrapper.setProps({ serverError: 'Falsche Eingabe' })
    expect(panel(wrapper).classes()).toContain('wp--error')
    expect(wrapper.find('.msg-err').text()).toBe('Falsche Eingabe')

    vi.advanceTimersByTime(1199)
    await wrapper.vm.$nextTick()
    expect(panel(wrapper).classes()).toContain('wp--error')

    vi.advanceTimersByTime(1)
    await wrapper.vm.$nextTick()
    expect(panel(wrapper).classes()).toContain('wp--armed')
    expect(wrapper.find('.msg-err').exists()).toBe(false)
  })

  it('gibt nach error wieder frei und der Server kann erneut geprüft werden', async () => {
    vi.useFakeTimers()
    const wrapper = mountTask()

    await kabel(wrapper)[0].trigger('click')
    await knopf(wrapper).trigger('click')
    await wrapper.setProps({ serverError: 'Falsche Eingabe' })
    vi.advanceTimersByTime(1200)
    await wrapper.vm.$nextTick()

    await kabel(wrapper)[2].trigger('click')
    await knopf(wrapper).trigger('click')

    expect(wrapper.emitted('solved')).toHaveLength(2)
    expect(wrapper.emitted('solved')[1][0]).toEqual({ player: 'P1', value: 'quadrat' })
  })

  it('reicht die Restzeit als Countdown an das Panel durch', () => {
    const wrapper = mountTask({ timeLeft: 95 })

    expect(wrapper.find('.wp__timer text').text()).toBe('01:35')
  })

  it('Rolle heißt Vorderseite', () => {
    const wrapper = mountTask()
    expect(wrapper.find('.role').text()).toBe('Vorderseite')
  })
})
