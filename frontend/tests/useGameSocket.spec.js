/**
 * useGameSocket — Outgoing nutzt { event, payload } laut JSON_Vertrag.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useGameSocket } from '../src/composables/useGameSocket.js'

class FakeWebSocket {
  static OPEN = 1
  static CONNECTING = 0
  static CLOSED = 3

  constructor(url) {
    this.url = url
    this.readyState = FakeWebSocket.CONNECTING
    this.sent = []
    FakeWebSocket.instances.push(this)
    queueMicrotask(() => {
      this.readyState = FakeWebSocket.OPEN
      this.onopen?.()
    })
  }

  send(data) {
    this.sent.push(data)
  }

  close() {
    this.readyState = FakeWebSocket.CLOSED
    this.onclose?.()
  }
}
FakeWebSocket.instances = []

describe('useGameSocket', () => {
  beforeEach(() => {
    FakeWebSocket.instances = []
    vi.stubGlobal('WebSocket', FakeWebSocket)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('sendet sendEvent als { event, payload }', async () => {
    const onMessage = vi.fn()
    const { connect, sendEvent } = useGameSocket({
      url: 'ws://localhost/ws/game/x/',
      onMessage,
    })

    connect()
    await Promise.resolve()

    sendEvent('player_register', { player_name: 'Pat' })

    const ws = FakeWebSocket.instances[0]
    expect(ws.sent).toHaveLength(1)
    expect(JSON.parse(ws.sent[0])).toEqual({
      event: 'player_register',
      payload: { player_name: 'Pat' },
    })
  })

  it('reicht eingehende Nachrichten an onMessage weiter', async () => {
    const onMessage = vi.fn()
    const { connect } = useGameSocket({
      url: 'ws://localhost/ws/game/x/',
      onMessage,
    })

    connect()
    await Promise.resolve()

    const ws = FakeWebSocket.instances[0]
    ws.onmessage({
      data: JSON.stringify({ event: 'lobby_update', payload: { players: [] } }),
    })

    expect(onMessage).toHaveBeenCalledWith({
      event: 'lobby_update',
      payload: { players: [] },
    })
  })

  it('reiht Nachrichten ein, die vor open gesendet werden', async () => {
    class SlowWS extends FakeWebSocket {
      constructor(url) {
        super(url)
        this.readyState = FakeWebSocket.CONNECTING
        // open nicht sofort
      }
      openNow() {
        this.readyState = FakeWebSocket.OPEN
        this.onopen?.()
      }
    }
    SlowWS.instances = FakeWebSocket.instances
    vi.stubGlobal('WebSocket', SlowWS)

    const { connect, sendEvent } = useGameSocket({ url: 'ws://localhost/ws/game/x/' })
    connect()
    sendEvent('host_register', {})

    const ws = SlowWS.instances[0]
    expect(ws.sent).toHaveLength(0)

    ws.openNow()
    expect(ws.sent).toHaveLength(1)
    expect(JSON.parse(ws.sent[0]).event).toBe('host_register')
  })
})
