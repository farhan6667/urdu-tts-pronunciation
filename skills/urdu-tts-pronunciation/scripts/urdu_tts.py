"""Shared logic for lint_script.py and check_takes.py. No audio and no Whisper here,
so all of it can be tested with plain text."""
import copy
import difflib
import json
import pathlib
import re
import unicodedata

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "lexicon.json"
# Short vowels and other marks that don't change which word it is (zabar, zer, pesh,
# tanween, shadda, sukun, superscript alif). Honorific signs (U+0610 to U+0614) are not here.
DIACRITICS = re.compile(r"[\u064B-\u0652\u0670]")
# A letter or one of those marks, in any script. Urdu punctuation (، ۔ ؟) is not one,
# so a word followed by ، still counts as a whole word.
LETTER = r"(?:[^\W\d_]|[\u064B-\u0652\u0670])"
DEV = r"[\u0900-\u097F]"
URDU = re.compile(r"[\u0600-\u06FF]")
# A pause: Urdu or Latin punctuation, a closing quote or bracket, or the end of the line.
PAUSE = r"(?=\s*(?:[،۔؟!,.;:\"'»)\]]|$))"
LATIN_WORD = re.compile(r"[A-Za-z0-9]*[A-Za-z][A-Za-z0-9\-']*")
DIGITS = re.compile(r"(?<![A-Za-z0-9])[0-9۰-۹٠-٩]+(?:[:,./\-][0-9۰-۹٠-٩]+)*%?[ءھ]?(?![A-Za-z])")
NEGATION = ("نہ", "مت")

# Arabic code points typed on an Arabic keyboard or pasted from the web, mapped to
# the Urdu ones. Only used for matching, and by --fix (which writes Urdu forms).
NORM = [("ي", "ی"), ("ى", "ی"), ("ك", "ک"), ("ه", "ہ"), ("ة", "ہ"), ("ۃ", "ہ"), ("أ", "ا"), ("إ", "ا"), ("ۀ", "ۂ")]
STRIP = re.compile("[\u0640\u200d\u200e\u200f\ufeff]")  # tatweel, ZWJ, direction marks, BOM

# Words ending in یں at a pause that are not commands.
NOT_COMMANDS = {"نہیں", "ہیں", "میں", "کہیں", "وہیں", "یہیں", "انہیں", "تمہیں", "ہمیں", "جنہیں", "تھیں",
                "گئیں", "کیں", "سکیں", "آپ", "جیں", "رہیں", "ہوئیں", "انھیں", "جنھیں", "کبھی"}
IRREGULAR = {"دیں": "دیجیے", "کریں": "کیجیے", "لیں": "لیجیے", "پیں": "پیجیے"}


def norm_text(s):
    s = unicodedata.normalize("NFC", s)  # ا + U+0653 becomes آ, ہ + U+0654 becomes ۂ
    for a, b in NORM:
        s = s.replace(a, b)
    # ZWNJ is often typed as an invisible word break in Urdu: treat it as a space.
    return STRIP.sub("", s).replace("\u200c", " ")


# ---------------------------------------------------------------- lexicon

class LexiconError(ValueError):
    pass


def _read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))


def validate_lexicon(lex):
    """Raise LexiconError naming the rule, before any slow work starts."""
    seen = set()
    for i, r in enumerate(lex.get("rules", [])):
        name = r.get("id", f"rule #{i + 1}")
        for k in ("id", "find", "use", "why"):
            if not isinstance(r.get(k), str) or not r[k].strip():
                raise LexiconError(f"{name}: '{k}' is missing")
        if r["id"] in seen:
            raise LexiconError(f"{name}: duplicate id")
        seen.add(r["id"])
        if r.get("level", "fix") not in ("fix", "check"):
            raise LexiconError(f"{name}: level must be 'fix' or 'check'")
        for k, pat in r.get("heard", {}).items():
            try:
                re.compile(pat)
            except re.error as e:
                raise LexiconError(f"{name}: heard.{k} is not a valid regex ({e})")
    return lex


def load_lexicon(path=None, extra=None):
    """The built-in lexicon (or `path` instead of it), with `extra` merged on top:
    extra rules are added, and a rule with the same id replaces the built-in one.
    Other sections are merged key by key, so a file with only "rules" is fine."""
    lex = _read(path or DATA)
    if extra:
        lex = merge_lexicon(lex, extra if isinstance(extra, dict) else _read(extra))
    return validate_lexicon(lex)


