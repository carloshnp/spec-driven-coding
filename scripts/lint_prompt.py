"""Lint a PROMPT.md against the prompt contract.

Usage: python3 scripts/lint_prompt.py PROMPT_FILE [--json]
Exit 0 on pass, 1 on findings, 2 on usage error.
Each finding prints as: ERROR <path>:<line>: <text> or WARN <path>:<line>: <text>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PUBLIC_TYPES = [
    "public function", "public method", "public class", "public type",
    "public constant", "endpoint", "command",
]
FIELDS = ["Path", "Name", "Type", "Input", "Output", "Description"]
ALLOW_MARKER = "<!-- allow-banned -->"

BANNED = [
    ("should", r"(?<!\w)should(?!\w)"),
    ("or", r"(?<!\w)or(?!\w)"),
    ("alternatively", r"(?<!\w)alternatively(?!\w)"),
    ("either", r"(?<!\w)either(?!\w)"),
    ("recommended", r"(?<!\w)recommended(?!\w)"),
    ("etc.", r"(?<!\w)etc\."),
    ("you can", r"(?<!\w)you\s+can(?!\w)"),
    ("something like", r"(?<!\w)something\s+like(?!\w)"),
    ("relevant technologies", r"(?<!\w)relevant\s+technologies(?!\w)"),
]
BANNED_RE = [(label, re.compile(p, re.IGNORECASE)) for label, p in BANNED]

INTERNAL_REFS = [
    ("TODO", re.compile(r"\bTODO\b")),
    ("FIXME", re.compile(r"\bFIXME\b")),
    ("TBD", re.compile(r"\bTBD\b")),
    ("task <number>", re.compile(r"\btask\s+\d+\b", re.IGNORECASE)),
    ("AD-<number>", re.compile(r"\bAD-\d+\b")),
    ("TLC-<number>", re.compile(r"\bTLC-\d+\b")),
]

COMMON = ["Title", "Description", "Expected Interface"]
PATTERN_A = ["Tech Stack", "Key Requirements", "Current State"]
PATTERN_B = ["Current State", "Required Implementation", "Deliverables"]
A_ONLY = ["Tech Stack", "Key Requirements"]
B_ONLY = ["Required Implementation", "Deliverables"]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FIELD_RE = re.compile(r"^-\s+([A-Za-z]+):\s*(.*?)\s*$")
PLACEHOLDER_RE = re.compile(r"^\[[^\[\]]*\]$")
COMPILE_MARKER = "Compile notes (delete this block before linting):"
DUNDER_RE = re.compile(r"^__[A-Za-z0-9](?:\w*[A-Za-z0-9])?__$")
WORD_SPLIT_RE = re.compile(r"[^A-Za-z0-9]+")
RUBRIC_RE = re.compile(r"^-\s+\(w([^)]*)\)\s*(.*)$")


def scan_lines(text):
    """Return list of (lineno, line, in_fence). Fence delimiter lines count as in_fence."""
    out = []
    fence = None
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if fence is None:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence = stripped[:3]
                out.append((i, line, True))
                continue
            out.append((i, line, False))
        else:
            out.append((i, line, True))
            if stripped.startswith(fence):
                fence = None
    return out


def sections(lines):
    """Map level-2 heading title to (start_line_index, end_line_index) over `lines` (exclusive end)."""
    heads = []
    for idx, (no, line, fenced) in enumerate(lines):
        if fenced:
            continue
        m = HEADING_RE.match(line)
        if m and len(m.group(1)) == 2:
            heads.append((m.group(2).strip(), idx))
    result = {}
    for n, (title, idx) in enumerate(heads):
        end = heads[n + 1][1] if n + 1 < len(heads) else len(lines)
        if title not in result:
            result[title] = (idx, end)
    return result


def detect_pattern(text):
    secs = sections(scan_lines(text))
    has_a = any(s in secs for s in A_ONLY)
    has_b = any(s in secs for s in B_ONLY)
    if has_a and not has_b:
        return "A"
    if has_b and not has_a:
        return "B"
    return None


def lint_text(text):
    """Return a list of (level, line, text) tuples."""
    findings = []
    lines = scan_lines(text)

    def add(level, line, msg):
        findings.append((level, line, msg))

    # 1. banned words
    for no, line, fenced in lines:
        if fenced or ALLOW_MARKER in line:
            continue
        for label, rx in BANNED_RE:
            if rx.search(line):
                add("ERROR", no, 'banned word "%s"' % label)

    # 2. required sections
    secs = sections(lines)
    pattern = detect_pattern(text)
    if pattern is None:
        if any(s in secs for s in A_ONLY) and any(s in secs for s in B_ONLY):
            add("ERROR", 0, "cannot detect pattern: sections of pattern A and pattern B are mixed")
        else:
            add("ERROR", 0, "cannot detect pattern: add the pattern A sections (Tech Stack, Key Requirements) "
                            "or the pattern B sections (Required Implementation, Deliverables)")
    required = list(COMMON) + (PATTERN_A if pattern == "A" else PATTERN_B if pattern == "B" else ["Current State"])
    seen = set()
    for name in required:
        if name in seen:
            continue
        seen.add(name)
        if name not in secs:
            add("ERROR", 0, "missing required section: %s" % name)

    # 2b. placeholders and the compile block
    in_section = False
    for no, line, fenced in lines:
        if COMPILE_MARKER in line:
            add("ERROR", no, "compile block is still present; delete the compile notes and the instruction list")
        if fenced:
            continue
        m = HEADING_RE.match(line)
        if m and len(m.group(1)) == 2:
            in_section = True
            continue
        if in_section and PLACEHOLDER_RE.match(line.strip()):
            add("ERROR", no, "placeholder not replaced: %s" % line.strip())

    # 3. Expected Interface
    if "Expected Interface" in secs:
        s, e = secs["Expected Interface"]
        lint_interface(lines[s + 1:e], lines[s][0], add)

    # 4. Rubric
    if "Rubric" in secs:
        s, e = secs["Rubric"]
        lint_rubric(lines[s + 1:e], lines[s][0], add)

    # 5. internal references
    for no, line, fenced in lines:
        for label, rx in INTERNAL_REFS:
            if rx.search(line):
                add("ERROR", no, "internal reference (%s)" % label)

    # 6. dashes
    for no, line, fenced in lines:
        if "\u2014" in line or "\u2013" in line:
            add("WARN", no, "em or en dash; use a hyphen or a colon")

    findings.sort(key=lambda f: (f[1], f[0] != "ERROR"))
    return findings


CAMEL_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def first_word(title):
    """First word of a heading, split at camel-case boundaries and non-alphanumerics, lowercased."""
    words = [w for w in WORD_SPLIT_RE.split(CAMEL_RE.sub(" ", title)) if w]
    return words[0].lower() if words else ""


def lint_interface(body, head_no, add):
    entries = []  # (heading_no, heading_text, [(lineno, key, value)])
    current = None
    for no, line, fenced in body:
        if fenced:
            continue
        m = HEADING_RE.match(line)
        if m and len(m.group(1)) >= 3:
            title = m.group(2).strip()
            words = [w.lower() for w in WORD_SPLIT_RE.split(title) if w]
            if "private" in words or "internal" in words:
                add("ERROR", no, 'heading "%s" in Expected Interface mentions private or internal items; '
                                 "list public names only" % title)
            elif first_word(title) in ("internal", "private"):
                add("WARN", no, "heading %s starts with Internal or Private; confirm it is public" % title)
            current = (no, title, [])
            entries.append(current)
            continue
        if current is not None:
            fm = FIELD_RE.match(line)
            if fm:
                current[2].append((no, fm.group(1), fm.group(2)))
    if not entries:
        add("ERROR", head_no, "Expected Interface has no entry (### Name)")
        return
    for no, title, fields in entries:
        keys = [k for _, k, _ in fields]
        if keys != FIELDS:
            missing = [f for f in FIELDS if f not in keys]
            extra = [k for k in keys if k not in FIELDS]
            dup = sorted(set(k for k in keys if keys.count(k) > 1))
            if missing:
                add("ERROR", no, "entry %s is missing field(s): %s" % (title, ", ".join(missing)))
            if extra:
                add("ERROR", no, "entry %s has unknown field(s): %s" % (title, ", ".join(extra)))
            if dup:
                add("ERROR", no, "entry %s repeats field(s): %s" % (title, ", ".join(dup)))
            if not missing and not extra and not dup:
                add("ERROR", no, "entry %s fields are out of order; required order: %s" % (title, ", ".join(FIELDS)))
        values = {}
        for fno, k, v in fields:
            values.setdefault(k, (fno, v))
            if k in FIELDS and not v:
                add("ERROR", fno, "entry %s: field %s has no content (use N/A when there is none)" % (title, k))
            if v.startswith("["):
                add("ERROR", fno, "placeholder not replaced in field %s: - %s: %s" % (k, k, v))
        if "Name" in values:
            fno, name = values["Name"]
            if name and name != title:
                add("ERROR", fno, "Name %s does not match heading %s" % (name, title))
            if name.startswith("_") and not DUNDER_RE.match(name):
                add("ERROR", fno, "Name %s begins with an underscore; private names are not listed" % name)
        if title.startswith("_") and not DUNDER_RE.match(title):
            add("ERROR", no, "heading %s begins with an underscore; private names are not listed" % title)
        if "Type" in values:
            fno, typ = values["Type"]
            if typ and typ not in PUBLIC_TYPES:
                add("ERROR", fno, "Type %s is not an allowed public type (%s)" % (typ, ", ".join(PUBLIC_TYPES)))


def lint_rubric(body, head_no, add):
    count = 0
    for no, line, fenced in body:
        if fenced:
            continue
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        count += 1
        m = RUBRIC_RE.match(stripped)
        if not m:
            add("ERROR", no, "rubric line must look like: - (w1) criterion")
            continue
        if m.group(1) not in ("1", "3", "5"):
            add("ERROR", no, "rubric weight w%s is not allowed; use 1, 3, or 5" % m.group(1))
        if not m.group(2):
            add("ERROR", no, "rubric line has no criterion text")
    if count < 5 or count > 30:
        add("ERROR", head_no, "Rubric has %d criteria; it needs 5 to 30" % count)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint a PROMPT.md against the prompt contract.")
    ap.add_argument("prompt_file", help="path to PROMPT.md")
    ap.add_argument("--json", action="store_true", help="print findings as a JSON list")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    path = Path(args.prompt_file)
    if not path.is_file():
        print("usage error: not a file: %s" % path, file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    findings = lint_text(text)
    if args.json:
        print(json.dumps([{"level": l, "line": n, "text": t} for l, n, t in findings], indent=2))
    else:
        pat = detect_pattern(text)
        print("pattern %s" % (pat if pat else "unknown"))
        for level, no, msg in findings:
            print("%s %s:%d: %s" % (level, path, no, msg))
        ne = sum(1 for f in findings if f[0] == "ERROR")
        print("%d errors, %d warnings" % (ne, len(findings) - ne))
    return 1 if any(f[0] == "ERROR" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
