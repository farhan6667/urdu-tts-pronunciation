import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "urdu-tts-pronunciation" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from urdu_tts import fix_text, lint, load_lexicon, merge_lexicon  # noqa: E402


def by_id(text, id_):
    return [p for p in lint(text) if p["id"] == id_]


class LinesAndLevels(unittest.TestCase):
    def test_line_numbers(self):
        found = lint("پہلی لائن ٹھیک ہے۔\nاپنا خفیہ کوڈ۔")
        self.assertEqual([p["line"] for p in found if p["id"] == "khufiya"], [2])

    def test_command_after_na_is_a_fix(self):
        self.assertEqual([p["level"] for p in by_id("کسی کو کوڈ نہ دیں۔", "polite-imperative")], ["fix"])

    def test_statement_is_only_a_check(self):
        self.assertEqual([p["level"] for p in by_id("وہ کل آئیں۔", "polite-imperative")], ["check"])

    def test_digits_are_numbers_not_latin(self):
        found = lint("پروگرام 15 مارچ کو 3:30 بجے ہوگا۔")
        self.assertEqual({p["id"] for p in found}, {"numbers"})
        self.assertTrue(all(p["level"] == "check" for p in found))
        self.assertIn("ساڑھے تین بجے", [p["use"] for p in found])

    def test_latin_word(self):
        self.assertEqual([p["found"] for p in by_id("WhatsApp پر رپورٹ کیجیے۔", "latin-letters")], ["WhatsApp"])

    def test_honorific_signs(self):
        found = by_id("نبی کریم ﷺ نے فرمایا۔", "honorific-sign")
        self.assertEqual(found[0]["use"], "صلی اللہ علیہ وآلہ وسلم")
        self.assertEqual(found[0]["level"], "fix")

    def test_bom_is_ignored(self):
        self.assertEqual([p["line"] for p in lint("\ufeffاپنا خفیہ کوڈ۔") if p["id"] == "khufiya"], [1])


class Fix(unittest.TestCase):
    def test_safe_replacements(self):
        out = fix_text("اپنا خفیہ پن اور ٹو اسٹیپ۔ کسی کو نہ دیں۔ نبی کریم ﷺ نے فرمایا۔")
        self.assertIn("خُفیہ پِن", out)
        self.assertIn("ٹو سٹیپ", out)
        self.assertIn("نہ دیجیے", out)
        self.assertIn("نبی کریم صلی اللہ علیہ وآلہ وسلم نے", out)

    def test_rewrites_are_left_to_a_person(self):
        out = fix_text("لنک پر کلک کیجیے۔ سائبر سیکیورٹی ڈیپارٹمنٹ۔")
        self.assertIn("کلک", out)
        self.assertIn("ڈیپارٹمنٹ", out)

    def test_fixed_text_has_no_safe_fixes_left(self):
        text = "اپنا خفیہ پن۔ ٹو اسٹیپ آن رکھیے۔"
        self.assertEqual([p for p in lint(fix_text(text)) if p["level"] == "fix"], [])


class Lexicon(unittest.TestCase):
    def test_user_rules_are_added(self):
        lex = merge_lexicon(load_lexicon(), {"rules": [{"id": "my-word", "find": "اسکول", "use": "سکول", "why": "test"}]})
        self.assertIn("my-word", [r["id"] for r in lex["rules"]])
        self.assertIn("khufiya", [r["id"] for r in lex["rules"]])
        self.assertTrue(any(p["id"] == "my-word" for p in lint("اسکول جائیے", lex)))

    def test_same_id_replaces(self):
        lex = merge_lexicon(load_lexicon(), {"rules": [{"id": "khufiya", "find": "خفیہ", "use": "ذاتی", "why": "house style"}]})
        self.assertEqual([r["use"] for r in lex["rules"] if r["id"] == "khufiya"], ["ذاتی"])

    def test_partial_sections_merge(self):
        lex = merge_lexicon(load_lexicon(), {"weak_endings": {"words": ["سائٹ"]}})
        self.assertIn("سائٹ", lex["weak_endings"]["words"])
        self.assertIn("گائیڈ", lex["weak_endings"]["words"])


class Cli(unittest.TestCase):
    def run_lint(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(SCRIPTS / "lint_script.py"), *args], input=stdin,
                              capture_output=True, cwd=str(SCRIPTS))

    def test_stdin_is_read_as_utf8(self):
        r = self.run_lint("-", stdin="اپنا خفیہ کوڈ کسی کو نہ دیں۔".encode("utf-8"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("خُفیہ", r.stdout.decode("utf-8"))

    def test_clean_file_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d, "ok.txt")
            p.write_text("اپنا خُفیہ پِن کسی کو نہ بتائیے۔", encoding="utf-8-sig")
            r = self.run_lint(str(p))
            self.assertEqual(r.returncode, 0, r.stdout.decode("utf-8"))

    def test_fix_writes_a_copy(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d, "s.txt")
            p.write_text("اپنا خفیہ پن۔", encoding="utf-8")
            self.run_lint(str(p), "--fix")
            self.assertEqual(pathlib.Path(d, "s.fixed.txt").read_text(encoding="utf-8"), "اپنا خُفیہ پِن۔")

    def test_json_output(self):
        r = self.run_lint("-", "--json", stdin="اپنا خفیہ کوڈ۔".encode("utf-8"))
        data = json.loads(r.stdout.decode("utf-8"))
        self.assertEqual(data[0]["id"], "khufiya")

    def test_missing_file(self):
        self.assertEqual(self.run_lint("no-such-file.txt").returncode, 2)


if __name__ == "__main__":
    unittest.main()
