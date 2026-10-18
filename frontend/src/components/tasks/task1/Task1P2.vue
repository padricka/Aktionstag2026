<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Code-Aufkleber</h2>
      <span class="role">Rückseite</span>
    </header>

    <p class="hint">
      Beschreibe dem Leitstand die farbigen Aufkleber — du tippst nichts ein.
    </p>

    <div v-if="!stickers.length" class="empty">Warte auf Aufkleber …</div>

    <div v-else class="stickers">
      <div
        v-for="(s, i) in stickers"
        :key="`${s.symbol}-${s.color}-${i}`"
        class="sticker"
        :style="{ borderColor: colorHex(s.color), background: colorBg(s.color) }"
      >
        <span class="sticker-color">{{ s.color }}</span>
        <SymbolIcon :name="s.symbol" :farbe="colorHex(s.color)" :size="96" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SymbolIcon from '../graphic-symbols/SymbolIcon.vue'

const props = defineProps({
  view: { type: Object, default: null },
})

const COLOR_MAP = {
  ROT: '#ff3a4d',
  GELB: '#ffb830',
  GRÜN: '#00cc66',
  GRUEN: '#00cc66',
  BLAU: '#3aa0ff',
}

const stickers = computed(() => props.view?.stickers || [])

function colorHex(name) {
  return COLOR_MAP[String(name || '').toUpperCase()] || '#ffffff'
}

function colorBg(name) {
  const hex = colorHex(name)
  return `${hex}22`
}
</script>

<style scoped>
.task {
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background: var(--bg-1);
  border: 1px solid var(--border);
  padding: 28px 36px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.title {
  font-size: 16px;
  font-weight: 700;
  color: var(--fg);
  margin: 0;
}

.role {
  font-size: 11px;
  font-weight: 600;
  color: var(--green);
  padding: 4px 12px;
  border: 1px solid var(--green-border);
  letter-spacing: 0.15em;
}

.hint {
  font-size: 13px;
  color: var(--fg-3);
  margin: 0 0 24px 0;
}

.empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fg-3);
}

.stickers {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  min-height: 0;
  align-content: center;
}

.sticker {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 260px;
  padding: 24px;
  border: 3px solid;
  background: var(--bg-2);
}

.sticker-color {
  font-family: var(--mono);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: var(--fg);
}
</style>
