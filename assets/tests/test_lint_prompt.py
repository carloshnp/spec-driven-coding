"""Tests for scripts/lint_prompt.py. Run: python3 assets/tests/test_lint_prompt.py"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lint_prompt  # noqa: E402

ENTRY = """### parse_config
- Path: src/config.py
- Name: parse_config
- Type: public function
- Input: path to a file
- Output: a dict of settings
- Description: Returns the settings for a valid file. Raises ValueError for a missing key.
"""

PATTERN_A = """## Title
Config loader
## Description
Load settings from a file.
## Tech Stack
Python 3.9 with pytest.
## Key Requirements
Read the file and return a dict.
## Current State
Empty repository.
## Expected Interface
""" + ENTRY

PATTERN_B = """## Title
Config loader
## Description
Load settings from a file.
## Current State
Empty repository.
## Required Implementation
Add the loader.
## Expected Interface
""" + ENTRY + """## Deliverables
A working loader.
"""


def rubric(weights):
    lines = ["## Rubric"]
    for i, w in enumerate(weights):
        lines.append("- (w%s) Criterion number %d holds" % (w, i))
    return "\n".join(lines) + "\n"


def errors(findings):
    return [f for f in findings if f[0] == "ERROR"]


def texts(findings, level="ERROR"):
    return [f[2] for f in findings if f[0] == level]


class ValidPrompts(unittest.TestCase):
    def test_pattern_a_clean(self):
        f = lint_prompt.lint_text(PATTERN_A)
        self.assertEqual(errors(f), [])
        self.assertEqual(lint_prompt.detect_pattern(PATTERN_A), "A")

    def test_pattern_b_clean(self):
        f = lint_prompt.lint_text(PATTERN_B)
        self.assertEqual(errors(f), [])
        self.assertEqual(lint_prompt.detect_pattern(PATTERN_B), "B")

    def test_missing_pattern_a_section(self):
        text = PATTERN_A.replace("## Tech Stack\nPython 3.9 with pytest.\n", "")
        self.assertTrue(any("Tech Stack" in t for t in texts(lint_prompt.lint_text(text))))

    def test_missing_pattern_b_deliverables(self):
        text = PATTERN_B.replace("## Deliverables\nA working loader.\n", "")
        self.assertTrue(any("Deliverables" in t for t in texts(lint_prompt.lint_text(text))))

    def test_pattern_a_missing_current_state(self):
        text = PATTERN_A.replace("## Current State\nEmpty repository.\n", "")
        f = lint_prompt.lint_text(text)
        self.assertTrue(any("Current State" in t for t in texts(f)))
        self.assertEqual(lint_prompt.detect_pattern(text), "A")

    def test_missing_common_section(self):
        text = PATTERN_A.replace("## Title\nConfig loader\n", "")
        self.assertTrue(any("Title" in t for t in texts(lint_prompt.lint_text(text))))


class InterfaceRule(unittest.TestCase):
    def test_underscore_name_is_error(self):
        text = PATTERN_A.replace("parse_config", "_parse_config")
        self.assertTrue(any("underscore" in t for t in texts(lint_prompt.lint_text(text))))

    def test_type_outside_public_list(self):
        text = PATTERN_A.replace("public function", "private function")
        self.assertTrue(any("Type" in t for t in texts(lint_prompt.lint_text(text))))

    def test_type_helper_is_error(self):
        text = PATTERN_A.replace("public function", "helper")
        self.assertTrue(any("Type" in t for t in texts(lint_prompt.lint_text(text))))

    def test_all_allowed_types_pass(self):
        for t in lint_prompt.PUBLIC_TYPES:
            text = PATTERN_A.replace("public function", t)
            self.assertEqual(errors(lint_prompt.lint_text(text)), [], t)
        self.assertEqual(len(lint_prompt.PUBLIC_TYPES), 7)

    def test_private_heading_is_error(self):
        text = PATTERN_A + "### Private helpers\n- Path: N/A\n"
        f = lint_prompt.lint_text(text)
        self.assertTrue(any("private" in t.lower() for t in texts(f)))

    FRAGMENT = "mentions private or internal items"

    def _entry_with_heading(self, head):
        entry = ENTRY.replace("### parse_config", "### " + head).replace("- Name: parse_config", "- Name: " + head)
        return PATTERN_A.replace(ENTRY, entry)

    def test_internal_heading_is_error(self):
        f = lint_prompt.lint_text(self._entry_with_heading("Internal Helper"))
        self.assertEqual(len(texts(f)), 1, texts(f))
        self.assertIn(self.FRAGMENT, texts(f)[0])

    def test_internal_word_inside_heading_is_error(self):
        for head in ["Helpers (internal)", "Module-internal helpers", "internal_helpers", "INTERNAL"]:
            f = lint_prompt.lint_text(self._entry_with_heading(head))
            self.assertTrue(any(self.FRAGMENT in t for t in texts(f)), (head, texts(f)))

    def test_private_word_boundaries(self):
        f = lint_prompt.lint_text(PATTERN_A + "### private_helpers\n")
        self.assertTrue(any("private" in t.lower() for t in texts(f)))

    def test_privatekey_heading_passes(self):
        text = PATTERN_A.replace("parse_config", "PrivateKey")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])
        text = PATTERN_A.replace("parse_config", "InternalClock")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_dunder_name_passes(self):
        text = PATTERN_A.replace("parse_config", "__version__")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_single_underscore_name_still_errors(self):
        text = PATTERN_A.replace("parse_config", "_x")
        self.assertTrue(any("underscore" in t for t in texts(lint_prompt.lint_text(text))))

    def test_half_dunder_name_errors(self):
        for n in ["__x", "x__", "__private"]:
            f = lint_prompt.lint_text(PATTERN_A.replace("- Name: parse_config", "- Name: %s" % n))
            if n.startswith("_"):
                self.assertTrue(any("underscore" in t for t in texts(f)), n)

    def test_name_must_match_heading(self):
        text = PATTERN_A.replace("- Name: parse_config", "- Name: load_config")
        self.assertTrue(any("heading" in t for t in texts(lint_prompt.lint_text(text))))

    def test_field_order(self):
        text = PATTERN_A.replace(
            "- Input: path to a file\n- Output: a dict of settings\n",
            "- Output: a dict of settings\n- Input: path to a file\n")
        self.assertTrue(any("order" in t for t in texts(lint_prompt.lint_text(text))))

    def test_missing_field(self):
        text = PATTERN_A.replace("- Input: path to a file\n", "")
        self.assertTrue(errors(lint_prompt.lint_text(text)))

    def test_empty_field(self):
        text = PATTERN_A.replace("- Path: src/config.py", "- Path:")
        self.assertTrue(any("Path" in t for t in texts(lint_prompt.lint_text(text))))

    def test_na_is_content(self):
        text = PATTERN_A.replace("- Input: path to a file", "- Input: N/A")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_no_entries(self):
        text = PATTERN_A.split("### parse_config")[0]
        self.assertTrue(any("entry" in t for t in texts(lint_prompt.lint_text(text))))


class BannedWords(unittest.TestCase):
    def test_reports_line_numbers(self):
        text = PATTERN_A.replace("Load settings from a file.", "Load settings from a file.\nIt should work.")
        hits = [f for f in lint_prompt.lint_text(text) if "should" in f[2]]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][1], 5)
        self.assertEqual(hits[0][0], "ERROR")

    def test_all_banned_phrases(self):
        for w in ["should", "or", "alternatively", "either", "recommended", "etc.",
                  "you can", "something like", "relevant technologies"]:
            text = PATTERN_A.replace("Empty repository.", "Empty %s repository." % w)
            self.assertTrue(any("banned" in t for t in texts(lint_prompt.lint_text(text))), w)

    def test_whole_word_only(self):
        text = PATTERN_A.replace("Empty repository.", "Order of the shoulder and orchestrator.")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_case_insensitive(self):
        text = PATTERN_A.replace("Empty repository.", "Should be empty.")
        self.assertTrue(errors(lint_prompt.lint_text(text)))

    def test_code_fence_skipped(self):
        text = PATTERN_A.replace("Empty repository.", "```\nx = a or b\n```")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_allow_marker_honored(self):
        text = PATTERN_A.replace("Empty repository.", "It should work. <!-- allow-banned -->")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])


class Rubric(unittest.TestCase):
    def test_valid_rubric(self):
        text = PATTERN_A + rubric([1, 3, 5, 1, 3])
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_too_few(self):
        text = PATTERN_A + rubric([1, 3, 5, 1])
        self.assertTrue(any("5 to 30" in t for t in texts(lint_prompt.lint_text(text))))

    def test_too_many(self):
        text = PATTERN_A + rubric([1] * 31)
        self.assertTrue(any("5 to 30" in t for t in texts(lint_prompt.lint_text(text))))

    def test_thirty_ok(self):
        text = PATTERN_A + rubric([3] * 30)
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_bad_weight(self):
        text = PATTERN_A + rubric([1, 3, 5, 1, 2])
        self.assertTrue(any("weight" in t for t in texts(lint_prompt.lint_text(text))))

    def test_no_rubric_ok(self):
        self.assertEqual(errors(lint_prompt.lint_text(PATTERN_A)), [])


class InternalRefsAndDashes(unittest.TestCase):
    def test_internal_references(self):
        for ref in ["TODO", "FIXME", "TBD", "task 12", "AD-004", "TLC-7"]:
            text = PATTERN_A.replace("Empty repository.", "See %s now." % ref)
            self.assertTrue(any("internal reference" in t for t in texts(lint_prompt.lint_text(text))), ref)

    def test_dash_is_warn_only(self):
        text = PATTERN_A.replace("Empty repository.", "Empty \u2014 repository.")
        f = lint_prompt.lint_text(text)
        self.assertEqual(errors(f), [])
        self.assertEqual(len(texts(f, "WARN")), 1)

    def test_en_dash_warn(self):
        text = PATTERN_A.replace("Empty repository.", "Empty \u2013 repository.")
        self.assertEqual(len(texts(lint_prompt.lint_text(text), "WARN")), 1)


class PlaceholdersAndCompileBlock(unittest.TestCase):
    def test_bracketed_line_is_error(self):
        text = PATTERN_A.replace("Config loader\n", "[One line naming the deliverable]\n", 1)
        f = lint_prompt.lint_text(text)
        hits = [x for x in f if x[0] == "ERROR" and "placeholder" in x[2]]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][1], 2)

    def test_indented_bracket_line_is_error(self):
        text = PATTERN_A.replace("Empty repository.", "  [Describe the current code]")
        self.assertTrue(any("placeholder" in t for t in texts(lint_prompt.lint_text(text))))

    def test_bracket_inside_sentence_passes(self):
        text = PATTERN_A.replace("Empty repository.", "Empty repository [see notes] for now.")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_bracket_in_fence_passes(self):
        text = PATTERN_A.replace("Empty repository.", "```\n[x]\n```")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_link_line_passes(self):
        text = PATTERN_A.replace("Empty repository.", "[docs](docs/a.md)")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_compile_marker_is_error(self):
        marker = "Compile notes (delete this block before linting):"
        text = PATTERN_A.replace("## Title\n", "## Title\n" + marker + "\n", 1)
        f = lint_prompt.lint_text(text)
        hits = [x for x in f if x[0] == "ERROR" and "compile" in x[2].lower()]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][1], 2)

    def test_no_marker_no_error(self):
        self.assertEqual(errors(lint_prompt.lint_text(PATTERN_A)), [])


class FieldPlaceholders(unittest.TestCase):
    def test_path_placeholder_is_error(self):
        text = PATTERN_A.replace("- Path: src/config.py", "- Path: [value]")
        f = lint_prompt.lint_text(text)
        self.assertIn("placeholder not replaced in field Path: - Path: [value]", texts(f))

    def test_description_leading_placeholder_is_error(self):
        line = "- Description: [value] Returns the number of words."
        text = PATTERN_A.replace(
            "- Description: Returns the settings for a valid file. Raises ValueError for a missing key.", line)
        f = lint_prompt.lint_text(text)
        self.assertIn("placeholder not replaced in field Description: " + line, texts(f))

    def test_placeholder_in_pattern_b(self):
        text = PATTERN_B.replace("- Input: path to a file", "- Input: [value]")
        self.assertTrue(any("in field Input" in t for t in texts(lint_prompt.lint_text(text))))

    def test_na_input_passes(self):
        text = PATTERN_A.replace("- Input: path to a file", "- Input: N/A")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_plain_input_passes(self):
        text = PATTERN_A.replace("- Input: path to a file", "- Input: text as a string")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_later_bracket_passes(self):
        text = PATTERN_A.replace("- Input: path to a file", "- Input: a list [of strings] as input")
        self.assertEqual(errors(lint_prompt.lint_text(text)), [])

    def test_cli_exit_one_on_field_placeholder(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "PROMPT.md"
            p.write_text(PATTERN_A.replace("- Path: src/config.py", "- Path: [value]"), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPTS / "lint_prompt.py"), str(p)],
                               capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 1)


class Cli(unittest.TestCase):
    def run_cli(self, text, *extra):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "PROMPT.md"
            p.write_text(text, encoding="utf-8")
            return subprocess.run([sys.executable, str(SCRIPTS / "lint_prompt.py"), str(p)] + list(extra),
                                  capture_output=True, text=True, encoding="utf-8")

    def test_exit_zero(self):
        r = self.run_cli(PATTERN_A)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("pattern A", r.stdout)

    def test_exit_one_and_line_format(self):
        r = self.run_cli(PATTERN_A.replace("parse_config", "_x", 1))
        self.assertEqual(r.returncode, 1)
        self.assertRegex(r.stdout, r"ERROR .*PROMPT\.md:\d+: ")

    def test_json(self):
        r = self.run_cli(PATTERN_A.replace("Empty repository.", "TODO"), "--json")
        data = json.loads(r.stdout)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(set(data[0]), {"level", "line", "text"})

    def test_usage_error(self):
        r = subprocess.run([sys.executable, str(SCRIPTS / "lint_prompt.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        r = subprocess.run([sys.executable, str(SCRIPTS / "lint_prompt.py"), "no-such-file-x.md"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_help(self):
        r = subprocess.run([sys.executable, str(SCRIPTS / "lint_prompt.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


class InternalPrivateWarn(unittest.TestCase):
    def prompt(self, name):
        return PATTERN_A.replace("parse_config", name)

    def warns(self, name):
        f = lint_prompt.lint_text(self.prompt(name))
        return f, texts(f, "WARN")

    def expected(self, name):
        return "heading %s starts with Internal or Private; confirm it is public" % name

    def test_internal_cache_warns(self):
        f, w = self.warns("InternalCache")
        self.assertEqual(errors(f), [])
        self.assertEqual(w, [self.expected("InternalCache")])

    def test_private_key_warns(self):
        f, w = self.warns("PrivateKey")
        self.assertEqual(errors(f), [])
        self.assertEqual(w, [self.expected("PrivateKey")])

    def test_internal_helper_error_only(self):
        f, w = self.warns("Internal Helper")
        self.assertEqual(w, [])
        self.assertEqual(len([t for t in texts(f) if "mentions private or internal items" in t]), 1)

    def test_internals_no_finding(self):
        f, w = self.warns("Internals")
        self.assertEqual(f, [])

    def test_cache_no_finding(self):
        f, w = self.warns("Cache")
        self.assertEqual(f, [])

    def test_cli_warn_exit_zero(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "PROMPT.md"
            p.write_text(self.prompt("InternalCache"), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPTS / "lint_prompt.py"), str(p)],
                               capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARN", r.stdout)


if __name__ == "__main__":
    unittest.main()
