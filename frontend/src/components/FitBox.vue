<!--
  FitBox — verkleinert seinen Inhalt als Ganzes, bis er in die verfügbare Fläche passt:
  kein Scrollen, nichts abgeschnitten (fix/alles-passt). Passt alles, bleibt es bei 1.
  Unter `scrollUnter` px Fensterbreite (Handy, Inhalt untereinander) wird nicht verkleinert,
  dann darf senkrecht gescrollt werden – sonst würde alles winzig.
-->
<template>
  <div ref="box" class="fit" :class="{ 'is-scroll': scrollen }">
    <div ref="inner" class="fit-inner" :style="innerStyle"><slot /></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { skalaFlaeche } from '../utils/passend.js'

const props = defineProps({
  scrollUnter: { type: Number, default: 0 },
})

const box = ref(null)
const inner = ref(null)
const skala = ref(1)
const scrollen = ref(false)

const innerStyle = computed(() => ({
  transform: skala.value < 1 ? `scale(${skala.value})` : 'none',
}))

function messen() {
  const b = box.value
  const i = inner.value
  if (!b || !i) return
  scrollen.value = window.innerWidth < props.scrollUnter
  if (scrollen.value) { skala.value = 1; i.style.width = ''; return }
  const { skala: s, breite: w } = skalaFlaeche(b.clientWidth, b.clientHeight, (wTest) => {
    i.style.width = `${wTest}px`
    return i.offsetHeight
  })
  i.style.width = s < 1 ? `${w}px` : ''   // Breite direkt setzen: Vue weiß nichts vom Messen
  skala.value = s
}

let ro = null
let frame = 0
const spaeter = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(messen) }
onMounted(() => {
  if (typeof ResizeObserver === 'undefined') return   // Tests (jsdom): kein Layout, nichts zu tun
  ro = new ResizeObserver(spaeter)
  ro.observe(box.value)
  ro.observe(inner.value)
  window.addEventListener('resize', spaeter)
  spaeter()
})
onUnmounted(() => {
  ro?.disconnect()
  window.removeEventListener('resize', spaeter)
  cancelAnimationFrame(frame)
})
</script>

<style scoped>
.fit {
  position: relative;
  flex: 1;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}
.fit.is-scroll { overflow-x: hidden; overflow-y: auto; }
.fit-inner { transform-origin: top left; }
</style>
