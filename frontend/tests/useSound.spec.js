/**
 * useSound — Funkspruch, Ambience und Effekte, gesteuert über die Einstellungen
 * (localStorage "drv_game_settings"). Audio ist gestubbt, es kommt kein echter Ton heraus.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

class FakeAudio {
  static instances = []
  constructor(src) {
    this.src = src
    this.volume = 1
    this.loop = false
    this.paused = true
    FakeAudio.instances.push(this)
  }
  play() {
    this.paused = false
    return FakeAudio.playResult()
  }
  pause() { this.paused = true }
  addEventListener(type, handler) { (this.handlers ??= {})[type] = handler }
  finish() { this.handlers?.ended?.() }
  static playResult() { return Promise.resolve() }
}

const spielt = (name) => FakeAudio.instances.filter((a) => a.src.endsWith(`/sound/${name}.mp3`))

async function frischesModul(einstellungen) {
  localStorage.clear()
  if (einstellungen) localStorage.setItem('drv_game_settings', JSON.stringify(einstellungen))
  vi.resetModules()
  return import('../src/composables/useSound.js')
}

describe('useSound', () => {
  beforeEach(() => {
    FakeAudio.instances = []
    FakeAudio.playResult = () => Promise.resolve()
    vi.stubGlobal('Audio', FakeAudio)
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  describe('Effekte', () => {
    it('spielt die Datei mit der Hauptlautstärke (Standard 80 %)', async () => {
      const { playSfx } = await frischesModul()
      playSfx('sfx-error')
      const [a] = spielt('sfx-error')
      expect(a.paused).toBe(false)
      expect(a.volume).toBeCloseTo(0.8)
    })

    it('bleibt stumm, wenn Soundeffekte aus sind', async () => {
      const { playSfx } = await frischesModul({ sfxEnabled: false })
      playSfx('sfx-error')
      expect(FakeAudio.instances).toHaveLength(0)
    })

    it('liest die Einstellungen bei jedem Aufruf neu', async () => {
      const { playSfx } = await frischesModul({ masterVolume: 50 })
      playSfx('sfx-solved')
      localStorage.setItem('drv_game_settings', JSON.stringify({ masterVolume: 20 }))
      playSfx('sfx-solved')
      const [erster, zweiter] = spielt('sfx-solved')
      expect(erster.volume).toBeCloseTo(0.5)
      expect(zweiter.volume).toBeCloseTo(0.2)
    })

    it('wirft nicht, wenn der Browser das Abspielen blockiert', async () => {
      FakeAudio.playResult = () => Promise.reject(new Error('NotAllowedError'))
      const { playSfx } = await frischesModul()
      expect(() => playSfx('sfx-go')).not.toThrow()
      await vi.advanceTimersByTimeAsync(0)
    })

    it('übersteht kaputte Einstellungen im Speicher', async () => {
      localStorage.setItem('drv_game_settings', '{kaputt')
      vi.resetModules()
      const { playSfx } = await import('../src/composables/useSound.js')
      playSfx('sfx-hint')
      expect(spielt('sfx-hint')[0].volume).toBeCloseTo(0.8)
    })
  })

  describe('Funkspruch', () => {
    it('spielt immer nur einen Spruch: der neue stoppt den alten', async () => {
      const { playVoice } = await frischesModul()
      playVoice('intro-slide-1')
      playVoice('intro-slide-2')
      expect(spielt('intro-slide-1')[0].paused).toBe(true)
      expect(spielt('intro-slide-2')[0].paused).toBe(false)
    })

    it('stopVoice hält den laufenden Spruch an', async () => {
      const { playVoice, stopVoice } = await frischesModul()
      playVoice('intro-slide-3')
      stopVoice()
      expect(spielt('intro-slide-3')[0].paused).toBe(true)
    })

    it('bleibt stumm, wenn die Stimme aus ist, und sagt das dem Aufrufer', async () => {
      const { playVoice } = await frischesModul({ voiceEnabled: false })
      const beiEnde = vi.fn()
      expect(playVoice('intro-slide-1', beiEnde)).toBe(false)
      expect(FakeAudio.instances).toHaveLength(0)
      expect(beiEnde).not.toHaveBeenCalled()
    })

    it('meldet das Ende des Spruchs zurück', async () => {
      const { playVoice } = await frischesModul()
      const beiEnde = vi.fn()
      expect(playVoice('intro-slide-1', beiEnde)).toBe(true)
      expect(beiEnde).not.toHaveBeenCalled()
      spielt('intro-slide-1')[0].finish()
      expect(beiEnde).toHaveBeenCalledTimes(1)
    })

    it('meldet das Ende auch, wenn der Browser den Ton blockiert', async () => {
      FakeAudio.playResult = () => Promise.reject(new Error('NotAllowedError'))
      const { playVoice } = await frischesModul()
      const beiEnde = vi.fn()
      playVoice('intro-slide-1', beiEnde)
      await vi.advanceTimersByTimeAsync(0)
      expect(beiEnde).toHaveBeenCalledTimes(1)
    })

    it('ein gestoppter Spruch meldet kein Ende mehr', async () => {
      const { playVoice } = await frischesModul()
      const erstes = vi.fn()
      playVoice('intro-slide-1', erstes)
      playVoice('intro-slide-2')
      spielt('intro-slide-1')[0].finish()
      expect(erstes).not.toHaveBeenCalled()
    })
  })

  describe('Ambience', () => {
    it('läuft als Schleife und blendet bis Haupt- mal Musiklautstärke auf', async () => {
      const { startBed } = await frischesModul({ masterVolume: 80, musicVolume: 50 })
      startBed()
      const [bed] = spielt('bed-serverraum')
      expect(bed.loop).toBe(true)
      await vi.advanceTimersByTimeAsync(3000)
      expect(bed.volume).toBeCloseTo(0.4)
    })

    it('startet nicht doppelt', async () => {
      const { startBed } = await frischesModul()
      startBed()
      startBed()
      expect(spielt('bed-serverraum')).toHaveLength(1)
    })

    it('bleibt aus, wenn die Hintergrundmusik aus ist', async () => {
      const { startBed } = await frischesModul({ musicEnabled: false })
      startBed()
      expect(FakeAudio.instances).toHaveLength(0)
    })

    it('Intro-Stufe ist leiser als das Spiel', async () => {
      const { startBed, setBedLevel } = await frischesModul({ masterVolume: 100, musicVolume: 100 })
      startBed(0.4)
      await vi.advanceTimersByTimeAsync(3000)
      const [bed] = spielt('bed-serverraum')
      expect(bed.volume).toBeCloseTo(0.4)
      setBedLevel(1)
      await vi.advanceTimersByTimeAsync(3000)
      expect(bed.volume).toBeCloseTo(1)
    })

    it('stopBed blendet aus und hält an', async () => {
      const { startBed, stopBed } = await frischesModul()
      startBed()
      await vi.advanceTimersByTimeAsync(3000)
      stopBed()
      await vi.advanceTimersByTimeAsync(3000)
      const [bed] = spielt('bed-serverraum')
      expect(bed.paused).toBe(true)
    })

    it('nach dem Stoppen lässt sich die Ambience neu starten', async () => {
      const { startBed, stopBed } = await frischesModul()
      startBed()
      stopBed()
      await vi.advanceTimersByTimeAsync(3000)
      startBed()
      expect(spielt('bed-serverraum').some((a) => !a.paused)).toBe(true)
    })
  })
})
