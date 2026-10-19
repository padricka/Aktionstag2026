<template>
  <div class="release" :class="`is-${phase}`">
    <button
      class="release-btn"
      type="button"
      :disabled="!armed"
      @click="druecken"
    >
      FREIGABE
    </button>
    <p class="release-status" role="status" aria-live="polite">{{ statusText }}</p>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'

/**
 * Vier-Augen-Freigabe (Aufgabe 2, Löschplan ④). Nur Darstellung: meldet `press`,
 * ob beide rechtzeitig gedrückt haben, entscheidet das Backend. Der Countdown
 * zeigt nur, wie lange der eigene Druck auf den Partner wartet.
 */
const props = defineProps({
  armed: { type: Boolean, default: false },
  window: { type: Number, default: 3 },
  partner: { type: String, default: '' },
})
const emit = defineEmits(['press'])

const phase = ref('idle')      // idle | waiting | expired
const rest = ref(0)
let timer = null

const statusText = computed(() => {
  if (!props.armed) return 'Freigabe erst nach dem Löschen möglich.'
  if (phase.value === 'waiting') return `Gedrückt – ${props.partner} muss jetzt auch drücken … ${rest.value}`
  if (phase.value === 'expired') return `Zu spät! Zählt laut runter und drückt gleichzeitig mit ${props.partner}.`
  return `Zusammen mit ${props.partner} drücken – höchstens ${props.window} s Abstand.`
})

function stoppen() {
  if (timer) { clearInterval(timer); timer = null }
}

function druecken() {
  if (!props.armed) return
  emit('press')
  stoppen()
  phase.value = 'waiting'
  rest.value = props.window
  timer = setInterval(() => {
    rest.value -= 1
    if (rest.value <= 0) {
      stoppen()
      phase.value = 'expired'
    }
  }, 1000)
}

onUnmounted(stoppen)
</script>

<style scoped>
.release {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background: var(--bg-2);
  border: 1px solid var(--border-2);
}

.release-btn {
  width: 100%;
  max-width: 260px;
  padding: 18px 24px;
  font-family: var(--mono);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.2em;
  color: var(--fg);
  background: var(--red-bg);
  border: 2px solid var(--red-border);
  cursor: pointer;
}

.release-btn:hover:not(:disabled) { border-color: var(--red); }
.release-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.is-waiting .release-btn {
  background: var(--amber-bg);
  border-color: var(--amber-border);
  animation: puls 0.5s steps(1) infinite;
}

@keyframes puls { 50% { border-color: var(--amber); } }

.release-status {
  margin: 0;
  font-size: 13px;
  color: var(--fg-3);
  text-align: center;
}

.is-waiting .release-status { color: var(--amber); font-weight: 600; }
.is-expired .release-status { color: var(--red); }

@media (prefers-reduced-motion: reduce) {
  .is-waiting .release-btn { animation: none; }
}
</style>
