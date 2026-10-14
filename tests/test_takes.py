"""check_take() on real Whisper transcripts of 8 takes of one line (tests/fixtures/takes.json).
A listener approved only take 2; the checks must agree."""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "skills" / "urdu-tts-pronunciation" / "scripts"))
from urdu_tts import check_take, rank, said_twice, word_ratio  # noqa: E402

FIX = json.loads((ROOT / "fixtures" / "takes.json").read_text(encoding="utf-8"))
SCRIPT = FIX["script"]


def result(name):
    t = next(t for t in FIX["takes"] if t["take"] == name)
    return check_take(SCRIPT, t["ur"], t["en"], t["hi"])


class RealTakes(unittest.TestCase):
    def test_the_approved_take_passes_everything(self):
        c = result("p8_t2.wav")
        self.assertTrue(all(c.values()), c)

    def test_the_line_triggers_its_word_checks(self):
        c = result("p8_t2.wav")
        for k in ("khufiya", "pin", "step", "whatsapp"):
            self.assertIn(k, c)

    def test_two_steep_is_caught(self):
        self.assertFalse(result("p8_t3.wav")["step"])

    def test_whatsapp_as_aap_is_caught(self):
        # t1's Devanagari has वाट्स आप; t0 fails only on the English count.
        self.assertFalse(result("p8_t1.wav")["whatsapp"])
        self.assertFalse(result("p8_t0.wav")["whatsapp"])

    def test_ranking_picks_the_approved_take(self):
        rows = []
        for t in FIX["takes"]:
            rows.append({"take": t["take"], "checks": check_take(SCRIPT, t["ur"], t["en"], t["hi"]), "ratio": word_ratio(SCRIPT, t["ur"])})
        self.assertEqual(rank(rows)[0]["take"], "p8_t2.wav")

    def test_more_words_right_does_not_beat_a_mispronunciation(self):
        # Take 7 has the best word match but says "steep": it must still lose.
        t7 = next(t for t in FIX["takes"] if t["take"] == "p8_t7.wav")
        t2 = next(t for t in FIX["takes"] if t["take"] == "p8_t2.wav")
        self.assertGreater(word_ratio(SCRIPT, t7["ur"]), word_ratio(SCRIPT, t2["ur"]))


class Synthetic(unittest.TestCase):
    def test_stutter(self):
        self.assertTrue(said_twice("download the apps, apps today"))
        self.assertFalse(said_twice("a a short word twice is fine"))

    def test_stall(self):
        c = check_take("ایک لائن", "ایک لائن", "one line", "एक लाइन", gaps=[0.2, 0.9])
        self.assertFalse(c["no_stall"])

    def test_department_soft_d(self):
        s = "شعبۂ سائبر سیکیورٹی ڈیپارٹمنٹ"
        self.assertFalse(check_take(s, s, "cyber security dipartment", "साइबर सिक्योरिटी दिपार्टमेंट")["department"])
        self.assertTrue(check_take(s, s, "cyber security department", "साइबर सिक्योरिटी डिपार्टमेंट")["department"])

    def test_khufiya(self):
        s = "اپنا خُفیہ کوڈ"
        self.assertTrue(check_take(s, s, "your secret code", "अपना खुफिया कोड")["khufiya"])
        self.assertFalse(check_take(s, s, "your secret code", "अपना खफिया कोड")["khufiya"])


if __name__ == "__main__":
    unittest.main()
