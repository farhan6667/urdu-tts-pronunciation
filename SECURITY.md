# Security

## What runs, and what it touches

- `lint_script.py` reads one text file (or stdin) and prints results. No network, no other files.
- `check_takes.py` reads the audio files you give it through ffmpeg (as raw samples, nothing else) and runs Whisper on your own computer. The only network use is faster-whisper's one-time model download from Hugging Face. Your audio and scripts never leave the machine.
- No shell commands are built from your text. ffmpeg is started with an argument list, not a shell string.
- `--lexicon` loads JSON only. The regexes in it run with Python's `re`; a very badly written pattern could be slow, so only use lexicon files you trust.

## Reporting

Please open a [private security advisory](https://github.com/farhan6667/urdu-tts-pronunciation/security/advisories/new) rather than a public issue.

If you can't use GitHub advisories, email nexaforge.services@gmail.com with the subject "urdu-tts-pronunciation security".
