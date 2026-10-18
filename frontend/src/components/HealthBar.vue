<script setup>
import { computed } from 'vue'

const props = defineProps({
  health: {
    type: Number,
    default: 100,
  },
})

const istGefahr = computed(() => props.health < 20)
</script>

<template>
  <div class="health-bar" :class="{ danger: istGefahr }">
    <div
      class="health-bar__fill"
      :class="{ danger: istGefahr }"
      :style="{ width: `${props.health}%` }"
    ></div>
  </div>
</template>

<style scoped>
.health-bar {
  width: 100%;
  height: 12px;
  background: #1f2933;
  border-radius: 6px;
  overflow: hidden;
}

.health-bar__fill {
  height: 100%;
  background: #38bdf8;
  transition: width 0.3s ease;
}

.health-bar__fill.danger,
.health-bar.danger .health-bar__fill {
  background: #ef4444;
}
</style>
