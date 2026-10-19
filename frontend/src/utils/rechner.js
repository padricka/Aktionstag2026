/**
 * Rechenkern des Taschenrechners (Calculator.vue): + − × ÷ mit Punkt-vor-Strich.
 * Bewusst ohne eval – die Eingabe kommt aus Tasten und Tastatur.
 * Rückgabe null, wenn der Ausdruck unvollständig oder nicht berechenbar ist.
 */
const OPERATOREN = { '+': '+', '−': '-', '-': '-', '×': '*', '*': '*', 'x': '*', '÷': '/', '/': '/' }

function zerlege(ausdruck) {
  const teile = []
  let zahl = ''
  for (const z of String(ausdruck).replace(/\s+/g, '')) {
    if (/[0-9]/.test(z)) { zahl += z; continue }
    if (z === ',' || z === '.') {
      if (zahl.includes('.')) return null
      zahl += '.'
      continue
    }
    const op = OPERATOREN[z]
    if (!op) return null
    if (zahl) { teile.push(Number(zahl)); zahl = '' }
    teile.push(op)
  }
  if (zahl) teile.push(Number(zahl))
  return teile
}

export function berechne(ausdruck) {
  const teile = zerlege(ausdruck)
  if (!teile || !teile.length) return null

  // Vorzeichen: Minus am Anfang gehört zur Zahl
  if (teile[0] === '-' && typeof teile[1] === 'number') teile.splice(0, 2, -teile[1])

  // abwechselnd Zahl, Operator, Zahl …
  if (teile.length % 2 === 0) return null
  for (let i = 0; i < teile.length; i++) {
    if ((i % 2 === 0) !== (typeof teile[i] === 'number')) return null
  }

  // erst × ÷, dann + −
  const summanden = [teile[0]]
  const vorzeichen = []
  for (let i = 1; i < teile.length; i += 2) {
    const op = teile[i]
    const b = teile[i + 1]
    if (op === '*' || op === '/') {
      if (op === '/' && b === 0) return null
      const a = summanden.pop()
      summanden.push(op === '*' ? a * b : a / b)
    } else {
      vorzeichen.push(op)
      summanden.push(b)
    }
  }
  let ergebnis = summanden[0]
  vorzeichen.forEach((op, i) => { ergebnis = op === '+' ? ergebnis + summanden[i + 1] : ergebnis - summanden[i + 1] })

  // 0.1 + 0.2 soll 0.3 sein, nicht 0.30000000000000004
  return Number.isFinite(ergebnis) ? Number(ergebnis.toPrecision(12)) : null
}

/** Anzeige im deutschen Format (Komma). */
export function zeigeZahl(wert) {
  return String(wert).replace('.', ',')
}
