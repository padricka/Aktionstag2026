<!--
  Zwischenszene — nach jeder gelösten Aufgabe (GAME_DESIGN.md, „Fundorte und Teilekiste“):
    1. Der Fundort öffnet sich: Ersatzteilschrank (Netzteil), Brandschutztür zum Lager
       (Lüfter) oder Datentresor (Backup-Platte). Alles SVG/CSS, keine Bilder.
    2. Das Teil kommt zum Vorschein, darunter, wo es jetzt liegt (Teilekiste beim Leitstand).
    3. Titelkarte der nächsten Aufgabe, dann `fertig` – die Aufgabe liegt schon dahinter.
  Die Spielzeit läuft weiter (nur gut 4 Sekunden). gross = Beamer.
-->
<template>
  <div
    class="zwischenszene"
    :class="{ 'is-gross': gross, 'is-tresor': teil.fundort === 'tresor' }"
    role="status"
    aria-live="polite"
  >
    <Transition name="zs" mode="out-in">
      <div v-if="phase !== 'titel'" key="fund" class="zs-fund">
        <p class="zs-ort">{{ ort.titel }}</p>

        <!-- Datentresor: derselbe Tresor wie bisher am Beamer, die Platte liegt darin -->
        <div v-if="teil.fundort === 'tresor'" class="fundort fundort--tresor" :class="{ 'is-offen': offen }">
          <VaultDoor label="DATENTRESOR" status="GESPERRT" :state="offen ? 'open' : 'locked'">
            <TeilGrafik class="fo-teil fo-teil--tresor" :teil="teil.id" />
          </VaultDoor>
        </div>

        <div v-else class="fundort" :class="[`fundort--${teil.fundort}`, { 'is-offen': offen }]">
          <!-- dahinter: das Teil -->
          <div class="fo-innen">
            <span class="fo-regal" aria-hidden="true"></span>
            <TeilGrafik class="fo-teil" :teil="teil.id" :dreht="teil.id === 'fan' && offen" />
          </div>

          <!-- Ersatzteilschrank: zwei Blechtüren mit elektronischem Schloss -->
          <template v-if="teil.fundort === 'schrank'">
            <div class="fo-tuer fo-tuer--links" aria-hidden="true"><span class="fo-griff"></span></div>
            <div class="fo-tuer fo-tuer--rechts" aria-hidden="true">
              <span class="fo-griff"></span>
              <span class="fo-schloss"><i></i><b></b><b></b><b></b><b></b></span>
            </div>
          </template>

          <!-- Lager: rote Brandschutz-Schiebetür -->
          <div v-else class="fo-schiebetuer" aria-hidden="true">
            <span class="fo-schild">BRANDSCHUTZTÜR<br />T90 · LAGER</span>
            <span class="fo-streifen"></span>
          </div>
        </div>

        <p class="zs-text">{{ ort.text }}</p>
        <p class="zs-gefunden" :class="{ 'is-da': offen }">
          <strong>{{ teil.name }} gefunden</strong>
          <span>{{ woLiegt }}</span>
        </p>
      </div>

      <div v-else key="titel" class="zs-titel">
        <span class="zs-nr">{{ naechste >= 4 ? 'Finale' : `Aufgabe ${naechste}` }}</span>
        <span class="zs-name">{{ AUFGABEN_TITEL[naechste] }}</span>
      </div>
    </Transition>
  </div>
</template>

<script>
// Zeitplan in ms ab Erscheinen (auch für die Tests). Der Tresor braucht länger:
// erst fahren die Riegel zurück, dann schwingt die schwere Tür auf.
export const DAUER = { oeffnen: 600, titel: 3000, ende: 4600 }
export const DAUER_TRESOR = { oeffnen: 300, titel: 4000, ende: 5600 }
</script>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import TeilGrafik from './TeilGrafik.vue'
import VaultDoor from './VaultDoor.vue'
import { FUNDORTE, AUFGABEN_TITEL } from '../utils/teile.js'

