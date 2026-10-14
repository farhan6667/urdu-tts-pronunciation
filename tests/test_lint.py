import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "skills" / "urdu-tts-pronunciation" / "scripts"))
from urdu_tts import bare, contains, lint, load_lexicon  # noqa: E402


def ids(text):
    return [p["id"] for p in lint(text)]


class Lexicon(unittest.TestCase):
    def test_every_rule_is_complete(self):
        lex = load_lexicon()
        for r in lex["rules"]:
            for k in ("id", "find", "use", "why"):
                self.assertTrue(r.get(k), f"{r.get('id')}: {k} is missing")

    def test_rule_ids_are_unique(self):
        lex = load_lexicon()
        seen = [r["id"] for r in lex["rules"]]
        self.assertEqual(len(seen), len(set(seen)))

    def test_lexicon_is_valid_json_utf8(self):
        p = pathlib.Path(__file__).resolve().parent.parent / "skills" / "urdu-tts-pronunciation" / "data" / "lexicon.json"
        json.loads(p.read_text(encoding="utf-8"))


class Words(unittest.TestCase):
    def test_khufiya_without_pesh_is_flagged(self):
        self.assertIn("khufiya", ids("اپنا خفیہ پِن کسی کو نہ بتائیے۔"))

    def test_khufiya_with_pesh_passes(self):
        self.assertNotIn("khufiya", ids("اپنا خُفیہ پِن کسی کو نہ بتائیے۔"))

    def test_pin_without_zer_is_flagged(self):
        self.assertIn("pin", ids("اپنا پن یاد رکھیے۔"))

    def test_pin_inside_a_longer_word_is_not_flagged(self):
        self.assertNotIn("pin", ids("اپنا پنجاب"))

    def test_two_steep(self):
        self.assertIn("step", ids("ٹو اسٹیپ ویریفکیشن آن رکھیے۔"))
        self.assertNotIn("step", ids("ٹو سٹیپ ویریفکیشن آن رکھیے۔"))

    def test_click_and_department(self):
        found = ids("سائبر سیکیورٹی ڈیپارٹمنٹ کے لنک پر کلک کیجیے۔")
        self.assertIn("click", found)
        self.assertIn("department", found)

    def test_whatsapp_and_cyber_are_check_only(self):
        # find == use: nothing to rewrite, they are only checked in the audio.
        self.assertEqual(ids("واٹس ایپ اور سائبر سیکیورٹی"), [])


class Writing(unittest.TestCase):
    def test_imperative_at_a_pause(self):
        found = lint("کسی کو کوڈ نہ دیں۔")
        self.assertTrue(any(p["id"] == "polite-imperative" and p["use"] == "دیجیے" for p in found))

    def test_imperative_mid_sentence_is_fine(self):
        self.assertNotIn("polite-imperative", ids("آپ دیں گے تو بہتر ہوگا"))

    def test_weak_ending(self):
        self.assertIn("weak-ending", ids("پیش ہے، واٹس ایپ سیکیورٹی گائیڈ۔"))
        self.assertNotIn("weak-ending", ids("واٹس ایپ سیکیورٹی گائیڈ پیش ہے۔"))

    def test_latin_letters_inside_urdu(self):
        found = lint("NCCIA کو رپورٹ کیجیے۔")
        self.assertTrue(any(p["id"] == "latin-letters" and p["use"] == "این سی سی آئی اے" for p in found))

    def test_comma_inside_cyber_security(self):
        self.assertIn("cyber-comma", ids("سائبر، سیکیورٹی کا شعبہ"))

    def test_clean_script(self):
        self.assertEqual(lint("دعوتِ اسلامی کی جانب سے پیش ہے، واٹس ایپ سیکیورٹی گائیڈ کی رہنمائی۔"), [])


class Helpers(unittest.TestCase):
    def test_bare_drops_short_vowels(self):
        self.assertEqual(bare("خُفیہ پِن"), "خفیہ پن")

    def test_contains_is_whole_word(self):
        self.assertTrue(contains("ٹو سٹیپ", "سٹیپ"))
        self.assertFalse(contains("اسٹیپ", "سٹیپ"))


if __name__ == "__main__":
    unittest.main()
