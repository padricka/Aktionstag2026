/**
 * ReleaseButton — Vier-Augen-Freigabe (Aufgabe 2, Leitstand und Rückseite).
 * Prüft nichts selbst: meldet `press`, das Backend entscheidet, ob beide
 * innerhalb von view.release.window Sekunden gedrückt haben.
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ReleaseButton from '../src/components/tasks/task2/ReleaseButton.vue'

const knopf = (w) => w.find('button.release-btn')

afterEach(() => vi.useRealTimers())

describe('ReleaseButton.vue', () => {
  it('ist gesperrt, solange noch nicht gelöscht ist', async () => {
    const w = mount(ReleaseButton, { props: { armed: false, window: 3, partner: 'Rückseite' } })
    expect(knopf(w).attributes('disabled')).toBeDefined()
    await knopf(w).trigger('click')
    expect(w.emitted('press')).toBeUndefined()
    expect(w.find('.release-status').text()).toMatch(/erst nach dem Löschen/i)
  })

  it('meldet press und wartet sichtbar auf den Partner', async () => {
    vi.useFakeTimers()
    const w = mount(ReleaseButton, { props: { armed: true, window: 3, partner: 'Rückseite' } })
    await knopf(w).trigger('click')
    expect(w.emitted('press')).toHaveLength(1)
    expect(w.find('.release-status').text()).toContain('Rückseite')
    expect(w.find('.release-status').text()).toContain('3')

    vi.advanceTimersByTime(1000)
    await w.vm.$nextTick()
    expect(w.find('.release-status').text()).toContain('2')
  })

  it('nach Ablauf des Fensters: zu spät, nochmal gemeinsam', async () => {
    vi.useFakeTimers()
    const w = mount(ReleaseButton, { props: { armed: true, window: 3, partner: 'Leitstand' } })
    await knopf(w).trigger('click')
    vi.advanceTimersByTime(3000)
    await w.vm.$nextTick()
    expect(w.find('.release-status').text()).toMatch(/zu spät/i)
    expect(knopf(w).attributes('disabled')).toBeUndefined()
  })
})
