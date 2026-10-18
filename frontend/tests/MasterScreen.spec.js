/**
 * MasterScreen.spec.js
 *
 * Aktueller (erreichbarer) Zustand der Komponente:
 * Solange `hasJoined` false ist, wird die Master-Authentifizierung (JOIN SECTION)
 * angezeigt. Der "Verbinden"-Button ist disabled, solange `gameId` leer ist.
 *
 * HINWEIS (bekannter Mangel, bitte separat fixen):
 * Die Auth-Sektion enthält KEIN Input-Feld für die Game-ID → über die UI wird
 * `hasJoined` nie true. Die init/manual-Ansichten sind damit im Frontend noch
 * nicht erreichbar. Diese Spez testet daher den erreichbaren Zustand (Auth).
 */
// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MasterScreen from '../src/components/MasterScreen.vue'

vi.mock('../src/composables/useGameSocket.js', () => import('./mocks/useGameSocket.js'))

describe('MasterScreen.vue', () => {
  it('zeigt anfangs die Master-Authentifizierung', () => {
    const wrapper = mount(MasterScreen)

    expect(wrapper.find('.auth-section').exists()).toBe(true)
    expect(wrapper.find('.section-title').text()).toBe('// MASTER_AUTHENTICATION')
    expect(wrapper.find('.section-subtitle').text()).toContain('Game ID')
  })

  it('deaktiviert "Verbinden", solange keine Game-ID vorliegt', () => {
    const wrapper = mount(MasterScreen)

    const btn = wrapper.find('.btn-connect')
    expect(btn.exists()).toBe(true)
    expect(btn.attributes('disabled')).toBeDefined()
    expect(btn.text()).toBe('Verbinden')
  })
})
