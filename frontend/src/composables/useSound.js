/**
 * Ton im Spiel: Funkspruch (Intro), Ambience (Serverraum) und Effekte.
 * Dateien liegen in public/sound (gebaut mit tools/sound/build_sounds.py).
 * Lautstärken kommen aus den Einstellungen (localStorage "drv_game_settings"),
 * die bei jedem Abspielen frisch gelesen werden: Änderungen wirken sofort.
 */
const SOUND_BASE = '/sound/'
const BED_FILE = 'bed-serverraum'
const FADE_MS = 1500
const FADE_STEP_MS = 50

const DEFAULTS = {
  masterVolume: 80,
  musicEnabled: true,
  musicVolume: 60,
  sfxEnabled: true,
  voiceEnabled: true,
}

let voice = null
let bed = null
let bedLevel = 1
let fadeTimer = null

function readSettings() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem('drv_game_settings') || '{}') }
  } catch {
    return { ...DEFAULTS }
  }
}

const fraction = (percent) => Math.min(1, Math.max(0, Number(percent) / 100))

function start(audio, beiBlockade) {
  // Der Browser darf das Abspielen blockieren (noch kein Klick auf der Seite): dann still bleiben
  Promise.resolve(audio.play()).catch(() => { if (beiBlockade) beiBlockade() })
}

function create(name) {
  return new Audio(`${SOUND_BASE}${name}.mp3`)
}

export function playSfx(name) {
  const settings = readSettings()
  if (!settings.sfxEnabled) return
  const audio = create(name)
  audio.volume = fraction(settings.masterVolume)
  start(audio)
}

export function stopVoice() {
  if (voice) voice.pause()
  voice = null
}

/**
 * Spielt einen Funkspruch; ein neuer stoppt den alten. `beiEnde` kommt, wenn der Spruch
 * zu Ende ist (oder der Browser den Ton blockiert, damit nichts hängen bleibt).
 * Rückgabe: false, wenn die Stimme aus ist (dann kommt kein beiEnde).
 */
export function playVoice(name, beiEnde) {
  stopVoice()
  const settings = readSettings()
  if (!settings.voiceEnabled) return false
  const audio = create(name)
  audio.volume = fraction(settings.masterVolume)
  voice = audio
  const melden = () => { if (voice === audio && beiEnde) beiEnde() }
  audio.addEventListener('ended', melden)
  start(audio, melden)
  return true
}

function bedTarget() {
  const settings = readSettings()
  return fraction(settings.masterVolume) * fraction(settings.musicVolume) * bedLevel
}

/** Blendet die Ambience in FADE_MS auf `target`; `then` läuft danach (z. B. Anhalten). */
function fadeBedTo(target, then) {
  clearInterval(fadeTimer)
  const audio = bed
  if (!audio) return
  const steps = FADE_MS / FADE_STEP_MS
  const delta = (target - audio.volume) / steps
  let left = steps
  fadeTimer = setInterval(() => {
    left -= 1
    audio.volume = left <= 0 ? target : Math.min(1, Math.max(0, audio.volume + delta))
    if (left <= 0) {
      clearInterval(fadeTimer)
      fadeTimer = null
      if (then) then()
    }
  }, FADE_STEP_MS)
}

/** Startet die Ambience als Schleife. `level` (0–1) staffelt sie: Intro leiser, Spiel voll. */
export function startBed(level = 1) {
  const settings = readSettings()
  if (!settings.musicEnabled) return
  bedLevel = level
  if (bed) {
    fadeBedTo(bedTarget())
    return
  }
  bed = create(BED_FILE)
  bed.loop = true
  bed.volume = 0
  start(bed)
  fadeBedTo(bedTarget())
}

export function setBedLevel(level) {
  bedLevel = level
  if (bed) fadeBedTo(bedTarget())
}

export function stopBed() {
  const audio = bed
  if (!audio) return
  fadeBedTo(0, () => {
    audio.pause()
    if (bed === audio) bed = null
  })
}
