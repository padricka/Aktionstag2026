/**
 * TornNote — ein Stück eines zerrissenen Notizzettels (Panel, PANELS.md).
 * Inhalt kommt fertig vom Backend (view.note): nur ganze Wörter, Zeilen mit Position.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TornNote from '../src/components/TornNote.vue'

const note = {
  id: 'alarm',
  title: 'Wartungsnotiz',
  torn: ['right', 'bottom'],
  lines: [
    { row: 0, style: 'typed', text: 'DRV SCHWABEN · RAUM B-04' },
    { row: 3, style: 'rule', text: '① Brennt ein Steckplatz:' },
    { row: 4, style: 'text', text: 'Gerade Nummer → das' },
    { row: 10, style: 'strike', text: 'Der Code fängt' },
    { row: 10, style: 'red', text: 'stimmt nicht!' },
  ],
}

describe('TornNote.vue', () => {
  it('zeigt jede Zeile als ganzen Text, in Reihenfolge', () => {
    const w = mount(TornNote, { props: { note, seed: 'task-001' } })
    const texte = w.findAll('.tn-text').map((t) => t.text())
    expect(texte).toEqual(note.lines.map((l) => l.text))
  })

  it('setzt Zeilen auf ihre Position, Zeilen mit gleicher Nummer nebeneinander', () => {
    const w = mount(TornNote, { props: { note, seed: 'task-001' } })
    const reihen = w.findAll('.tn-row')
    expect(reihen.map((r) => r.attributes('data-row'))).toEqual(['0', '3', '4', '10'])
    expect(reihen[3].findAll('.tn-text')).toHaveLength(2)
    expect(reihen[1].attributes('style')).toContain('top: calc(3 * var(--tn-line))')
  })

  it('übernimmt den Stil je Zeile (Schreibmaschine, Regel, durchgestrichen, rote Notiz)', () => {
    const w = mount(TornNote, { props: { note, seed: 'task-001' } })
    const klassen = w.findAll('.tn-text').map((t) => t.classes().find((c) => c.startsWith('is-')))
    expect(klassen).toEqual(['is-typed', 'is-rule', 'is-text', 'is-strike', 'is-red'])
  })

  it('reißt nur die Kanten aus note.torn, gleiche Form bei gleichem seed', () => {
    const a = mount(TornNote, { props: { note, seed: 'task-001' } })
    const b = mount(TornNote, { props: { note, seed: 'task-001' } })
    const c = mount(TornNote, { props: { note, seed: 'task-002' } })
    const clip = (w) => w.find('.tn-paper').attributes('style')
    expect(clip(a)).toContain('clip-path: polygon(')
    expect(clip(a)).toBe(clip(b))
    expect(clip(a)).not.toBe(clip(c))
    expect(a.find('.tn').classes()).toEqual(expect.arrayContaining(['torn-right', 'torn-bottom']))
    expect(a.find('.tn').classes()).not.toContain('torn-left')
  })

  it('ist für Screenreader als Notiz beschriftet', () => {
    const w = mount(TornNote, { props: { note, seed: 'x' } })
    expect(w.find('.tn').attributes('role')).toBe('note')
    expect(w.find('.tn').attributes('aria-label')).toContain('Wartungsnotiz')
  })

  it('ein Stück beginnt bei seiner ersten eigenen Zeile (kein leeres Papier oben)', () => {
    const unten = { id: 'alarm', title: 'Wartungsnotiz', torn: ['top'], lines: [
      { row: 12, style: 'rule', text: '③ Ein Aufkleber zerkratzt?' },
      { row: 13, style: 'text', text: 'Dann gilt dort' },
      { row: 16, style: 'sign', text: '– M. Kaiser, IT' },
    ] }
    const w = mount(TornNote, { props: { note: unten, seed: 'x' } })
    const reihen = w.findAll('.tn-row')
    expect(reihen[0].attributes('style')).toContain('top: calc(0 * var(--tn-line))')
    expect(reihen[2].attributes('style')).toContain('top: calc(4 * var(--tn-line))')   // Abstände bleiben
    expect(w.find('.tn-paper').attributes('style')).toContain('--tn-lines: 5')
  })

  it('ohne Zettel nichts', () => {
    const w = mount(TornNote, { props: { note: null } })
    expect(w.find('.tn').exists()).toBe(false)
  })
})
