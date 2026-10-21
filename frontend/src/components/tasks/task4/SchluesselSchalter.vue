<!--
  SchluesselSchalter — ein Schlüssel im Schloss für den Drei-Schlüssel-Start im Finale.
  bereit = alle Teile eingebaut (sonst gesperrt); gedreht = laut Server schon gedreht
  (der Schlüssel steht quer, die LED wird grün). Klick → `drehen`.
-->
<template>
  <div class="schluessel" :class="{ 'is-gedreht': gedreht, 'is-bereit': bereit }">
    <button
      class="schloss"
      type="button"
      :disabled="!bereit || gedreht"
      :aria-pressed="gedreht ? 'true' : 'false'"
      :aria-label="`Schlüssel ${label} drehen`"
      @click="emit('drehen')"
    >
      <svg viewBox="0 0 100 100" aria-hidden="true">
        <circle class="platte" cx="50" cy="50" r="46" />
        <circle class="ring" cx="50" cy="50" r="34" />
        <text class="mark mark--aus" x="50" y="13">AUS</text>
        <text class="mark mark--an" x="91" y="53">AN</text>
        <g class="schluessel-dreh">
          <rect class="bart" x="46" y="22" width="8" height="40" rx="2" />
          <path class="griff" d="M34 62 h32 a6 6 0 0 1 6 6 v14 a6 6 0 0 1 -6 6 h-32 a6 6 0 0 1 -6 -6 v-14 a6 6 0 0 1 6 -6 z" />
          <circle class="loch" cx="50" cy="76" r="4" />
        </g>
        <circle class="led" cx="84" cy="84" r="5" />
      </svg>
    </button>
    <span class="name">{{ label }}</span>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  bereit: { type: Boolean, default: false },
  gedreht: { type: Boolean, default: false },
})
const emit = defineEmits(['drehen'])
</script>

<style scoped>
.schluessel { display: inline-flex; flex-direction: column; align-items: center; gap: 6px; }
.schloss {
  width: 96px;
  height: 96px;
  padding: 0;
  border: none;
  background: none;
  cursor: pointer;
  filter: drop-shadow(0 6px 10px rgba(0, 0, 0, 0.55));
}
.schloss:disabled { cursor: default; }
.schluessel:not(.is-bereit) .schloss { opacity: 0.45; }
.schloss svg { width: 100%; height: 100%; display: block; }

.platte { fill: #2b3038; stroke: #4a505a; stroke-width: 2; }
.ring { fill: #1a1d22; stroke: #8a929c; stroke-width: 3; }
.mark { fill: #9aa3ae; font-family: var(--mono); font-size: 9px; text-anchor: middle; }
.is-gedreht .mark--an { fill: var(--green); }

.schluessel-dreh {
  transform-origin: 50px 50px;
  transition: transform 0.45s cubic-bezier(0.3, 1.4, 0.5, 1);
}
.is-bereit:not(.is-gedreht) .schloss:hover .schluessel-dreh { transform: rotate(12deg); }
.is-gedreht .schluessel-dreh { transform: rotate(90deg); }
.bart { fill: #c9b37a; }
.griff { fill: #d8c27f; stroke: #8a7640; stroke-width: 1.5; }
.loch { fill: #2b3038; }

.led { fill: var(--red); filter: drop-shadow(0 0 4px var(--red)); transition: fill 0.3s; }
.is-gedreht .led { fill: var(--green); filter: drop-shadow(0 0 5px var(--green)); }

.name {
  font-family: var(--mono);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--fg-2);
}
.is-gedreht .name { color: var(--green); }
</style>
