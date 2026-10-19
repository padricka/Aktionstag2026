import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import GameOver from '../src/components/GameOver.vue'

describe('GameOver.vue', () => {
  it('zeigt Niederlage bei meltdown', () => {
    const wrapper = mount(GameOver, {
      props: { result: 'meltdown', score: 12, survivedSeconds: 90 },
    })

    expect(wrapper.find('.end-status').text()).toBe('Server ausgefallen')
    expect(wrapper.find('.end-status').classes()).toContain('lose')
    expect(wrapper.find('.end-score').text()).toBe('12')
    expect(wrapper.text()).toContain('90s')
  })

  it('zeigt Sieg bei victory', () => {
    const wrapper = mount(GameOver, {
      props: { result: 'victory', score: 500, survivedSeconds: 200 },
    })

    expect(wrapper.find('.end-status').text()).toBe('Mission erfüllt')
    expect(wrapper.find('.end-status').classes()).toContain('win')
  })

  it('emittiert restart wenn Neustart geklickt wird', async () => {
    const wrapper = mount(GameOver, {
      props: { result: 'meltdown', showRestart: true },
    })

    await wrapper.find('.restart-btn').trigger('click')
    expect(wrapper.emitted('restart')).toHaveLength(1)
  })

  it('versteckt Neustart-Button ohne showRestart', () => {
    const wrapper = mount(GameOver, {
      props: { result: 'meltdown', showRestart: false },
    })
    expect(wrapper.find('.restart-btn').exists()).toBe(false)
  })
})

describe('GameOver.vue — Popup über dem Bild', () => {
  const props = { result: 'victory', score: 840, survivedSeconds: 120, showRestart: true, showExit: true }

  it('zeigt das Bild vollständig und die Punkte-Karte als Dialog', () => {
    const wrapper = mount(GameOver, { props })
    expect(wrapper.find('.end-bild').attributes('alt')).toMatch(/Zeitung|Sieg/i)
    const karte = wrapper.find('.end-card')
    expect(karte.attributes('role')).toBe('dialog')
    expect(karte.attributes('aria-modal')).toBe('true')
    expect(wrapper.find('.end-bar').exists()).toBe(false)
  })

  it('X blendet die Karte aus und zeigt unten die Leiste mit Pfeil', async () => {
    const wrapper = mount(GameOver, { props })
    await wrapper.find('.end-close').trigger('click')

    expect(wrapper.find('.end-card').exists()).toBe(false)
    expect(wrapper.find('.end-bar').exists()).toBe(true)
    expect(wrapper.find('.end-handle').attributes('aria-label')).toBe('Punkte anzeigen')
  })

  it('Klick neben die Karte blendet sie ebenfalls aus', async () => {
    const wrapper = mount(GameOver, { props })
    await wrapper.find('.end-scrim').trigger('click')
    expect(wrapper.find('.end-card').exists()).toBe(false)
  })

  it('Esc blendet die Karte aus', async () => {
    const wrapper = mount(GameOver, { props, attachTo: document.body })
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.end-card').exists()).toBe(false)
    wrapper.unmount()
  })

  it('der Pfeil unten holt die Karte zurück', async () => {
    const wrapper = mount(GameOver, { props })
    await wrapper.find('.end-close').trigger('click')
    await wrapper.find('.end-handle').trigger('click')

    expect(wrapper.find('.end-card').exists()).toBe(true)
    expect(wrapper.find('.end-bar').exists()).toBe(false)
  })

  it('Leiste: links „Spiel beenden“, Mitte Pfeil, rechts „Neustart“', async () => {
    const wrapper = mount(GameOver, { props })
    await wrapper.find('.end-close').trigger('click')

    const knoepfe = wrapper.findAll('.end-bar button')
    expect(knoepfe.map((b) => b.classes().includes('end-handle'))).toEqual([false, true, false])
    expect(knoepfe[0].text()).toContain('Spiel beenden')
    expect(knoepfe[2].text()).toContain('Neustart')

    await knoepfe[0].trigger('click')
    await knoepfe[2].trigger('click')
    expect(wrapper.emitted('exit')).toHaveLength(1)
    expect(wrapper.emitted('restart')).toHaveLength(1)
  })

  it('auch in der Karte selbst: Spiel beenden und Neustart', async () => {
    const wrapper = mount(GameOver, { props })
    await wrapper.find('.end-card .end-exit').trigger('click')
    await wrapper.find('.end-card .restart-btn').trigger('click')
    expect(wrapper.emitted('exit')).toHaveLength(1)
    expect(wrapper.emitted('restart')).toHaveLength(1)
  })

  it('Beamer (ohne Aktionen): nur der Pfeil in der Leiste', async () => {
    const wrapper = mount(GameOver, { props: { result: 'meltdown', score: 0 } })
    expect(wrapper.find('.end-card .end-actions').exists()).toBe(false)
    await wrapper.find('.end-close').trigger('click')
    expect(wrapper.findAll('.end-bar button')).toHaveLength(1)
  })

  it('Niederlage: eigenes Bild und rote Variante', () => {
    const wrapper = mount(GameOver, { props: { result: 'meltdown', score: 0 } })
    expect(wrapper.find('.end').classes()).toContain('is-lose')
    expect(wrapper.find('.end-bild').attributes('alt')).toMatch(/Nachrichten|Niederlage/i)
  })
})

