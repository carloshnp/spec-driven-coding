"""Tests for scripts/validate_verification.py. Run: python3 assets/tests/test_validate_verification.py"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "validate_verification.py"
HEAD = "a" * 40


def doc(head=HEAD, tree="clean", proofs=None, verifier=None, findings=None, verdict="PASS",
        drop=None):
    proofs = proofs if proofs is not None else [
        "| C1 | pytest -q | 3 passed; 0 failed | 3 passed in 0.1s; 0 failed | pass |"]
    verifier = verifier if verifier is not None else ["| Tests judged | yes | |"]
    findings = findings if findings is not None else []
    parts = {
        "Head": "## Head\n%s\n" % head,
        "Tree": "## Tree\n%s\n" % tree,
        "Proofs": "## Proofs\n| Criterion | Command | Expected words | Output excerpt | Result |\n"
                  "|---|---|---|---|---|\n" + "\n".join(proofs) + "\n",
        "Verifier": "## Verifier\n| Check | Holds | Finding |\n|---|---|---|\n"
                    + "\n".join(verifier) + "\n",
        "Findings": "## Findings\n| ID | Severity | Summary | Status | Closed by |\n"
                    "|---|---|---|---|---|\n" + "\n".join(findings) + "\n",
        "Verdict": "## Verdict\n%s\n" % verdict,
    }
    if drop:
        del parts[drop]
    return "# Verification\n" + "".join(parts.values())


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.file = self.dir / "VERIFY.md"

    def tearDown(self):
        self._tmp.cleanup()

    def run_text(self, text, *args):
        self.file.write_text(text, encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPT), str(self.file)] + list(args),
                           capture_output=True, text=True, encoding="utf-8")
        return p.returncode, p.stdout

    def assertError(self, text, needle, *args):
        code, out = self.run_text(text, *args)
        self.assertEqual(code, 1, out)
        self.assertTrue(any(l.startswith("ERROR") and needle in l for l in out.splitlines()), out)

    def assertClean(self, text, *args):
        code, out = self.run_text(text, *args)
        self.assertEqual(code, 0, out)


class TestBasics(Base):
    def test_valid_pass(self):
        self.assertClean(doc())

    def test_help(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)

    def test_usage(self):
        p = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)

    def test_missing_file(self):
        p = subprocess.run([sys.executable, str(SCRIPT), str(self.dir / "none.md")],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)

    def test_missing_section(self):
        for s in ["Head", "Tree", "Proofs", "Verifier", "Findings", "Verdict"]:
            self.assertError(doc(drop=s), s)


class TestHeadTree(Base):
    def test_head_short(self):
        self.assertError(doc(head="abc123"), "Head")

    def test_head_uppercase(self):
        self.assertError(doc(head="A" * 40), "Head")

    def test_tree_value(self):
        self.assertError(doc(tree="muddy"), "Tree")


class TestProofs(Base):
    def test_words_in_order_pass(self):
        self.assertClean(doc())

    def test_words_out_of_order(self):
        p = ["| C1 | x | beta; alpha | alpha then beta | pass |"]
        self.assertError(doc(proofs=p), "order")

    def test_word_missing_marked_fail_is_ok_but_blocks_pass(self):
        p = ["| C1 | x | gamma | alpha beta | fail |"]
        code, out = self.run_text(doc(proofs=p, verdict="FAIL"))
        self.assertEqual(code, 0, out)

    def test_words_must_be_on_one_line_excerpt(self):
        p = ["| C1 | x | alpha; beta | alpha | pass |"]
        self.assertError(doc(proofs=p), "alpha; beta")

    def test_no_test_ran(self):
        p = ["| C1 | pytest | passed | no tests ran? no test ran, passed | pass |"]
        self.assertError(doc(proofs=p), "no test ran")

    def test_no_test_ran_marked_fail_ok(self):
        p = ["| C1 | pytest | passed | no test ran | fail |"]
        code, out = self.run_text(doc(proofs=p, verdict="FAIL"))
        self.assertEqual(code, 0, out)

    def test_empty_excerpt(self):
        p = ["| C1 | pytest | passed |  | fail |"]
        self.assertError(doc(proofs=p, verdict="FAIL"), "excerpt")

    def test_bad_result(self):
        p = ["| C1 | pytest | passed | passed | maybe |"]
        self.assertError(doc(proofs=p), "Result")


class TestVerifierFindings(Base):
    F_OPEN = "| F-01 | BLOCKER | bad | open | |"

    def test_holds_value(self):
        self.assertError(doc(verifier=["| T | sure | |"]), "Holds")

    def test_holds_no_needs_finding_id(self):
        self.assertError(doc(verifier=["| T | no | |"], verdict="FAIL"), "Finding")

    def test_holds_no_unknown_id(self):
        self.assertError(doc(verifier=["| T | no | F-09 |"], findings=[self.F_OPEN],
                             verdict="FAIL"), "F-09")

    def test_holds_no_linked_ok(self):
        code, out = self.run_text(doc(verifier=["| T | no | F-01 |"], findings=[self.F_OPEN],
                                      verdict="FAIL"))
        self.assertEqual(code, 0, out)

    def test_bad_finding_status(self):
        self.assertError(doc(findings=["| F-01 | NOTE | x | pending | |"], verdict="PARTIAL"),
                         "Status")

    def test_closed_sha_length(self):
        for sha, bad in [("abc123", True), ("a" * 41, True), ("abc1234", False),
                         ("b" * 40, False), ("xyz1234", True), ("", True)]:
            f = ["| F-01 | NOTE | x | closed | %s |" % sha]
            code, out = self.run_text(doc(findings=f))
            if bad:
                self.assertEqual(code, 1, (sha, out))
                self.assertIn("Closed by", out)
            else:
                self.assertEqual(code, 0, (sha, out))


class TestVerdict(Base):
    def test_bad_verdict(self):
        self.assertError(doc(verdict="MAYBE"), "Verdict")

    def test_pass_with_dirty_tree(self):
        self.assertError(doc(tree="dirty"), "PASS")

    def test_pass_with_failed_proof(self):
        p = ["| C1 | x | a | a | fail |"]
        self.assertError(doc(proofs=p), "PASS")

    def test_pass_with_holds_no(self):
        f = ["| F-01 | NOTE | x | closed | abcdef1 |"]
        self.assertError(doc(verifier=["| T | no | F-01 |"], findings=f), "PASS")

    def test_pass_with_open_finding(self):
        self.assertError(doc(findings=["| F-01 | NOTE | x | open | |"]), "PASS")

    def test_pass_with_bad_head(self):
        self.assertError(doc(head="zz"), "PASS")

    def test_fail_verdict_with_problems_is_fine(self):
        self.assertClean(doc(tree="dirty " + "c" * 64, verdict="FAIL"))

    def test_partial_fine(self):
        self.assertClean(doc(tree="dirty " + "c" * 64, verdict="PARTIAL"))

    def test_dirty_without_fingerprint(self):
        self.assertError(doc(tree="dirty", verdict="FAIL"), "fingerprint")

    def test_dirty_pass_without_root(self):
        self.assertError(doc(tree="dirty " + "c" * 64), "PASS")

    def test_placeholders(self):
        cases = [doc(head="[40 hex]"), doc(tree="[clean]"), doc(verdict="[PASS]"),
                 doc(proofs=["| C1 | x | a | a | [pass] |"])]
        for text in cases:
            self.assertError(text, "placeholder not replaced: replace [")

    def test_no_tests_ran_plural(self):
        p = ["| C1 | pytest | passed | No Tests Ran, passed | pass |"]
        self.assertError(doc(proofs=p), "no test ran")


def git(root, *args):
    return subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True,
                          text=True, encoding="utf-8", check=True).stdout.strip()


@unittest.skipUnless(shutil.which("git"), "git not installed")
class TestGit(Base):
    def setUp(self):
        super().setUp()
        self.repo = self.dir / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "T")
        git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "a.txt").write_text("one\n", encoding="utf-8")
        git(self.repo, "add", "a.txt")
        git(self.repo, "commit", "-q", "-m", "first")
        self.head = git(self.repo, "rev-parse", "HEAD")
        self.vdir = self.dir / "out"
        self.vdir.mkdir()
        self.file = self.vdir / "VERIFY.md"

    def fp(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--fingerprint", "--root", str(self.repo)],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout.strip()

    def test_fingerprint_format(self):
        self.assertRegex(self.fp(), r"^[0-9a-f]{64}$")

    def test_clean_tree_clean_claim_pass(self):
        self.assertClean(doc(head=self.head), "--root", str(self.repo))

    def test_dirty_pass_matching_fingerprint(self):
        (self.repo / "a.txt").write_text("two\n", encoding="utf-8")
        self.assertClean(doc(head=self.head, tree="dirty " + self.fp()), "--root", str(self.repo))

    def test_dirty_pass_wrong_fingerprint(self):
        (self.repo / "a.txt").write_text("two\n", encoding="utf-8")
        self.assertError(doc(head=self.head, tree="dirty " + "0" * 64), "fingerprint",
                         "--root", str(self.repo))

    def test_dirty_pass_no_root(self):
        (self.repo / "a.txt").write_text("two\n", encoding="utf-8")
        self.assertError(doc(head=self.head, tree="dirty " + self.fp()), "PASS")

    def test_dirty_no_fingerprint_with_root(self):
        (self.repo / "a.txt").write_text("two\n", encoding="utf-8")
        self.assertError(doc(head=self.head, tree="dirty"), "fingerprint",
                         "--root", str(self.repo))

    def test_verify_md_excluded(self):
        (self.repo / "a.txt").write_text("two\n", encoding="utf-8")
        before = self.fp()
        (self.repo / "VERIFY.md").write_text("# Verification\n", encoding="utf-8")
        self.assertEqual(self.fp(), before)
        (self.repo / "VERIFY.md").write_text("changed\n", encoding="utf-8")
        self.assertEqual(self.fp(), before)

    def test_nested_untracked_verify_md_excluded(self):
        (self.repo / "a.txt").write_text("two\n", encoding="utf-8")
        before = self.fp()
        (self.repo / "sub").mkdir()
        (self.repo / "sub" / "VERIFY.md").write_text("# Verification\n", encoding="utf-8")
        self.assertEqual(self.fp(), before)

    def test_nested_tracked_verify_md_modified_excluded(self):
        (self.repo / "sub").mkdir()
        (self.repo / "sub" / "VERIFY.md").write_text("old\n", encoding="utf-8")
        git(self.repo, "add", "sub/VERIFY.md")
        git(self.repo, "commit", "-q", "-m", "add nested verify")
        (self.repo / "a.txt").write_text("two\n", encoding="utf-8")
        before = self.fp()
        (self.repo / "sub" / "VERIFY.md").write_text("new\n", encoding="utf-8")
        self.assertEqual(self.fp(), before)

    def test_fingerprint_byte_layout(self):
        import hashlib
        (self.repo / "a.txt").write_text("two\n", encoding="utf-8")
        (self.repo / "my file.txt").write_bytes(b"hello\n")
        diff = subprocess.run(["git", "-C", str(self.repo), "diff", "HEAD", "--binary"],
                              capture_output=True, check=True).stdout
        self.assertTrue(diff)
        h = hashlib.sha256(diff)
        h.update(b"my file.txt" + b"\0" + b"hello\n" + b"\0")
        self.assertEqual(self.fp(), h.hexdigest())

    def test_ignored_files_do_not_change_fingerprint(self):
        (self.repo / ".gitignore").write_text("ignored/\n", encoding="utf-8")
        before = self.fp()
        (self.repo / "ignored").mkdir()
        (self.repo / "ignored" / "x.txt").write_text("junk\n", encoding="utf-8")
        self.assertEqual(self.fp(), before)

    def test_untracked_changes_fingerprint(self):
        before = self.fp()
        (self.repo / "new.txt").write_text("x\n", encoding="utf-8")
        mid = self.fp()
        self.assertNotEqual(before, mid)
        (self.repo / "new.txt").write_text("y\n", encoding="utf-8")
        self.assertNotEqual(mid, self.fp())

    def test_head_matches(self):
        self.assertClean(doc(head=self.head), "--root", str(self.repo))

    def test_head_mismatch(self):
        self.assertError(doc(head="b" * 40), "match", "--root", str(self.repo))

    def test_no_root_skips_git(self):
        self.assertClean(doc(head="b" * 40))

    def test_clean_claim_with_dirty_repo(self):
        (self.repo / "a.txt").write_text("two\n", encoding="utf-8")
        self.assertError(doc(head=self.head, tree="clean", verdict="FAIL"), "clean",
                         "--root", str(self.repo))

    def test_dirty_claim_with_dirty_repo_ok(self):
        (self.repo / "a.txt").write_text("two\n", encoding="utf-8")
        self.assertClean(doc(head=self.head, tree="dirty " + self.fp(), verdict="FAIL"),
                         "--root", str(self.repo))

    def test_closed_sha_exists(self):
        f = ["| F-01 | NOTE | x | closed | %s |" % self.head[:10]]
        self.assertClean(doc(head=self.head, findings=f), "--root", str(self.repo))

    def test_closed_sha_missing_in_repo(self):
        f = ["| F-01 | NOTE | x | closed | deadbee |"]
        self.assertError(doc(head=self.head, findings=f), "deadbee", "--root", str(self.repo))

    def test_bad_root_is_error(self):
        self.assertError(doc(head=self.head), "git", "--root", str(self.dir / "norepo"))


if __name__ == "__main__":
    unittest.main()
