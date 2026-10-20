/**
 * IntroStory — Einsatzbesprechung am Beamer vor dem Spielstart.
 * Bilder im Neon-Stil des Spiels + Sprechblasen mit der Story, zum Schluss ein kurzes
 * Tutorial. Erst „Einsatz starten“ meldet start (dann startet das Spiel und die Zeit).
 * Die Sieg-/Niederlage-Bilder kommen im Intro nicht vor.
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import IntroStory, { SLIDES } from '../src/components/IntroStory.vue'

const weiter = (w) => w.find('button.intro-next')
const zurueck = (w) => w.find('button.intro-back')

function mountIntro() {
  return mount(IntroStory, { props: { typeSpeed: 0, outroSpeed: 0 } })
}

async function bisZumEnde(w) {
  for (let i = 1; i < SLIDES.length; i++) await weiter(w).trigger('click')
}

describe('IntroStory.vue', () => {
  it('beginnt mit Bild und Sprechblase der ersten Szene', () => {
    const w = mountIntro()
    expect(w.find('.intro-image img, .intro-scene-frame img').exists()).toBe(true)
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

describe('IntroStory.vue – Bilder und letzte Seite (Feedback)', () => {
  it('keine Icon-Bilder mehr: die Szenen sind Ausschnitte des Startbilds, eigene Bilder oder die echten Zettel', () => {
    for (const s of SLIDES) {
      if (s.image) expect(s.image).not.toMatch(/_role/)
    }
    expect(SLIDES.slice(1, 5).every((s) => s.visual === 'scene' || s.visual === 'notes')).toBe(true)
  })

  it('die Notiz-Szene zeigt die drei echten Zettel-Stücke', async () => {
    const w = mountIntro()
    const n = SLIDES.findIndex((s) => s.visual === 'notes')
    for (let i = 0; i < n; i++) await weiter(w).trigger('click')
    expect(w.findAll('.intro-notes .tn')).toHaveLength(3)
  })

  it('letzte Seite: großes Beispiel-Notizblatt und der Taschenrechner', async () => {
    const w = mountIntro()
    await bisZumEnde(w)
    expect(w.find('.tutorial-note .tn').exists()).toBe(true)
    expect(w.find('.calc-mini').exists()).toBe(true)
    const punkte = w.findAll('.tutorial li').map((li) => li.text())
    expect(punkte).toHaveLength(5)
    expect(punkte.some((p) => /Reihenfolge/.test(p))).toBe(true)
    expect(punkte.some((p) => /Taschenrechner/.test(p))).toBe(true)
    expect(punkte.join(' ')).not.toMatch(/Hilfe-Zettel/)
  })
})

describe('IntroStory.vue – Übergang ins Spiel', () => {
  afterEach(() => vi.useRealTimers())

  it('nach „Einsatz starten“: Verbinden, Countdown 3-2-1, LOS – erst dann start', async () => {
    vi.useFakeTimers()
    const w = mount(IntroStory, { props: { typeSpeed: 0, outroSpeed: 900 } })
    await bisZumEnde(w)
    await w.find('button.intro-start').trigger('click')

    const outro = () => w.find('.intro-outro')
    expect(outro().exists()).toBe(true)
    expect(outro().text()).toMatch(/Verbinde/i)
    expect(w.emitted('start')).toBeUndefined()

    const gesehen = []
    for (let i = 0; i < 4; i++) {
      vi.advanceTimersByTime(900)
      await w.vm.$nextTick()
      gesehen.push(w.find('.outro-count').exists() ? w.find('.outro-count').text() : '')
    }
    expect(gesehen).toEqual(['3', '2', '1', 'LOS!'])
    expect(w.emitted('start')).toBeUndefined()

    vi.advanceTimersByTime(900)
    await w.vm.$nextTick()
    expect(w.emitted('start')).toHaveLength(1)
  })

  it('Navigation ist während des Übergangs weg (kein Zurückblättern)', async () => {
    vi.useFakeTimers()
    const w = mount(IntroStory, { props: { typeSpeed: 0, outroSpeed: 900 } })
    await bisZumEnde(w)
    await w.find('button.intro-start').trigger('click')
    expect(w.find('.intro-nav').exists()).toBe(false)
  })
})

describe('IntroStory.vue — wartet auf „Bereit“ der Spieler', () => {
  const bereit = (count, all = count === 3) => ({ count, total: 3, all })

  function mountMitBereit(b) {
    return mount(IntroStory, { props: { typeSpeed: 0, outroSpeed: 0, bereit: b } })
  }

  it('hält die letzte Folie an, solange nicht alle bereit sind', async () => {
    const w = mountMitBereit(bereit(1))
    await bisZumEnde(w)
    expect(w.find('button.intro-start').attributes('disabled')).toBeDefined()
    expect(w.find('.intro-ready').text()).toContain('1/3')
    expect(w.emitted('start')).toBeUndefined()
  })

  it('startet von selbst, sobald auf der letzten Folie alle bereit sind', async () => {
    const w = mountMitBereit(bereit(2))
    await bisZumEnde(w)
    await w.setProps({ bereit: bereit(3) })
    expect(w.emitted('start')).toHaveLength(1)
  })

  it('waren schon vorher alle bereit, gibt der Knopf frei, aber der Host entscheidet', async () => {
    const w = mountMitBereit(bereit(3))
    await bisZumEnde(w)
    expect(w.emitted('start')).toBeUndefined()   // Tutorial bleibt lesbar
    expect(w.find('button.intro-start').attributes('disabled')).toBeUndefined()
    await w.find('button.intro-start').trigger('click')
    expect(w.emitted('start')).toHaveLength(1)
  })

  it('ohne bereit-Angabe bleibt der Knopf frei (Tests, DEV-Modus)', async () => {
    const w = mountIntro()
    await bisZumEnde(w)
    expect(w.find('button.intro-start').attributes('disabled')).toBeUndefined()
    expect(w.find('.intro-ready').exists()).toBe(false)
  })
})

