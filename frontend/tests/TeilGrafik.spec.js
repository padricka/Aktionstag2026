/**
 * TeilGrafik — gezeichnete Hardware-Teile (SVG) für Zwischenszene, Teilekiste und Beamer.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TeilGrafik from '../src/components/TeilGrafik.vue'

describe('TeilGrafik.vue', () => {
  it.each(['psu', 'fan', 'disk'])('zeichnet %s als SVG mit Beschriftung für Screenreader', (id) => {
    const w = mount(TeilGrafik, { props: { teil: id } })
    expect(w.find('svg').exists()).toBe(true)
    expect(w.classes()).toContain(`teil--${id}`)
    expect(w.attributes('aria-label')).toMatch(/Netzteil|Lüfter|Backup-Platte/)
  })

  it('leer = nur der Umriss (noch nicht gefunden)', () => {
    const w = mount(TeilGrafik, { props: { teil: 'fan', leer: true } })
    expect(w.classes()).toContain('is-leer')
    expect(w.attributes('aria-label')).toContain('noch nicht gefunden')
  })
})
