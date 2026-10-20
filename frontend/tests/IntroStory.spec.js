/**
 * IntroStory — Einsatzbesprechung am Beamer vor dem Spielstart.
 * Bilder im Neon-Stil des Spiels + Sprechblasen mit der Story, zum Schluss ein kurzes
 * Tutorial. Erst „Einsatz starten“ meldet start (dann startet das Spiel und die Zeit).
 * Die Sieg-/Niederlage-Bilder kommen im Intro nicht vor.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import IntroStory, { SLIDES } from '../src/components/IntroStory.vue'

const weiter = (w) => w.find('button.intro-next')
const zurueck = (w) => w.find('button.intro-back')

function mountIntro() {
  return mount(IntroStory, { props: { typeSpeed: 0 } })
}

async function bisZumEnde(w) {
  for (let i = 1; i < SLIDES.length; i++) await weiter(w).trigger('click')
}

describe('IntroStory.vue', () => {
  it('beginnt mit Bild und Sprechblase der ersten Szene', () => {
    const w = mountIntro()
    expect(w.find('.intro-image img').exists()).toBe(true)
    expect(w.find('.bubble').text()).toContain(SLIDES[0].text)
    expect(w.find('.bubble-speaker').text()).toContain(SLIDES[0].speaker)
    expect(w.findAll('.intro-dot')).toHaveLength(SLIDES.length)
  })

  it('erzählt eine Geschichte in mehreren Szenen und endet mit dem Tutorial', () => {
    expect(SLIDES.length).toBeGreaterThanOrEqual(5)
    expect(SLIDES.at(-1).tutorial?.length).toBeGreaterThanOrEqual(4)
  })

  it('nutzt nicht die Bilder vom Gewinnen oder Verlieren', () => {
    for (const s of SLIDES) {
      if (s.image) expect(s.image).not.toMatch(/win-screen|game-over/)
    }
  })

  it('Weiter und Zurück blättern durch die Szenen', async () => {
    const w = mountIntro()
    expect(zurueck(w).attributes('disabled')).toBeDefined()
    await weiter(w).trigger('click')
    expect(w.find('.bubble').text()).toContain(SLIDES[1].text)
    expect(w.findAll('.intro-dot')[1].classes()).toContain('is-active')
    await zurueck(w).trigger('click')
    expect(w.find('.bubble').text()).toContain(SLIDES[0].text)
  })

  it('Pfeiltaste rechts blättert weiter', async () => {
    const w = mountIntro()
    await w.find('.intro').trigger('keydown', { key: 'ArrowRight' })
    expect(w.find('.bubble').text()).toContain(SLIDES[1].text)
  })

  it('am Ende: Tutorial und „Einsatz starten“ meldet start', async () => {
    const w = mountIntro()
    expect(w.emitted('start')).toBeUndefined()
    await bisZumEnde(w)
    expect(w.findAll('.tutorial li')).toHaveLength(SLIDES.at(-1).tutorial.length)
    const los = w.find('button.intro-start')
    expect(los.text()).toMatch(/Einsatz starten/)
    await los.trigger('click')
    expect(w.emitted('start')).toHaveLength(1)
  })

  it('„Intro überspringen“ springt zum Tutorial, startet aber nicht', async () => {
    const w = mountIntro()
    await w.find('button.intro-skip').trigger('click')
    expect(w.find('.tutorial').exists()).toBe(true)
    expect(w.emitted('start')).toBeUndefined()
  })

  it('nach dem Start sperrt der Knopf (kein doppelter Start)', async () => {
    const w = mountIntro()
    await bisZumEnde(w)
    await w.find('button.intro-start').trigger('click')
    await w.find('button.intro-start').trigger('click')
    expect(w.emitted('start')).toHaveLength(1)
  })
})
