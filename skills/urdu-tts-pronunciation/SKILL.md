---
name: urdu-tts-pronunciation
description: Write and check Urdu narration so AI text-to-speech voices pronounce it correctly. Use when making Urdu voice-overs, narration, promos, explainers or ads with any TTS engine or voice clone (ElevenLabs, Azure, Google, OmniVoice, Piper, XTTS), when an AI voice mispronounces an Urdu word, or when picking the best of several Urdu audio takes. Gives spellings that fix commonly misread words, rules for writing lines a voice reads cleanly (numbers, dates, honorifics, English words), a script linter and a Whisper-based take checker. Not for Hindi-only, Arabic-only or English-only narration, or for plain Urdu transcription.
license: MIT
compatibility: Python 3.9+. check_takes.py also needs faster-whisper and ffmpeg.
---

# Urdu TTS pronunciation

Goal: the person you're making audio for never has to say "that word is wrong" twice.
Everything here came from real takes that went wrong and the fix that worked.

`<skill>` below means the folder this file is in.

## Order of work

0. **Ask first:** which engine and voice, who will hear it, any house rules (greetings,
   honorific forms, words the organisation avoids or never says, such as calling its
   services "free"), and whether a person will review each stage.
1. **Script.** Write it in Urdu script. Convert Roman Urdu first: an Urdu voice reads
   Latin letters as English. Save it as UTF-8, one paragraph per line, in the order it
   will be voiced. Run:

   ```
   python <skill>/scripts/lint_script.py script.txt
   ```

   Exit code 1 means there are `fix` items: rewrite around each one unless the person
   overrules it. `check` items are words to listen for. `--fix` writes a corrected copy
   for the simple one-to-one replacements. Show the whole script as numbered lines and
   wait until the person calls it final.
2. **Audio.** Voice each line separately and name takes `line03_take1.wav` and so on.
   On a local engine make 4 to 8 takes per line (takes of the same text differ a lot).
   On a paid engine start with 2 or 3 and add more only for lines that fail. Check them:

   ```
   python <skill>/scripts/check_takes.py --script script.txt "takes/line{n}_*.wav"
   ```

   If faster-whisper or ffmpeg isn't available, say so, and give the person the list of
   words to listen for (the lint output). Deliver ONE joined file and ask for "all good"
   or the line numbers to redo. Never send a pile of A/B takes to compare.
3. **Video** (if any) only after the audio is approved.

If no person is reviewing, still lint and check, and say plainly which lines passed and
which didn't.

## Words AI voices get wrong

| Write | Not | What the voice did |
|---|---|---|
| خُفیہ (with pesh) | خفیہ | said "khafiya" instead of "khufiya" |
| پِن (with zer) | پن | said PIN as "pan" |
| ٹو سٹیپ | ٹو اسٹیپ | the alif made "two steep" |
| منتخب کیجیے، دبائیے، کھولیے | کلک | "click" came out as "kil" |
| شعبۂ ... | ڈیپارٹمنٹ | the hard ڈ became a soft د in every spelling tried |
| چھین لے | چھن جائے | read as "chhan" |
| پیج | صفحہ | heard as "sufa" |
| خدا نخواستہ | خدانخواستہ | the joined form ran together |
| این سی سی آئی اے | NCCIA | Latin letters inside Urdu are read unpredictably |

These came from one OmniVoice voice clone. Other engines guess vowels the same way but
not always on the same words: lint for them, then confirm by listening or with
`check_takes.py`. The full list, with reasons and check patterns, is `data/lexicon.json`.

- When a `use` value has `...` or `/`, rewrite the sentence around it. Don't paste it in.
- Some fixes change the register (صفحہ to پیج, ڈیپارٹمنٹ to شعبہ). In formal or religious
  copy, offer them to the person instead of applying them silently.

## Writing lines a voice can say

- **Diacritics, sparingly.** Add a pesh, zer or zabar only on the vowel that gets misread,
  not full vowel marks everywhere. Write izafat with zer or ۂ (دعوتِ اسلامی، شعبۂ).
  Mark homographs when the context is thin: عالِم (scholar) and عالَم (world), مُلک
  (country) and مِلک (ownership). Check a take to be sure the engine didn't drop the mark.
- **Polite commands.** A final ں can drop at a pause (دیں became دی, نہ دیں became ندی).
  Use دیجیے، کیجیے، کھولیے، رکھیے، بتائیے، پڑھیے، بھیجیے، دیکھیے. They also sound more respectful.
