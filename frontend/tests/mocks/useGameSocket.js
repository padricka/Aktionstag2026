/**
 * Fake-WebSocket für Komponenten-Tests.
 * - connect() ruft onOpen sofort auf (wie eine offene Verbindung)
 * - sendEvent-Aufrufe werden aufgezeichnet
 * - simulateMessage() speist Server-Events ein
 * - setConnected(false/true) simuliert Verbindungsabbruch und Wiederverbinden
 */
import { ref } from 'vue'

let registrierter_on_message_callback = null
let sentEvents = []
let connectCalls = []
const verbunden = ref(true)

export function useGameSocket(options = {}) {
  if (typeof options === 'object' && typeof options?.onMessage === 'function') {
    registrierter_on_message_callback = options.onMessage
  }

  return {
    isConnected: verbunden,
    error: { value: null },
    connect: (url, onMsg, onOpen) => {
      connectCalls.push({ url })
      if (typeof onMsg === 'function') {
        registrierter_on_message_callback = onMsg
      }
      if (typeof onOpen === 'function') {
        onOpen()
      }
    },
    disconnect: () => {},
    sendEvent: (event, payload = {}) => {
      sentEvents.push({ event, payload })
    },
    sendMessage: () => {},
  }
}

export function simulateMessage(payload) {
  if (typeof registrierter_on_message_callback !== 'function') {
    throw new Error('Kein onMessage registriert. Die Vue-Komponente muss useGameSocket({ onMessage }) aufrufen.')
  }
  registrierter_on_message_callback(payload)
}

export function setConnected(wert) {
  verbunden.value = wert
}

export function getSentEvents() {
  return sentEvents
}

export function getConnectCalls() {
  return connectCalls
}

export function resetGameSocketMock() {
  registrierter_on_message_callback = null
  sentEvents = []
  connectCalls = []
  verbunden.value = true
}
