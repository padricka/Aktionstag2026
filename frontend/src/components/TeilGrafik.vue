<!--
  TeilGrafik — die drei Hardware-Teile als Zeichnung (SVG + CSS, keine Bilder):
  Netzteil (psu), Lüfter (fan), Backup-Platte (disk). Für Zwischenszene, Teilekiste
  und Beamer. leer = nur gestrichelter Umriss (noch nicht gefunden), dreht = Lüfter läuft.
-->
<template>
  <svg
    class="teil"
    :class="[`teil--${teil}`, { 'is-leer': leer, 'is-dreht': dreht }]"
    viewBox="0 0 160 110"
    role="img"
    :aria-label="leer ? `${name} – noch nicht gefunden` : name"
  >
    <defs>
      <linearGradient :id="`tg-metall-${uid}`" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#d7dce3" />
        <stop offset="55%" stop-color="#9aa2ac" />
        <stop offset="100%" stop-color="#6c747f" />
      </linearGradient>
      <radialGradient :id="`tg-dunkel-${uid}`" cx="40%" cy="35%" r="75%">
        <stop offset="0%" stop-color="#3a3f48" />
        <stop offset="100%" stop-color="#121418" />
      </radialGradient>
    </defs>

    <!-- Netzteil: Blechgehäuse, Lüftergitter, Kaltgerätebuchse, Schalter, Kabelstrang -->
    <g v-if="teil === 'psu'">
      <path class="kabel kabel--gelb" d="M14 40 C-4 44 -2 66 10 74" />
      <path class="kabel kabel--rot" d="M14 46 C0 52 2 70 14 80" />
      <path class="kabel kabel--schwarz" d="M14 52 C4 60 8 76 20 86" />
      <rect class="koerper" x="14" y="16" width="136" height="80" rx="4" :fill="`url(#tg-metall-${uid})`" />
      <rect class="kante" x="14" y="16" width="136" height="6" rx="2" />
      <circle class="gitter-grund" cx="56" cy="58" r="30" :fill="`url(#tg-dunkel-${uid})`" />
      <circle class="gitter" cx="56" cy="58" r="24" />
      <circle class="gitter" cx="56" cy="58" r="16" />
      <circle class="gitter" cx="56" cy="58" r="8" />
      <path class="gitter" d="M26 58 H86 M56 28 V88" />
      <rect class="buchse" x="104" y="30" width="34" height="24" rx="3" />
      <path class="buchse-innen" d="M110 36 H132 L128 48 H114 Z" />
      <path class="pin" d="M116 40 V44 M121 40 V44 M126 40 V44" />
      <rect class="schalter" x="112" y="62" width="18" height="22" rx="2" />
      <rect class="schalter-wippe" x="115" y="65" width="12" height="9" rx="1" />
      <path class="warnung" d="M138 66 L146 80 H130 Z" />
      <path class="warnung-blitz" d="M139 70 L136 75 H140 L137 79" />
    </g>

    <!-- Lüfter: Rahmen mit Schraublöchern, Rotor mit Schaufeln, Pfeil-Aufkleber -->
    <g v-else-if="teil === 'fan'">
      <rect class="rahmen" x="32" y="7" width="96" height="96" rx="10" />
      <circle v-for="(p, i) in ECKEN" :key="i" class="loch" :cx="p[0]" :cy="p[1]" r="4" />
      <circle class="schacht" cx="80" cy="55" r="42" :fill="`url(#tg-dunkel-${uid})`" />
      <g class="rotor">
        <path
          v-for="i in 7"
          :key="i"
          class="schaufel"
          :transform="`translate(80 55) rotate(${(i - 1) * (360 / 7)})`"
          d="M0 -12 C10 -30 30 -34 36 -16 C24 -20 12 -14 4 -4 Z"
        />
        <circle class="nabe" cx="80" cy="55" r="12" />
        <circle class="nabe-aufkleber" cx="80" cy="55" r="7" />
      </g>
      <rect class="pfeil-aufkleber" x="104" y="12" width="22" height="14" rx="2" />
      <path class="pfeil" d="M108 19 H121 M117 15 L121 19 L117 23" />
    </g>

    <!-- Backup-Platte: 3,5-Zoll-Festplatte, Deckel mit Plattenumriss, Etikett, SATA-Anschluss -->
    <g v-else-if="teil === 'disk'">
      <rect class="koerper" x="16" y="10" width="128" height="86" rx="6" :fill="`url(#tg-metall-${uid})`" />
      <rect class="deckel" x="24" y="16" width="112" height="74" rx="4" />
      <circle class="scheibe" cx="70" cy="53" r="30" />
      <circle class="scheibe" cx="70" cy="53" r="20" />
      <circle class="spindel" cx="70" cy="53" r="6" />
      <path class="arm" d="M122 80 L86 56" />
      <circle class="arm-lager" cx="122" cy="80" r="6" />
      <rect class="etikett" x="100" y="22" width="32" height="26" rx="1" />
      <path class="etikett-zeile" d="M104 30 H128 M104 36 H124 M104 42 H118" />
      <circle v-for="(p, i) in SCHRAUBEN" :key="i" class="schraube" :cx="p[0]" :cy="p[1]" r="2.5" />
      <rect class="sata" x="40" y="96" width="44" height="7" rx="1" />
      <path class="sata-pins" d="M44 99.5 H80" />
    </g>
  </svg>
