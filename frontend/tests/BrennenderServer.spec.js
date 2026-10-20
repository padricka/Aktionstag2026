/**
 * BrennenderServer — der Beamer zeigt statt des Tresors das brennende Server-Rack.
 * Je weniger Leben, desto mehr Feuer (Stufe 1–3); ein Fehler lässt es auflodern.
 * Daneben die drei Teile fürs Finale (Umriss, bis sie gefunden sind). Sieg: Feuer aus.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BrennenderServer from '../src/components/BrennenderServer.vue'

const NETZTEIL = { id: 'psu', name: 'Netzteil', fundort: 'schrank', label: '230 V' }

function server(props = {}) {
  return mount(BrennenderServer, { props: { hp: 300, maxHp: 300, teile: [], ...props } })
}

describe('BrennenderServer.vue', () => {
  it.each([
    [300, 1],
    [200, 1],
    [150, 2],
    [60, 3],
    [0, 3],
  ])('bei %i Leben brennt es in Stufe %i', (hp, stufe) => {
    expect(server({ hp }).classes()).toContain(`bs--stufe-${stufe}`)
  })

  it('weniger Leben → größeres Feuer (CSS-Variable --feuer)', () => {
    const viel = parseFloat(server({ hp: 300 }).attributes('style').match(/--feuer:\s*([\d.]+)/)[1])
    const wenig = parseFloat(server({ hp: 30 }).attributes('style').match(/--feuer:\s*([\d.]+)/)[1])
    expect(wenig).toBeGreaterThan(viel)
  })

  it('zeigt die drei Teile: gefundene gefüllt, die anderen als Umriss', () => {
    const w = server({ teile: [NETZTEIL] })
    const teile = w.findAll('.bs-teil')
    expect(teile.map((t) => t.text())).toEqual(['Netzteil', 'Lüfter', 'Backup-Platte'])
    expect(teile[0].classes()).toContain('is-da')
    expect(teile[1].find('.teil').classes()).toContain('is-leer')
  })

  it('ein Fehler (−60) lässt das Feuer kurz auflodern, das Feuer-Leben (−1) nicht', async () => {
    const w = server({ hp: 300 })
    await w.setProps({ hp: 299 })
    expect(w.classes()).not.toContain('is-auflodern')
    await w.setProps({ hp: 239 })
    expect(w.classes()).toContain('is-auflodern')
  })

  it('Sieg: das Feuer geht aus, der Server ist wieder online', () => {
    const w = server({ hp: 120, sieg: true })
    expect(w.classes()).toContain('is-geloescht')
    expect(w.find('.bs-online').text()).toContain('SERVER ONLINE')
  })
})
