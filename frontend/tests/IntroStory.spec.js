/**
 * IntroStory — Einsatzbesprechung am Beamer vor dem Spielstart.
 * Bilder im Neon-Stil des Spiels + Sprechblasen mit der Story, zum Schluss ein kurzes
 * Tutorial. Erst „Einsatz starten“ meldet start (dann startet das Spiel und die Zeit).
 * Die Sieg-/Niederlage-Bilder kommen im Intro nicht vor.
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import IntroStory, { SLIDES } from '../src/components/IntroStory.vue'
import * as sound from '../src/composables/useSound.js'

vi.mock('../src/composables/useSound.js')

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

  it('letzte Seite: großes Beispiel-Notizblatt, kein Taschenrechner mehr (feat/ohne-taschenrechner)', async () => {
    const w = mountIntro()
    await bisZumEnde(w)
    expect(w.find('.tutorial-note .tn').exists()).toBe(true)
    expect(w.find('.calc-mini').exists()).toBe(false)
    const punkte = w.findAll('.tutorial li').map((li) => li.text())
    expect(punkte).toHaveLength(4)
    expect(punkte.some((p) => /Reihenfolge/.test(p))).toBe(true)
    expect(punkte.join(' ')).not.toMatch(/Taschenrechner/)
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

describe('IntroStory.vue — Funkspruch und Countdown-Töne', () => {
  afterEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  const mitTon = (extra = {}) => mount(IntroStory, { props: { typeSpeed: 0, outroSpeed: 0, sound: true, ...extra } })

  it('spielt zu jeder Folie den passenden Funkspruch', async () => {
    const w = mitTon()
    expect(sound.playVoice).toHaveBeenLastCalledWith('intro-slide-1')
    await weiter(w).trigger('click')
    expect(sound.playVoice).toHaveBeenLastCalledWith('intro-slide-2')
    await w.find('button.intro-skip').trigger('click')
    expect(sound.playVoice).toHaveBeenLastCalledWith(`intro-slide-${SLIDES.length}`)
  })

  it('hält den Funkspruch an, wenn das Intro verschwindet', () => {
    const w = mitTon()
    w.unmount()
    expect(sound.stopVoice).toHaveBeenCalled()
  })

  it('bleibt ohne sound-Angabe stumm', async () => {
    const w = mount(IntroStory, { props: { typeSpeed: 0, outroSpeed: 0 } })
    await weiter(w).trigger('click')
    expect(sound.playVoice).not.toHaveBeenCalled()
    expect(sound.playSfx).not.toHaveBeenCalled()
  })

  it('piept beim Countdown 3, 2, 1 und gibt bei LOS das Startsignal', async () => {
    vi.useFakeTimers()
    const w = mitTon({ outroSpeed: 900 })
    await bisZumEnde(w)
    await w.find('button.intro-start').trigger('click')
    expect(sound.stopVoice).toHaveBeenCalled()   // kein Funkspruch über den Countdown
    for (let i = 0; i < 3; i++) {
      vi.advanceTimersByTime(900)
      await w.vm.$nextTick()
    }
    expect(sound.playSfx.mock.calls.filter(([n]) => n === 'sfx-count')).toHaveLength(3)
    vi.advanceTimersByTime(900)
    await w.vm.$nextTick()
    expect(sound.playSfx).toHaveBeenLastCalledWith('sfx-go')
  })
})

describe('IntroStory.vue — Folien laufen von selbst (auto)', () => {
  afterEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  const auto = (extra = {}) => mount(IntroStory, { props: { typeSpeed: 0, outroSpeed: 0, auto: true, ...extra } })
  const aktuellerText = (w) => w.find('.bubble').text()

  it('geht mit Ton nach dem Funkspruch kurz darauf zur nächsten Folie', async () => {
    vi.useFakeTimers()
    let beiEnde
    sound.playVoice.mockImplementation((name, cb) => { beiEnde = cb; return true })
    const w = auto({ sound: true })
    expect(aktuellerText(w)).toContain(SLIDES[0].text)
    vi.advanceTimersByTime(20000)
    await w.vm.$nextTick()
    expect(aktuellerText(w)).toContain(SLIDES[0].text)   // Spruch läuft noch
    beiEnde()
    vi.advanceTimersByTime(1500)
    await w.vm.$nextTick()
    expect(aktuellerText(w)).toContain(SLIDES[1].text)
  })

  it('ohne Ton blättert es nach der Lesezeit weiter (Länge des Textes)', async () => {
    vi.useFakeTimers()
    const w = auto()
    vi.advanceTimersByTime(2500)
    await w.vm.$nextTick()
    expect(aktuellerText(w)).toContain(SLIDES[0].text)
    vi.advanceTimersByTime(6000)
    await w.vm.$nextTick()
    expect(aktuellerText(w)).toContain(SLIDES[1].text)
  })

  it('bleibt auf der letzten Folie stehen und wartet auf die Spieler', async () => {
    vi.useFakeTimers()
    const w = auto({ bereit: { count: 0, total: 3, all: false } })
    for (let i = 0; i < 40; i++) {   // jede Folie wartet ihre Lesezeit; zwischen den Folien läuft Vue
      await vi.advanceTimersByTimeAsync(7000)
    }
    expect(w.find('button.intro-start').exists()).toBe(true)   // letzte Folie erreicht ...
    expect(w.find('button.intro-start').attributes('disabled')).toBeDefined()   // ... und sie wartet
    expect(w.find('.intro-ready').text()).toContain('0/3')
    expect(w.emitted('start')).toBeUndefined()
  })

  it('manuelles Weiter plant die Automatik neu, es wird keine Folie übersprungen', async () => {
    vi.useFakeTimers()
    const w = auto()
    vi.advanceTimersByTime(4000)
    await w.find('button.intro-next').trigger('click')
    expect(aktuellerText(w)).toContain(SLIDES[1].text)
    vi.advanceTimersByTime(2000)
    await w.vm.$nextTick()
    expect(aktuellerText(w)).toContain(SLIDES[1].text)   // der alte Timer ist weg
  })

  it('ohne auto bleibt alles manuell', async () => {
    vi.useFakeTimers()
    const w = mount(IntroStory, { props: { typeSpeed: 0, outroSpeed: 0 } })
    vi.advanceTimersByTime(60000)
    await w.vm.$nextTick()
    expect(aktuellerText(w)).toContain(SLIDES[0].text)
  })
})

