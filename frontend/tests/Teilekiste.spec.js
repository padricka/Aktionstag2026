/**
 * Teilekiste — nur beim Leitstand: liegt halb im Bild am linken Rand (wie der
 * Taschenrechner rechts), ein Klick zieht sie herein. Drei Fächer: gefundene Teile mit
 * Etikett, sonst nur der Umriss.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Teilekiste from '../src/components/Teilekiste.vue'

const NETZTEIL = { id: 'psu', name: 'Netzteil', fundort: 'schrank', label: '230 V' }

describe('Teilekiste.vue', () => {
  it('zu: nur der Griff mit der Anzahl gefundener Teile', () => {
    const w = mount(Teilekiste, { props: { teile: [NETZTEIL] } })
    expect(w.find('.kiste-handle').exists()).toBe(true)
    expect(w.find('.kiste-zahl').text()).toBe('1/3')
    expect(w.find('.kiste-body').attributes('inert')).toBeDefined()
  })

  it('Klick zieht sie herein: drei Fächer, gefundenes Teil mit Etikett', async () => {
    const w = mount(Teilekiste, { props: { teile: [NETZTEIL] } })
    await w.find('.kiste-handle').trigger('click')
    expect(w.emitted('update:open')[0]).toEqual([true])
    expect(w.classes()).toContain('is-open')

    const faecher = w.findAll('.kiste-fach')
    expect(faecher).toHaveLength(3)
    expect(faecher[0].text()).toContain('Netzteil')
    expect(faecher[0].find('.kiste-etikett').text()).toBe('230 V')
    expect(faecher[1].text()).toContain('noch nicht gefunden')
    expect(faecher[1].find('.teil--fan').classes()).toContain('is-leer')
  })

  it('„Wegschieben“ und Esc legen sie zurück', async () => {
    const w = mount(Teilekiste, { props: { teile: [], open: true } })
    await w.find('.kiste-close').trigger('click')
    expect(w.emitted('update:open').at(-1)).toEqual([false])

    const w2 = mount(Teilekiste, { props: { teile: [], open: true } })
    await w2.find('.kiste-panel').trigger('keydown', { key: 'Escape' })
    expect(w2.emitted('update:open').at(-1)).toEqual([false])
  })

  it('neues Teil: die Kiste wackelt kurz', async () => {
    const w = mount(Teilekiste, { props: { teile: [] } })
    await w.setProps({ teile: [NETZTEIL] })
    expect(w.find('.kiste-panel').classes()).toContain('is-neu')
  })
})
