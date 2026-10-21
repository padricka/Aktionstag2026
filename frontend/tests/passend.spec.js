/**
 * passend — Verkleinern statt Abschneiden oder Scrollen (fix/alles-passt).
 * skalaBreite: ein Zettel mit fester natürlicher Breite passt in die Spalte.
 * skalaFlaeche: ein Inhalt, dessen Höhe von der Breite abhängt, passt ganz in eine Fläche.
 */
import { describe, it, expect } from 'vitest'
import { skalaBreite, skalaFlaeche } from '../src/utils/passend.js'

describe('skalaBreite', () => {
  it('passt es, bleibt alles bei 1', () => {
    expect(skalaBreite(400, 520)).toBe(1)
  })
  it('zu breit: genau so weit verkleinern, dass es passt – ohne Untergrenze', () => {
    expect(skalaBreite(600, 300)).toBe(0.5)
    expect(skalaBreite(1000, 100)).toBeCloseTo(0.1)
  })
  it('ohne Messwerte (z. B. noch nicht sichtbar) nichts ändern', () => {
    expect(skalaBreite(0, 300)).toBe(1)
    expect(skalaBreite(500, 0)).toBe(1)
  })
})

describe('skalaFlaeche', () => {
  // Inhalt wie ein Fließtext: Fläche 600 000 px², schmaler = höher
  const hoeheBei = (breite) => 600000 / breite

  it('passt es, bleibt alles bei 1 und volle Breite', () => {
    expect(skalaFlaeche(1000, 800, hoeheBei)).toEqual({ skala: 1, breite: 1000 })
  })
  it('zu hoch: verkleinert, bis die Höhe passt; die Breite füllt danach wieder die Fläche', () => {
    const { skala, breite } = skalaFlaeche(800, 400, hoeheBei)
    expect(skala).toBeLessThan(1)
    expect(breite * skala).toBeCloseTo(800, 0)              // füllt die Breite
    expect(hoeheBei(breite) * skala).toBeLessThanOrEqual(400.5)   // passt in die Höhe
  })
  it('ohne Messwerte nichts ändern', () => {
    expect(skalaFlaeche(0, 400, hoeheBei)).toEqual({ skala: 1, breite: 0 })
    expect(skalaFlaeche(800, 0, hoeheBei)).toEqual({ skala: 1, breite: 800 })
  })
})