- **Key word not last.** The last consonant of a paragraph can get swallowed (گائیڈ came
  out as گائب). Keep names and words like گائیڈ، کوڈ، اکاؤنٹ، ویب سائٹ، ایپ away from the very
  end of a paragraph, or check the ending is heard.
- **English words** people say in English go in Urdu letters (واٹس ایپ، سائبر سیکیورٹی،
  ٹو سٹیپ) and get checked as English. Acronyms letter by letter: این سی سی آئی اے، او ٹی پی.
  Never put a comma inside a compound term such as سائبر سیکیورٹی.
- **Numbers, dates, times and money as words.** Engines read Urdu numbers unreliably,
  and words also set the register:
  - 3:30 ساڑھے تین بجے، 1:30 ڈیڑھ بجے، 2:30 ڈھائی بجے، 4:15 سوا چار بجے، 4:45 پونے پانچ بجے
  - 15 مارچ 2026 → پندرہ مارچ، دو ہزار چھبیس
  - Rs. 500 → پانچ سو روپے، 1,500 → پندرہ سو روپے، 25% → پچیس فیصد. Use لاکھ and کروڑ.
  - 2026ء → دو ہزار چھبیس عیسوی، 1447ھ → چودہ سو سینتالیس ہجری (the ء and ھ marks get
    dropped or misread)
  - Ordinals: پہلا، دوسرا، تیسرا. Phone numbers digit by digit, in groups (ask the person
    whether to say صفر or زیرو).
- **Honorific signs written out.** ﷺ ؐ ؑ ؒ ؓ ﷻ are special characters that engines may
  skip silently. Write them in full, in the organisation's own form: ﷺ → صلی اللہ علیہ
  وآلہ وسلم، ؑ → علیہ السلام، ؓ → رضی اللہ عنہ (عنہا، عنہم as needed)، ؒ → رحمۃ اللہ علیہ،
  ﷻ → جل جلالہ. `--fix` writes out only ﷺ, ؐ and ﷻ; the others depend on who is meant
  (عنہ for a man, عنہا for a woman, عنہم for a group), so a person chooses.
- **Quran and Arabic.** Don't voice Quranic verses with TTS; use a real recitation
  recording. Listen closely to Arabic names with the article: عبدالرحمن is said "Abdur
  Rahman", not "Abdul Rahman".
- **Pauses.** ، for a short pause, ۔ to end a sentence. Split long sentences.

## Checking takes

`check_takes.py` transcribes each take three times with faster-whisper and ranks them:

- **Urdu:** are all the script's words there. A take that drops, blurs or swaps a word
  loses, however nice the rest sounds.
- **English:** are English words said as English ("WhatsApp" heard as many times as the
  script says it).
- **Devanagari (Hindi):** Whisper writes the voice's sounds in Devanagari, which marks
  the vowels and hard vs soft consonants that Urdu script hides:

  | Word | Good | Bad |
  |---|---|---|
  | WhatsApp | वाट्स **एप** | वाट्स **आप** |
  | khufiya | **खु**फिया | **ख**फिया |
  | pin | **पिन** | **पन** |
  | step | स्**टे**प | स्**टी**प |
  | Department | **डि** | **दि** |

- **No stutter** (the same word twice in a row) and **no stall** (a gap over 0.6 s).

Rules for the checking:

- **Never give Whisper the script as a prompt.** It fills in swallowed words and hides
  the very mistakes you're looking for. `--hint` takes a few vocabulary words if needed.
- Whisper wobbles on single words. When two checks disagree, prefer the take whose
  English transcript reads like a clean sentence.
- If no take passes, make more takes or reword the line around the hard word. Don't send
  a line you already know is wrong.
- **Splicing works.** If one take has the good start and another the good end, cut both
  at a comma pause, match loudness, and join with a 20 ms crossfade:
  `ffmpeg -i start.wav -i end.wav -filter_complex "[0][1]acrossfade=d=0.02" line.wav`
- Keep approved takes untouched. Re-voice only the lines that changed.

## When someone corrects a word

Add it to your own lexicon file and pass it with `--lexicon my-words.json` (it is added
to the built-in list; a rule with the same `id` replaces the built-in one). Give `find`,
`use`, `why`, and if you can a `heard` pattern so `check_takes.py` catches it in future
takes. Better still, send it upstream as a word report so everyone gets it.

## Without an agent

`PROMPT.md` in the repository is a ready-to-paste prompt for ChatGPT, Gemini or any chat
assistant that has no skill support.
