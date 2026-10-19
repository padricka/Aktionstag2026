/**
 * rechner.js — rechnet die Eingabe des Taschenrechners aus (ohne eval).
 * + − × ÷ mit Punkt-vor-Strich, Komma oder Punkt als Dezimaltrenner.
 */
import { describe, it, expect } from 'vitest'
import { berechne, zeigeZahl } from '../src/utils/rechner.js'

describe('berechne', () => {
  it.each([
    ['64 + 2 + 1', 67],
    ['128+64', 192],
    ['90 − 65', 25],
    ['2 + 3 × 4', 14],
    ['20 ÷ 4 − 1', 4],
    ['7 * 6', 42],
    ['9 / 2', 4.5],
    ['1,5 + 1,5', 3],
    ['0.1 + 0.2', 0.3],
    ['−5 + 8', 3],
    ['42', 42],
  ])('%s = %s', (ausdruck, ergebnis) => {
    expect(berechne(ausdruck)).toBe(ergebnis)
  })

  it.each(['', '5 +', '× 3', '5 ÷ 0', '1,2,3', 'abc', '2 + + 3'])('„%s“ ergibt keinen Wert', (ausdruck) => {
    expect(berechne(ausdruck)).toBeNull()
  })
})

describe('zeigeZahl', () => {
  it('zeigt Dezimalzahlen mit Komma', () => {
    expect(zeigeZahl(4.5)).toBe('4,5')
    expect(zeigeZahl(67)).toBe('67')
  })
})