def merge_lexicon(base, add):
    out = copy.deepcopy(base)
    by_id = {r["id"]: i for i, r in enumerate(out.get("rules", []))}
    for r in add.get("rules", []):
        if r.get("id") in by_id:
            out["rules"][by_id[r["id"]]] = r
        else:
            out.setdefault("rules", []).append(r)
    for key, val in add.items():
        if key == "rules" or not isinstance(val, dict):
            continue
        sec = out.setdefault(key, {})
        for k, v in val.items():
            if isinstance(v, dict) and isinstance(sec.get(k), dict):
                sec[k] = {**sec[k], **v}
            elif isinstance(v, list) and isinstance(sec.get(k), list):
                sec[k] = sec[k] + [x for x in v if x not in sec[k]]
            else:
                sec[k] = v
    return validate_lexicon(out)


# ---------------------------------------------------------------- text helpers

def bare(s):
    """The text without short-vowel marks, so خُفیہ and خفیہ compare equal."""
    return DIACRITICS.sub("", s)


def norm_words(s):
    s = norm_text(s)
    for ch in "،۔؟:;‘’,.?!\"'«»":
        s = s.replace(ch, " ")
    return bare(s.replace("ۂ", "ہ")).split()


def word_re(find):
    # \b doesn't work for Arabic script, so use letter look-arounds. Any run of
    # spaces between the words of a phrase counts.
    body = r"\s+".join(re.escape(w) for w in find.split())
    return re.compile(rf"(?<!{LETTER}){body}(?!{LETTER})")


def contains(text, find):
    return bool(word_re(find).search(text))


def fixable(r):
    """True when --fix may put `use` in place of `find` by itself."""
    return (r.get("level", "fix") == "fix" and r.get("fixable", True) and r["find"] != r["use"]
            and "..." not in r["use"] and "/" not in r["use"])


def polite_form(word):
    """The -یے form of a -یں command, or None if it isn't one."""
    if word in IRREGULAR:
        return IRREGULAR[word]
    if word in NOT_COMMANDS or len(word) < 3:
        return None
    if word.endswith("ائیں"):
        return word[:-1] + "ے"
    if word.endswith("یں"):
        return word[:-2] + "یے"
    return None


# ---------------------------------------------------------------- script lint

def _item(level, id_, found, use, why, line, m=None):
    d = {"level": level, "id": id_, "found": found, "use": use, "why": why, "line": line}
    if m is not None:
        d["start"], d["end"] = m.start(), m.end()
    return d


def lint(text, lex=None):
    """Problems in a script before any audio is made, one dict per hit with level
    ("fix" or "check"), id, found, use, why, line (1-based, counting every physical
    line) and, where known, start/end offsets in the normalised line."""
    lex = lex or load_lexicon()
    out = []
    pol = lex.get("polite_imperatives", {})
    known = pol.get("forms", {})
    for n, raw in enumerate(text.splitlines() or [text], 1):
        line = norm_text(raw)
        if not line.strip():
            continue
        for r in lex.get("rules", []):
            if r["find"] != r["use"]:
                for m in word_re(norm_text(r["find"])).finditer(line):
                    out.append(_item(r.get("level", "fix"), r["id"], r["find"], r["use"], r["why"], n, m))
        # -یں at a pause. A clear command (after نہ or مت) must change; elsewhere it
        # may be a statement ("وہ کل آئیں۔"), so it's only a check. Verbs not in the
        # list get the regular -یے form, as a check.
        for m in re.finditer(rf"(?<!{LETTER})([^\W\d_]+یں){PAUSE}", line):
            word = m.group(1)
            polite = known.get(word) or polite_form(word)
            if not polite:
                continue
            before = line[:m.start()].split()
            level = "fix" if word in known and before and before[-1] in NEGATION else "check"
            out.append(_item(level, "polite-imperative", word, polite, pol.get("why", ""), n, m))
        tail = re.sub(r"[\s،۔؟!.,;:\"'»)\]]+$", "", line)
        for w in lex.get("weak_endings", {}).get("words", []):
            m = re.search(rf"(?<!{LETTER}){re.escape(w)}$", tail)
            if m:
                out.append(_item("check", "weak-ending", w, "move it away from the end of the paragraph",
                                 lex["weak_endings"].get("why", ""), n, m))
        if URDU.search(line):
            lat = lex.get("latin_letters", {})
            for m in LATIN_WORD.finditer(line):
                out.append(_item("fix", "latin-letters", m.group(0),
                                 lat.get("examples", {}).get(m.group(0), "spell it in Urdu letters"), lat.get("why", ""), n, m))
            num = lex.get("numbers", {})
            for m in DIGITS.finditer(line):
                out.append(_item("check", "numbers", m.group(0),
                                 num.get("examples", {}).get(m.group(0), "write it as words"), num.get("why", ""), n, m))
        hon = lex.get("honorifics", {})
        for sign, full in hon.get("signs", {}).items():
            for m in re.finditer(re.escape(sign), line):
                out.append(_item("fix", "honorific-sign", sign, full, hon.get("why", ""), n, m))
        m = re.search(r"سائبر\s*[،,]\s*سیکیورٹی", line)
        if m:
            out.append(_item("fix", "cyber-comma", "سائبر، سیکیورٹی", "سائبر سیکیورٹی",
                             "a comma between them makes a pause", n, m))
    return out


