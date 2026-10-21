// Verkleinern statt Abschneiden oder Scrollen (fix/alles-passt).

// Inhalt mit fester natürlicher Breite (z. B. ein Notizzettel) in eine Spalte einpassen.
export function skalaBreite(natur, platz) {
  if (!natur || !platz) return 1
  return Math.min(1, platz / natur)
}

// Inhalt, dessen Höhe von seiner Breite abhängt, ganz in eine Fläche einpassen.
// Verkleinert man ihn, darf er (vor dem Verkleinern) breiter werden – das macht ihn
// wieder niedriger. Gedämpft (geometrisches Mittel), sonst springt die Skala hin und her.
export function skalaFlaeche(platzBreite, platzHoehe, hoeheBei) {
  if (!platzBreite || !platzHoehe) return { skala: 1, breite: platzBreite }
  let skala = 1
  for (let i = 0; i < 12; i++) {
    const ziel = Math.min(1, platzHoehe / hoeheBei(platzBreite / skala))
    const neu = Math.sqrt(skala * ziel)
    if (Math.abs(neu - skala) < 0.001) break
    skala = neu
  }
  // Sicherheitsrand: lieber minimal kleiner als einen Pixel abgeschnitten
  skala = Math.min(skala, platzHoehe / hoeheBei(platzBreite / skala))
  return { skala, breite: platzBreite / skala }
}