describe('GameOver.vue — Top 5 aus dem Leaderboard', () => {
  const eintrag = (rank, score, players = ['Anna', 'Ben', 'Cem']) => ({ rank, score, players, result: 'victory' })
  const top = [eintrag(1, 900), eintrag(2, 700), eintrag(3, 600), eintrag(4, 500), eintrag(5, 300)]

  it('zeigt die Top 5 mit Team und Punkten, das eigene Team hervorgehoben', () => {
    const wrapper = mount(GameOver, {
      props: { result: 'victory', score: 600, leaderboard: { rank: 3, total: 9, top } },
    })
    const zeilen = wrapper.findAll('.end-board li')
    expect(zeilen).toHaveLength(5)
    expect(zeilen[0].text()).toContain('900')
    expect(zeilen[0].text()).toContain('Anna · Ben · Cem')
    expect(zeilen[2].classes()).toContain('is-own')
    expect(wrapper.find('.end-board-own').exists()).toBe(false)   // eigener Platz steht schon in der Liste
  })

  it('außerhalb der Top 5: eigener Platz unter der Liste', () => {
    const wrapper = mount(GameOver, {
      props: { result: 'meltdown', score: 10, leaderboard: { rank: 12, total: 30, top } },
    })
    expect(wrapper.findAll('.end-board li.is-own')).toHaveLength(0)
    expect(wrapper.find('.end-board-own').text()).toBe('Euer Platz: 12 von 30')
  })

  it('DEV-Modus: Hinweis, dass die Runde nicht gewertet wurde', () => {
    const wrapper = mount(GameOver, {
      props: { result: 'victory', score: 0, leaderboard: { rank: null, total: 5, top } },
    })
    expect(wrapper.find('.end-board-own').text()).toContain('nicht gewertet')
  })

  it('ohne Leaderboard-Daten kein Abschnitt', () => {
    const wrapper = mount(GameOver, { props: { result: 'victory', score: 1 } })
    expect(wrapper.find('.end-board').exists()).toBe(false)
  })
})

describe('GameOver.vue — DEV-Runde ist erkennbar', () => {
  it('auch ohne gewertete Runden: Abschnitt sichtbar mit deutlichem DEV-Hinweis', () => {
    const wrapper = mount(GameOver, {
      props: { result: 'victory', score: 1200, leaderboard: { rank: null, total: 0, top: [] } },
    })
    expect(wrapper.find('.end-board').exists()).toBe(true)
    expect(wrapper.find('.end-board-dev').text()).toContain('nicht gewertet')
    expect(wrapper.find('.end-board-dev').text()).toContain('Leaderboard')
    expect(wrapper.find('.end-board-empty').text()).toContain('Noch keine gewerteten Runden')
  })

  it('der DEV-Hinweis steht über der Liste, nicht darunter', () => {
    const top = [{ rank: 1, score: 900, players: ['A', 'B', 'C'] }]
    const wrapper = mount(GameOver, {
      props: { result: 'victory', score: 1200, leaderboard: { rank: null, total: 1, top } },
    })
    const html = wrapper.find('.end-board').html()
    expect(html.indexOf('end-board-dev')).toBeGreaterThan(-1)
    expect(html.indexOf('end-board-dev')).toBeLessThan(html.indexOf('<ol'))
  })
})
