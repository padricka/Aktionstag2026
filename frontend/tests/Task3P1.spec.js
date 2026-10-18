/**
 * Task3P1 — Vorderseite, Aufgabe 3 „Datenrettung" (view.type "ascii_puzzle").
 *
 * Kern der Escape-Room-Regel: die Vorderseite hat nur die Tabellenhälfte N–Z.
 * Die Lösung darf deshalb im Browser weder berechnet noch geprüft werden —
 * jede Antwort geht als `solved` an PlayerScreen, das Backend antwortet mit
 * `serverError` oder `view.button_unlocked`.
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3P1 from '../src/components/tasks/task3/Task3P1.vue'
import SyncButton from '../src/components/SyncButton.vue'

const asciiView = {
  type: 'ascii_puzzle',
  ascii_codes: [83, 69, 82, 86, 69, 82],
  ascii_half: { N: 78, O: 79, P: 80, Q: 81, R: 82, S: 83, T: 84, U: 85, V: 86, W: 87, X: 88, Y: 89, Z: 90 },
  button_unlocked: false,
}

const knopf = (w) => w.find('button[aria-label="Notknopf"]')
const klappe = (w) => w.find('button[aria-label="Klappe"]')

async function offen(props = {}) {
  const w = mount(Task3P1, { props: { view: { ...asciiView, button_unlocked: true, ...props } } })
  await klappe(w).trigger('click')
  return w
}

afterEach(() => {
  vi.useRealTimers()
})

describe('Task3P1.vue (ascii_puzzle) – Anzeige', () => {
  it('zeigt die eigenen ASCII-Codes gross', () => {
    const w = mount(Task3P1, { props: { view: asciiView } })

    const werte = w.findAll('.code-value').map((el) => el.text())
    expect(werte).toEqual(['83', '69', '82', '86', '69', '82'])
    expect(w.find('.role').text()).toBe('Vorderseite')
  })

  it('zeigt die eigene Tabellenhälfte N–Z, aber nicht A–M', () => {
    const w = mount(Task3P1, { props: { view: asciiView } })

    const buchstaben = w.findAll('.cell-key').map((el) => el.text())
    expect(buchstaben).toContain('N')
    expect(buchstaben).toContain('Z')
    expect(buchstaben).not.toContain('A')
    expect(buchstaben).not.toContain('M')
    expect(w.findAll('.cell-val').map((el) => el.text())).toContain('90')
  })

  it('verrät die Lösung nicht und verweist auf den Leitstand', () => {
    const w = mount(Task3P1, { props: { view: asciiView } })

    // Aus 83 69 82 86 69 82 würde hier lokal "SERVER" — genau das darf nicht passieren.
    expect(w.html()).not.toContain('SERVER')
    expect(w.find('.hint').text()).toContain('Leitstand')
    expect(w.find('.hint').text()).toMatch(/A–M/)
  })
})

describe('Task3P1.vue – Antwort geht immer zum Backend', () => {
  it('sendet auch eine falsche Antwort, ohne sie lokal zu prüfen', async () => {
    const w = mount(Task3P1, { props: { view: asciiView } })

    await w.find('.input-big').setValue('FALSCH')
    await w.find('.btn-action').trigger('click')

    expect(w.emitted('solved')).toHaveLength(1)
    expect(w.emitted('solved')[0][0]).toEqual({ player: 'P1', answer: 'FALSCH' })
    // Kein Erfolgszustand, kein lokales "richtig":
    expect(w.find('.msg-ok').exists()).toBe(false)
    expect(w.find('.btn-action').text()).toBe('Prüfe …')
  })

  it('nimmt jede Eingabe an, auch wenn sie wie die Lösung aussieht', async () => {
    const w = mount(Task3P1, { props: { view: asciiView } })

    await w.find('.input-big').setValue('SERVER')
    await w.find('.btn-action').trigger('click')

    expect(w.emitted('solved')[0][0]).toEqual({ player: 'P1', answer: 'SERVER' })
  })

  it('gibt die Eingabe nach serverError wieder frei', async () => {
    const w = mount(Task3P1, { props: { view: asciiView } })

    await w.find('.input-big').setValue('FALSCH')
    await w.find('.btn-action').trigger('click')
    await w.setProps({ serverError: 'Falsche Eingabe' })

    expect(w.find('.msg-err').text()).toBe('Falsche Eingabe')
    expect(w.find('.btn-action').attributes('disabled')).toBeDefined()
    expect(w.find('.input-big').element.value).toBe('')

    await w.find('.input-big').setValue('NOCHMAL')
    await w.find('.btn-action').trigger('click')
    expect(w.emitted('solved').at(-1)[0]).toEqual({ player: 'P1', answer: 'NOCHMAL' })
  })

  it('zeigt nach button_unlocked den akzeptierten Zustand', async () => {
    const w = mount(Task3P1, { props: { view: asciiView } })
    await w.setProps({ view: { ...asciiView, button_unlocked: true } })

    expect(w.find('.msg-ok').text()).toMatch(/akzeptiert/i)
    expect(w.find('.btn-action').text()).toBe('Akzeptiert')
  })
})

describe('Task3P1.vue – Sync-Knopf', () => {
  it('erscheint erst, wenn der Server freischaltet', async () => {
    const w = mount(Task3P1, { props: { view: asciiView } })

    expect(knopf(w).exists()).toBe(false)
    expect(w.find('.sync-locked').exists()).toBe(true)

    await w.setProps({ view: { ...asciiView, button_unlocked: true } })

    expect(knopf(w).exists()).toBe(true)
    expect(w.find('.sync-locked').exists()).toBe(false)
  })

  it('senden erst nach Klappe öffnen und Drücken sync_button', async () => {
    const w = mount(Task3P1, {
      props: { view: { ...asciiView, button_unlocked: true } },
    })

    // Klappe noch zu: der Knopf löst nicht aus.
    await knopf(w).trigger('click')
    expect(w.emitted('solved')).toBeUndefined()

    await klappe(w).trigger('click')
    await knopf(w).trigger('click')

    expect(w.emitted('solved')).toHaveLength(1)
    expect(w.emitted('solved')[0][0]).toEqual({ target: 'sync_button' })

    w.unmount()
  })

  it('läuft waiting -> error -> idle, danach ist erneut Drücken möglich', async () => {
    vi.useFakeTimers()
    const w = await offen()

    await knopf(w).trigger('click')
    expect(w.findComponent(SyncButton).props('state')).toBe('waiting')

    vi.advanceTimersByTime(3500)
    await w.vm.$nextTick()
    expect(w.findComponent(SyncButton).props('state')).toBe('error')

    vi.advanceTimersByTime(1200)
    await w.vm.$nextTick()
    expect(w.findComponent(SyncButton).props('state')).toBe('idle')

    await knopf(w).trigger('click')
    expect(w.emitted('solved')).toHaveLength(2)
  })
})