const props = defineProps({
  teil: { type: Object, required: true },        // { id, name, fundort, label } aus game_tick.parts
  naechste: { type: Number, required: true },    // Nummer der nächsten Aufgabe (2–4)
  rolle: { type: String, default: '' },          // MASTER | FI-SI | FI-AE | HOST
  gross: { type: Boolean, default: false },
})
const emit = defineEmits(['fertig'])

const offen = ref(false)
const phase = ref('fund')
const timer = []

const ort = computed(() => FUNDORTE[props.teil.fundort] || { titel: '', text: '' })
const woLiegt = computed(() => {
  if (props.rolle === 'MASTER') return 'liegt jetzt in deiner Teilekiste'
  if (props.rolle === 'HOST') return `Teil ${props.naechste - 1} von 3 für die Reparatur`
  return 'liegt in der Teilekiste beim Leitstand'
})

onMounted(() => {
  const plan = props.teil.fundort === 'tresor' ? DAUER_TRESOR : DAUER
  timer.push(setTimeout(() => { offen.value = true }, plan.oeffnen))
  timer.push(setTimeout(() => { phase.value = 'titel' }, plan.titel))
  timer.push(setTimeout(() => emit('fertig'), plan.ende))
})
onUnmounted(() => timer.forEach(clearTimeout))
</script>

<style scoped>
.zwischenszene {
  --zs-ease: cubic-bezier(0.22, 1, 0.36, 1);
  --zs-b: 240px;   /* Breite des Fundorts */
  position: fixed;
  inset: 0;
  z-index: 60;
  display: grid;
  place-items: center;
  padding: 16px;
  background: radial-gradient(ellipse at center, rgba(10, 15, 12, 0.92) 0%, rgba(4, 6, 5, 0.98) 75%);
  backdrop-filter: blur(3px);
  font-family: var(--mono);
  color: var(--fg);
  text-align: center;
}

.is-gross { --zs-b: min(52vw, 73vh); }   /* Beamer: so groß wie es die Höhe erlaubt */

.zs-fund { display: flex; flex-direction: column; align-items: center; gap: 14px; }

.zs-ort {
  margin: 0;
  font-size: 13px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--amber);
}
.is-gross .zs-ort { font-size: 22px; }

.zs-text { margin: 0; font-size: 14px; color: var(--fg-2); max-width: 34ch; }
.is-gross .zs-text { font-size: 24px; max-width: 40ch; }

.zs-gefunden {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  opacity: 0;
  transform: translateY(8px);
  transition: opacity 0.4s ease 0.7s, transform 0.5s var(--zs-ease) 0.7s;
}
.zs-gefunden.is-da { opacity: 1; transform: none; }
.is-tresor .zs-gefunden { transition-delay: 2.4s; }   /* erst wenn die Tresortür offen ist */
.zs-gefunden strong { font-size: 22px; color: var(--green); letter-spacing: 0.06em; }
.zs-gefunden span { font-size: 13px; color: var(--fg-2); }
.is-gross .zs-gefunden strong { font-size: 40px; }
.is-gross .zs-gefunden span { font-size: 22px; }

/* ----------------------------------------------------------------- Fundort (gemeinsam) */
.fundort {
  position: relative;
  width: var(--zs-b);
  aspect-ratio: 4 / 3;
  perspective: 900px;
  border: 6px solid #2b3038;
  background: #0c0f0d;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.6), inset 0 0 0 2px #15181c;
  overflow: hidden;
}

.fo-innen {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: radial-gradient(circle at 50% 55%, rgba(0, 255, 102, 0.16), transparent 65%), #101512;
}

.fo-regal {
  position: absolute;
  left: 8%;
  right: 8%;
  top: 74%;
  height: 4%;
  background: #3a3f48;
  box-shadow: 0 6px 10px rgba(0, 0, 0, 0.5);
}

