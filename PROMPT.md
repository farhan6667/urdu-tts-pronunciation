# Ready-to-paste prompt

For ChatGPT, Gemini, Copilot or any chat assistant without skill support. Paste this before you ask it to write or fix an Urdu script for a text-to-speech voice. Keep the Urdu examples exactly as they are.

```
You are writing an Urdu script for an AI text-to-speech voice. Follow these rules.

1. Write in Urdu script, never Roman Urdu.
2. Write numbers, dates, times and amounts as words: پندرہ اکتوبر، ساڑھے تین بجے،
   پانچ سو روپے، پچیس فیصد. Years in words too: دو ہزار چھبیس.
3. Spell English words and acronyms in Urdu letters: واٹس ایپ، او ٹی پی، این سی سی آئی اے.
4. Write honorifics out in full instead of signs like ﷺ or ؓ.
5. End commands with the polite form (کیجیے، دیجیے، کھولیے), not -یں before a pause.
6. Add a pesh or zer only where a word could be misread: خُفیہ، پِن.
7. Use these spellings: ٹو سٹیپ (not ٹو اسٹیپ), خدا نخواستہ (two words), چھین لے
   (not چھن جائے). Instead of "کلک" write منتخب کیجیے or دبائیے. Instead of
   "ڈیپارٹمنٹ" write شعبہ.
8. Don't end a paragraph on a short loanword like گائیڈ، کوڈ or ایپ.
9. Keep sentences short. Use ، where you want a short pause and ۔ at the end of a
   sentence. Never put a comma inside a compound term like سائبر سیکیورٹی.
10. Return the script as numbered lines, one paragraph per line.
```

The full list of words and why each rule exists: [SKILL.md](skills/urdu-tts-pronunciation/SKILL.md) and [lexicon.json](skills/urdu-tts-pronunciation/data/lexicon.json).
