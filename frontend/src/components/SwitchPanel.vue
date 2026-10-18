<script setup>
const props = defineProps({
  panelId: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['panel-changed'])

function toggle() {
  emit('panel-changed', { id: props.panelId, value: true })
}
</script>

<template>
  <div class="switch-panel">
    <button class="switch-panel__btn" type="button" @click="toggle">
      {{ panelId }}
    </button>
  </div>
</template>

<style scoped>
.switch-panel {
  display: inline-block;
}

.switch-panel__btn {
  padding: 8px 16px;
  cursor: pointer;
}
</style>
