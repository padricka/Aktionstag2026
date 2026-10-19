/**
 * Task3P2 — Rückseite, view.type packet_dump (GAME_DESIGN Aufgabe 3).
 * Erst die richtige Backup-Platte einlegen (mount_disk), dann erscheinen die
 * Datenpakete (Prüfbit vorne abgesetzt) und die Key-ID im Paket-Kopf. Teil 3/3.
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
  packets: null,
  note,
}
const nachher = {
  ...vorher,
  mounted: true,
  key_id: '0110',
  packets: ['11010111', '01001010', '11010111', '01010110', '01011001', '01001010'],
}

describe('Task3P2.vue (packet_dump)', () => {
  it('zeigt vor dem Einlegen die vier Platten und noch keine Pakete', () => {
    const w = mount(Task3P2, { props: { view: vorher } })
    const platten = w.findAll('button.disk')
    expect(platten).toHaveLength(4)
    expect(platten[2].text()).toContain('SN-9083')
    expect(w.find('.packets').exists()).toBe(false)
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

  it('nach dem Einlegen: Key-ID im Paket-Kopf und die Pakete, Prüfbit abgesetzt', () => {
    const w = mount(Task3P2, { props: { view: nachher } })
    expect(w.find('.key-id').text()).toContain('0110')
    const pakete = w.findAll('.packet')
    expect(pakete).toHaveLength(6)
    expect(pakete[0].text()).toContain('Paket 1')
    expect(pakete[1].find('.packet-p').text()).toBe('0')
    expect(pakete[1].find('.packet-data').text().replace(/\s/g, '')).toBe('1001010')
    expect(w.find('button.disk').exists()).toBe(false)
  })

  it('zählt nichts vor und zeigt Teil 3 der Anleitung', () => {
    const w = mount(Task3P2, { props: { view: nachher } })
    expect(w.find('.packets').text()).not.toMatch(/\b(74|86|89)\b|Einsen/)
    expect(w.find('.tn').attributes('aria-label')).toBe('Teil 3 von 3: Datenrettung')
    expect(w.find('.role').text()).toBe('Rückseite')
  })
})
