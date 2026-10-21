"""
Baut alle Sounds von DRV-BOX neu (nur ffmpeg, keine Lizenzen, keine KI nötig):

  python tools/sound/build_sounds.py                     # alles
  python tools/sound/build_sounds.py --raw C:\\pfad\\vo    # Funk-Sprüche aus Roh-Sprachdateien

Ausgabe: frontend/public/sound/*.mp3  (wird im Spiel per /sound/<name>.mp3 geladen)

Voraussetzung: `ffmpeg` und `ffprobe` im PATH.
Die Roh-Sprachdateien (slide-1.wav … slide-6.wav) erzeugt generate_voice.py mit VoiceStudio.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "sound"
SR = 24000
BED_SECONDS = 60          # ganze Perioden aller Töne passen hinein → nahtloser Loop


def ffmpeg(*args: str) -> None:
    cmd = ["ffmpeg", "-y", "-v", "error", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"ffmpeg fehlgeschlagen:\n{' '.join(cmd)}\n{result.stderr}")


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def mp3(*inputs_and_filter: str, out_name: str) -> None:
    """Letzte Argumente: ffmpeg-Eingaben und Filter; schreibt als mp3 nach OUT."""
    OUT.mkdir(parents=True, exist_ok=True)
    ffmpeg(*inputs_and_filter, "-ar", "44100", "-ac", "1", "-b:a", "128k", str(OUT / out_name))
    print(f"  {out_name}")


def tone(expr: str, seconds: float) -> list[str]:
    """Eingabe aus einer Formel in t (Sekunden)."""
    return ["-f", "lavfi", "-i", f"aevalsrc=exprs='{expr}':s={SR}:d={seconds}"]


# ------------------------------------------------------------------ Funk-Sprüche
def funk(raw: Path, name: str) -> None:
    """Sprache → Funkgerät: Start-Piep, Bandpass + Verzerrung, Rauschen/Knacken, End-Piep."""
    voice = duration(raw)
    lead = 0.33                       # Pause nach dem Start-Piep
    end_beep_at = int((lead + voice + 0.03) * 1000)
    total = lead + voice + 0.45
    graph = (
        "[0:a]highpass=f=380,lowpass=f=3000,acompressor=threshold=-22dB:ratio=8:attack=3:release=60,"
        f"volume=2.2,asoftclip=type=tanh,volume=0.7,adelay={int(lead * 1000)}|{int(lead * 1000)}[v];"
        "[1:a]volume=0.55[b1];"
        f"[2:a]volume=0.55,adelay={end_beep_at}|{end_beep_at}[b2];"
        "[3:a]highpass=f=600,lowpass=f=3400,volume=0.018[n];"
        "[4:a]highpass=f=500,lowpass=f=3800,volume=0.5[c];"
        f"[v][b1][b2][n][c]amix=inputs=5:normalize=0:duration=longest,atrim=0:{total:.2f},"
        "loudnorm=I=-13:TP=-1.0:LRA=7[o]"
    )
    mp3(
        "-i", str(raw),
        "-f", "lavfi", "-i", f"sine=frequency=1250:duration=0.16:sample_rate={SR}",
        "-f", "lavfi", "-i", f"sine=frequency=950:duration=0.10:sample_rate={SR}",
        "-f", "lavfi", "-i", f"anoisesrc=color=white:amplitude=0.5:duration={total + 1:.1f}:sample_rate={SR}",
        "-f", "lavfi", "-i",
        f"aevalsrc=exprs='gt(random(0),0.9985)*(random(1)-0.5)*3':s={SR}:d={total + 1:.1f}",
        "-filter_complex", graph, "-map", "[o]",
        out_name=name,
    )


def build_voice(raw_dir: Path) -> None:
    print("Funk-Spruche:")
    files = sorted(raw_dir.glob("slide-*.wav"))
    if not files:
        print(f"  keine slide-*.wav in {raw_dir} – übersprungen")
        return
    for raw in files:
        funk(raw, f"intro-{raw.stem}.mp3")


# ------------------------------------------------------------------ Ambience
def build_bed() -> None:
    """Serverraum: Lüfterrauschen, 50-Hz-Brummen, dunkler Drone, gelegentlich Relais-Klicks."""
    print("Ambience:")
    clicks = [7.2, 19.8, 31.1, 44.6, 53.3]
    click_inputs: list[str] = []
    for _ in clicks:
        click_inputs += ["-f", "lavfi", "-i",
                         f"aevalsrc=exprs='(random(0)-0.5)*exp(-t*420)*0.9':s={SR}:d=0.06"]
    # Eingänge: 0 brown, 1 pink, 2-4 Brummen (50/100/150 Hz), 5-6 Drone, ab 7 die Klicks
    click_graph = [
        f"[{7 + i}:a]highpass=f=900,adelay={int(at * 1000)}|{int(at * 1000)}[k{i}]"
        for i, at in enumerate(clicks)
    ]
    mix_inputs = "[fan][hum][drone]" + "".join(f"[k{i}]" for i in range(len(clicks)))
    graph = (
        "[0:a]lowpass=f=420,volume=0.9[fan0];"
        "[1:a]highpass=f=900,lowpass=f=2600,volume=0.035[air];"
        "[fan0][air]amix=inputs=2:normalize=0[fan];"
        "[2:a][3:a][4:a]amix=inputs=3:normalize=0,volume=0.07,tremolo=f=0.1:d=0.25[hum];"
        "[5:a][6:a]amix=inputs=2:normalize=0,volume=0.05[drone];"
        + ";".join(click_graph) + ";"
        f"{mix_inputs}amix=inputs={3 + len(clicks)}:normalize=0,atrim=0:{BED_SECONDS},"
        "loudnorm=I=-26:TP=-3:LRA=5[o]"
    )
    mp3(
        "-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.6:duration={BED_SECONDS}:sample_rate={SR}",
        "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.6:duration={BED_SECONDS}:sample_rate={SR}",
        "-f", "lavfi", "-i", f"sine=frequency=50:duration={BED_SECONDS}:sample_rate={SR}",
        "-f", "lavfi", "-i", f"sine=frequency=100:duration={BED_SECONDS}:sample_rate={SR}",
        "-f", "lavfi", "-i", f"sine=frequency=150:duration={BED_SECONDS}:sample_rate={SR}",
        "-f", "lavfi", "-i", f"sine=frequency=55:duration={BED_SECONDS}:sample_rate={SR}",
        "-f", "lavfi", "-i", f"sine=frequency=55.5:duration={BED_SECONDS}:sample_rate={SR}",
        *click_inputs,
        "-filter_complex", graph, "-map", "[o]",
        out_name="bed-serverraum.mp3",
    )


# ------------------------------------------------------------------ Effekte
def build_sfx() -> None:
    print("Effekte:")
    # Fehler: kurzer, rauer Buzz (zwei leicht verstimmte tiefe Rechtecke)
    mp3(*tone("0.35*(gt(sin(2*PI*140*t),0)*2-1)*exp(-t*5)+0.3*(gt(sin(2*PI*147*t),0)*2-1)*exp(-t*5)", 0.4),
        "-af", "lowpass=f=1800,volume=0.5", out_name="sfx-error.mp3")
    # Aufgabe gelöst: zwei steigende, weiche Töne
    mp3(*tone("0.5*sin(2*PI*880*t)*exp(-t*9)*lt(t,0.14)+0.5*sin(2*PI*1320*(t-0.12))*exp(-(t-0.12)*7)*gt(t,0.12)", 0.55),
        "-af", "volume=0.6", out_name="sfx-solved.mp3")
    # Hilfe-Notiz abreißen: Papier-Rauschen mit raschem Zittern
    mp3("-f", "lavfi", "-i", f"anoisesrc=color=white:amplitude=0.8:duration=0.45:sample_rate={SR}",
        "-af", "highpass=f=1500,lowpass=f=7000,tremolo=f=38:d=0.9,afade=t=in:d=0.05,afade=t=out:st=0.25:d=0.2,volume=0.5",
        out_name="sfx-hint.mp3")
    # Countdown-Piep (3, 2, 1) und „LOS“
    mp3(*tone("0.5*sin(2*PI*1000*t)*lt(t,0.14)*(1-exp(-t*400))", 0.2), out_name="sfx-count.mp3")
    mp3(*tone("0.5*sin(2*PI*1500*t)*exp(-t*3.5)", 0.7), out_name="sfx-go.mp3")
    # „System online“: dumpfer Schlag mit Nachhall
    mp3(*tone("0.9*sin(2*PI*(48+60*exp(-t*14))*t)*exp(-t*4.5)", 1.4),
        "-af", "aecho=0.7:0.6:80|160:0.35|0.2,volume=0.8", out_name="sfx-online.mp3")
    # Sieg: aufsteigendes Arpeggio
    arp = "+".join(
        f"0.35*sin(2*PI*{f}*(t-{i * 0.16}))*exp(-(t-{i * 0.16})*5)*gt(t,{i * 0.16})"
        for i, f in enumerate((523, 659, 784, 1047))
    )
    mp3(*tone(arp, 1.4), "-af", "aecho=0.6:0.5:60:0.25,volume=0.7", out_name="sfx-win.mp3")
    # Game Over: fallender Ton + Schlag
    mp3(*tone("0.6*sin(2*PI*(430*exp(-t*1.6)+40)*t)*exp(-t*1.3)", 2.0),
        "-af", "lowpass=f=900,volume=0.7", out_name="sfx-gameover.mp3")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--raw", type=Path, default=ROOT / "tools" / "sound" / "raw",
                        help="Ordner mit slide-1.wav … slide-6.wav (Roh-Sprache aus VoiceStudio)")
    parser.add_argument("--only", choices=("voice", "bed", "sfx"), help="nur eine Gruppe bauen")
    args = parser.parse_args()
    if args.only in (None, "voice"):
        build_voice(args.raw)
    if args.only in (None, "bed"):
        build_bed()
    if args.only in (None, "sfx"):
        build_sfx()
    print(f"Fertig: {OUT}")


if __name__ == "__main__":
    main()
