"""Tests for scripts/validate_tasks.py. Run: python3 assets/tests/test_validate_tasks.py"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "validate_tasks.py"


def task_text(nn, title="Thing", status="todo", blocked="None", extra="", criteria=None,
              method="tests"):
    if criteria is None:
        criteria = ["It works. False if: the demo shows nothing."]
    crit = "\n".join("- " + c for c in criteria)
    return (
        "# %s: %s\nStatus: %s\nBlocked by: %s\nDemo: Does the user see a result?\n"
        "What it delivers: A visible result.\nInterface: None\nValidation method: %s\n"
        "## Criteria\n%s\n## Evidence required\n- Test output\n%s"
    ) % (nn, title, status, blocked, method, crit, extra)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text):
        (self.dir / name).write_text(text, encoding="utf-8")

    def plan(self, names, statuses=None):
        lines = ["# Plan"]
        for i, n in enumerate(names):
            lines.append("- %s: %s" % (n, (statuses or {}).get(n, "todo")))
        self.write("plan.md", "\n".join(lines) + "\n")

    def good(self):
        self.write("01-first.md", task_text("01"))
        self.write("02-second.md", task_text("02", blocked="01"))
        self.plan(["01-first.md", "02-second.md"])

    def run_script(self, *args):
        p = subprocess.run([sys.executable, str(SCRIPT), str(self.dir)] + list(args),
                           capture_output=True, text=True, encoding="utf-8")
        self.last_err = p.stderr
        return p.returncode, p.stdout

    def assertError(self, needle, *args):
        code, out = self.run_script(*args)
        self.assertEqual(code, 1, out)
        self.assertTrue(any(l.startswith("ERROR") and needle in l for l in out.splitlines()), out)


class TestValid(Base):
    def test_valid_passes(self):
        self.good()
        code, out = self.run_script()
        self.assertEqual(code, 0, out)

    def test_help(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)

    def test_usage_error(self):
        p = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)

    def test_missing_dir_is_usage_error(self):
        p = subprocess.run([sys.executable, str(SCRIPT), str(self.dir / "nope")],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)


class TestNumbering(Base):
    def test_gap(self):
        self.write("01-first.md", task_text("01"))
        self.write("03-third.md", task_text("03"))
        self.plan(["01-first.md", "03-third.md"])
        self.assertError("02")

    def test_not_starting_at_01(self):
        self.write("02-second.md", task_text("02"))
        self.plan(["02-second.md"])
        self.assertError("01")

    def test_duplicate_number(self):
        self.write("01-first.md", task_text("01"))
        self.write("01-other.md", task_text("01"))
        self.plan(["01-first.md", "01-other.md"])
        self.assertError("duplicate")

    def test_title_number_mismatch(self):
        self.good()
        self.write("02-second.md", task_text("03", blocked="01"))
        self.assertError("title")

    def test_bad_file_name_slug(self):
        self.good()
        self.write("03-Bad_Slug.md", task_text("03"))
        self.assertError("03-Bad_Slug.md")


class TestPlanIndex(Base):
    def test_missing_plan(self):
        self.good()
        (self.dir / "plan.md").unlink()
        self.assertError("plan.md")

    def test_entry_missing(self):
        self.good()
        self.plan(["01-first.md"])
        self.assertError("02-second.md")

    def test_entry_duplicated(self):
        self.good()
        self.plan(["01-first.md", "02-second.md", "02-second.md"])
        self.assertError("more than once")


class TestFields(Base):
    def test_bad_status(self):
        self.good()
        self.write("01-first.md", task_text("01", status="finished"))
        self.assertError("Status")

    def test_bad_validation_method(self):
        self.good()
        self.write("01-first.md", task_text("01", method="vibes"))
        self.assertError("Validation method")

    def test_missing_demo(self):
        self.good()
        t = task_text("01").replace("Demo: Does the user see a result?\n", "")
        self.write("01-first.md", t)
        self.assertError("Demo")

    def test_empty_interface(self):
        self.good()
        t = task_text("01").replace("Interface: None", "Interface:")
        self.write("01-first.md", t)
        self.assertError("Interface")

    def test_evidence_missing(self):
        self.good()
        t = task_text("01").replace("- Test output\n", "")
        self.write("01-first.md", t)
        self.assertError("Evidence")

    def test_no_criteria_bullets(self):
        self.good()
        self.write("01-first.md", task_text("01", criteria=[]).replace("- ", "", 0))
        self.assertError("Criteria")


class TestBlockers(Base):
    def test_lower_number_rule_equal(self):
        self.good()
        self.write("02-second.md", task_text("02", blocked="02"))
        self.assertError("lower")

    def test_lower_number_rule_higher(self):
        self.good()
        self.write("01-first.md", task_text("01", blocked="02"))
        self.assertError("lower")

    def test_nonexistent_blocker(self):
        self.good()
        self.write("02-second.md", task_text("02", blocked="01, 07"))
        self.assertError("07")

    def test_list_ok(self):
        self.good()
        self.write("03-third.md", task_text("03", blocked="01, 02"))
        self.plan(["01-first.md", "02-second.md", "03-third.md"])
        code, out = self.run_script()
        self.assertEqual(code, 0, out)


class TestFalseIf(Base):
    def test_clause_required(self):
        self.good()
        self.write("01-first.md", task_text("01", criteria=["It works.", "Ok. False if: no."]))
        self.assertError("False if")

    def test_clause_present_passes(self):
        self.good()
        code, _ = self.run_script()
        self.assertEqual(code, 0)


class TestPaths(Base):
    def test_path_outside_prototype_is_error(self):
        self.good()
        self.write("01-first.md", task_text("01", extra="\nSee src/app/main.py for details.\n"))
        self.assertError("path")

    def test_path_in_criterion_is_error(self):
        self.good()
        self.write("01-first.md",
                   task_text("01", criteria=["Edit lib/x.ts. False if: no change."]))
        self.assertError("path")

    def test_path_in_other_fence_is_error(self):
        self.good()
        self.write("01-first.md", task_text("01", extra="\n```text\ndocs/a.md\n```\n"))
        self.assertError("path")

    def test_path_in_prototype_block_ok(self):
        self.good()
        self.write("01-first.md",
                   task_text("01", extra="\n```prototype\nsrc/app/main.py\n```\n"))
        code, out = self.run_script()
        self.assertEqual(code, 0, out)

    def test_path_after_prototype_block_still_checked(self):
        self.good()
        self.write("01-first.md", task_text(
            "01", extra="\n```prototype\nok\n```\nThen edit a/b.go now.\n"))
        self.assertError("path")

    def test_slashless_filename_not_flagged(self):
        self.good()
        self.write("01-first.md", task_text("01", extra="\nand/or both work.\n"))
        code, out = self.run_script()
        self.assertEqual(code, 0, out)


class TestFrontier(Base):
    def test_frontier(self):
        self.write("01-first.md", task_text("01", status="done"))
        self.write("02-second.md", task_text("02", blocked="01"))
        self.write("03-third.md", task_text("03", blocked="02"))
        self.write("04-fourth.md", task_text("04", status="running"))
        self.write("05-fifth.md", task_text("05"))
        self.plan(["01-first.md", "02-second.md", "03-third.md", "04-fourth.md", "05-fifth.md"])
        code, out = self.run_script("--frontier")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.split(), ["02-second.md", "05-fifth.md"])

    def test_frontier_empty(self):
        self.write("01-first.md", task_text("01", status="done"))
        self.plan(["01-first.md"])
        code, out = self.run_script("--frontier")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")

    def test_frontier_errors_exit_1(self):
        self.good()
        self.write("02-second.md", task_text("02", blocked="02"))
        code, _ = self.run_script("--frontier")
        self.assertEqual(code, 1)


class TestJ7(Base):
    def test_zero_task_is_error(self):
        self.write("00-zero.md", task_text("00"))
        self.write("01-first.md", task_text("01"))
        self.plan(["00-zero.md", "01-first.md"])
        self.assertError("00")
        self.assertError("start at 01")

    def test_set_starting_at_zero_is_error(self):
        self.write("00-zero.md", task_text("00"))
        self.write("01-first.md", task_text("01"))
        self.plan(["00-zero.md", "01-first.md"])
        code, out = self.run_script()
        self.assertEqual(code, 1, out)
        self.assertIn("numbers start at 01", out)

    def test_placeholder_status(self):
        self.good()
        self.write("01-first.md", task_text("01", status="[todo]"))
        code, out = self.run_script()
        self.assertEqual(code, 1, out)
        self.assertIn("placeholder not replaced: replace [todo] with one of: "
                      "todo, running, done, blocked", out)
        self.assertNotIn("is not one of", out)

    def test_placeholder_other_field(self):
        self.good()
        t = task_text("01").replace("Demo: Does the user see a result?", "Demo: [describe]")
        self.write("01-first.md", t)
        self.assertError("placeholder not replaced: replace [describe]")

    def test_errors_in_line_order(self):
        self.good()
        t = task_text("01", status="bogus", method="nope")
        t = t.replace("Interface: None\n", "Interface: [x]\n")
        self.write("01-first.md", t)
        code, out = self.run_script()
        self.assertEqual(code, 1, out)
        lns = [int(l.split(":")[1]) for l in out.splitlines() if l.startswith("ERROR 01-first.md")]
        self.assertGreaterEqual(len(lns), 3, out)
        self.assertEqual(lns, sorted(lns), out)

    def test_plan_names_missing_file(self):
        self.good()
        self.plan(["01-first.md", "02-second.md", "03-ghost.md"])
        self.assertError("03-ghost.md is listed but no such task file exists")

    def test_frontier_stream_split(self):
        self.good()
        self.write("02-second.md", task_text("02", status="bogus"))
        self.write("03-third.md", task_text("03"))
        self.plan(["01-first.md", "02-second.md", "03-third.md"])
        code, out = self.run_script("--frontier")
        self.assertEqual(code, 1)
        self.assertEqual(out.split(), ["01-first.md", "03-third.md"])
        self.assertIn("ERROR", self.last_err)
        self.assertNotIn("ERROR", out)

    def test_frontier_invalid_todo_task_still_listed(self):
        # Pinned decision: an invalid todo task with all blockers done is still
        # printed on stdout, its ERROR goes to stderr, and the exit code is 1.
        self.write("01-first.md", task_text("01", status="done"))
        self.write("02-second.md", task_text("02", blocked="01", method="bogus-method"))
        self.plan(["01-first.md", "02-second.md"], {"01-first.md": "done"})
        code, out = self.run_script("--frontier")
        self.assertEqual(code, 1)
        self.assertIn("02-second.md", out.split())
        self.assertNotIn("ERROR", out)
        self.assertTrue(any(l.startswith("ERROR 02-second.md") for l in self.last_err.splitlines()),
                        self.last_err)


if __name__ == "__main__":
    unittest.main()
