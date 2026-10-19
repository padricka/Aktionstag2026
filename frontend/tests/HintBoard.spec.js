/**
 * HintBoard — Hilfe-Notizen am Beamer (nur Host). Der Host öffnet sie der Reihe nach;
 * Texte und Anzahl kommen fertig vom Backend (game_tick.hints), hier wird nichts gerechnet.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import HintBoard from '../src/components/HintBoard.vue'

const zu = { total: 4, opened: [], cost: 50 }
const zwei = { total: 4, opened: ['Lest euch eure Teile vor.', 'Kabel an Platz 4 kappen.'], cost: 50 }

const knopf = (w) => w.find('button.hint-open')

describe('HintBoard.vue', () => {
  it('zeigt, welche Hilfe als nächste kommt und was sie kostet', () => {
    const w = mount(HintBoard, { props: { hints: zu } })
    expect(knopf(w).text()).toContain('Hilfe 1 von 4')
    expect(knopf(w).text()).toContain('−50 Punkte')
    expect(w.findAll('.hint-note')).toHaveLength(0)
  })

  it('Klick meldet open und sperrt, bis die Hilfe da ist', async () => {
    const w = mount(HintBoard, { props: { hints: zu } })
    await knopf(w).trigger('click')
    expect(w.emitted('open')).toHaveLength(1)
    expect(knopf(w).attributes('disabled')).toBeDefined()
    await w.setProps({ hints: { ...zu, opened: ['Lest euch eure Teile vor.'] } })
    expect(knopf(w).attributes('disabled')).toBeUndefined()
  })

  it('zeigt die geöffneten Hilfen nummeriert, die neueste oben', () => {
    const w = mount(HintBoard, { props: { hints: zwei } })
    const notizen = w.findAll('.hint-note')
    expect(notizen).toHaveLength(2)
    expect(notizen[0].text()).toContain('Hilfe 2')
    expect(notizen[0].text()).toContain('Kabel an Platz 4 kappen.')
    expect(notizen[1].text()).toContain('Hilfe 1')
    expect(knopf(w).text()).toContain('Hilfe 3 von 4')
  })

  it('zeigt die bisherigen Kosten', () => {
    const w = mount(HintBoard, { props: { hints: zwei } })
    expect(w.find('.hint-cost').text()).toContain('−100')
  })

  it('alle offen: kein weiterer Klick möglich', () => {
    const w = mount(HintBoard, { props: { hints: { total: 2, opened: ['a', 'b'], cost: 50 } } })
    expect(knopf(w).attributes('disabled')).toBeDefined()
    expect(knopf(w).text()).toMatch(/Alle Hilfen offen/)
  })

  it('im DEV-Modus kostenlos', () => {
    const w = mount(HintBoard, { props: { hints: zu, dev: true } })
    expect(knopf(w).text()).toContain('kostenlos')
    expect(knopf(w).text()).not.toContain('−50')
  })

  it('zeigt eine Ablehnung des Servers und gibt wieder frei', async () => {
    const w = mount(HintBoard, { props: { hints: zu } })
    await knopf(w).trigger('click')
    await w.setProps({ error: 'Spiel läuft nicht' })
    expect(w.find('.hint-error').text()).toBe('Spiel läuft nicht')
    expect(knopf(w).attributes('disabled')).toBeUndefined()
  })
})
