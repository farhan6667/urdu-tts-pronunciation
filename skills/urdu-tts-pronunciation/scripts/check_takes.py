"""Rank Urdu narration takes the way a careful listener would, before anyone listens.

One line:     python check_takes.py --text-file line.txt take_1.wav take_2.wav ...
Whole script: python check_takes.py --script script.txt "takes/line{n}_*.wav"

Each take is transcribed three times with faster-whisper: Urdu (are all the
script's words there), English (are English words said as English) and
Devanagari (which shows khufiya vs khafiya, pin vs pan, step vs steep, WhatsApp
as "ep" vs "aap", Department with a hard or soft D). It also catches a word said
twice in a row and a long stall. Works with any TTS engine: it only listens.

With --script, line n of the script (1-based, counted like lint_script.py: every
physical line, blank ones included but never checked) is matched with
the files from the pattern where {n} is n, written as 1 or 01 or 001.

Needs: pip install faster-whisper, and ffmpeg on PATH (or FFMPEG=<path>).
Exit code: 0 every line has a take that passes, 1 some line has none, 2 bad input.
"""
import argparse
import glob
import json
import os
import pathlib
import shutil
import subprocess
import sys

from urdu_tts import LexiconError, check_take, load_lexicon, merge_lexicon, rank, word_ratio


def out_stream():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    return sys.stdout


def sentence_gaps(words):
    """Gaps between consecutive words, leaving out the pause after a sentence end."""
    return [y.start - x.end for x, y in zip(words, words[1:]) if not x.word.strip().endswith(("۔", ".", "؟", "?", "!"))]


def expand(patterns):
    files = []
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        files += hits if hits else ([pat] if os.path.exists(pat) else [])
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("takes", nargs="+", help="audio files or glob patterns; with --script, one pattern containing {n}")
    ap.add_argument("--text", help="the script line these takes should say")
    ap.add_argument("--text-file", help="the script line, from a UTF-8 file")
    ap.add_argument("--script", help="the whole script, one paragraph per line, to check every line")
    ap.add_argument("--lexicon", action="append", default=[], help="your own lexicon.json, added to the built-in one")
    ap.add_argument("--hint", default="", help="a few vocabulary words for Whisper (never the script itself)")
    ap.add_argument("--model", default="small", help="faster-whisper model (default: small)")
    ap.add_argument("--models", default=None, help="where to keep the model (default: faster-whisper's own cache)")
    ap.add_argument("--stall", type=float, default=0.6, help="longest allowed gap between words, seconds")
    ap.add_argument("--json", help="write the full report here")
    a = ap.parse_args(argv)
    out = out_stream()

    try:
        lex = load_lexicon()
        for extra in a.lexicon:
            lex = merge_lexicon(lex, json.loads(pathlib.Path(extra).read_text(encoding="utf-8-sig")))
        if a.script:
            lines = pathlib.Path(a.script).read_text(encoding="utf-8-sig").splitlines()
            if len(a.takes) != 1 or "{n}" not in a.takes[0]:
                ap.error("with --script, give one pattern containing {n}, e.g. \"takes/line{n}_*.wav\"")
            jobs = []
            for n, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                line = line.strip()
                files = []
                for form in (str(n), f"{n:02d}", f"{n:03d}"):
                    files += [f for f in expand([a.takes[0].replace("{n}", form)]) if f not in files]
                jobs.append((n, line, files))
        else:
            if not (a.text or a.text_file):
                ap.error("give --text, --text-file or --script")
            text = a.text or pathlib.Path(a.text_file).read_text(encoding="utf-8-sig").strip()
            jobs = [(1, text, expand(a.takes))]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, LexiconError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not any(files for _, _, files in jobs):
        print("error: no audio files matched", file=sys.stderr)
        return 2
    ff = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if not ff:
        print("error: ffmpeg not found: put it on PATH or set FFMPEG", file=sys.stderr)
        return 2
    try:
        import numpy as np
        from faster_whisper import WhisperModel
    except ImportError:
        print("error: faster-whisper is not installed: pip install faster-whisper", file=sys.stderr)
        return 2

    def load(f):
        raw = subprocess.run([ff, "-v", "error", "-nostdin", "-i", f, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                             capture_output=True, check=True).stdout
        return np.frombuffer(raw, dtype=np.float32)

    wm = WhisperModel(a.model, device="cpu", compute_type="int8", download_root=a.models)
    report, all_ok = [], True
    for n, text, files in jobs:
        if a.script:
            out.write(f"\nline {n}: {text[:60]}{'...' if len(text) > 60 else ''}\n")
        if a.script:
            out.write("  takes: " + (", ".join(os.path.basename(f) for f in files) or "none matched") + "\n")
        if not files:
            out.write("  no takes found\n")
            all_ok = False
            continue
        rows = []
        for f in files:
            try:
                audio = load(f)
            except subprocess.CalledProcessError as e:
                out.write(f"  {os.path.basename(f)}  could not be read: {e.stderr.decode(errors='replace').strip()[:120]}\n")
                continue
            segs = wm.transcribe(audio, language="ur", beam_size=5, word_timestamps=True, initial_prompt=a.hint or None)[0]
            words = [w for s in segs for w in s.words]
            ur = " ".join(w.word.strip() for w in words)
            hi = " ".join(x.text.strip() for x in wm.transcribe(audio, language="hi", beam_size=5, temperature=0)[0])
            en = " ".join(x.text.strip() for x in wm.transcribe(audio, language="en", beam_size=5, temperature=0)[0])
            gaps = sentence_gaps(words)
            checks = check_take(text, ur, en, hi, gaps, lex, a.stall)
            ratio = word_ratio(text, ur)
            rows.append({"line": n, "take": f, "ratio": round(ratio, 3), "checks": checks,
                         "seconds": round(len(audio) / 16000, 2), "ur": ur, "en": en, "hi": hi})
            bad = [k for k, v in checks.items() if not v]
            out.write(f"  {os.path.basename(f)}  words {ratio:.0%}  {'OK' if not bad else 'fails: ' + ', '.join(bad)}\n")
        if not rows:
            all_ok = False
            continue
        rows = rank(rows)
        w = rows[0]
        ok = all(w["checks"].values())
        all_ok &= ok
        verdict = "passes every check" if ok else "no take passes everything: make more takes or reword the line"
        out.write(f"  BEST {os.path.basename(w['take'])}  words {w['ratio']:.0%}  ({verdict})\n")
        if not a.script:
            out.write(f"    EN: {w['en'][:200]}\n    HI: {w['hi'][:200]}\n")
        report += rows
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    out.flush()
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
