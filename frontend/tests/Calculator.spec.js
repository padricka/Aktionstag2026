/**
 * Calculator — Taschenrechner am rechten Rand, für alle Rollen im Spiel.
 * Zu: nur ein Griff am Rand. Auf: schmale Leiste rechts (die Aufgabe rückt zur Seite).
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
  it('ist anfangs zu und öffnet sich über den Griff', async () => {
    const w = mount(Calculator)
    expect(w.find('.calc-panel').exists()).toBe(false)
    expect(griff(w).attributes('aria-expanded')).toBe('false')

    await griff(w).trigger('click')
    expect(w.find('.calc-panel').exists()).toBe(true)
    expect(griff(w).attributes('aria-expanded')).toBe('true')
    expect(w.emitted('update:open')[0]).toEqual([true])
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
