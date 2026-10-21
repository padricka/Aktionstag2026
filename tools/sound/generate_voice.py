"""
Erzeugt die Roh-Sprache fürs Intro mit VoiceStudio (lokal, kostenlos).

  1. VoiceStudio starten (Backend lauscht auf http://127.0.0.1:3900)
  2. python tools/sound/generate_voice.py            # schreibt tools/sound/raw/slide-N.wav
  3. python tools/sound/build_sounds.py              # macht daraus die Funk-Sprüche

Dauert auf der CPU ca. 1,5 Minuten pro Zeile. Die fertigen mp3-Dateien liegen im Repo
(frontend/public/sound), diesen Schritt braucht man nur, wenn sich ein Text ändert.

Die Texte müssen zu SLIDES in frontend/src/components/IntroStory.vue passen.
"""
import subprocess
import sys
from pathlib import Path

API = "http://127.0.0.1:3900/generate"
RAW = Path(__file__).resolve().parent / "raw"

# Sprecher M. Kaiser: männlich, mittleres Alter, tief (festgelegte Stimme, seed 11)
VOICE = {
    "language": "de",
    "instruct": "male, middle-aged, low pitch",
    "speed": "1.05",
    "seed": "11",
    "effect_preset": "raw",
}

LINES = [
    "Alarm im Rechenzentrum! In Raum B-04 brennt ein Server-Rack – ausgerechnet das mit den Rentendaten.",
    "Uns bleiben nur ein paar Minuten, bis das System ganz ausfällt. Dann sind die Daten von Millionen Versicherten weg.",
    "Ihr drei seid das Notfall-Team: der Leitstand im Kontrollraum, einer vor dem Rack, einer dahinter. "
    "Jeder sieht nur seinen Teil – keiner hat die ganze Lösung.",
    "Meine Wartungsnotizen liegen bei euch – leider zerrissen. Jeder hat ein Stück mit einer Regel. "
    "Lest sie euch gegenseitig vor!",
    "Und ganz wichtig: Redet miteinander – nicht durcheinander! Jede falsche Eingabe kostet den Server Leben.",
    "Kurz die Regeln – dann rettet den Server!",
]


def generate(number: int, text: str) -> None:
    target = RAW / f"slide-{number}.wav"
    cmd = ["curl", "-s", "--fail-with-body", "-m", "900", "-o", str(target), "-F", f"text={text}"]
    for key, value in VOICE.items():
        cmd += ["-F", f"{key}={value}"]
    cmd.append(API)
    print(f"slide-{number} ...", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"VoiceStudio nicht erreichbar oder Fehler ({result.returncode}): {result.stderr or result.stdout}")


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for number, text in enumerate(LINES, start=1):
        generate(number, text)
    print(f"Fertig: {RAW}")


if __name__ == "__main__":
    main()
