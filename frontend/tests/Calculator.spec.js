/**
 * Calculator — Taschenrechner für alle Rollen im Spiel.
 * Zu: liegt als kleine Grafik schräg und halb im Bild am rechten Rand (wie auf dem Tisch),
 * Tasten sind dann nicht bedienbar. Klick: wird hereingezogen (CSS-Übergang), die Aufgabe
 * rückt zur Seite. „Wegschieben“ oder Esc: zurück an den Rand.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Calculator from '../src/components/Calculator.vue'

const griff = (w) => w.find('button.calc-handle')
const taste = (w, t) => w.findAll('button.calc-key').find((b) => b.text() === t)
async function tippe(w, ...tasten) {
  for (const t of tasten) await taste(w, t).trigger('click')
}

describe('Calculator.vue', () => {
  it('liegt anfangs halb im Bild: Grafik sichtbar, Tasten gesperrt', () => {
    const w = mount(Calculator)
    expect(w.find('.calc').classes()).not.toContain('is-open')
    expect(w.find('.calc-panel').exists()).toBe(true)              // die Grafik ist immer da
    expect(w.find('.calc-body').attributes('inert')).toBeDefined()  // aber nicht bedienbar
    expect(griff(w).attributes('aria-expanded')).toBe('false')
  })

  it('Klick zieht ihn herein und gibt die Tasten frei', async () => {
    const w = mount(Calculator)
    await griff(w).trigger('click')
    expect(w.find('.calc').classes()).toContain('is-open')
    expect(w.find('.calc-body').attributes('inert')).toBeUndefined()
    expect(griff(w).exists()).toBe(false)
    expect(w.emitted('update:open')[0]).toEqual([true])
  })

  it('„Wegschieben“ legt ihn zurück an den Rand', async () => {
    const w = mount(Calculator, { props: { open: true } })
    await w.find('button.calc-close').trigger('click')
    expect(w.find('.calc').classes()).not.toContain('is-open')
    expect(w.emitted('update:open').at(-1)).toEqual([false])
  })

  it('rechnet 64 + 2 + 1 = 67 und merkt sich die Rechnung', async () => {
    const w = mount(Calculator, { props: { open: true } })
    await tippe(w, '6', '4', '+', '2', '+', '1')
    expect(w.find('.calc-expr').text()).toBe('64 + 2 + 1')
    await tippe(w, '=')
    expect(w.find('.calc-result').text()).toBe('67')
    expect(w.find('.calc-history').text()).toContain('64 + 2 + 1 = 67')
  })

  it('rechnet mit dem Ergebnis weiter', async () => {
    const w = mount(Calculator, { props: { open: true } })
    await tippe(w, '9', '0', '−', '6', '5', '=', '−', '3', '=')
    expect(w.find('.calc-result').text()).toBe('22')
  })

  it('C löscht alles, ⌫ das letzte Zeichen', async () => {
    const w = mount(Calculator, { props: { open: true } })
    await tippe(w, '1', '2', '⌫')
    expect(w.find('.calc-expr').text()).toBe('1')
    await tippe(w, 'C')
    expect(w.find('.calc-expr').text()).toBe('')
  })

  it('zeigt „Fehler“ statt eines Ergebnisses bei Division durch 0', async () => {
    const w = mount(Calculator, { props: { open: true } })
    await tippe(w, '5', '÷', '0', '=')
    expect(w.find('.calc-result').text()).toBe('Fehler')
  })

  it('nimmt Tastatur-Eingaben an, solange der Rechner den Fokus hat', async () => {
    const w = mount(Calculator, { props: { open: true } })
    const panel = w.find('.calc-panel')
    for (const key of ['3', '2', '*', '2', 'Enter']) await panel.trigger('keydown', { key })
    expect(w.find('.calc-result').text()).toBe('64')
    await panel.trigger('keydown', { key: 'Escape' })
    expect(w.emitted('update:open').at(-1)).toEqual([false])
  })

  it('zwei Operatoren hintereinander: der zweite ersetzt den ersten', async () => {
    const w = mount(Calculator, { props: { open: true } })
    await tippe(w, '8', '+', '×', '2', '=')
    expect(w.find('.calc-result').text()).toBe('16')
  })
})
