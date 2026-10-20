/**
 * LeaderboardScreen — alle Runden, höchste Punktzahl zuerst, 20 pro Seite.
 * fetch ist gestubbt: GET /leaderboard/?page=N&per_page=20
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import LeaderboardScreen from '../src/components/LeaderboardScreen.vue'

const PER_PAGE = 20

function antwort(page, total) {
  const pages = Math.max(1, Math.ceil(total / PER_PAGE))
  const start = (page - 1) * PER_PAGE
  const entries = Array.from({ length: Math.max(0, Math.min(PER_PAGE, total - start)) }, (_, i) => ({
    rank: start + i + 1,
    players: ['Anna', 'Ben', `Cem${start + i + 1}`],
    score: 1000 - (start + i),
    result: (start + i) % 2 ? 'meltdown' : 'victory',
    survived_seconds: 125,
    created_at: '2026-10-19T12:30:00+00:00',
  }))
  return { entries, page, per_page: PER_PAGE, total, pages }
}

function fetchMit(total) {
  return vi.fn(async (url) => {
    const page = Number(new URL(url).searchParams.get('page'))
    return { ok: true, json: async () => antwort(page, total) }
  })
}

describe('LeaderboardScreen.vue', () => {
  beforeEach(() => {
    vi.stubGlobal('location', { protocol: 'http:', hostname: 'localhost' })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('lädt Seite 1 und zeigt 20 Zeilen, höchste Punktzahl zuerst', async () => {
    const f = fetchMit(45)
    vi.stubGlobal('fetch', f)
    const wrapper = mount(LeaderboardScreen)
    await flushPromises()

    expect(f).toHaveBeenCalledWith('http://localhost:8000/leaderboard/?page=1&per_page=20')
    const zeilen = wrapper.findAll('tbody tr')
    expect(zeilen).toHaveLength(20)
    expect(zeilen[0].text()).toContain('1000')
    expect(zeilen[0].text()).toContain('Anna · Ben · Cem1')
    expect(zeilen[0].find('.lb-rank').text()).toBe('1')
    expect(wrapper.find('.lb-range').text()).toBe('Runden 1–20 von 45')
  })

  it('Zeilen erscheinen gestaffelt (Index als --i für die Verzögerung)', async () => {
    vi.stubGlobal('fetch', fetchMit(3))
    const wrapper = mount(LeaderboardScreen)
    await flushPromises()

    const zeilen = wrapper.findAll('tbody tr.lb-row')
    expect(zeilen).toHaveLength(3)
    expect(zeilen.map((z) => z.attributes('style'))).toEqual(['--i: 0;', '--i: 1;', '--i: 2;'])
  })

  it('zeigt Ergebnis, Spielzeit und Datum lesbar an', async () => {
    vi.stubGlobal('fetch', fetchMit(2))
    const wrapper = mount(LeaderboardScreen)
    await flushPromises()

    const [sieg, niederlage] = wrapper.findAll('tbody tr')
    expect(sieg.text()).toContain('Sieg')
    expect(niederlage.text()).toContain('Niederlage')
    expect(sieg.text()).toContain('2:05')
    expect(sieg.text()).toMatch(/19\.10\.2026/)
  })

  it('Seitenzahlen: Klick auf 2 lädt Plätze 21–40', async () => {
    const f = fetchMit(45)
    vi.stubGlobal('fetch', f)
    const wrapper = mount(LeaderboardScreen)
    await flushPromises()

    const seiten = wrapper.findAll('.lb-page')
    expect(seiten.map((b) => b.text())).toEqual(['1', '2', '3'])
    expect(seiten[0].attributes('aria-current')).toBe('page')

    await seiten[1].trigger('click')
    await flushPromises()
    expect(f).toHaveBeenLastCalledWith('http://localhost:8000/leaderboard/?page=2&per_page=20')
    expect(wrapper.find('tbody tr .lb-rank').text()).toBe('21')
    expect(wrapper.find('.lb-page[aria-current="page"]').text()).toBe('2')
  })

  it('Pfeile: zurück auf Seite 1 gesperrt, weiter auf der letzten Seite gesperrt', async () => {
    vi.stubGlobal('fetch', fetchMit(45))
    const wrapper = mount(LeaderboardScreen)
    await flushPromises()

    expect(wrapper.find('.lb-prev').attributes('disabled')).toBeDefined()
    await wrapper.find('.lb-next').trigger('click')
    await flushPromises()
    await wrapper.find('.lb-next').trigger('click')
    await flushPromises()
    expect(wrapper.find('.lb-page[aria-current="page"]').text()).toBe('3')
    expect(wrapper.find('.lb-next').attributes('disabled')).toBeDefined()
    expect(wrapper.findAll('tbody tr')).toHaveLength(5)
  })

  it('viele Seiten: Auslassungspunkte statt aller Zahlen', async () => {
    vi.stubGlobal('fetch', fetchMit(20 * 12))
    const wrapper = mount(LeaderboardScreen)
    await flushPromises()

    const items = wrapper.findAll('.lb-pages li').map((li) => li.text())
    expect(items).toEqual(['1', '2', '…', '12'])
  })

  it('ohne Runden: freundlicher Leerzustand, keine Seitennavigation', async () => {
    vi.stubGlobal('fetch', fetchMit(0))
    const wrapper = mount(LeaderboardScreen)
    await flushPromises()

    expect(wrapper.find('.lb-empty').text()).toContain('Noch keine Runden')
    expect(wrapper.find('.lb-pager').exists()).toBe(false)
  })

  it('Fehler beim Laden: Meldung und „Erneut versuchen“', async () => {
    const f = vi.fn().mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValue({ ok: true, json: async () => antwort(1, 3) })
    vi.stubGlobal('fetch', f)
    const wrapper = mount(LeaderboardScreen)
    await flushPromises()

    expect(wrapper.find('.lb-error').exists()).toBe(true)
    await wrapper.find('.lb-retry').trigger('click')
    await flushPromises()
    expect(wrapper.findAll('tbody tr')).toHaveLength(3)
  })

  it('„Zurück“ führt ins Hauptmenü', async () => {
    vi.stubGlobal('fetch', fetchMit(1))
    const wrapper = mount(LeaderboardScreen)
    await wrapper.find('.lb-back').trigger('click')
    expect(wrapper.emitted('back')).toHaveLength(1)
  })
})
