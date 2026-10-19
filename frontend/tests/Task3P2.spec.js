/**
 * Task3P2 — Rückseite, view.type packet_dump (GAME_DESIGN Aufgabe 3).
 * Sieht 6 Datenpakete à 8 Bit (Prüfbit vorne abgesetzt) und Teil 3/3 der Anleitung.
 * Keine Eingabe – die Rückseite liest vor und entschlüsselt mit.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3P2 from '../src/components/tasks/task3/Task3P2.vue'

const view = {
  type: 'packet_dump',
  packets: ['11010111', '01001010', '11010111', '01010110', '01011001', '01001010'],
  note: { id: 'rescue', title: 'Datenrettung', part: 3, of: 3, torn: ['top'], lines: [{ row: 2, style: 'rule', text: '③ Zahl → Buchstabe' }] },
}

describe('Task3P2.vue (packet_dump)', () => {
  it('zeigt jedes Paket nummeriert, das Prüfbit vorne abgesetzt', () => {
    const w = mount(Task3P2, { props: { view } })
    const pakete = w.findAll('.packet')
    expect(pakete).toHaveLength(6)
    expect(pakete[0].text()).toContain('Paket 1')
    expect(pakete[1].find('.packet-p').text()).toBe('0')
    expect(pakete[1].find('.packet-data').text().replace(/\s/g, '')).toBe('1001010')
  })

  it('zählt nichts vor (keine Einsen-Zahl, kein Dezimalwert)', () => {
    const w = mount(Task3P2, { props: { view } })
    expect(w.find('.packets').text()).not.toMatch(/\b(74|86|89)\b/)
    expect(w.find('.packets').text()).not.toMatch(/Einsen/)
  })

  it('zeigt Teil 3 der Anleitung und hat keine Eingabe', () => {
    const w = mount(Task3P2, { props: { view } })
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 3 von 3: Datenrettung')
    expect(w.find('input').exists()).toBe(false)
    expect(w.find('.role').text()).toBe('Rückseite')
  })
})
