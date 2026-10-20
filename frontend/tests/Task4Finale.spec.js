/**
 * Finale „Server reparieren“ (kind repair) – die drei Ansichten und der Schlüsselschalter.
 * Jede Ansicht meldet Eingaben als `eingabe` { target, value }; PlayerScreen schickt sie
 * als player_input. Regeln und Prüfung: Backend (test_taskReparatur.py).
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SchluesselSchalter from '../src/components/tasks/task4/SchluesselSchalter.vue'
import Task4Leitstand from '../src/components/tasks/task4/Task4Leitstand.vue'
import Task4Vorderseite from '../src/components/tasks/task4/Task4Vorderseite.vue'
import Task4Rueckseite from '../src/components/tasks/task4/Task4Rueckseite.vue'

const NOTE = { id: 'repair', title: 'Einbauanleitung', part: 1, of: 3, torn: ['right'], lines: [{ row: 0, style: 'typed', text: 'TEIL 1/3' }] }
const NICHTS = { disk: false, fan: false, psu: false }
const eingaben = (w) => (w.emitted('eingabe') || []).map((e) => e[0])

// ------------------------------------------------------------------ Schlüssel
describe('SchluesselSchalter.vue', () => {
  it('dreht nur, wenn er bereit ist', async () => {
    const zu = mount(SchluesselSchalter, { props: { label: 'Strom', bereit: false } })
    expect(zu.find('button').attributes('disabled')).toBeDefined()

    const w = mount(SchluesselSchalter, { props: { label: 'Strom', bereit: true } })
    await w.find('button').trigger('click')
    expect(w.emitted('drehen')).toHaveLength(1)
    expect(w.text()).toContain('Strom')
  })

  it('gedreht: steht quer und leuchtet grün', () => {
    const w = mount(SchluesselSchalter, { props: { label: 'System', bereit: true, gedreht: true } })
    expect(w.classes()).toContain('is-gedreht')
  })
})

// ------------------------------------------------------------------ Leitstand
function leitstand(view = {}, props = {}) {
  return mount(Task4Leitstand, {
    props: {
      view: {
        type: 'repair_console',
        parts: [
          { id: 'disk', name: 'Backup-Platte', label: 'RAID-Platz 3', ort: 'kiste' },
          { id: 'fan', name: 'Lüfter', label: 'Pfeil = Luftstrom', ort: 'FI-SI' },
          { id: 'psu', name: 'Netzteil', label: '230 V', ort: 'eingebaut' },
        ],
        console: { bay: 4, fan: 3, psu: 2 },
        wartung: ['bay:2'],
        installed: NICHTS,
        phase: 'einbau',
        keys: [],
        note: NOTE,
        ...view,
      },
      ...props,
    },
  })
}

describe('Task4Leitstand.vue', () => {
  it('zeigt die Teile mit Etikett und wo sie gerade sind', () => {
    const w = leitstand()
    const zeilen = w.findAll('.teil-zeile')
    expect(zeilen[0].text()).toContain('RAID-Platz 3')
    expect(zeilen[0].text()).toContain('in der Kiste')
    expect(zeilen[1].text()).toContain('bei der Vorderseite')
    expect(zeilen[2].text()).toContain('eingebaut')
    expect(zeilen[2].findAll('button')).toHaveLength(0)
  })

  it('gibt ein Teil weiter', async () => {
    const w = leitstand()
    await w.findAll('.teil-zeile')[0].find('.geben-vorne').trigger('click')
    await w.findAll('.teil-zeile')[0].find('.geben-hinten').trigger('click')
    expect(eingaben(w)).toEqual([
      { target: 'give', value: 'disk:FI-SI' },
      { target: 'give', value: 'disk:FI-AE' },
    ])
  })

  it('Konsole: Plätze ab 0 gezählt, Wartung umschalten', async () => {
    const w = leitstand()
    const bays = w.findAll('.konsole-platz[data-art="bay"]')
    expect(bays.map((b) => b.find('.platz-name').text())).toEqual(['BAY 0', 'BAY 1', 'BAY 2', 'BAY 3'])
    expect(w.findAll('.konsole-platz[data-art="fan"]')).toHaveLength(3)
    expect(w.findAll('.konsole-platz[data-art="psu"]')).toHaveLength(2)
    expect(bays[2].classes()).toContain('is-wartung')
    expect(bays[2].text()).toContain('WARTUNG')

    await bays[1].trigger('click')
    expect(eingaben(w)).toEqual([{ target: 'maintenance', value: 'bay:1' }])
  })

  it('Schlüssel „System“ erst nach dem Einbau', async () => {
    expect(leitstand().findComponent(SchluesselSchalter).props('bereit')).toBe(false)
    const w = leitstand({ phase: 'start', keys: ['strom', 'kuehlung'] })
    expect(w.findComponent(SchluesselSchalter).props('bereit')).toBe(true)
    expect(w.find('.schluessel-stand').text()).toContain('2/3')
    await w.findComponent(SchluesselSchalter).find('button').trigger('click')
    expect(eingaben(w)).toEqual([{ target: 'key', value: 'system' }])
  })

  it('zeigt die Meldung vom Server und beim Sieg „Server fährt hoch“', () => {
    expect(leitstand({}, { serverError: 'Stromschlag! Platz 3 war nicht in Wartung.' }).find('.msg-err').text())
      .toContain('Stromschlag')
    expect(leitstand({}, { victory: true }).find('.sieg').text()).toContain('SERVER FÄHRT HOCH')
  })
})

// ------------------------------------------------------------------ Vorderseite
function vorne(view = {}) {
  return mount(Task4Vorderseite, {
    props: {
      view: {
        type: 'repair_front',
        bays: [{ nr: 1, led: 'gruen' }, { nr: 2, led: 'rot' }, { nr: 3, led: 'aus' }, { nr: 4, led: 'aus' }],
        fan_slots: [{ nr: 1, belegt: true }, { nr: 2, belegt: false }, { nr: 3, belegt: true }],
        hand: [{ id: 'disk', name: 'Backup-Platte' }, { id: 'fan', name: 'Lüfter' }],
        installed: NICHTS,
        phase: 'einbau',
        keys: [],
        note: NOTE,
        ...view,
      },
    },
  })
}

describe('Task4Vorderseite.vue', () => {
  it('zeigt die Schächte mit ihren LEDs und die Lücke in der Lüfterwand', () => {
    const w = vorne()
    const leds = w.findAll('.schacht').map((s) => s.attributes('data-led'))
    expect(leds).toEqual(['gruen', 'rot', 'aus', 'aus'])
    expect(w.findAll('.luefter-platz.is-luecke')).toHaveLength(1)
  })

  it('Platte nehmen und in Schacht 3 schieben', async () => {
    const w = vorne()
    await w.findAll('.schacht')[2].trigger('click')
    expect(eingaben(w)).toEqual([])                       // nichts in der Hand gewählt
    await w.find('.hand-teil[data-teil="disk"]').trigger('click')
    await w.findAll('.schacht')[2].trigger('click')
    expect(eingaben(w)).toEqual([{ target: 'install_disk', value: '3' }])
  })

  it('Lüfter: Richtung wählen, dann in die Lücke', async () => {
    const w = vorne()
    await w.find('.hand-teil[data-teil="fan"]').trigger('click')
    await w.find('.richtung-hinten').trigger('click')
    await w.find('.luefter-platz.is-luecke').trigger('click')
    expect(eingaben(w)).toEqual([{ target: 'install_fan', value: '2:hinten' }])
  })

  it('ein Teil, das hier nicht passt, geht zurück', async () => {
    const w = vorne({ hand: [{ id: 'psu', name: 'Netzteil' }] })
    await w.find('.zurueck[data-teil="psu"]').trigger('click')
    expect(eingaben(w)).toEqual([{ target: 'return', value: 'psu' }])
  })

  it('Schlüssel „Kühlung“', async () => {
    const w = vorne({ phase: 'start', installed: { disk: true, fan: true, psu: true } })
    await w.findComponent(SchluesselSchalter).find('button').trigger('click')
    expect(eingaben(w)).toEqual([{ target: 'key', value: 'kuehlung' }])
  })
})

// ------------------------------------------------------------------ Rückseite
function hinten(view = {}) {
  return mount(Task4Rueckseite, {
    props: {
      view: {
        type: 'repair_back',
        psu_bays: [{ nr: 1, sicherung: 'durch' }, { nr: 2, sicherung: 'ok' }],
        gang: 'Warmgang',
        hand: [{ id: 'psu', name: 'Netzteil' }],
        installed: { disk: true, fan: true, psu: false },
        phase: 'einbau',
        keys: [],
        note: NOTE,
        ...view,
      },
    },
  })
}

describe('Task4Rueckseite.vue', () => {
  it('zeigt das Gang-Schild und die Sicherungen', () => {
    const w = hinten()
    expect(w.find('.gang-schild').text()).toContain('WARMGANG')
    expect(w.findAll('.nt-schacht').map((s) => s.attributes('data-sicherung'))).toEqual(['durch', 'ok'])
  })

  it('Spannung einstellen und das Netzteil einschieben', async () => {
    const w = hinten()
    await w.find('.hand-teil[data-teil="psu"]').trigger('click')
    await w.find('.spannung-230').trigger('click')
    await w.findAll('.nt-schacht')[1].trigger('click')
    expect(eingaben(w)).toEqual([{ target: 'install_psu', value: '2:230' }])
  })

  it('Schlüssel „Strom“', async () => {
    const w = hinten({ phase: 'start', hand: [], installed: { disk: true, fan: true, psu: true } })
    await w.findComponent(SchluesselSchalter).find('button').trigger('click')
    expect(eingaben(w)).toEqual([{ target: 'key', value: 'strom' }])
  })
})
