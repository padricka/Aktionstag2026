<template>
  <svg
    :width="size" :height="size" viewBox="0 0 40 40"
    :fill="gefuellt ? farbe : 'none'" :stroke="farbe"
    stroke-width="3" stroke-linejoin="round" stroke-linecap="round"
  >
    <polygon v-if="name === 'raute'" points="20,4 36,20 20,36 4,20" />
    <polygon v-else-if="name === 'dreieck'" points="20,5 36,35 4,35" />
    <rect v-else-if="name === 'quadrat'" x="6" y="6" width="28" height="28" />
    <circle v-else-if="name === 'kreis'" cx="20" cy="20" r="15" />
    <polygon v-else-if="name === 'dreieck-runter'" points="4,6 36,6 20,35" />
    <polygon v-else-if="name === 'dreieck-runter-voll'" points="4,6 36,6 20,35" :fill="farbe" />
    <polygon v-else-if="name === 'dreieck-voll'" points="20,5 36,35 4,35" :fill="farbe" />
    <g v-else-if="name === 'kreuz'" stroke-width="8">
      <line x1="8" y1="8" x2="32" y2="32" />
      <line x1="32" y1="8" x2="8" y2="32" />
    </g>
    <polygon v-else-if="name === 'stern'" :fill="farbe" points="20,2 25,15 38,16 28,25 31,38 20,31 9,38 12,25 2,16 15,15" />
    <g v-else-if="name === 'plus'" stroke-width="8">
      <line x1="20" y1="6" x2="20" y2="34" />
      <line x1="6" y1="20" x2="34" y2="20" />
    </g>
    <polygon v-else-if="name === 'sechseck'" points="20,3 34,11 34,29 20,37 6,29 6,11" />
    <path v-else-if="name === 'herz'" :fill="farbe" d="M20 35C4 24 4 10 13 9C17 9 19 12 20 14C21 12 23 9 27 9C36 10 36 24 20 35Z" />
    <polygon v-else-if="name === 'blitz'" :fill="farbe" points="23,2 8,23 19,23 16,38 32,15 21,15" />
    <polygon v-else-if="name === 'fuenfeck'" points="20,3 37,16 31,36 9,36 3,16" />
    <path v-else-if="name === 'pfeil'" stroke-width="5" d="M20 36V6M8 18L20 6L32 18" />
    <g v-else-if="name === 'ring'">
      <circle cx="20" cy="20" r="15" />
      <circle cx="20" cy="20" r="6" :fill="farbe" />
    </g>
  </svg>
</template>

<script setup>
defineProps({
  name: { type: String, required: true },
  farbe: { type: String, default: 'currentColor' },
  gefuellt: { type: Boolean, default: false },
  size: { type: Number, default: 40 }
})
</script>