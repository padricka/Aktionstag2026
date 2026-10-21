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

describe('useGameSocket – Wiederverbinden', () => {
  beforeEach(() => {
    FakeWebSocket.instances = []
    vi.stubGlobal('WebSocket', FakeWebSocket)
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('verbindet nach einem Abbruch von selbst neu und meldet sich erneut an (onOpen)', async () => {
    const onOpen = vi.fn()
    const { connect, isConnected, reconnecting } = useGameSocket({ onMessage: vi.fn() })
    connect('ws://x/ws/game/abcd/', vi.fn(), onOpen)
    await Promise.resolve()
    expect(isConnected.value).toBe(true)

    FakeWebSocket.instances[0].close()                 // Server/WLAN weg
    expect(isConnected.value).toBe(false)
    expect(reconnecting.value).toBe(true)

    vi.advanceTimersByTime(1000)
    await Promise.resolve()
    expect(FakeWebSocket.instances).toHaveLength(2)
    expect(FakeWebSocket.instances[1].url).toBe('ws://x/ws/game/abcd/')
    expect(onOpen).toHaveBeenCalledTimes(2)
    expect(isConnected.value).toBe(true)
    expect(reconnecting.value).toBe(false)
  })

  it('wartet bei wiederholten Abbrüchen länger (1 s, 2 s, …, höchstens 5 s)', async () => {
    const { connect } = useGameSocket({ onMessage: vi.fn() })
    connect('ws://x/', vi.fn(), vi.fn())
    await Promise.resolve()
    FakeWebSocket.instances[0].close()

    // Server bleibt weg: neue Verbindungen schließen sich sofort wieder
    vi.advanceTimersByTime(1000)
    FakeWebSocket.instances[1].readyState = FakeWebSocket.CLOSED
    FakeWebSocket.instances[1].onclose?.()
    vi.advanceTimersByTime(1999)
    expect(FakeWebSocket.instances).toHaveLength(2)
    vi.advanceTimersByTime(1)
    expect(FakeWebSocket.instances).toHaveLength(3)
  })

  it('nach disconnect() wird nicht neu verbunden', async () => {
    const { connect, disconnect, reconnecting } = useGameSocket({ onMessage: vi.fn() })
    connect('ws://x/', vi.fn(), vi.fn())
    await Promise.resolve()
    disconnect()
    vi.advanceTimersByTime(10000)
    expect(FakeWebSocket.instances).toHaveLength(1)
    expect(reconnecting.value).toBe(false)
  })
})
