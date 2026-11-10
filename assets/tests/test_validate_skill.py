"""Tests for scripts/validate_skill.py. Run: python3 assets/tests/test_validate_skill.py"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "validate_skill.py"
SL = chr(47)
EM = chr(0x2014)
EN = chr(0x2013)

GOOD_SKILL = """---
name: demo-skill
description: Use when testing the validator.
license: MIT
compatibility: Any agent harness.
metadata:
  version: 0.1.0
  build: test
---
# Demo

Read references/01-a.md when needed. Templates live in templates/t.md.
Run scripts/ok.py and see assets/evals/x.json.
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run(skill_dir: Path):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(skill_dir)],
        capture_output=True, text=True, encoding="utf-8",
    )
    return proc.returncode, proc.stdout


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "demo-skill"
        write(self.root / "SKILL.md", GOOD_SKILL)
        write(self.root / "references" / "01-a.md", "# A\n\nRead this when testing.\n")
        write(self.root / "templates" / "t.md", "# T\n")
        write(self.root / "scripts" / "ok.py", "import os\nimport sys\nfrom pathlib import Path\n")
        write(self.root / "assets" / "evals" / "x.json", '{"a": 1}\n')

    def skill(self, text: str) -> None:
        write(self.root / "SKILL.md", text)

    def swap(self, old: str, new: str) -> None:
        self.skill(GOOD_SKILL.replace(old, new))

    def expect_error(self, needle: str):
        code, out = run(self.root)
        self.assertEqual(code, 1, out)
        self.assertTrue(
            any(l.startswith("ERROR ") and needle in l for l in out.splitlines()),
            "no ERROR line containing %r in:\n%s" % (needle, out),
        )
        return out


class TestPassing(Base):
    def test_good_tree_passes(self):
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("0 errors, 0 warnings", out)

    def test_quoted_values_pass(self):
        self.swap("name: demo-skill", 'name: "demo-skill"')
        code, out = run(self.root)
        self.assertEqual(code, 0, out)


