# Changelog

## 0.1.1 (2026-10-24)

Hardening after a thorough QA pass:

- `ci.yml`: `actions/checkout` and `actions/setup-python` pinned to commit SHAs instead of
  floating version tags, so CI can't silently change behavior if an upstream tag moves.
- README: the quick-start example now says the sample output is trimmed, matching how
  `check_takes.py`'s own example already describes its output.
- Full test suite (64 tests) still passes; fresh install and the full `check_takes.py`
  pipeline (including a real Whisper transcription) re-verified end to end on Windows.

## 0.1.0 (2026-10-15)

First public release.

- `SKILL.md`: the order of work (ask first, then the script, one checked narration, then video), the words AI voices get wrong, and how to write lines a voice reads cleanly: diacritics, polite commands, English words, numbers, dates, times and money, honorific signs, Arabic names, pauses.
- `data/lexicon.json`: word rules from real takes, with check patterns, plus Latin letters, numbers, honorifics, polite command forms and weak paragraph endings.
- `lint_script.py`: checks a script before any audio is made, with line numbers, `--fix` for the safe one-to-one fixes, `--json`, and `--lexicon` to add your own words.
- `check_takes.py`: ranks takes with Whisper in Urdu, English and Devanagari, plus stutter and stall checks, for one line or a whole script (`--script` with a `{n}` pattern).
- `PROMPT.md`: a ready-to-paste prompt for chat assistants without skill support.
- Tests for the linter, the fixer and the take checks, using real transcripts.