</template>

<script setup>
import { computed } from 'vue'
import { TEILE } from '../utils/teile.js'

const props = defineProps({
  teil: { type: String, required: true },   // psu | fan | disk
  leer: { type: Boolean, default: false },
  dreht: { type: Boolean, default: false },
})

// eigene IDs für die Verläufe, damit mehrere Grafiken auf einer Seite sich nicht stören
const uid = `${props.teil}-${Math.random().toString(36).slice(2, 8)}`

const ECKEN = [[40, 15], [120, 15], [40, 95], [120, 95]]
const SCHRAUBEN = [[20, 14], [140, 14], [20, 92], [140, 92], [80, 14], [80, 92]]

const name = computed(() => TEILE[props.teil]?.name || props.teil)
</script>

<style scoped>
.teil { width: 100%; height: auto; display: block; overflow: visible; }

/* Netzteil */
.kante { fill: rgba(255, 255, 255, 0.35); }
.koerper { stroke: #3a3f48; stroke-width: 1.5; }
.gitter { fill: none; stroke: #8a929c; stroke-width: 1.4; }
.gitter-grund { stroke: #2b3038; stroke-width: 2; }
.buchse { fill: #1a1d22; stroke: #0c0d10; }
.buchse-innen { fill: #2b3038; }
.pin { stroke: #c9b37a; stroke-width: 2; }
.schalter { fill: #1a1d22; }
.schalter-wippe { fill: #c4332f; }
.warnung { fill: #ffd23a; stroke: #1a1d22; stroke-width: 1; }
.warnung-blitz { fill: none; stroke: #1a1d22; stroke-width: 1.4; }
.kabel { fill: none; stroke-width: 3.5; stroke-linecap: round; }
.kabel--gelb { stroke: #e6c229; }
.kabel--rot { stroke: #c4332f; }
.kabel--schwarz { stroke: #15171b; }

/* Lüfter */
.rahmen { fill: #262a31; stroke: #4a505a; stroke-width: 2; }
.loch { fill: #0c0d10; stroke: #4a505a; }
.schacht { stroke: #3a3f48; stroke-width: 2; }
.schaufel { fill: #3e444d; stroke: #5d646e; stroke-width: 1; }
.nabe { fill: #2b3038; stroke: #5d646e; }
.nabe-aufkleber { fill: var(--green, #00ff66); opacity: 0.85; }
.rotor { transform-origin: 80px 55px; }
.is-dreht .rotor { animation: drehen 1.1s linear infinite; }
.pfeil-aufkleber { fill: #ffd23a; }
.pfeil { fill: none; stroke: #1a1d22; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

/* Platte */
.deckel { fill: #b3bac4; stroke: #7d8590; }
.scheibe { fill: none; stroke: #7d8590; stroke-width: 1.4; }
.spindel { fill: #6c747f; stroke: #4a505a; }
.arm { stroke: #4a505a; stroke-width: 5; stroke-linecap: round; }
.arm-lager { fill: #4a505a; }
.etikett { fill: #f3eee1; stroke: #c9c2ad; }
.etikett-zeile { stroke: #1f5a39; stroke-width: 2; }
.schraube { fill: #5d646e; }
.sata { fill: #1a1d22; }
.sata-pins { stroke: #c9b37a; stroke-width: 2; stroke-dasharray: 2 1.5; }

/* noch nicht gefunden: nur der gestrichelte Umriss */
.teil.is-leer { opacity: 0.6; }
.is-leer * {
  fill: none !important;
  stroke: var(--fg-3, #5a9a73) !important;
  stroke-width: 1.5 !important;
  stroke-dasharray: 5 4;
}

@keyframes drehen { to { transform: rotate(360deg); } }
</style>
