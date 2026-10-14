# Contributing

Thanks for helping Urdu voices sound right. This project is small and every report counts.

## Ways to help

1. **Report a word your voice says wrong.** This is the most useful thing you can do. Open a [word report](https://github.com/farhan6667/urdu-tts-pronunciation/issues/new?template=word-report.yml): the word, what the voice said, which engine, and the spelling that fixed it (if you found one). A word that is still broken is welcome too.
2. **Tell us how it went with your engine.** ElevenLabs, Azure, Google, Piper, XTTS, OmniVoice or anything else: an [engine report](https://github.com/farhan6667/urdu-tts-pronunciation/issues/new?template=engine-report.yml) saying which checks were right and which were wrong helps everyone.
3. **Add a check pattern.** If you know how Whisper writes a word in Devanagari when it is said right and when it is said wrong, add a `heard` entry to `data/lexicon.json` with a test.
4. **Fix a false alarm.** If `lint_script.py` flags something that is fine, open an issue with the line.

## Adding a word

Edit `skills/urdu-tts-pronunciation/data/lexicon.json` and add a rule:

```json
{
  "id": "short-name",
  "find": "what the script had",
  "use": "the spelling or wording that fixed it",
  "roman": "how it should sound, in Latin letters",
  "wrong": "what the voice said instead",
  "why": "one plain sentence",
  "heard": { "hi_good": "Devanagari regex for the right sound", "hi_bad": "and for the wrong one" }
}
```

Only add what you have actually heard go wrong and come right. No guesses. Then add a test in `tests/` and run:

```
python -m unittest discover -s tests
```

## Pull requests

Keep them small, say how you checked the change, and write in plain English. By sending a pull request you agree that your contribution is licensed under the MIT License.
