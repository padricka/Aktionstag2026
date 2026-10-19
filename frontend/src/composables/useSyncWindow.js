/**
 * Zeitfenster des Sync-Knopfes (Aufgabe 3, siehe GAME_DESIGN.md und PANELS.md).
 *
 * Der Knopf selbst ist reine Darstellung; ob beide Seiten rechtzeitig gedrückt
 * haben, entscheidet allein der Server. Dieses Composable führt nur den lokalen
 * Anzeigezustand nach einem Druck:
 *
 *   press -> "waiting"  (Ring läuft, windowMs)
 *          -> "error"    (windowMs + 500 ms ohne Lösung, Klappe bleibt offen)
 *          -> "idle"     (nach 1200 ms, erneut drücken möglich)
 *
 * Wird die Aufgabe gelöst, verschwindet die Komponente — dann räumt
 * onBeforeUnmount die Timer ab.
 */
import { onBeforeUnmount, ref } from 'vue'

export const SYNC_WINDOW_MS = 3000
const NACHLAUF_MS = 500
const FEHLER_ANZEIGE_MS = 1200

export function useSyncWindow(windowMs = SYNC_WINDOW_MS) {
  const state = ref('idle')
  let fehlerTimer = null
  let idleTimer = null

  function timerLoeschen() {
    if (fehlerTimer) { clearTimeout(fehlerTimer); fehlerTimer = null }
    if (idleTimer) { clearTimeout(idleTimer); idleTimer = null }
  }

  function reset() {
    timerLoeschen()
    state.value = 'idle'
  }

  // true, wenn der Druck angenommen wurde (nicht doppelt im laufenden Fenster).
  function begin() {
    if (state.value === 'waiting' || state.value === 'synced') return false
    timerLoeschen()
    state.value = 'waiting'
    fehlerTimer = setTimeout(() => {
      fehlerTimer = null
      state.value = 'error'
      idleTimer = setTimeout(() => {
        idleTimer = null
        if (state.value === 'error') state.value = 'idle'
      }, FEHLER_ANZEIGE_MS)
    }, windowMs + NACHLAUF_MS)
    return true
  }

  onBeforeUnmount(timerLoeschen)

  return { state, begin, reset }
}
