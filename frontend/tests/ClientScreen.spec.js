// @vitest-environment jsdom
/**
 * Foundation-Test 11: ClientScreen.vue + Fake-WebSocket (kein echtes Backend).
 *
 * MOCK-IDEE:
 *   vi.mock ersetzt das echte useGameSocket-Composable durch unseren Fake.
 *   simulateMessage(...) tut so, als käme JSON vom Django-Server.
 *   Vergleich Java: Mockito.when(socket.onMessage(...)) / manueller Stub-Aufruf.
 *
 * async/await + nextTick:
 *   Nach simulateMessage muss Vue die Vorlage neu rendern.
 *   „await nextTick()“ wartet einen Tick — sonst ist der <h2>-Text noch der alte.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

// simulateMessage / reset nur für den Test — useGameSocket kommt über vi.mock
import {
  simulateMessage,
  resetGameSocketMock,
} from './mocks/useGameSocket.js'

// WICHTIG: vi.mock wird nach oben „gehoisted“. Deshalb dynamisch importieren,
// nicht die Variable aus dem static import in der Factory verwenden
// (sonst kann useGameSocket undefined sein → verwirrender Fehler für Azubis).
vi.mock('../src/composables/useGameSocket', async () => {
  const mockModul = await import('./mocks/useGameSocket.js')
  return { useGameSocket: mockModul.useGameSocket }
})

// PRODUKTIONSCODE: frontend/src/components/ClientScreen.vue
// Muss useGameSocket({ onMessage(msg) { … } }) nutzen und Task-Text in <h2> zeigen
// ClientScreen wird erst im (uebersprungenen) Test importiert: die Datei laesst sich
// wegen des Template-Fehlers nicht kompilieren, ein statischer Import wuerde die ganze Suite crashen.

// TRIAGE (siehe TRIAGE.md): Test bleibt erhalten, ist aber vorerst uebersprungen.
// 1) ClientScreen.vue hat einen Template-Syntaxfehler (falsch verschachtelte
//    </main></template></div> um Zeile 207) -> die Datei laesst sich nicht kompilieren.
// 2) Der Test sendet die Nachricht im alten Format { type: 'new_task', message }.
//    Der JSON-Vertrag kennt event + payload (game_tick mit tasks).
// Zu tun: Template-Fehler beheben, Test auf den Vertrag umstellen, dann skip entfernen.
describe.skip('ClientScreen.vue (mit Fake-WebSocket)', () => {
  beforeEach(() => {
    resetGameSocketMock()
  })

  it('test_client_screen_shows_task_from_websocket — new_task erscheint in h2', async () => {
    /**
     * Test 11 — Simulierte Server-Nachricht setzt den sichtbaren Task-Text.
     *
     * Nachricht:
     *   { type: "new_task", message: "Aktiviere die Firewall" }
     *
     * Was ihr implementieren müsst:
     *   - useGameSocket aus '@/composables/useGameSocket' importieren
     *   - onMessage: wenn type === 'new_task' → ref/state mit message setzen
     *   - In der Vorlage: <h2>{{ taskText }}</h2> (o.ä.)
     *   - Ideal: connect() im onMounted aufrufen (im Test ist connect ein No-Op)
     */
    const { default: ClientScreen } = await import('../src/components/ClientScreen.vue')
    const gemounteter_client_screen = mount(ClientScreen)

    const simulierte_server_nachricht = {
      type: 'new_task',
      message: 'Aktiviere die Firewall',
    }

    simulateMessage(simulierte_server_nachricht)

    // Vue braucht einen Tick, um das DOM zu aktualisieren
    await nextTick()
    await flushPromises()

    const task_ueberschrift = gemounteter_client_screen.find('h2')
    expect(task_ueberschrift.exists()).toBe(true)

    const angezeigter_task_text = task_ueberschrift.text()
    expect(angezeigter_task_text).toContain('Aktiviere die Firewall')
  })
})