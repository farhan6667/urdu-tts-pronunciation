"""Check an Urdu narration script before any audio is made.

    python lint_script.py script.txt
    python lint_script.py script.txt --fix            # also writes script.fixed.txt
    python lint_script.py script.txt --lexicon my-words.json --json
    python lint_script.py - < script.txt

Finds words AI voices say wrong (with the spelling that fixes each), -یں commands
at a pause, key words at the very end of a paragraph, Latin letters and digits
inside Urdu, honorific signs, and a comma inside سائبر سیکیورٹی.
Exit code: 0 nothing to fix, 1 something must be fixed, 2 the file couldn't be read.
"""
import argparse
import json
import pathlib
import sys
from collections import OrderedDict

from urdu_tts import LexiconError, fix_text, lint, load_lexicon, merge_lexicon


def out_stream():
    # Urdu on a Windows console: write UTF-8 whatever the console code page is.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    return sys.stdout


def read_text(name):
    if name == "-":
        return sys.stdin.buffer.read().decode("utf-8-sig")
    return pathlib.Path(name).read_text(encoding="utf-8-sig")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file", help="the script (UTF-8 text, one paragraph per line), or - for stdin")
    ap.add_argument("--lexicon", action="append", default=[], help="your own lexicon.json, added to the built-in one (repeatable)")
    ap.add_argument("--fix", action="store_true", help="write <file>.fixed.txt with the safe one-to-one fixes applied")
    ap.add_argument("--json", action="store_true", help="print every problem as JSON")
    a = ap.parse_args(argv)
    out = out_stream()
    try:
        text = read_text(a.file)
        lex = load_lexicon()
        for extra in a.lexicon:
            lex = merge_lexicon(lex, json.loads(pathlib.Path(extra).read_text(encoding="utf-8-sig")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, LexiconError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    problems = lint(text, lex)

    if a.json:
        out.write(json.dumps(problems, ensure_ascii=False, indent=1) + "\n")
    elif not problems:
        out.write("No problems found.\n")
    else:
        # One line per (line, problem), with a count when it repeats on that line.
        grouped = OrderedDict()
        for p in problems:
            key = (p["line"], p["level"], p["id"], p["found"])
            grouped.setdefault(key, [p, 0])[1] += 1
        for (line, level, _, found), (p, count) in grouped.items():
            times = f" (x{count})" if count > 1 else ""
            out.write(f"line {line}: [{level}] {found}{times}  ->  {p['use']}\n        {p['why']}\n")
        fixes = sum(1 for p in problems if p["level"] == "fix")
        out.write(f"\n{fixes} to fix, {len(problems) - fixes} to check by ear.\n")

    if a.fix and a.file == "-":
        out.write("\n--- fixed script ---\n" + fix_text(text, lex) + "\n")
    elif a.fix:
        src = pathlib.Path(a.file)
        dst = src.with_name(src.stem + ".fixed" + src.suffix)
        dst.write_text(fix_text(text, lex), encoding="utf-8")
        left = [p for p in lint(dst.read_text(encoding="utf-8"), lex) if p["level"] == "fix"]
        out.write(f"Wrote {dst.name}. {len(left)} fix item(s) still need a rewrite by hand.\n")
    out.flush()
    return 1 if any(p["level"] == "fix" for p in problems) else 0


if __name__ == "__main__":
    sys.exit(main())
