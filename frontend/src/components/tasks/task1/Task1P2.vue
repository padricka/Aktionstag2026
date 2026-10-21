<template>
  <div class="task">
    <header class="head">
      <h2 class="title">Code-Aufkleber</h2>
      <span class="role">Rückseite</span>
    </header>

    <p class="hint">
      Beschreibe dem Leitstand die farbigen Aufkleber – du tippst nichts ein.
      Ist einer zerkratzt? Dann gilt Regel ③ auf deinem Teil der Wartungsnotiz – dafür
      brauchst du die rote Stelle (Leitstand) und das Symbol vom kaputten Kabel dort (Vorderseite).
    </p>

    <div v-if="!stickers.length" class="empty">Warte auf Aufkleber …</div>

    <div v-else class="p2-body">
      <div class="stickers">
        <div
          v-for="(s, i) in stickers"
          :key="`${s.symbol}-${s.color}-${i}`"
          class="sticker"
          :class="{ 'is-scratched': s.scratched }"
          :style="{ borderColor: colorHex(s.color), background: colorBg(s.color) }"
        >
          <span class="sticker-color">{{ s.color }}</span>
          <svg
            v-if="s.scratched"
            class="scratch"
            viewBox="0 0 40 40"
            role="img"
            aria-label="Symbol zerkratzt, nicht lesbar"
          >
            <path d="M4 8l32 24M8 4l26 32M3 20h34M10 36L31 3M6 28l14-22" />
          </svg>
          <SymbolIcon v-else :name="s.symbol" :farbe="colorHex(s.color)" :size="96" />
          <span v-if="s.scratched" class="scratch-label">zerkratzt</span>
        </div>
      </div>

      <aside v-if="view?.note" class="note-col">
        <span class="note-label">Dein Teil der Wartungsnotiz</span>
        <TornNote :note="view.note" :seed="noteSeed" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SymbolIcon from '../graphic-symbols/SymbolIcon.vue'
import TornNote from '../../TornNote.vue'

const props = defineProps({
  view: { type: Object, default: null },
  noteSeed: { type: String, default: '' },
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
  font-size: 17px;
  line-height: 1.45;
  color: var(--fg);
  margin: 0 0 24px 0;
}

.empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fg-3);
}

.p2-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 28px;
  overflow: auto;
}

.stickers {
  flex: 1 1 480px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  min-height: 0;
  align-content: center;
}

.note-col {
  flex: 0 1 420px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.note-label {
  font-size: 11px;
  color: var(--fg-3);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.scratch {
  width: 96px;
  height: 96px;
  fill: none;
  stroke: var(--fg-3);
  stroke-width: 1.6;
  stroke-linecap: round;
}

.scratch-label {
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 0.12em;
  color: var(--fg-2);
}

.sticker {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 190px;
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
