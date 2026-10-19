<template>
  <div ref="wurzel" class="lb">
    <header class="lb-top">
      <button class="lb-back" @click="$emit('back')">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
        Zurück
      </button>
      <span class="lb-brand">DRV-BOX</span>
    </header>

    <main class="lb-main">
      <div class="lb-head">
        <p class="lb-kicker">Bestenliste</p>
        <h1 class="lb-title">Leaderboard</h1>
        <p class="lb-sub">Alle Runden – höchste Punktzahl zuerst</p>
      </div>

      <section class="lb-panel" :aria-busy="laden ? 'true' : 'false'">
        <p v-if="fehler" class="lb-error" role="alert">
          Leaderboard konnte nicht geladen werden.
          <button class="lb-retry" @click="laden_(seite)">Erneut versuchen</button>
        </p>

        <p v-else-if="!laden && daten && daten.total === 0" class="lb-empty">
          Noch keine Runden gespielt. Die erste Runde landet hier ganz oben.
        </p>

        <table v-else class="lb-table">
          <thead>
            <tr>
              <th class="c-rank" scope="col">Platz</th>
              <th class="c-team" scope="col">Team</th>
              <th class="c-score" scope="col">Punkte</th>
              <th class="c-result" scope="col">Ergebnis</th>
              <th class="c-time" scope="col">Spielzeit</th>
              <th class="c-date" scope="col">Datum</th>
            </tr>
          </thead>
          <tbody v-if="laden && !daten">
            <tr v-for="i in 8" :key="i" class="lb-skeleton" aria-hidden="true">
              <td colspan="6"><span></span></td>
            </tr>
          </tbody>
          <tbody v-else :class="{ 'is-loading': laden }">
            <tr v-for="e in daten?.entries || []" :key="e.rank" :class="podest(e.rank)">
              <td class="c-rank"><span class="lb-rank">{{ e.rank }}</span></td>
              <td class="c-team">{{ (e.players || []).join(' · ') }}</td>
              <td class="c-score">{{ e.score }}</td>
              <td class="c-result">
                <span class="lb-badge" :class="e.result === 'victory' ? 'win' : 'lose'">
                  {{ e.result === 'victory' ? 'Sieg' : 'Niederlage' }}
                </span>
              </td>
              <td class="c-time">{{ dauer(e.survived_seconds) }}</td>
              <td class="c-date">{{ datum(e.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <nav v-if="daten && daten.total > 0" class="lb-pager" aria-label="Seiten">
        <p class="lb-range">{{ bereich }}</p>
        <div class="lb-pager-row">
          <button
            class="lb-arrow lb-prev"
            aria-label="Vorherige Seite"
            :disabled="seite <= 1 || laden"
            @click="laden_(seite - 1)"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
          </button>
          <ol class="lb-pages">
            <li v-for="(p, i) in seitenListe" :key="`${p}-${i}`">
              <span v-if="p === '…'" class="lb-gap" aria-hidden="true">…</span>
              <button
                v-else
                class="lb-page"
                :aria-current="p === seite ? 'page' : undefined"
                :aria-label="`Seite ${p}`"
                :disabled="laden"
                @click="laden_(p)"
              >
                {{ p }}
              </button>
            </li>
          </ol>
          <button
            class="lb-arrow lb-next"
            aria-label="Nächste Seite"
            :disabled="seite >= daten.pages || laden"
            @click="laden_(seite + 1)"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg>
          </button>
        </div>
      </nav>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

defineEmits(['back'])

const PER_PAGE = 20
const API = `${location.protocol === 'https:' ? 'https' : 'http'}://${location.hostname}:8000`

const wurzel = ref(null)
const daten = ref(null)
const seite = ref(1)
const laden = ref(false)
const fehler = ref(false)
let anfrage = 0   // nur die letzte Antwort zählt (schnelles Klicken)

async function laden_(p) {
  const nr = ++anfrage
  laden.value = true
  fehler.value = false
  try {
    const res = await fetch(`${API}/leaderboard/?page=${p}&per_page=${PER_PAGE}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = await res.json()
    if (nr !== anfrage) return
    const wechsel = daten.value && json.page !== seite.value
    daten.value = json
    seite.value = json.page
    // Wie auf Webseiten: neue Seite beginnt oben
    if (wechsel) wurzel.value?.scrollTo?.({ top: 0, behavior: 'smooth' })
  } catch (e) {
    if (nr !== anfrage) return
    console.error('[LEADERBOARD]', e)
    fehler.value = true
  } finally {
    if (nr === anfrage) laden.value = false
  }
}

onMounted(() => laden_(1))

/** 1 2 3 … 12 – immer erste/letzte Seite und die Nachbarn der aktuellen. */
const seitenListe = computed(() => {
  const gesamt = daten.value?.pages || 1
  if (gesamt <= 7) return Array.from({ length: gesamt }, (_, i) => i + 1)
  const sichtbar = [1, gesamt, seite.value - 1, seite.value, seite.value + 1]
    .filter((n) => n >= 1 && n <= gesamt)
  const sortiert = [...new Set(sichtbar)].sort((a, b) => a - b)
  const out = []
  sortiert.forEach((n, i) => {
    if (i > 0 && n - sortiert[i - 1] > 1) out.push('…')
    out.push(n)
  })
  return out
})

const bereich = computed(() => {
  const d = daten.value
  if (!d || !d.total) return ''
  const von = (d.page - 1) * d.per_page + 1
  const bis = von + d.entries.length - 1
  return `Runden ${von}–${bis} von ${d.total}`
})

function podest(rank) {
  return rank <= 3 ? `is-podium p${rank}` : ''
}

function dauer(s) {
  const t = Math.max(0, Number(s) || 0)
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, '0')}`
}

const DATUM = new Intl.DateTimeFormat('de-DE', {
  day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
})

function datum(iso) {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '–' : DATUM.format(d)
}
</script>

<style scoped>
.lb {
  --gold: #ffd66b;
  --silver: #d9e2ec;
  --bronze: #e7a272;

  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background:
    radial-gradient(900px 400px at 50% -10%, var(--green-bg), transparent 70%),
    var(--bg);
  color: var(--fg);
  font-family: var(--mono);
}

.lb-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px clamp(16px, 4vw, 48px);
  border-bottom: 1px solid var(--border);
}

.lb-back {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: none;
  border: 1px solid var(--border-2);
  color: var(--fg-2);
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.lb-back:hover { color: var(--green); border-color: var(--green-border); }

.lb-brand {
  color: var(--green);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.15em;
}

.lb-main {
  width: min(1040px, 100%);
  margin: 0 auto;
  padding: clamp(24px, 5vh, 48px) clamp(16px, 4vw, 32px) 48px;
}

.lb-head { margin-bottom: 24px; }

.lb-kicker {
  margin: 0 0 6px;
  font-size: 11px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--green);
}

.lb-title {
  margin: 0;
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 700;
  letter-spacing: -0.02em;
}

.lb-sub {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--fg-2);
}

.lb-panel {
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  border-top: 2px solid var(--green);
  overflow-x: auto;
}

.lb-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.lb-table th {
  padding: 12px 16px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  text-align: left;
  color: var(--fg-3);
  border-bottom: 1px solid var(--border-2);
  white-space: nowrap;
}

.lb-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}

.lb-table tbody tr { transition: background 0.15s; }
.lb-table tbody tr:hover { background: var(--bg-2); }
.lb-table tbody tr:last-child td { border-bottom: none; }
.lb-table tbody.is-loading { opacity: 0.45; transition: opacity 0.15s; }

.c-rank  { width: 72px; }
.c-team  { white-space: normal !important; min-width: 200px; }
.c-score { text-align: right !important; font-weight: 700; font-variant-numeric: tabular-nums; font-size: 16px; }
.c-time,
.c-date  { color: var(--fg-2); font-variant-numeric: tabular-nums; }

.lb-rank {
  display: inline-grid;
  place-items: center;
  min-width: 34px;
  height: 28px;
  padding: 0 6px;
  font-weight: 700;
  font-size: 13px;
  color: var(--fg-2);
  border: 1px solid var(--border-2);
  font-variant-numeric: tabular-nums;
}

.is-podium.p1 .lb-rank { color: var(--gold);   border-color: color-mix(in srgb, var(--gold) 55%, transparent);   background: color-mix(in srgb, var(--gold) 10%, transparent); }
.is-podium.p2 .lb-rank { color: var(--silver); border-color: color-mix(in srgb, var(--silver) 50%, transparent); background: color-mix(in srgb, var(--silver) 8%, transparent); }
.is-podium.p3 .lb-rank { color: var(--bronze); border-color: color-mix(in srgb, var(--bronze) 50%, transparent); background: color-mix(in srgb, var(--bronze) 8%, transparent); }
.is-podium.p1 .c-score { color: var(--gold); }

.lb-badge {
  display: inline-block;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border: 1px solid;
}
.lb-badge.win  { color: var(--green); border-color: var(--green-border); background: var(--green-bg); }
.lb-badge.lose { color: var(--red);   border-color: var(--red-border);   background: var(--red-bg); }

.lb-skeleton td { padding: 16px; }
.lb-skeleton span {
  display: block;
  height: 14px;
  background: linear-gradient(90deg, var(--bg-2), var(--bg-3), var(--bg-2));
  background-size: 200% 100%;
  animation: schimmer 1.2s linear infinite;
}

@keyframes schimmer {
  to { background-position: -200% 0; }
}

.lb-empty,
.lb-error {
  margin: 0;
  padding: 48px 24px;
  text-align: center;
  color: var(--fg-2);
  font-size: 14px;
}
.lb-error { color: var(--red); }

.lb-retry {
  display: block;
  margin: 16px auto 0;
  padding: 8px 16px;
  background: none;
  border: 1px solid var(--red-border);
  color: var(--red);
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
}

/* ---------------------------------------------------------------- Seiten */
.lb-pager {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
}

.lb-range {
  margin: 0;
  font-size: 12px;
  color: var(--fg-3);
  letter-spacing: 0.06em;
}

.lb-pager-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.lb-pages {
  display: flex;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.lb-page,
.lb-arrow {
  min-width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  padding: 0 10px;
  background: var(--bg-1);
  border: 1px solid var(--border-2);
  color: var(--fg-2);
  font-family: var(--mono);
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}

.lb-page:hover:not(:disabled),
.lb-arrow:hover:not(:disabled) {
  color: var(--green);
  border-color: var(--green-border);
}

.lb-page[aria-current='page'] {
  color: var(--bg);
  background: var(--green);
  border-color: var(--green);
  font-weight: 700;
}

.lb-arrow:disabled { opacity: 0.3; cursor: not-allowed; }
.lb-page:disabled:not([aria-current='page']) { cursor: wait; }

.lb-arrow svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.lb-back svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
}

.lb-gap {
  display: grid;
  place-items: center;
  min-width: 24px;
  height: 40px;
  color: var(--fg-3);
}

.lb-back:focus-visible,
.lb-page:focus-visible,
.lb-arrow:focus-visible,
.lb-retry:focus-visible {
  outline: 2px solid var(--green);
  outline-offset: 2px;
}

@media (max-width: 720px) {
  .c-time, .c-date { display: none; }
  .lb-table th, .lb-table td { padding: 10px; }
}

@media (prefers-reduced-motion: reduce) {
  .lb-skeleton span { animation: none; }
}
</style>