class TestUsage(unittest.TestCase):
    def test_help_exit_zero(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("SKILL_DIR", proc.stdout)

    def test_no_args_exit_two(self):
        proc = subprocess.run([sys.executable, str(SCRIPT)],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 2)

    def test_missing_dir_exit_two(self):
        with tempfile.TemporaryDirectory() as t:
            proc = subprocess.run([sys.executable, str(SCRIPT), str(Path(t) / "nope")],
                                  capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 2)


class TestCheck1Frontmatter(Base):
    def test_missing_skill_md(self):
        (self.root / "SKILL.md").unlink()
        self.expect_error("SKILL.md")

    def test_first_line_not_dashes(self):
        self.skill("# no frontmatter\n" + GOOD_SKILL)
        self.expect_error("---")

    def test_unclosed_frontmatter(self):
        self.skill("---\nname: demo-skill\n")
        self.expect_error("frontmatter")


class TestCheck2Keys(Base):
    def test_each_required_key(self):
        for key in ("name", "description", "license", "compatibility", "metadata"):
            with self.subTest(key=key):
                lines = [l for l in GOOD_SKILL.splitlines() if not l.startswith(key + ":")]
                if key == "metadata":
                    lines = [l for l in lines if not l.startswith("  ")]
                self.skill("\n".join(lines) + "\n")
                self.expect_error("missing required key: " + key)


class TestCheck3Name(Base):
    def test_name_mismatch_dir(self):
        self.swap("name: demo-skill", "name: other-skill")
        self.expect_error("directory")

    def test_name_bad_pattern(self):
        bad = self.root.parent / "Demo_Skill"
        self.root.rename(bad)
        self.root = bad
        self.swap("name: demo-skill", "name: Demo_Skill")
        self.expect_error("pattern")

    def test_name_too_long(self):
        long = "a" * 65
        new = self.root.parent / long
        self.root.rename(new)
        self.root = new
        self.swap("name: demo-skill", "name: " + long)
        self.expect_error("64")


class TestCheck4Description(Base):
    def test_too_long(self):
        self.swap("Use when testing the validator.", "Use when " + "x" * 60 + ".")
        self.expect_error("60")

    def test_no_final_period(self):
        self.swap("validator.", "validator")
        self.expect_error("end with a period")

    def test_two_sentences(self):
        self.swap("Use when testing the validator.", "Use it. Then stop.")
        self.expect_error("one sentence")

    def test_not_starting_with_use(self):
        self.swap("Use when testing", "Run when testing")
        self.expect_error('start with "Use"')


class TestCheck5Size(Base):
    def test_too_many_lines(self):
        self.skill(GOOD_SKILL + "line\n" * 200)
        self.expect_error("lines")

    def test_too_many_chars(self):
        self.skill(GOOD_SKILL + ("x" * 199 + "\n") * 150)
        self.expect_error("characters")

    def test_exactly_200_lines_ok(self):
        n = len(GOOD_SKILL.splitlines())
        self.skill(GOOD_SKILL + "line\n" * (200 - n))
        code, out = run(self.root)
        self.assertEqual(code, 0, out)

    def test_201_lines_fails(self):
        n = len(GOOD_SKILL.splitlines())
        self.skill(GOOD_SKILL + "line\n" * (201 - n))
        code, out = run(self.root)
        self.assertEqual(code, 1, out)
        self.assertIn("at most 200 allowed", out)


class TestCheck6Paths(Base):
    def test_missing_reference(self):
        self.skill(GOOD_SKILL + "\nSee references/99-none.md.\n")
        self.expect_error("references/99-none.md")

    def test_missing_each_prefix(self):
        for p in ("templates/zz.md", "scripts/zz.py", "assets/zz.json"):
            with self.subTest(p=p):
                self.skill(GOOD_SKILL + "\nSee %s now.\n" % p)
                self.expect_error(p)


class TestCheck7References(Base):
    def test_subdirectory(self):
        write(self.root / "references" / "sub" / "x.md", "# x\n")
        self.expect_error("flat")

    def test_too_long(self):
        write(self.root / "references" / "02-b.md", "# B\n\n## Contents\n" + "l\n" * 150)
        self.expect_error("150")

    def test_over_100_needs_contents(self):
        write(self.root / "references" / "02-b.md", "# B\n" + "l\n" * 110)
        self.expect_error("## Contents")

    def test_over_100_with_contents_ok(self):
        write(self.root / "references" / "02-b.md", "# B\n## Contents\n" + "l\n" * 110)
        code, out = run(self.root)
        self.assertEqual(code, 0, out)


class TestCheck8Forbidden(Base):
    def test_forbidden_names(self):
        for name in ("README.md", "CHANGELOG.md", "install.sh", ".env",
                     ".env.example", ".gitignore"):
            with self.subTest(name=name):
                p = self.root / "templates" / name
                write(p, "x\n")
                self.expect_error(name)
                p.unlink()

    def test_nested_skill_md(self):
        write(self.root / "templates" / "SKILL.md", "x\n")
        self.expect_error("nested SKILL.md")


class TestCheck9Scripts(Base):
    def test_non_stdlib_import(self):
        write(self.root / "scripts" / "bad.py", "import requests\n")
        self.expect_error("requests")

    def test_from_import_non_stdlib(self):
        write(self.root / "scripts" / "bad.py", "from yaml import safe_load\n")
        self.expect_error("yaml")

    def test_relative_import(self):
        write(self.root / "scripts" / "bad.py", "from . import ok\n")
        self.expect_error("relative import")

    def test_nested_dir_in_scripts(self):
        write(self.root / "scripts" / "sub" / "x.py", "import os\n")
        self.expect_error("flat")


class TestCheck10CrossRefs(Base):
    def test_denylist_word(self):
        self.skill(GOOD_SKILL + "\nUse " + "sa" + "ga here.\n")
        self.expect_error("sa" + "ga")

    def test_denylist_case_insensitive_hyphenated(self):
        self.skill(GOOD_SKILL + "\nSee Writing-" + "Plans.\n")
        self.expect_error("Writing-" + "Plans")

    def test_denylist_in_py_and_json(self):
        write(self.root / "scripts" / "w.py", "# " + "td" + "d\n")
        write(self.root / "assets" / "evals" / "y.json", '{"a": "' + "grill" + 'ing"}\n')
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("w.py:1", out)
        self.assertIn("y.json:1", out)

    def test_sources_file_exempt(self):
        write(self.root / "references" / "16-sources.md", "# S\nmatt" + "pocock and " + "sa" + "ga\n" + SL + "foo\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)

    def test_slash_command(self):
        self.skill(GOOD_SKILL + "\nRun " + SL + "deploy now.\n")
        out = self.expect_error(SL + "deploy")
        self.assertIn("SKILL.md:", out)

    def test_url_and_relative_path_not_flagged(self):
        self.skill(GOOD_SKILL + "\nSee https://example.com/page and references/01-a.md.\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)

    def test_line_number_reported(self):
        self.skill(GOOD_SKILL + "\nRun " + SL + "deploy now.\n")
        n = len((GOOD_SKILL + "\n").splitlines()) + 1
        code, out = run(self.root)
        self.assertIn("SKILL.md:%d:" % n, out)


class TestCheck11Dashes(Base):
    def test_em_dash(self):
        self.skill(GOOD_SKILL + "\na " + EM + " b\n")
        self.expect_error("dash")

    def test_en_dash_in_json(self):
        write(self.root / "assets" / "evals" / "y.json", '{"a": "1%s2"}\n' % EN)
        self.expect_error("y.json:1")


class TestCheck12Json(Base):
    def test_bad_json(self):
        write(self.root / "assets" / "evals" / "bad.json", "{not json")
        self.expect_error("bad.json")

    def test_valid_json_ok(self):
        code, out = run(self.root)
        self.assertEqual(code, 0, out)


# C4 denylist as fragments (this file is inside the skill tree and is scanned).
# A trailing "!" on the joined form means: join without hyphens.
C4_PARTS = [
    ("writing", "plans"), ("subagent", "driven", "development"), ("grill", "ing!"),
    ("grill", "me"), ("grill", "with", "docs"), ("domain", "modeling"),
    ("to", "tickets"), ("to", "spec"), ("td", "d!"), ("implement", "spec"),
    ("sa", "ga!"), ("tlc", "spec", "driven"), ("tech", "leads", "club"),
    ("multi", "agent", "review"), ("writing", "for", "agents"),
    ("writing", "great", "skills"), ("spec", "driven", "development"),
    ("incremental", "implementation"), ("planning", "and", "task", "breakdown"),
    ("test", "driven", "development"), ("api", "and", "interface", "design"),
    ("context", "engineering"), ("using", "agent", "skills"), ("interview", "me"),
    ("source", "driven", "development"), ("matt", "pocock!"), ("addy", "osmani!"),
    ("warp", "dot", "dev!"), ("riek", "elt!"), ("way", "finder!"),
    ("setup", "matt", "pocock", "skills"), ("diagnosing", "bugs"),
    ("codebase", "design"), ("improve", "codebase", "architecture"),
]


def c4_names():
    out = []
    for parts in C4_PARTS:
        if parts[-1].endswith("!"):
            out.append("".join(parts).replace("!", ""))
        else:
            out.append("-".join(parts))
    return out


class TestC4Denylist(Base):
    def test_has_34_names(self):
        self.assertEqual(len(set(c4_names())), 34)

    def test_every_name_flagged(self):
        for name in c4_names():
            with self.subTest(name=name):
                self.skill(GOOD_SKILL + "\nSee " + name + " now.\n")
                self.expect_error(name)

    def test_old_warp_spelling_not_in_list(self):
        self.skill(GOOD_SKILL + "\nSee " + "warp" + "dev" + " now.\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)


class TestBoundaries(Base):
    def desc(self, n):
        return "Use " + "x" * (n - 5) + "."

    def test_description_60_ok_61_fails(self):
        self.swap("Use when testing the validator.", self.desc(60))
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.swap("Use when testing the validator.", self.desc(61))
        self.expect_error("60")

    def test_skill_md_24000_ok_24001_fails(self):
        base = len(GOOD_SKILL)
        filler = 24000 - base
        # 150 lines of filler: keep under 200 lines, split into lines of < 200 chars
        lines = []
        left = filler
        while left > 0:
            n = min(left, 160)
            lines.append("y" * (n - 1) + "\n")
            left -= n
        body = GOOD_SKILL + "".join(lines)
        self.assertEqual(len(body), 24000)
        self.assertLessEqual(len(body.splitlines()), 200)
        self.skill(body)
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.skill(body + "z")
        self.expect_error("characters")

    def test_reference_100_lines_without_contents(self):
        write(self.root / "references" / "02-b.md", "l\n" * 100)
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        write(self.root / "references" / "02-b.md", "l\n" * 101)
        self.expect_error("## Contents")

    def test_reference_150_lines_with_contents(self):
        write(self.root / "references" / "02-b.md", "## Contents\n" + "l\n" * 149)
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        write(self.root / "references" / "02-b.md", "## Contents\n" + "l\n" * 150)
        self.expect_error("150")


class TestSummary(Base):
    def test_summary_counts_errors(self):
        self.skill(GOOD_SKILL + "\nRun " + SL + "a and " + SL + "b.\n")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("2 errors, 0 warnings", out.splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
