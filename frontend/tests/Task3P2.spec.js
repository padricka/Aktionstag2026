/**
 * Task3P2 — Rückseite, view.type packet_dump (GAME_DESIGN Aufgabe 3, leichte Fassung).
 * Erst die richtige Backup-Platte einlegen (mount_disk). Dann erscheinen die Nr. der Platte
 * (4-stellig binär, wird umgerechnet) und ZWEI Tabellen mit je 6 Codes, überschrieben mit
 * dem Namen eines Schlüssels. Die Codes werden nicht gerechnet, nur vorgelesen. Teil 3/3.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3P2 from '../src/components/tasks/task3/Task3P2.vue'

const note = { id: 'rescue', title: 'Datenrettung', part: 3, of: 3, torn: ['top'], lines: [{ row: 2, style: 'rule', text: '① Richtige Backup-Platte' }] }
const vorher = {
  type: 'packet_dump',
  disks: ['SN-4471', 'SN-2210', 'SN-9083', 'SN-1356'],
  mounted: false,
  key_id: null,
  tables: null,
  note,
}
const nachher = {
  ...vorher,
  mounted: true,
  key_id: '0110',
  tables: [
    { name: 'ECHO', rows: ['01001101', '11010010', '00011100', '01001101', '10100001', '00111010'] },
    { name: 'DELTA', rows: ['11110000', '00001111', '10101010', '01010101', '11001100', '00110011'] },
  ],
}

describe('Task3P2.vue (packet_dump)', () => {
  it('zeigt vor dem Einlegen die vier Platten und noch keine Tabellen', () => {
    const w = mount(Task3P2, { props: { view: vorher } })
    const platten = w.findAll('button.disk')
    expect(platten).toHaveLength(4)
    expect(platten[2].text()).toContain('SN-9083')
    expect(w.find('.code-tables').exists()).toBe(false)
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

  it('nach dem Einlegen: die Nr. der Platte 4-stellig binär, nicht umgerechnet', () => {
    const w = mount(Task3P2, { props: { view: nachher } })
    expect(w.find('.key-nr').text()).toContain('0110')
    expect(w.find('.key-nr').text()).not.toMatch(/\b6\b/)
    expect(w.find('button.disk').exists()).toBe(false)
  })

  it('zwei Tabellen mit Schlüssel-Namen und je 6 Codes', () => {
    const w = mount(Task3P2, { props: { view: nachher } })
    const tabellen = w.findAll('.code-table')
    expect(tabellen).toHaveLength(2)
    expect(tabellen[0].find('.code-table-name').text()).toContain('ECHO')
    expect(tabellen[1].find('.code-table-name').text()).toContain('DELTA')
    const zeilen = tabellen[0].findAll('.code-row')
    expect(zeilen).toHaveLength(6)
    expect(zeilen[0].text().replace(/\s/g, '')).toContain('01001101')
  })

  it('ohne IT-Begriffe, zeigt Teil 3 der Anleitung', () => {
    const w = mount(Task3P2, { props: { view: nachher } })
    expect(w.text()).not.toMatch(/Paket|Prüfbit|Key-ID|Bit\b|ASCII/)
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 3 von 3: Datenrettung')
    expect(w.find('.role').text()).toBe('Rückseite')
  })
})
