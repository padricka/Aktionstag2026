/**
 * Task3P2 — Rückseite, view.type packet_dump (GAME_DESIGN Aufgabe 3, leichte Fassung).
 * Erst die richtige Backup-Platte einlegen (mount_disk), dann erscheinen die
 * Schlüssel-Nr. (normale Zahl) und 5 Datenzeilen mit den Stellenwerten darüber. Teil 3/3.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3P2 from '../src/components/tasks/task3/Task3P2.vue'

const note = { id: 'rescue', title: 'Datenrettung', part: 3, of: 3, torn: ['top'], lines: [{ row: 2, style: 'rule', text: '① Richtige Backup-Platte' }] }
const vorher = {
  type: 'packet_dump',
  disks: ['SN-4471', 'SN-2210', 'SN-9083', 'SN-1356'],
  mounted: false,
  key_nr: null,
  rows: null,
  weights: [128, 64, 32, 16, 8, 4, 2, 1],
  key: null,
  note,
}
const nachher = {
  ...vorher,
  mounted: true,
  key_nr: 6,
  rows: ['01010101', '01001000', '01010001', '01010111', '01001000'],
}

describe('Task3P2.vue (packet_dump)', () => {
  it('zeigt vor dem Einlegen die vier Platten und noch keine Datenzeilen', () => {
    const w = mount(Task3P2, { props: { view: vorher } })
    const platten = w.findAll('button.disk')
    expect(platten).toHaveLength(4)
    expect(platten[2].text()).toContain('SN-9083')
    expect(w.find('.rows').exists()).toBe(false)
  })

  it('Platte anklicken meldet mount_disk und wartet auf den Server', async () => {
    const w = mount(Task3P2, { props: { view: vorher } })
    await w.findAll('button.disk')[2].trigger('click')
    expect(w.emitted('solved')[0][0]).toEqual({ target: 'mount_disk', value: 'SN-9083' })
    expect(w.findAll('button.disk').every((b) => b.attributes('disabled') !== undefined)).toBe(true)
  })

  it('falsche Platte: Fehler zeigen und wieder frei', async () => {
    const w = mount(Task3P2, { props: { view: vorher } })
    await w.findAll('button.disk')[0].trigger('click')
    await w.setProps({ serverError: 'Falsche Eingabe' })
    expect(w.find('.msg-err').text()).toBe('Falsche Eingabe')
    expect(w.findAll('button.disk')[1].attributes('disabled')).toBeUndefined()
  })

  it('nach dem Einlegen: Schlüssel-Nr. als normale Zahl und 5 Datenzeilen', () => {
    const w = mount(Task3P2, { props: { view: nachher } })
    expect(w.find('.key-nr').text()).toContain('Schlüssel-Nr. 6')
    const zeilen = w.findAll('.data-row')
    expect(zeilen).toHaveLength(5)
    expect(zeilen[0].text()).toContain('Zeile 1')
    expect(zeilen[0].findAll('.digit').map((d) => d.text()).join('')).toBe('01010101')
    expect(w.find('button.disk').exists()).toBe(false)
  })

  it('die Stellenwerte stehen über den Ziffern, Einsen sind hervorgehoben', () => {
    const w = mount(Task3P2, { props: { view: nachher } })
    expect(w.findAll('.weights .weight').map((d) => d.text())).toEqual(['128', '64', '32', '16', '8', '4', '2', '1'])
    const ziffern = w.findAll('.data-row')[0].findAll('.digit')
    expect(ziffern[1].classes()).toContain('is-eins')
    expect(ziffern[0].classes()).not.toContain('is-eins')
  })

  it('rechnet nichts vor, ohne IT-Begriffe, zeigt Teil 3 der Anleitung', () => {
    const w = mount(Task3P2, { props: { view: nachher } })
    expect(w.find('.rows').text()).not.toMatch(/\b(85|72|81|87)\b/)
    expect(w.text()).not.toMatch(/Paket|Prüfbit|Key-ID|Bit/)
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 3 von 3: Datenrettung')
    expect(w.find('.role').text()).toBe('Rückseite')
  })

  it('zeigt k, sobald der Leitstand es eingetragen hat', async () => {
    const w = mount(Task3P2, { props: { view: nachher } })
    expect(w.find('.key-badge').exists()).toBe(false)
    await w.setProps({ view: { ...nachher, key: 3 } })
    expect(w.find('.key-badge').text()).toContain('k = 3')
  })
})
