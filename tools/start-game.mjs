// Startet DRV-BOX lokal OHNE Docker – für Entwicklung an EINEM Rechner.
// Aufruf im Projektordner:  npm run game
//
// Was passiert:
//   1. backend/.venv anlegen und requirements.txt installieren (nur wenn nötig)
//   2. frontend/node_modules installieren (nur wenn nötig)
//   3. Redis-Ersatz (backend/dev_redis.py, fakeredis) auf Port 6379
//      – läuft dort schon ein Redis, wird dieser benutzt
//   4. Backend (daphne) auf 127.0.0.1:8000
//   5. Frontend (vite) auf Port 5173, Browser öffnet sich
// Beenden: Strg+C – stoppt alles.
//
// Läuft unter Windows, macOS und Linux. Bewusst ohne zusätzliche npm-Pakete.

import { spawn, spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { existsSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import net from 'node:net'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const BACKEND = path.join(ROOT, 'backend')
const FRONTEND = path.join(ROOT, 'frontend')
const IS_WIN = process.platform === 'win32'

const REDIS_PORT = 6379
const BACKEND_PORT = 8000
const FRONTEND_PORT = 5173

const children = []
let stopping = false

function log(msg) {
  console.log(`\x1b[36m[start]\x1b[0m ${msg}`)
}

function fail(msg) {
  console.error(`\x1b[31m[start] FEHLER:\x1b[0m ${msg}`)
  shutdown(1)
}

// ---------- Hilfsfunktionen ----------

function run(cmd, args, opts = {}) {
  const res = spawnSync(cmd, args, { stdio: 'inherit', ...opts })
  return res.status === 0
}

function works(cmd, args) {
  const res = spawnSync(cmd, args, { encoding: 'utf8' })
  return res.status === 0 ? `${res.stdout}${res.stderr}`.trim() : null
}

function portOpen(port) {
  return new Promise((resolve) => {
    const sock = net.connect({ host: '127.0.0.1', port })
    sock.once('connect', () => { sock.destroy(); resolve(true) })
    sock.once('error', () => resolve(false))
  })
}

async function waitForPort(port, name, child, seconds = 60) {
  for (let i = 0; i < seconds * 4; i++) {
    if (await portOpen(port)) return
    if (child && child.exitCode !== null) fail(`${name} hat sich beendet (siehe Ausgabe oben).`)
    await new Promise((r) => setTimeout(r, 250))
  }
  fail(`${name} antwortet nach ${seconds} s nicht auf Port ${port}.`)
}

function hashFile(file) {
  return createHash('sha256').update(readFileSync(file)).digest('hex')
}

// Startet einen Dauerprozess und versieht jede Ausgabezeile mit einem Präfix.
function start(name, color, cmd, args, opts) {
  const child = spawn(cmd, args, { stdio: ['ignore', 'pipe', 'pipe'], ...opts })
  const prefix = `\x1b[${color}m[${name}]\x1b[0m `
  for (const stream of [child.stdout, child.stderr]) {
    let rest = ''
    stream.setEncoding('utf8')
    stream.on('data', (chunk) => {
      const lines = (rest + chunk).split(/\r?\n/)
      rest = lines.pop()
      for (const line of lines) process.stdout.write(prefix + line + '\n')
    })
  }
  child.on('exit', (code) => {
    if (!stopping) {
      console.error(`\x1b[31m[start]\x1b[0m ${name} wurde beendet (Code ${code}). Stoppe alles.`)
      shutdown(code || 1)
    }
  })
  children.push(child)
  return child
}

function shutdown(code = 0) {
  if (stopping) return
  stopping = true
  for (const child of children) {
    if (child.exitCode !== null) continue
    if (IS_WIN) spawnSync('taskkill', ['/pid', String(child.pid), '/T', '/F'], { stdio: 'ignore' })
    else child.kill('SIGTERM')
  }
  process.exit(code)
}

process.on('SIGINT', () => { log('Stoppe alles …'); shutdown(0) })
process.on('SIGTERM', () => shutdown(0))

// ---------- 1. Python / Backend-Abhängigkeiten ----------

function findPython() {
  // Unter Windows zuerst den Launcher "py" (der Store-Platzhalter "python" ist sonst eine Falle).
  const candidates = IS_WIN
    ? [['py', ['-3']], ['python', []], ['python3', []]]
    : [['python3', []], ['python', []]]
  for (const [cmd, pre] of candidates) {
    const out = works(cmd, [...pre, '--version'])
    if (out && /Python 3\.(1[0-9]|[2-9][0-9])/.test(out)) return { cmd, pre, version: out }
  }
  return null
}

function setupBackend() {
  const venv = path.join(BACKEND, '.venv')
  const venvPython = IS_WIN
    ? path.join(venv, 'Scripts', 'python.exe')
    : path.join(venv, 'bin', 'python')

  if (!existsSync(venvPython)) {
    const py = findPython()
    if (!py) fail('Kein Python 3.10+ gefunden. Bitte Python 3.13 installieren (python.org, Haken bei "Add to PATH").')
    log(`Lege backend/.venv an (${py.version}) …`)
    if (!run(py.cmd, [...py.pre, '-m', 'venv', venv])) fail('Konnte backend/.venv nicht anlegen.')
  }

  const req = path.join(BACKEND, 'requirements.txt')
  const marker = path.join(venv, '.requirements-hash')
  const hash = hashFile(req)
  if (!existsSync(marker) || readFileSync(marker, 'utf8') !== hash) {
    log('Installiere Backend-Pakete (requirements.txt) …')
    if (!run(venvPython, ['-m', 'pip', 'install', '-r', req], { cwd: BACKEND })) {
      fail('pip install ist fehlgeschlagen (siehe Ausgabe oben).')
    }
    writeFileSync(marker, hash)
  }
  return venvPython
}

// ---------- 2. Frontend-Abhängigkeiten ----------

function setupFrontend() {
  const installed = path.join(FRONTEND, 'node_modules', '.package-lock.json')
  const lock = path.join(FRONTEND, 'package-lock.json')
  const needed = !existsSync(installed) || statSync(lock).mtimeMs > statSync(installed).mtimeMs
  if (!needed) return

  log('Installiere Frontend-Pakete (npm ci) …')
  // Über "npm run" gestartet, zeigt npm_execpath auf npm-cli.js → ohne Shell, auch unter Windows.
  const npmCli = process.env.npm_execpath
  const ok = npmCli && npmCli.endsWith('.js')
    ? run(process.execPath, [npmCli, 'ci'], { cwd: FRONTEND })
    : run('npm', ['ci'], { cwd: FRONTEND, shell: IS_WIN })
  if (!ok) fail('npm ci ist fehlgeschlagen (siehe Ausgabe oben).')
}

// ---------- Start ----------

const [major, minor] = process.versions.node.split('.').map(Number)
if (major < 20 || (major === 20 && minor < 19)) {
  fail(`Node ${process.versions.node} ist zu alt. Vite braucht Node 20.19 oder neuer (empfohlen: 22 LTS).`)
}

const python = setupBackend()
setupFrontend()

const env = {
  ...process.env,
  // Feste lokale Werte – überschreiben evtl. alte Docker-Einstellungen in der Umgebung.
  DEBUG: 'True',
  REDIS_HOST: '127.0.0.1',
  REDIS_PORT: String(REDIS_PORT),
  USE_IN_MEMORY_CHANNEL_LAYER: 'False',
  PYTHONUNBUFFERED: '1',
  PYTHONIOENCODING: 'utf-8',
}

if (await portOpen(REDIS_PORT)) {
  log(`Auf Port ${REDIS_PORT} läuft schon ein Redis – den benutze ich.`)
} else {
  log('Starte Redis-Ersatz …')
  const redis = start('redis', '35', python, ['dev_redis.py', String(REDIS_PORT)], { cwd: BACKEND, env })
  await waitForPort(REDIS_PORT, 'Redis-Ersatz', redis)
}

if (await portOpen(BACKEND_PORT)) {
  fail(`Port ${BACKEND_PORT} ist schon belegt. Läuft das Spiel noch (oder Docker)? Bitte erst beenden.`)
}
log('Starte Backend …')
const backend = start('backend', '33', python,
  ['-m', 'daphne', '-b', '127.0.0.1', '-p', String(BACKEND_PORT), 'backend.asgi:application'],
  { cwd: BACKEND, env })
await waitForPort(BACKEND_PORT, 'Backend', backend)

if (await portOpen(FRONTEND_PORT)) {
  fail(`Port ${FRONTEND_PORT} ist schon belegt. Läuft das Frontend noch (oder Docker)? Bitte erst beenden.`)
}
log('Starte Frontend …')
const viteBin = path.join(FRONTEND, 'node_modules', 'vite', 'bin', 'vite.js')
const openBrowser = !process.argv.includes('--no-open')
start('frontend', '32', process.execPath,
  [viteBin, '--port', String(FRONTEND_PORT), '--strictPort', ...(openBrowser ? ['--open'] : [])],
  { cwd: FRONTEND, env })
await waitForPort(FRONTEND_PORT, 'Frontend', null)

log('')
log(`\x1b[1mDRV-BOX läuft:  http://localhost:${FRONTEND_PORT}\x1b[0m`)
log('Beenden mit Strg+C.')
