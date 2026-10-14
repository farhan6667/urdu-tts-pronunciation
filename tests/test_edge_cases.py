"""Edge cases found in review: Arabic code points, joiners, reduplication, gendered
honorifics, Devanagari word boundaries, bad user lexicons."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "urdu-tts-pronunciation" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from urdu_tts import LexiconError, check_take, fix_text, lint, load_lexicon, merge_lexicon  # noqa: E402


def ids(text):
    return [p["id"] for p in lint(text)]


class ArabicCodePoints(unittest.TestCase):
    def test_arabic_yeh_heh_kaf_and_tatweel(self):
        self.assertIn("khufiya", ids("اپنا خفيہ کوڈ"))   # Arabic yeh
        self.assertIn("khufiya", ids("اپنا خفیه کوڈ"))   # Arabic heh
        self.assertIn("click", ids("لنک پر كلك کیجیے"))   # Arabic kaf
        self.assertIn("khufiya", ids("اپنا خفـیہ کوڈ"))  # tatweel

    def test_zero_width_joiner_before_a_pause(self):
        found = [p for p in lint("کسی کو کوڈ نہ\u200cدیں۔") if p["id"] == "polite-imperative"]
        self.assertEqual([p["level"] for p in found], ["fix"])

    def test_latin_punctuation_is_a_pause(self):
        self.assertIn("polite-imperative", ids("کسی کو کوڈ نہ دیں."))
        self.assertIn("weak-ending", ids("یہ ہماری گائیڈ\""))


class Imperatives(unittest.TestCase):
    def test_unlisted_verbs_are_checks(self):
        found = [p for p in lint("یہاں اپنا نام لکھیں۔ پھر بٹن لگائیں۔") if p["id"] == "polite-imperative"]
        self.assertEqual({(p["found"], p["use"], p["level"]) for p in found},
                         {("لکھیں", "لکھیے", "check"), ("لگائیں", "لگائیے", "check")})

    def test_not_commands_are_ignored(self):
        self.assertNotIn("polite-imperative", ids("یہ سب ہمارے پاس نہیں۔ وہ یہاں ہیں۔"))


class Numbers(unittest.TestCase):
    def test_numbered_line_and_year_marks(self):
        found = [p["found"] for p in lint("1. پہلا قدم 2026ء میں۔") if p["id"] == "numbers"]
        self.assertEqual(found, ["1", "2026ء"])

    def test_2fa_is_one_latin_word(self):
        found = [p for p in lint("اپنا 2FA آن رکھیے۔") if p["id"] in ("latin-letters", "numbers")]
        self.assertEqual([(p["id"], p["found"], p["use"]) for p in found], [("latin-letters", "2FA", "ٹو سٹیپ ویریفکیشن")])


class Honorifics(unittest.TestCase):
    def test_gendered_signs_are_not_auto_fixed(self):
        out = fix_text("حضرت عائشہؓ نے فرمایا")
        self.assertIn("ؓ", out)
        found = [p for p in lint("حضرت عائشہؓ نے فرمایا") if p["id"] == "honorific-sign"]
        self.assertIn("عنہا", found[0]["use"])

    def test_sign_at_line_start_keeps_the_line_break(self):
        self.assertEqual(fix_text("یا رسول اللہ\nﷺ کا فرمان").count("\n"), 1)

    def test_register_changes_are_not_auto_fixed(self):
        self.assertIn("صفحہ", fix_text("اگلا صفحہ کھولیے"))


class Takes(unittest.TestCase):
    def test_reduplication_is_not_a_stutter(self):
        s = "آہستہ آہستہ بات کیجیے"
        c = check_take(s, "آہستہ آہستہ بات کیجیے", "slowly slowly talk", "आहिस्ता आहिस्ता बात कीजिए")
        self.assertTrue(c["no_repeat"])

    def test_real_stutter_still_caught(self):
        s = "ایپ ڈاؤن لوڈ کیجیے"
        self.assertFalse(check_take(s, "ایپ ایپ ڈاؤن لوڈ کیجیے", "app app download", "ऐप ऐप डाउनलोड")["no_repeat"])

    def test_pin_inside_a_longer_hindi_word_is_not_pan(self):
        s = "اپنا پِن"
        self.assertTrue(check_take(s, s, "your pin", "अपना पिन पनाह")["pin"])

    def test_department_not_confused_by_other_words(self):
        s = "شعبۂ سائبر سیکیورٹی ڈیپارٹمنٹ سے تصدیق کیجیے"
        good = check_take(s, s, "cyber security department", "साइबर सिक्योरिटी डिपार्टमेंट से तस्दीक कीजिए")
        self.assertTrue(good["department"])
        bad = check_take(s, s, "cyber security dipartment", "साइबर सिक्योरिटी दिपार्टमेंट से तस्दीक कीजिए")
        self.assertFalse(bad["department"])

    def test_precomposed_devanagari_nukta(self):
        s = "اپنا خُفیہ کوڈ"
        self.assertTrue(check_take(s, s, "secret code", "अपना ख़ुफिया कोड")["khufiya"])


class UserLexicon(unittest.TestCase):
    def test_missing_key(self):
        with self.assertRaises(LexiconError):
            merge_lexicon(load_lexicon(), {"rules": [{"id": "x", "find": "a"}]})

    def test_bad_regex_exits_2_before_any_work(self):
        with tempfile.TemporaryDirectory() as d:
            lx = pathlib.Path(d, "bad.json")
            lx.write_text(json.dumps({"rules": [{"id": "x", "find": "الف", "use": "ب", "why": "t", "heard": {"hi_good": "(a"}}]}), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPTS / "lint_script.py"), "-", "--lexicon", str(lx)],
                               input="ٹیسٹ".encode("utf-8"), capture_output=True, cwd=str(SCRIPTS))
            self.assertEqual(r.returncode, 2)
            self.assertIn(b"heard.hi_good", r.stderr)

    def test_backslash_in_use_does_not_crash_fix(self):
        lex = merge_lexicon(load_lexicon(), {"rules": [{"id": "x", "find": "ٹیسٹ", "use": "ٹ\\1", "why": "t"}]})
        self.assertEqual(fix_text("یہ ٹیسٹ ہے", lex), "یہ ٹ\\1 ہے")


if __name__ == "__main__":
    unittest.main()
