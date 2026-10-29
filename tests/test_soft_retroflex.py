"""Words a voice softened in real takes (2026-10-29): retroflex ڈ and ٹ said as د and ت, "screen" heard as
"saacreen" or "uscreen", and a final ں dropped from left and right."""
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "skills" / "urdu-tts-pronunciation" / "scripts"))
from urdu_tts import lint, load_lexicon  # noqa: E402


def ids(text):
    return [p["id"] for p in lint(text)]


class SoftRetroflex(unittest.TestCase):
    def test_each_word_is_flagged(self):
        cases = {"di-letters": "یہ ڈی آئی ورژن لینز ہے۔", "design": "اس کا ڈیزائن دیکھیے۔", "tap": "یہاں ٹیپ کیجیے۔",
                 "tab": "ہسٹری ٹیب کھولیے۔", "download": "رپورٹ ڈاؤن لوڈ کیجیے۔", "screen": "ہر اسکرین دیکھیے۔",
                 "left": "بائیں فون پر۔", "right": "دائیں فون پر۔"}
        for rule, text in cases.items():
            with self.subTest(rule=rule):
                self.assertIn(rule, ids(text))

    def test_the_fixed_spelling_of_screen_passes(self):
        self.assertNotIn("screen", ids("ہر اِسکرین دیکھیے۔"))

    def test_heard_patterns_tell_good_from_bad(self):
        rules = {r["id"]: r for r in load_lexicon()["rules"]}
        samples = {"screen": ("हर इस्क्रीन देखिए", "हर उस्क्रीन देखिए"), "design": ("इसका डिज़ाइन", "इसका दिज़ाइन"),
                   "tap": ("यहाँ टैप कीजिए", "यहाँ तेप कीजिए"), "download": ("रिपोर्ट डाउनलोड", "रिपोर्ट दौनलोड"),
                   "di-letters": ("डी आई वर्ज़न", "दियाई वर्ज़न")}
        for rule, (good, bad) in samples.items():
            with self.subTest(rule=rule):
                h = rules[rule]["heard"]
                self.assertTrue(re.search(h["hi_good"], good))
                self.assertFalse(re.search(h["hi_bad"], good))
                self.assertTrue(re.search(h["hi_bad"], bad))


if __name__ == "__main__":
    unittest.main()
