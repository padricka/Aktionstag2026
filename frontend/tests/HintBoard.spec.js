/**
 * HintBoard — Abreißblock mit Hilfe-Notizen am Beamer (nur Host).
 * Auf dem Block stehen die Themen, die noch passen (game_tick.hints.available);
 * ein Klick reißt den Zettel zu genau diesem Thema ab (open(id)). Texte, Themen und
 * Kosten kommen fertig vom Backend, hier wird nichts gerechnet.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import HintBoard from '../src/components/HintBoard.vue'

const block = {
  total: 6,
  cost: 50,
  available: [
    { id: 'parity', label: 'Kaputtes Paket' },
    { id: 'key', label: 'Key-ID / Schlüssel' },
  ],
  opened: [],
}
const mitZetteln = {
  ...block,
  available: [{ id: 'key', label: 'Key-ID / Schlüssel' }],
  opened: [
    { id: 'disk', label: 'Backup-Platte', text: 'Die richtige Platte ist SN-9083.' },
    { id: 'parity', label: 'Kaputtes Paket', text: 'Paket 4 ist beschädigt.' },
  ],
}

const themen = (w) => w.findAll('button.hint-topic')

describe('HintBoard.vue (Abreißblock)', () => {
  it('zeigt einen Block mit den passenden Themen und ihrem Preis', () => {
    const w = mount(HintBoard, { props: { hints: block } })
    expect(w.find('.pad').exists()).toBe(true)
    expect(themen(w).map((b) => b.text())).toEqual([
      expect.stringContaining('Kaputtes Paket'),
      expect.stringContaining('Key-ID / Schlüssel'),
    ])
    expect(themen(w)[0].text()).toContain('−50')
  })

  it('Klick auf ein Thema reißt genau diesen Zettel ab (open mit id) und sperrt kurz', async () => {
    const w = mount(HintBoard, { props: { hints: block } })
    await themen(w)[1].trigger('click')
    expect(w.emitted('open')[0]).toEqual(['key'])
    expect(w.find('.pad').classes()).toContain('is-tearing')
    expect(themen(w).every((b) => b.attributes('disabled') !== undefined)).toBe(true)

    await w.setProps({ hints: { ...block, available: [block.available[0]], opened: [{ id: 'key', label: 'Key-ID / Schlüssel', text: 'k = 3' }] } })
    expect(themen(w)[0].attributes('disabled')).toBeUndefined()
  })

  it('zeigt die abgerissenen Zettel mit Thema und Text, den neuesten oben', () => {
    const w = mount(HintBoard, { props: { hints: mitZetteln } })
    const zettel = w.findAll('.hint-note')
    expect(zettel).toHaveLength(2)
    expect(zettel[0].text()).toContain('Kaputtes Paket')
    expect(zettel[0].text()).toContain('Paket 4 ist beschädigt.')
    expect(zettel[1].text()).toContain('Backup-Platte')
  })

  it('zeigt die bisherigen Kosten', () => {
    const w = mount(HintBoard, { props: { hints: mitZetteln } })
    expect(w.find('.hint-cost').text()).toContain('−100')
  })

  it('ohne passende Themen: leerer Block mit Hinweis', () => {
    const w = mount(HintBoard, { props: { hints: { ...mitZetteln, available: [] } } })
    expect(themen(w)).toHaveLength(0)
    expect(w.find('.pad-empty').text()).toMatch(/keine passende Hilfe/i)
  })

  it('im DEV-Modus kostenlos', () => {
    const w = mount(HintBoard, { props: { hints: block, dev: true } })
    expect(themen(w)[0].text()).toContain('gratis')
    expect(themen(w)[0].text()).not.toContain('−50')
  })

  it('zeigt eine Ablehnung des Servers und gibt wieder frei', async () => {
    const w = mount(HintBoard, { props: { hints: block } })
    await themen(w)[0].trigger('click')
    await w.setProps({ error: 'Diese Hilfe gibt es gerade nicht' })
    expect(w.find('.hint-error').text()).toBe('Diese Hilfe gibt es gerade nicht')
    expect(themen(w)[0].attributes('disabled')).toBeUndefined()
  })
})
