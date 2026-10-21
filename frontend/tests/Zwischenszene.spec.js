/**
 * Zwischenszene — nach jeder Aufgabe: der Fundort öffnet sich, das Teil kommt zum
 * Vorschein, dann die Titelkarte der nächsten Aufgabe; danach `fertig`.
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Zwischenszene, { DAUER, DAUER_TRESOR, TUTORIAL_MS } from '../src/components/Zwischenszene.vue'

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

  it('der Datentresor ist derselbe Tresor wie bisher (VaultDoor) mit der Platte darin', async () => {
    vi.useFakeTimers()
    const w = szene({ teil: { id: 'disk', name: 'Backup-Platte', fundort: 'tresor', label: '' }, naechste: 4 })
    const tresor = w.findComponent({ name: 'VaultDoor' })
    expect(tresor.exists()).toBe(true)
    expect(tresor.find('.vd-panel__label').text()).toBe('DATENTRESOR')
    expect(tresor.classes()).toContain('vault--locked')

    vi.advanceTimersByTime(DAUER_TRESOR.oeffnen + 10)
    await w.vm.$nextTick()
    expect(tresor.classes()).toContain('vault--open')
    expect(tresor.find('.vault__inside .teil--disk').exists()).toBe(true)
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
    const w = szene({ teil: { id: 'fan', name: 'Lüfter', fundort: 'lager', label: '' }, naechste: 3 })
    vi.advanceTimersByTime(DAUER.titel + 10)
    await w.vm.$nextTick()
    expect(w.find('.zs-titel').text()).toContain('Aufgabe 3')
    expect(w.find('.zs-titel').text()).toContain('Datenrettung')
    expect(w.emitted('fertig')).toBeUndefined()

    vi.advanceTimersByTime(DAUER.ende - DAUER.titel + (TUTORIAL_MS[3] || 0))
    expect(w.emitted('fertig')).toHaveLength(1)
  })

  describe('Tutorial Löschanlage vor Aufgabe 2 (feat/tutorial-loeschanlage)', () => {
    it('nach der Titelkarte „Löschprotokoll“ zeigt es Schritt für Schritt das Steuerpult', async () => {
      vi.useFakeTimers()
      const w = szene({ naechste: 2 })
      vi.advanceTimersByTime(DAUER.titel + 10)
      await w.vm.$nextTick()
      expect(w.find('.zs-titel').text()).toContain('Löschprotokoll')

      vi.advanceTimersByTime(DAUER.ende - DAUER.titel)
      await w.vm.$nextTick()
      expect(w.emitted('fertig')).toBeUndefined()           // Tutorial läuft noch
      const tut = w.find('.tut-loesch')
      expect(tut.exists()).toBe(true)
      expect(tut.text()).toContain('So funktioniert die Löschanlage')
      expect(tut.find('.tut-schritt').text()).toContain('Schrank')
    })

    it('zeigt auch, wie man es falsch macht, und die Freigabe zu zweit', async () => {
      vi.useFakeTimers()
      const w = szene({ naechste: 2 })
      vi.advanceTimersByTime(DAUER.ende + 10)
      await w.vm.$nextTick()
      const texte = []
      for (let i = 0; i < 6; i++) {
        texte.push(w.find('.tut-schritt').text())
        vi.advanceTimersByTime(TUTORIAL_MS[2] / 5)
        await w.vm.$nextTick()
      }
      const alles = texte.join(' ')
      expect(alles).toMatch(/Löschmittel/)
      expect(alles).toMatch(/AUSLÖSEN/)
      expect(alles).toMatch(/So NICHT/)
      expect(alles).toMatch(/−30 Leben/)
      expect(alles).toMatch(/GLEICHZEITIG/)
    })

    it('nutzt das echte Steuerpult der Vorderseite und die echten Freigabe-Knöpfe', async () => {
      vi.useFakeTimers()
      const w = szene({ naechste: 2 })
      vi.advanceTimersByTime(DAUER.ende + 10)
      await w.vm.$nextTick()
      const pult = w.findComponent({ name: 'ControlDesk' })
      expect(pult.exists()).toBe(true)
      expect(pult.find('[role="slider"][aria-label="Schrank"]').exists()).toBe(true)
      expect(w.find('.tut-loesch').attributes('inert')).toBeDefined()   // nur Vorführung

      vi.advanceTimersByTime(TUTORIAL_MS[2] / 5)                       // ① Schrank gewählt
      await w.vm.$nextTick()
      expect(pult.find('[role="slider"][aria-label="Schrank"]').attributes('aria-valuetext')).toBe('B-01')
      vi.advanceTimersByTime(TUTORIAL_MS[2] / 5)                       // ② Löschmittel
      await w.vm.$nextTick()
      expect(pult.find('[role="slider"][aria-label="Löschmittel"]').attributes('aria-valuetext')).toBe('CO2')
      vi.advanceTimersByTime(TUTORIAL_MS[2] / 5)                       // So NICHT: Störung
      await w.vm.$nextTick()
      expect(pult.classes()).toContain('cd--error')
      vi.advanceTimersByTime(TUTORIAL_MS[2] / 5)                       // ④ Freigabe
      await w.vm.$nextTick()
      expect(w.findAllComponents({ name: 'ReleaseButton' })).toHaveLength(2)
    })

    it('ist nach TUTORIAL_MS vorbei, dann fertig', () => {
      vi.useFakeTimers()
      const w = szene({ naechste: 2 })
      vi.advanceTimersByTime(DAUER.ende + TUTORIAL_MS[2] - 10)
      expect(w.emitted('fertig')).toBeUndefined()
      vi.advanceTimersByTime(20)
      expect(w.emitted('fertig')).toHaveLength(1)
    })

    it('vor dem Finale gibt es kein Tutorial', () => {
      vi.useFakeTimers()
      const w = szene({ teil: { id: 'disk', name: 'Backup-Platte', fundort: 'tresor', label: '' }, naechste: 4 })
      vi.advanceTimersByTime(DAUER_TRESOR.ende + 10)
      expect(w.emitted('fertig')).toHaveLength(1)
    })
  })

  describe('Tutorial Binär vor Aufgabe 3 (feat/tutorial-binaer)', () => {
    const LUEFTER = { id: 'fan', name: 'Lüfter', fundort: 'lager', label: '' }
    const BILDER = 5

    async function bilder(w) {
      const texte = []
      for (let i = 0; i < BILDER + 1; i++) {
        texte.push(w.find('.tut-binaer').text())
        vi.advanceTimersByTime(TUTORIAL_MS[3] / BILDER)
        await w.vm.$nextTick()
      }
      return texte
    }

    it('nach der Titelkarte „Datenrettung“: die Nr. der Platte ausrechnen, dann Codes nur nachschlagen', async () => {
      vi.useFakeTimers()
      const w = szene({ teil: LUEFTER, naechste: 3 })
      vi.advanceTimersByTime(DAUER.ende + 10)
      await w.vm.$nextTick()
      expect(w.emitted('fertig')).toBeUndefined()
      expect(w.find('.tut-binaer').text()).toContain('Nr. auf der Platte')

      const alles = (await bilder(w)).join(' | ')
      expect(alles).toMatch(/4 \+ 2 = 6/)
      expect(alles).toMatch(/NICHT rechnen/)
      expect(alles).toMatch(/Code-Tabelle/)
      expect(alles).not.toMatch(/ASCII|64 \+ 16/)
    })

    it('zeigt die Werte 8 4 2 1 über den Ziffern und hebt die Einsen hervor', async () => {
      vi.useFakeTimers()
      const w = szene({ teil: LUEFTER, naechste: 3 })
      vi.advanceTimersByTime(DAUER.ende + 10)
      await w.vm.$nextTick()                                          // Tutorial hängt sich ein
      vi.advanceTimersByTime(TUTORIAL_MS[3] / BILDER)                 // zweites Bild: Einsen leuchten
      await w.vm.$nextTick()
      expect(w.findAll('.tut-binaer .tb-wert').map((x) => x.text())).toEqual(['8', '4', '2', '1'])
      expect(w.findAll('.tut-binaer .tb-ziffer').map((x) => x.text()).join('')).toBe('0110')
      expect(w.findAll('.tut-binaer .tb-ziffer.is-eins')).toHaveLength(2)
    })

    it('beim Nachschlagen ist die passende Zeile der Code-Tabelle markiert', async () => {
      vi.useFakeTimers()
      const w = szene({ teil: LUEFTER, naechste: 3 })
      vi.advanceTimersByTime(DAUER.ende + 10)
      await w.vm.$nextTick()
      vi.advanceTimersByTime((TUTORIAL_MS[3] / BILDER) * 4)          // letztes Bild
      await w.vm.$nextTick()
      const treffer = w.find('.tut-binaer .tb-eintrag.is-treffer')
      expect(treffer.exists()).toBe(true)
      expect(treffer.text()).toContain('R')
    })

    it('ist nach TUTORIAL_MS vorbei, dann fertig', () => {
      vi.useFakeTimers()
      const w = szene({ teil: LUEFTER, naechste: 3 })
      vi.advanceTimersByTime(DAUER.ende + TUTORIAL_MS[3] - 10)
      expect(w.emitted('fertig')).toBeUndefined()
      vi.advanceTimersByTime(20)
      expect(w.emitted('fertig')).toHaveLength(1)
    })
  })
})
