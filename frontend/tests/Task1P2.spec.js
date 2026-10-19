/**
 * Task1P2 — Rückseite, view.type code_stickers: nur Anzeige, keine Eingabe.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task1P2 from '../src/components/tasks/task1/Task1P2.vue'

const stubs = {
  SymbolIcon: {
    name: 'SymbolIcon',
    template: '<span class="sym" :data-name="name" :data-farbe="farbe" />',
    props: ['name', 'size', 'farbe'],
  },
}

const stickers = [
  { symbol: 'stern', color: 'ROT' },
  { symbol: 'kreuz', color: 'GELB' },
  { symbol: 'dreieck-runter', color: 'BLAU' },
  { symbol: 'dreieck-runter-voll', color: 'GRÜN' },
]

describe('Task1P2.vue (code_stickers)', () => {
  it('zeigt 4 farbige Aufkleber aus view.stickers', () => {
    const wrapper = mount(Task1P2, {
      props: { view: { type: 'code_stickers', stickers } },
      global: { stubs },
    })

    const cards = wrapper.findAll('.sticker')
    expect(cards).toHaveLength(4)
    expect(wrapper.findAll('.sym')).toHaveLength(4)
    expect(wrapper.find('.sym').attributes('data-name')).toBe('stern')
  })

  it('hat keine Code-Eingabe / kein Ausführen', () => {
    const wrapper = mount(Task1P2, {
      props: { view: { type: 'code_stickers', stickers } },
      global: { stubs },
    })

    expect(wrapper.find('.key').exists()).toBe(false)
    expect(wrapper.find('.btn-action').exists()).toBe(false)
    expect(wrapper.emitted('solved')).toBeUndefined()
  })

  it('Rolle heißt Rückseite', () => {
    const wrapper = mount(Task1P2, {
      props: { view: { type: 'code_stickers', stickers } },
      global: { stubs },
    })
    expect(wrapper.find('.role').text()).toBe('Rückseite')
  })
})

describe('Task1P2.vue — zerkratzter Aufkleber und Zettel', () => {
  const mitKratzer = [
    { symbol: 'stern', color: 'ROT' },
    { symbol: null, color: 'GELB', scratched: true },
    { symbol: 'dreieck-runter', color: 'BLAU' },
    { symbol: 'kreuz', color: 'GRÜN' },
  ]
  const note = { id: 'alarm', title: 'Wartungsnotiz', torn: ['top'], lines: [{ row: 12, style: 'rule', text: '③ Ein Aufkleber zerkratzt? Dann gilt dort' }] }

  it('zeigt den zerkratzten Aufkleber mit Farbe, aber ohne Symbol', () => {
    const wrapper = mount(Task1P2, {
      props: { view: { type: 'code_stickers', stickers: mitKratzer, note } },
      global: { stubs },
    })
    const kratzer = wrapper.find('.sticker.is-scratched')
    expect(kratzer.exists()).toBe(true)
    expect(kratzer.text()).toContain('GELB')
    expect(kratzer.text()).toContain('zerkratzt')
    expect(kratzer.find('.sym').exists()).toBe(false)
    expect(wrapper.findAll('.sym')).toHaveLength(3)
  })

  it('zeigt das eigene Stück der Wartungsnotiz', () => {
    const wrapper = mount(Task1P2, {
      props: { view: { type: 'code_stickers', stickers: mitKratzer, note } },
      global: { stubs },
    })
    expect(wrapper.find('.tn').exists()).toBe(true)
    expect(wrapper.find('.tn').text()).toContain('③ Ein Aufkleber zerkratzt?')
  })
})
