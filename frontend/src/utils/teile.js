// Fundorte und Teile (GAME_DESIGN.md, „Fundorte und Teilekiste“). Welches Teil gefunden ist
// und sein Etikett kommen vom Backend (game_tick.parts); hier stehen nur Namen und Texte.

export const TEIL_REIHENFOLGE = ['psu', 'fan', 'disk']

export const TEILE = {
  psu: { name: 'Netzteil', fundort: 'schrank' },
  fan: { name: 'Lüfter', fundort: 'lager' },
  disk: { name: 'Backup-Platte', fundort: 'tresor' },
}

export const FUNDORTE = {
  schrank: { titel: 'Ersatzteilschrank', text: 'Der Alarm ist aus – das Schloss springt auf.' },
  lager: { titel: 'Lager', text: 'Das Feuer ist gelöscht – die Brandschutztür entriegelt.' },
  tresor: { titel: 'Datentresor', text: 'Die Daten sind gerettet – der Tresor öffnet sich.' },
}

export const AUFGABEN_TITEL = {
  1: 'Alarm verifizieren',
  2: 'Löschprotokoll',
  3: 'Datenrettung',
  4: 'Neustart',
}