def fix_text(text, lex=None):
    """Apply only the safe, one-to-one fixes: plain spelling rules, the honorific signs
    whose wording never changes (ﷺ ؐ ﷻ), and listed -یں commands after نہ or مت.
    Everything else (register changes, ؑ ؓ ؒ, rewrites) needs a person. The result
    uses Urdu code points (Arabic ي ك ه become ی ک ہ)."""
    lex = lex or load_lexicon()
    text = norm_text(text)
    for r in lex.get("rules", []):
        if fixable(r):
            use = r["use"]
            text = word_re(norm_text(r["find"])).sub(lambda m: use, text)
    hon = lex.get("honorifics", {})
    for sign in hon.get("fixable", []):
        full = hon["signs"][sign]
        text = re.sub(rf"[ \t]*{re.escape(sign)}", lambda m: " " + full, text)
    for word, polite in lex.get("polite_imperatives", {}).get("forms", {}).items():
        for neg in NEGATION:
            text = re.sub(rf"(?<!{LETTER}){neg}(\s+){re.escape(word)}{PAUSE}",
                          lambda m: f"{neg}{m.group(1)}{polite}", text, flags=re.M)
    return text


# ---------------------------------------------------------------- take checks

def said_twice(s, allowed=frozenset()):
    """The same word (3+ letters) twice in a row, e.g. 'apps, apps', unless the
    script itself repeats it (آہستہ آہستہ، بہت بہت)."""
    w = [x.strip(".,!?;:'\"،۔").lower() for x in s.split()]
    return any(a == b and len(a) >= 3 and a not in allowed for a, b in zip(w, w[1:]))


def word_ratio(script, heard_ur):
    return difflib.SequenceMatcher(a=norm_words(script), b=norm_words(heard_ur), autojunk=False).ratio()


def check_take(script, ur, en, hi, gaps=(), lex=None, stall=0.6):
    """Checks for one take, from its three transcripts. gaps: seconds between
    consecutive Urdu words inside a sentence (from Whisper word timestamps).
    Returns {name: bool}."""
    lex = lex or load_lexicon()
    sb = bare(norm_text(script))
    ur, en, hi = (unicodedata.normalize("NFC", x) for x in (ur, en, hi))
    both = hi + " " + en
    sw = norm_words(script)
    doubles = {a for a, b in zip(sw, sw[1:]) if a == b}
    stutter = said_twice(" ".join(norm_words(ur)), doubles) or (not doubles and (said_twice(en) or said_twice(hi)))
    c = {"no_repeat": not stutter, "no_stall": not any(g > stall for g in gaps)}
    for r in lex.get("rules", []):
        h = r.get("heard")
        if not h:
            continue
        hit = contains(sb, bare(norm_text(r["find"]))) or contains(sb, bare(norm_text(r["use"].split(" / ")[0])))
        if not hit:
            continue
        pat = {k: unicodedata.normalize("NFC", v) for k, v in h.items()}
        ok = True
        if "hi_good" in pat:
            ok &= bool(re.search(pat["hi_good"], hi))
        if "any_good" in pat:
            ok &= bool(re.search(pat["any_good"], both, re.I))
        if "hi_bad" in pat:
            ok &= not re.search(pat["hi_bad"], hi)
        if "any_bad" in pat:
            ok &= not re.search(pat["any_bad"], both, re.I)
        if "en_count" in pat:
            want = len(word_re(bare(norm_text(r["find"]))).findall(sb))
            ok &= len(re.findall(pat["en_count"], en, re.I)) >= want
        c[r["id"]] = ok
    return c


def rank(rows):
    """Best take first: passes everything, then most checks passed, then most words right."""
    return sorted(rows, key=lambda r: (not all(r["checks"].values()), -sum(r["checks"].values()), -r["ratio"]))
