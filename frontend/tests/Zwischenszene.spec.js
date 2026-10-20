/**
 * Zwischenszene — nach jeder Aufgabe: der Fundort öffnet sich, das Teil kommt zum
 * Vorschein, dann die Titelkarte der nächsten Aufgabe; danach `fertig`.
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Zwischenszene, { DAUER } from '../src/components/Zwischenszene.vue'

const NETZTEIL = { id: 'psu', name: 'Netzteil', fundort: 'schrank', label: '230 V' }

function szene(props = {}) {
  return mount(Zwischenszene, { props: { teil: NETZTEIL, naechste: 2, rolle: 'MASTER', ...props } })
}

describe('Zwischenszene.vue', () => {
  afterEach(() => vi.useRealTimers())

  it('zeigt den passenden Fundort, erst geschlossen, dann offen mit dem Teil', async () => {
    vi.useFakeTimers()
    const w = szene()
    expect(w.find('.fundort--schrank').exists()).toBe(true)
    expect(w.find('.fundort').classes()).not.toContain('is-offen')
    expect(w.text()).toContain('Ersatzteilschrank')

    vi.advanceTimersByTime(DAUER.oeffnen + 10)
    await w.vm.$nextTick()
    expect(w.find('.fundort').classes()).toContain('is-offen')
    expect(w.find('.fundort .teil--psu').exists()).toBe(true)
    expect(w.text()).toContain('Netzteil gefunden')
  })

  it.each([
    ['lager', 'Lager', 'Lüfter', 'fan'],
    ['tresor', 'Datentresor', 'Backup-Platte', 'disk'],
  ])('Fundort %s heißt %s', (fundort, titel, name, id) => {
    const w = szene({ teil: { id, name, fundort, label: '' }, naechste: 3 })
    expect(w.find(`.fundort--${fundort}`).exists()).toBe(true)
    expect(w.text()).toContain(titel)
  })

  it('sagt jeder Rolle, wo das Teil jetzt liegt', () => {
    expect(szene({ rolle: 'MASTER' }).text()).toContain('in deiner Teilekiste')
    expect(szene({ rolle: 'FI-SI' }).text()).toContain('Teilekiste beim Leitstand')
  })

  it('danach die Titelkarte der nächsten Aufgabe, dann fertig', async () => {
    vi.useFakeTimers()
    const w = szene({ naechste: 2 })
    vi.advanceTimersByTime(DAUER.titel + 10)
    await w.vm.$nextTick()
    expect(w.find('.zs-titel').text()).toContain('Aufgabe 2')
    expect(w.find('.zs-titel').text()).toContain('Löschprotokoll')
    expect(w.emitted('fertig')).toBeUndefined()

    vi.advanceTimersByTime(DAUER.ende - DAUER.titel)
    expect(w.emitted('fertig')).toHaveLength(1)
  })

  it('vor dem Finale heißt die Titelkarte „Finale“', async () => {
    vi.useFakeTimers()
    const w = szene({ teil: { id: 'disk', name: 'Backup-Platte', fundort: 'tresor', label: '' }, naechste: 4 })
    vi.advanceTimersByTime(DAUER.titel + 10)
    await w.vm.$nextTick()
    expect(w.find('.zs-titel').text()).toContain('Finale')
  })
})
