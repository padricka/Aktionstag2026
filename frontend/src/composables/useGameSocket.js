import { ref, onUnmounted } from 'vue'

// Wiederverbinden nach einem Abbruch (WLAN-Aussetzer, Server-Neustart):
// 1 s, 2 s, 4 s, danach alle 5 s – bis die Verbindung wieder steht.
const RECONNECT_START_MS = 1000
const RECONNECT_MAX_MS = 5000

export function useGameSocket(optionsOrUrl = {}) {
  const isConnected = ref(false)
  const reconnecting = ref(false)   // Verbindung weg, neuer Versuch läuft
  const error = ref(null)
  let socket = null
  let messageQueue = []
  let letzteVerbindung = null       // { url, onMsg, onOpen } für das Wiederverbinden
  let versuche = 0
  let reconnectTimer = null

  let defaultUrl = typeof optionsOrUrl === 'string' ? optionsOrUrl : optionsOrUrl?.url || null
  let defaultOnMessage = typeof optionsOrUrl === 'object' ? optionsOrUrl?.onMessage : null

  const sendEvent = (event, payload = {}) => {
    const msgString = JSON.stringify({ event, payload })
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(msgString)
    } else if (socket && socket.readyState === WebSocket.CONNECTING) {
      messageQueue.push(msgString)
    } else {
      console.warn('[SOCKET] Verbindung nicht offen. readyState:', socket?.readyState)
    }
  }

  const sendMessage = (payload) => {
    const msgString = typeof payload === 'string' ? payload : JSON.stringify(payload)
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(msgString)
    } else if (socket && socket.readyState === WebSocket.CONNECTING) {
      messageQueue.push(msgString)
    } else {
      console.warn('[SOCKET] Verbindung nicht offen.')
    }
  }

  function stoppeReconnect() {
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  }

  function planeReconnect() {
    stoppeReconnect()
    reconnecting.value = true
    const warte = Math.min(RECONNECT_START_MS * 2 ** versuche, RECONNECT_MAX_MS)
    versuche += 1
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      if (letzteVerbindung) oeffnen(letzteVerbindung)
    }, warte)
  }

  function oeffnen({ url, onMsg, onOpen }) {
    try {
      const ws = new WebSocket(url)
      socket = ws

      ws.onopen = () => {
        console.log(`[SOCKET] Verbunden mit: ${url}`)
        isConnected.value = true
        reconnecting.value = false
        versuche = 0
        error.value = null

        // Vorab eingereihte Nachrichten senden
        while (messageQueue.length > 0) {
          ws.send(messageQueue.shift())
        }

        // auch beim Wiederverbinden: Anmeldung (player_register / host_register) erneut
        if (typeof onOpen === 'function') {
          onOpen()
        }
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (typeof onMsg === 'function') {
            onMsg(data)
          }
        } catch (e) {
          console.error('[SOCKET] Fehler beim Parsen der WebSocket-Nachricht:', e, event.data)
        }
      }

      // Unerwartet geschlossen (nicht über disconnect/connect): neu verbinden
      ws.onclose = () => {
        console.log('[SOCKET] Verbindung geschlossen')
        isConnected.value = false
        if (socket === ws) planeReconnect()
      }

      ws.onerror = (err) => {
        console.error('[SOCKET] WebSocket-Fehler:', err)
        error.value = 'CONNECTION_ERROR'
        isConnected.value = false
      }
    } catch (err) {
      console.error('[SOCKET] Verbindungsaufbau fehlgeschlagen:', err)
      error.value = 'CONNECTION_ERROR'
      isConnected.value = false
      planeReconnect()
    }
  }

  const connect = (urlOrCallback, onMessageCallback, onOpenCallback) => {
    let targetUrl = defaultUrl
    let onMsg = defaultOnMessage
    let onOpen = null

    if (typeof urlOrCallback === 'string') {
      targetUrl = urlOrCallback
      if (typeof onMessageCallback === 'function') {
        onMsg = onMessageCallback
      }
      if (typeof onOpenCallback === 'function') {
        onOpen = onOpenCallback
      }
    } else if (typeof urlOrCallback === 'function') {
      onMsg = urlOrCallback
      if (typeof onMessageCallback === 'function') {
        onOpen = onMessageCallback
      }
    }

    if (!targetUrl) {
      console.error('[SOCKET] Keine WebSocket-URL angegeben.')
      return
    }

    schliessen()
    versuche = 0
    letzteVerbindung = { url: targetUrl, onMsg, onOpen }
    oeffnen(letzteVerbindung)
  }

  // Gewollt schließen: kein Wiederverbinden
  function schliessen() {
    stoppeReconnect()
    reconnecting.value = false
    if (socket) {
      const alt = socket
      socket = null
      alt.onclose = null
      alt.onerror = null
      alt.close()
    }
  }

  const disconnect = () => {
    letzteVerbindung = null
    schliessen()
    isConnected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    reconnecting,
    error,
    connect,
    disconnect,
    sendEvent,
    sendMessage
  }
}
