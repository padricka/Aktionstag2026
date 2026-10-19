/**
 * Task3P2 — Rückseite, Aufgabe 3 „Datenrettung" (view.type "binary_puzzle").
 *
 * Die Rückseite hat nur die unteren Stellenwerte 8/4/2/1 und darf die
 * Dezimalwerte nicht selbst ausrechnen: jede Eingabe geht zum Backend,
 * freigeschaltet wird erst über `view.button_unlocked`.
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Task3P2 from '../src/components/tasks/task3/Task3P2.vue'
import SyncButton from '../src/components/SyncButton.vue'

const binaryView = {
  type: 'binary_puzzle',
  binary_codes: ['01001000', '01001111'],
  place_values: [8, 4, 2, 1],
  button_unlocked: false,
}

const knopf = (w) => w.find('button[aria-label="Notknopf"]')
const klappe = (w) => w.find('button[aria-label="Klappe"]')

async function offen(props = {}) {
  const w = mount(Task3P2, { props: { view: { ...binaryView, button_unlocked: true, ...props } } })
  await klappe(w).trigger('click')
  return w
}

afterEach(() => {
  vi.useRealTimers()
})

describe('Task3P2.vue (binary_puzzle) – Anzeige', () => {
  it('zeigt die eigenen Binärzahlen gross', () => {
    const w = mount(Task3P2, { props: { view: binaryView } })

    expect(w.findAll('.code-value').map((el) => el.text())).toEqual(['01001000', '01001111'])
    expect(w.find('.role').text()).toBe('Rückseite')
  })

  it('zeigt die unteren Stellenwerte 8/4/2/1, aber nicht 128/64/32/16', () => {
    const w = mount(Task3P2, { props: { view: binaryView } })

    const werte = w.findAll('.place-value').map((el) => el.text())
    expect(werte).toEqual(['8', '4', '2', '1'])
    // Die oberen Stellenwerte stehen nur beim Leitstand.
    expect(werte).not.toContain('128')
  })

  it('verrät die Lösung nicht und verweist auf den Leitstand', () => {
    const w = mount(Task3P2, { props: { view: binaryView } })

    // 01001000 wäre 72, 01001111 wäre 79 — beides darf nicht auftauchen.
    expect(w.html()).not.toContain('72')
    expect(w.html()).not.toContain('79')
    expect(w.find('.hint').text()).toContain('Leitstand')
    // GAME_DESIGN §4: die oberen Stellenwerte kennt NUR der Leitstand –
    // der Hinweis darf sie deshalb nicht verraten (früher stand hier 128, 64, 32, 16).
    expect(w.find('.hint').text()).not.toMatch(/128|64|32|16/)
  })
})

describe('Task3P2.vue (binary_puzzle) – Rechenhilfe', () => {
  it('Stellenwert-Zeile über den Spalten: ? ? ? ? | 8 4 2 1', () => {
    const w = mount(Task3P2, { props: { view: binaryView } })
    const kopf = w.findAll('.bits-head .bit-cell').map((el) => el.text())
    expect(kopf).toEqual(['?', '?', '?', '?', '8', '4', '2', '1'])
    expect(w.find('.bits-head .is-unknown').attributes('title')).toContain('Leitstand')
  })

  it('jeder Code als Zeile mit 8 einzelnen Bits, Einsen hervorgehoben', () => {
    const w = mount(Task3P2, { props: { view: binaryView } })
    const zeilen = w.findAll('.bits-row')
    expect(zeilen).toHaveLength(2)
    expect(zeilen[0].findAll('.bit-cell.bit').map((el) => el.text()).join('')).toBe('01001000')
    expect(zeilen[0].findAll('.bit.is-one')).toHaveLength(2)
    expect(zeilen[1].findAll('.bit.is-one')).toHaveLength(5)
  })

  it('erklärt das Prinzip in einem Satz und mit Beispiel aus den eigenen Stellenwerten', () => {
    const w = mount(Task3P2, { props: { view: binaryView } })
    expect(w.find('.hint').text()).toMatch(/Addiere die Stellenwerte über jeder 1/)
    expect(w.find('.example').text()).toContain('0000 0101')
    expect(w.find('.example').text()).toContain('4 + 1 = 5')
  })
})

describe('Task3P2.vue – Antwort geht immer zum Backend', () => {
  it('sendet auch eine falsche Antwort, ohne sie lokal zu prüfen', async () => {
    const w = mount(Task3P2, { props: { view: binaryView } })

    await w.find('.input-big').setValue('1 2')
    await w.find('.btn-action').trigger('click')

    expect(w.emitted('solved')).toHaveLength(1)
    expect(w.emitted('solved')[0][0]).toEqual({ player: 'P2', answer: '1 2' })
    expect(w.find('.msg-ok').exists()).toBe(false)
    expect(w.find('.btn-action').text()).toBe('Prüfe …')
  })

  it('sendet die eingegebenen Zahlen unverändert (nur Leerzeichen normalisiert)', async () => {
    const w = mount(Task3P2, { props: { view: binaryView } })

    await w.find('.input-big').setValue('  72   79 ')
    await w.find('.btn-action').trigger('click')

    expect(w.emitted('solved')[0][0]).toEqual({ player: 'P2', answer: '72 79' })
  })

  it('gibt die Eingabe nach serverError wieder frei', async () => {
    const w = mount(Task3P2, { props: { view: binaryView } })

    await w.find('.input-big').setValue('1 2')
    await w.find('.btn-action').trigger('click')
    await w.setProps({ serverError: 'Falsche Eingabe' })

    expect(w.find('.msg-err').text()).toBe('Falsche Eingabe')
    expect(w.find('.input-big').element.value).toBe('')

    await w.find('.input-big').setValue('65 66')
    await w.find('.btn-action').trigger('click')
    expect(w.emitted('solved').at(-1)[0]).toEqual({ player: 'P2', answer: '65 66' })
  })

  it('zeigt nach button_unlocked den akzeptierten Zustand', async () => {
    const w = mount(Task3P2, { props: { view: binaryView } })
    await w.setProps({ view: { ...binaryView, button_unlocked: true } })

    expect(w.find('.msg-ok').text()).toMatch(/akzeptiert/i)
    expect(w.find('.btn-action').text()).toBe('Akzeptiert')
  })
})

describe('Task3P2.vue – Sync-Knopf', () => {
  it('erscheint erst, wenn der Server freischaltet', async () => {
    const w = mount(Task3P2, { props: { view: binaryView } })

    expect(knopf(w).exists()).toBe(false)
    expect(w.find('.sync-locked').exists()).toBe(true)

    await w.setProps({ view: { ...binaryView, button_unlocked: true } })

    expect(knopf(w).exists()).toBe(true)
    expect(w.find('.sync-locked').exists()).toBe(false)
  })

  it('sendet nach Klappe und Drücken sync_button', async () => {
    const w = mount(Task3P2, {
      props: { view: { ...binaryView, button_unlocked: true } },
    })

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