.fo-teil {
  width: 62%;
  transform: scale(0.82);
  filter: drop-shadow(0 6px 10px rgba(0, 0, 0, 0.6));
  transition: transform 0.7s var(--zs-ease) 0.5s, filter 0.7s ease 0.5s;
}
.is-offen .fo-teil {
  transform: scale(1) translateY(-4%);
  filter: drop-shadow(0 0 18px rgba(0, 255, 102, 0.45)) drop-shadow(0 8px 12px rgba(0, 0, 0, 0.6));
}

/* ------------------------------------------------------------ Ersatzteilschrank */
.fundort--schrank { border-color: #4a505a; }
.fo-tuer {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 50%;
  background:
    repeating-linear-gradient(180deg, transparent 0 14%, rgba(0, 0, 0, 0.18) 14% 15%),
    linear-gradient(160deg, #6c747f, #4a505a 60%, #3a3f48);
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.08);
  transition: transform 0.9s var(--zs-ease);
}
.fo-tuer--links { left: 0; transform-origin: 0 50%; }
.fo-tuer--rechts { right: 0; transform-origin: 100% 50%; }
.is-offen .fo-tuer--links { transform: rotateY(-108deg); }
.is-offen .fo-tuer--rechts { transform: rotateY(108deg); }
.fo-griff {
  position: absolute;
  top: 42%;
  width: 6%;
  height: 16%;
  background: #23272e;
  border-radius: 2px;
}
.fo-tuer--links .fo-griff { right: 8%; }
.fo-tuer--rechts .fo-griff { left: 8%; }
.fo-schloss {
  position: absolute;
  left: 22%;
  top: 18%;
  width: 34%;
  padding: 4%;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6%;
  background: #15181c;
  border-radius: 3px;
}
.fo-schloss i {
  grid-column: span 2;
  height: 8px;
  border-radius: 4px;
  background: var(--red);
  box-shadow: 0 0 8px var(--red);
  transition: background 0.2s, box-shadow 0.2s;
}
.is-offen .fo-schloss i { background: var(--green); box-shadow: 0 0 8px var(--green); }
.fo-schloss b { height: 7px; background: #3a3f48; border-radius: 1px; }

/* ------------------------------------------------------- Lager: Brandschutztür */
.fundort--lager { border-color: #5a3a2c; }
.fo-schiebetuer {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: linear-gradient(160deg, #b8322b, #8e221d 60%, #6d1814);
  box-shadow: inset 0 0 0 3px rgba(0, 0, 0, 0.25);
  transition: transform 1s var(--zs-ease);
}
.is-offen .fo-schiebetuer { transform: translateX(102%); }
.fo-schild {
  padding: 6px 10px;
  background: #f3eee1;
  color: #8e221d;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  line-height: 1.4;
}
.is-gross .fo-schild { font-size: 20px; }
.fo-streifen {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 12%;
  background: repeating-linear-gradient(135deg, #ffd23a 0 12px, #1a1d22 12px 24px);
}

/* ------------------------------------------------------------- Datentresor */
/* der Tresor bringt seinen eigenen Rahmen mit (VaultDoor) */
.fundort--tresor {
  width: calc(var(--zs-b) * 1.25);
  aspect-ratio: auto;
  border: none;
  background: none;
  box-shadow: none;
  overflow: visible;
}
.fo-teil--tresor { width: 46%; }
.is-offen .fo-teil--tresor { transition-delay: 2.2s; }

/* ------------------------------------------------------------- Titelkarte */
.zs-titel { display: flex; flex-direction: column; gap: 8px; }
.zs-nr { font-size: 14px; letter-spacing: 0.4em; text-transform: uppercase; color: var(--fg-3); }
.zs-name { font-size: 36px; font-weight: 700; color: var(--green); letter-spacing: 0.04em; }
.is-gross .zs-nr { font-size: 26px; }
.is-gross .zs-name { font-size: 72px; }

.zs-enter-active,
.zs-leave-active { transition: opacity 0.35s ease, transform 0.45s var(--zs-ease), filter 0.35s ease; }
.zs-enter-from { opacity: 0; transform: scale(0.96); filter: blur(4px); }
.zs-leave-to { opacity: 0; transform: scale(1.03); filter: blur(4px); }
</style>
