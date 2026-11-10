"""Validate a VERIFY.md file.

Usage: python3 scripts/validate_verification.py VERIFY_FILE [--root GIT_ROOT]
       python3 scripts/validate_verification.py --fingerprint --root GIT_ROOT

The Tree line is "clean" or "dirty <64 hex>". The fingerprint is the SHA-256 of
the bytes of "git diff HEAD --binary", then for each untracked, not ignored file
sorted by path (VERIFY.md excluded): path, NUL, file bytes, NUL.

Git checks run only when --root is given. The script never runs the commands
quoted in the Proofs table. Exit 0 on pass, 1 on findings, 2 on usage error.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

SECTIONS = ("Head", "Tree", "Proofs", "Verifier", "Findings", "Verdict")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NOTEST = re.compile(r"no tests? ran", re.I)
PLACEHOLDER = re.compile(r"^\[.*\]$")
HEXSHA = re.compile(r"^[0-9a-f]{7,40}$")


def table_rows(lines):
    """Rows of a Markdown table as (line_no, [cells]); header and separator dropped."""
    rows = []
    for ln, raw in lines:
        s = raw.strip()
        if not s.startswith("|"):
            continue
        body = s[1:]
        if body.endswith("|"):
            body = body[:-1]
        cells = [c.strip() for c in body.split("|")]
        if all(re.match(r"^:?-{2,}:?$", c) for c in cells if c) and any(cells):
            continue
        rows.append((ln, cells))
    return rows[1:]  # first row is the header


def git(root, *args):
    return subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True,
                          text=True, encoding="utf-8")


def is_verify(rel, extra=None):
    return rel.split("/")[-1] == "VERIFY.md" or (extra is not None and rel == extra)


def fingerprint(root, extra=None):
    """SHA-256 fingerprint of the working tree changes (see module docstring)."""
    cmd = ["git", "-C", str(root), "-c", "core.quotepath=false"]
    spec = ["--", "."]
    nm = subprocess.run(cmd + ["diff", "HEAD", "--name-only", "--no-renames", "-z"],
                        capture_output=True)
    if nm.returncode != 0:
        raise RuntimeError(nm.stderr.decode("utf-8", "replace").strip() or "git diff failed")
    for n in nm.stdout.decode("utf-8", "surrogateescape").split("\0"):
        if n and Path(n).name == "VERIFY.md":
            spec.append(":(exclude,literal)" + n)
    if extra:
        spec.append(":(exclude,literal)" + extra)
    d = subprocess.run(cmd + ["diff", "HEAD", "--binary"] + spec, capture_output=True)
    if d.returncode != 0:
        raise RuntimeError(d.stderr.decode("utf-8", "replace").strip() or "git diff failed")
    o = subprocess.run(cmd + ["ls-files", "-z", "--others", "--exclude-standard"],
                       capture_output=True)
    if o.returncode != 0:
        raise RuntimeError(o.stderr.decode("utf-8", "replace").strip() or "git ls-files failed")
    h = hashlib.sha256()
    h.update(d.stdout)
    names = sorted(n for n in o.stdout.decode("utf-8", "surrogateescape").split("\0")
                   if n and not is_verify(n, extra))
    for n in names:
        h.update(n.encode("utf-8", "surrogateescape") + b"\0")
        h.update((Path(root) / n).read_bytes() + b"\0")
    return h.hexdigest()


def tree_is_dirty(root, extra=None):
    r = git(root, "-c", "core.quotepath=false", "status", "--porcelain", "-uall")
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "git status failed")
    for line in r.stdout.splitlines():
        if line[3:] and not is_verify(line[3:].strip('"'), extra):
            return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate a VERIFY.md file.")
    ap.add_argument("verify_file", nargs="?", help="path to VERIFY.md")
    ap.add_argument("--fingerprint", action="store_true",
                    help="print the working-tree fingerprint for --root and exit")
    ap.add_argument("--root", help="git repository root; enables Head, Tree and SHA checks")
    args = ap.parse_args(argv)
    if args.fingerprint:
        if not args.root or not shutil.which("git"):
            print("usage error: --fingerprint needs --root and git", file=sys.stderr)
            return 2
        try:
            print(fingerprint(args.root))
        except (RuntimeError, OSError) as e:
            print("error: %s" % e, file=sys.stderr)
            return 2
        return 0
    if not args.verify_file:
        ap.print_usage(sys.stderr)
        print("usage error: VERIFY_FILE is required", file=sys.stderr)
        return 2
    path = Path(args.verify_file)
    if not path.is_file():
        print("usage error: %s is not a file" % path, file=sys.stderr)
        return 2
    items = []
    extra = None
    if args.root:
        try:
            extra = path.resolve().relative_to(Path(args.root).resolve()).as_posix()
        except ValueError:
            extra = None

    def ph(ln, val, options):
        if PLACEHOLDER.match(val):
            err(ln, "placeholder not replaced: replace %s with one of: %s" % (val, options))
            return True
        return False

    def err(ln, text):
        items.append(("ERROR", ln, text))

    def warn(ln, text):
        items.append(("WARN", ln, text))

    sec = {}
    sec_line = {}
    current = None
    for ln, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if raw.startswith("## "):
            current = raw[3:].strip()
            sec[current] = []
            sec_line[current] = ln
        elif current is not None:
            sec[current].append((ln, raw))
    for name in SECTIONS:
        if name not in sec:
            err(0, "missing section ## %s" % name)

    def value(name):
        for ln, raw in sec.get(name, []):
            if raw.strip():
                return ln, raw.strip()
        return sec_line.get(name, 0), ""

    use_git = bool(args.root)
    git_ok = False
    if use_git:
        if shutil.which("git"):
            git_ok = True
        else:
            warn(0, "git is unavailable; skipping git checks")

    # Head
    head_ok = False
    if "Head" in sec:
        ln, head = value("Head")
        if ph(ln, head, "a 40 character lowercase hex commit id"):
            pass
        elif not HEX40.match(head):
            err(ln, "Head must be 40 lowercase hex characters")
        else:
            head_ok = True
            if use_git and git_ok:
                r = git(args.root, "rev-parse", "HEAD")
                if r.returncode != 0:
                    err(ln, "git rev-parse HEAD failed in %s: %s" % (args.root, r.stderr.strip()))
                elif r.stdout.strip() != head:
                    err(ln, "Head does not match git HEAD (%s)" % r.stdout.strip())

    # Tree
    tree_clean = False
    tree_fp_ok = False
    if "Tree" in sec:
        ln, tree = value("Tree")
        parts = tree.split()
        if ph(ln, tree, "clean, dirty <64 hex fingerprint>"):
            pass
        elif parts == ["clean"]:
            tree_clean = True
        elif parts and parts[0] == "dirty":
            if len(parts) != 2 or not HEX64.match(parts[1]):
                err(ln, "a dirty Tree needs a fingerprint: dirty <64 lowercase hex>; "
                    "run validate_verification.py --fingerprint --root ROOT")
            else:
                tree_fp_ok = True
        else:
            err(ln, "Tree must be clean or dirty <64 hex>")
        if use_git and git_ok and (tree_clean or tree_fp_ok):
            try:
                if tree_clean and tree_is_dirty(args.root, extra):
                    err(ln, "Tree says clean but git status shows changes")
                    tree_clean = False
                elif tree_fp_ok:
                    if fingerprint(args.root, extra) != parts[1]:
                        err(ln, "Tree fingerprint does not match the working tree")
                        tree_fp_ok = False
            except (RuntimeError, OSError) as e:
                err(ln, "git check of Tree failed in %s: %s" % (args.root, e))
                tree_clean = tree_fp_ok = False
        if tree_fp_ok and not (use_git and git_ok):
            tree_fp_ok = False  # cannot be confirmed without --root

    # Proofs
    all_pass = True
    if "Proofs" in sec:
        for ln, c in table_rows(sec["Proofs"]):
            if len(c) < 5:
                err(ln, "Proofs row needs 5 cells")
                all_pass = False
                continue
            crit, cmd, words, excerpt, result = c[:5]
            if ph(ln, result, "pass, fail"):
                all_pass = False
                continue
            if result not in ("pass", "fail"):
                err(ln, "Result must be pass or fail, got '%s'" % result)
                all_pass = False
                continue
            effective = result
            if not excerpt:
                err(ln, "Output excerpt is empty for %s" % (crit or "row"))
                effective = "fail"
            else:
                if NOTEST.search(excerpt):
                    effective = "fail"
                    if result == "pass":
                        err(ln, "excerpt says 'no test ran' but Result is pass")
                pos = 0
                missed = False
                for w in [w.strip() for w in words.split(";") if w.strip()]:
                    i = excerpt.find(w, pos)
                    if i < 0:
                        missed = True
                        break
                    pos = i + len(w)
                if not words.strip():
                    missed = True
                if missed:
                    effective = "fail"
                    if result == "pass":
                        err(ln, "expected words \"%s\" not found in order in the excerpt, "
                            "but Result is pass" % words)
            if result == "fail":
                effective = "fail"
            if effective != "pass":
                all_pass = False
        if not table_rows(sec["Proofs"]):
            all_pass = False

    # Findings (parse before Verifier so IDs are known)
    finding_ids = set()
    open_findings = False
    if "Findings" in sec:
        for ln, c in table_rows(sec["Findings"]):
            if len(c) < 5:
                err(ln, "Findings row needs 5 cells")
                continue
            fid, _sev, _sum, status, closed = c[:5]
            finding_ids.add(fid)
            if status not in ("open", "closed"):
                err(ln, "Status must be open or closed, got '%s'" % status)
            elif status == "open":
                open_findings = True
            else:
                if not HEXSHA.match(closed):
                    err(ln, "Closed by must be 7 to 40 hex characters for a closed finding")
                elif use_git and git_ok:
                    r = git(args.root, "cat-file", "-e", closed + "^{commit}")
                    if r.returncode != 0:
                        err(ln, "Closed by %s is not an object in the repository" % closed)

    # Verifier
    all_holds = True
    if "Verifier" in sec:
        for ln, c in table_rows(sec["Verifier"]):
            if len(c) < 3:
                err(ln, "Verifier row needs 3 cells")
                all_holds = False
                continue
            holds, fnd = c[1], c[2]
            if holds not in ("yes", "no"):
                err(ln, "Holds must be yes or no, got '%s'" % holds)
                all_holds = False
            elif holds == "no":
                all_holds = False
                if fnd not in finding_ids:
                    err(ln, "Holds is no but the Finding cell '%s' names no ID in Findings" % fnd)

    # Verdict
    if "Verdict" in sec:
        ln, verdict = value("Verdict")
        if ph(ln, verdict, "PASS, FAIL, PARTIAL"):
            pass
        elif verdict not in ("PASS", "FAIL", "PARTIAL"):
            err(ln, "Verdict must be PASS, FAIL, or PARTIAL")
        elif verdict == "PASS":
            reasons = []
            if not head_ok:
                reasons.append("Head is not valid")
            if not (tree_clean or tree_fp_ok):
                if re.match(r"^dirty\b", value("Tree")[1]) and not use_git:
                    reasons.append("Tree is dirty and --root was not given")
                else:
                    reasons.append("Tree is not clean and has no matching fingerprint")
            if not all_pass:
                reasons.append("not every proof passes")
            if not all_holds:
                reasons.append("not every Holds is yes")
            if open_findings:
                reasons.append("a finding is open")
            if reasons:
                err(ln, "Verdict PASS is not allowed: " + "; ".join(reasons))

    for sev, ln, text in items:
        print("%s %s:%d: %s" % (sev, path, ln, text))
    ne = sum(1 for i in items if i[0] == "ERROR")
    print("%d errors, %d warnings" % (ne, len(items) - ne))
    return 1 if ne else 0


if __name__ == "__main__":
    sys.exit(main())
