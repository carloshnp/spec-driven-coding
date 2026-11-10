"""Validate a tasks directory (task files and plan.md index).

Usage: python3 scripts/validate_tasks.py TASKS_DIR [--frontier]

Prints ERROR/WARN lines. With --frontier, prints the todo tasks whose blockers
are all done, one file name per line (findings go to stderr in that mode).
Exit 0 on pass, 1 on findings, 2 on usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^(\d{2})-[a-z0-9-]+\.md$")
STATUSES = ("todo", "running", "done", "blocked")
METHODS = ("tests", "cli transcript", "computer use")
EXTS = "py|ts|tsx|js|jsx|md|json|go|rs|toml|yaml|yml|sh|txt|css|html|java|c|cpp|h|rb"
PATH_RE = re.compile(r"(?<![\w.\-/])(?:\.{0,2}/)?[\w.\-]+(?:/[\w.\-]+)+\.(?:%s)(?![\w])" % EXTS)
PLAN_RE = re.compile(r"^-\s+(\S+\.md):\s*(\S.*)$")
PLACEHOLDER_RE = re.compile(r"^\[[^\]]*\]$")
FIELD_NAMES = ("Status", "Blocked by", "Demo", "What it delivers", "Interface",
               "Validation method")


class Report:
    def __init__(self):
        self.items = []

    def error(self, path, line, text):
        self.items.append(("ERROR", str(path), line, text))

    def errors(self):
        return sum(1 for i in self.items if i[0] == "ERROR")

    def warns(self):
        return sum(1 for i in self.items if i[0] == "WARN")


def parse_task(text):
    """Return (fields {name: (value, line)}, sections {title: [(line, text)]}, lines)."""
    lines = text.splitlines()
    fields = {}
    sections = {}
    current = None
    for idx, raw in enumerate(lines, 1):
        if raw.startswith("## "):
            current = raw[3:].strip()
            sections.setdefault(current, [])
            continue
        if current is None:
            m = re.match(r"^([A-Za-z][A-Za-z ]*):\s*(.*)$", raw)
            if m and m.group(1) in FIELD_NAMES and m.group(1) not in fields:
                fields[m.group(1)] = (m.group(2).strip(), idx)
        else:
            sections[current].append((idx, raw))
    return fields, sections, lines


def bullets(section):
    return [(n, t.strip()[2:].strip()) for n, t in section if re.match(r"^\s*-\s+\S", t)]


def find_paths(lines, report, path):
    in_fence = False
    proto = False
    for idx, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            if in_fence:
                in_fence = False
                proto = False
            else:
                in_fence = True
                info = stripped[3:].strip().split()
                proto = bool(info) and info[0] == "prototype"
            continue
        if in_fence and proto:
            continue
        for m in PATH_RE.finditer(raw):
            report.error(path, idx, "path-like token '%s' outside a prototype block; "
                         "task files carry no file paths or code" % m.group(0))


def validate(tasks_dir, report):
    """Return {nn: status} for tasks whose files parsed (plus blockers map)."""
    tasks = {}
    names_by_num = {}
    for p in sorted(tasks_dir.glob("*.md")):
        if p.name == "plan.md":
            continue
        m = NAME_RE.match(p.name)
        if not m:
            report.error(p.name, 0, "file name does not match NN-slug.md "
                         "(two digits, lowercase letters, digits, hyphens)")
            continue
        names_by_num.setdefault(int(m.group(1)), []).append(p.name)
    if 0 in names_by_num:
        report.error(names_by_num[0][0], 0, "task number 00 is not allowed: numbers start at 01")
    for num, names in sorted(names_by_num.items()):
        if len(names) > 1:
            report.error(names[1], 0, "duplicate task number %02d: %s" % (num, ", ".join(names)))
    if names_by_num:
        for num in range(1, max(names_by_num) + 1):
            if num not in names_by_num:
                report.error(tasks_dir.name, 0, "missing task number %02d (numbers must be "
                             "contiguous from 01)" % num)
        if 1 not in names_by_num and min(names_by_num) > 1:
            pass  # already reported by the loop above
    else:
        report.error(str(tasks_dir), 0, "no task files found")

    # plan.md
    plan = tasks_dir / "plan.md"
    all_names = [n for names in names_by_num.values() for n in names]
    if not plan.is_file():
        report.error("plan.md", 0, "plan.md is missing")
    else:
        listed = {}
        for idx, raw in enumerate(plan.read_text(encoding="utf-8").splitlines(), 1):
            m = PLAN_RE.match(raw.strip())
            if m:
                listed.setdefault(m.group(1), []).append(idx)
        for name, lns in listed.items():
            if len(lns) > 1:
                report.error("plan.md", lns[1], "%s is listed more than once" % name)
            if name not in all_names:
                report.error("plan.md", lns[0], "%s is listed but no such task file exists" % name)
        for name in sorted(all_names):
            if name not in listed:
                report.error("plan.md", 0, "task file %s is missing from the index" % name)

    # task files
    info = {}
    for num, names in sorted(names_by_num.items()):
        for name in names:
            fpath = tasks_dir / name
            text = fpath.read_text(encoding="utf-8")
            fields, sections, lines = parse_task(text)
            first = lines[0] if lines else ""
            m = re.match(r"^#\s+(\d{2}):\s*(\S.*)$", first)
            if not m:
                report.error(name, 1, "first line must be '# NN: title'")
            elif int(m.group(1)) != num:
                report.error(name, 1, "title number %s does not match file number %02d"
                             % (m.group(1), num))
            for f in ("Status", "Blocked by", "Demo", "What it delivers", "Interface",
                      "Validation method"):
                if f not in fields or not fields[f][0]:
                    report.error(name, fields[f][1] if f in fields else 0,
                                 "%s line is missing or empty" % f)
            ph = set()
            for f, (val, fl) in fields.items():
                if PLACEHOLDER_RE.match(val):
                    ph.add(f)
                    allowed = {"Status": STATUSES, "Validation method": METHODS}.get(f)
                    report.error(name, fl, "placeholder not replaced: replace %s with %s"
                                 % (val, "one of: " + ", ".join(allowed) if allowed
                                    else "real content"))
            status = fields.get("Status", ("", 0))[0]
            if "Status" in fields and "Status" not in ph and status not in STATUSES:
                report.error(name, fields["Status"][1],
                             "Status '%s' is not one of %s" % (status, ", ".join(STATUSES)))
            vm = fields.get("Validation method", ("", 0))[0]
            if vm and "Validation method" not in ph and vm not in METHODS:
                report.error(name, fields["Validation method"][1],
                             "Validation method '%s' is not one of %s" % (vm, ", ".join(METHODS)))
            blockers = []
            bb = fields.get("Blocked by", ("", 0))
            if bb[0] and bb[0] != "None" and "Blocked by" not in ph:
                for tok in [t.strip() for t in bb[0].split(",")]:
                    if not re.match(r"^\d{2}$", tok):
                        report.error(name, bb[1], "Blocked by entry '%s' is not a task number" % tok)
                        continue
                    n = int(tok)
                    if n >= num:
                        report.error(name, bb[1], "blocker %s must be a strictly lower number "
                                     "than %02d" % (tok, num))
                    elif n not in names_by_num:
                        report.error(name, bb[1], "blocker %s does not exist" % tok)
                    else:
                        blockers.append(n)
            crit = bullets(sections.get("Criteria", []))
            if "Criteria" not in sections or not crit:
                report.error(name, 0, "## Criteria needs at least one bullet")
            for ln, t in crit:
                if "False if:" not in t:
                    report.error(name, ln, "criterion lacks a 'False if:' clause")
            if not bullets(sections.get("Evidence required", [])):
                report.error(name, 0, "## Evidence required needs at least one bullet")
            find_paths(lines, report, name)
            info[num] = (name, status, blockers)
    return info


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate task files and plan.md in a tasks directory.")
    ap.add_argument("tasks_dir", help="directory holding NN-slug.md files and plan.md")
    ap.add_argument("--frontier", action="store_true",
                    help="print todo tasks whose blockers are all done (read-only)")
    args = ap.parse_args(argv)
    d = Path(args.tasks_dir)
    if not d.is_dir():
        print("usage error: %s is not a directory" % d, file=sys.stderr)
        return 2
    report = Report()
    info = validate(d, report)
    out = sys.stderr if args.frontier else sys.stdout
    for sev, p, ln, text in sorted(report.items, key=lambda i: (i[1], i[2])):
        print("%s %s:%d: %s" % (sev, p, ln, text), file=out)
    if args.frontier:
        for num in sorted(info):
            name, status, blockers = info[num]
            if status == "todo" and all(info.get(b, ("", ""))[1] == "done" for b in blockers):
                print(name)
    else:
        print("%d errors, %d warnings" % (report.errors(), report.warns()))
    return 1 if report.errors() else 0


if __name__ == "__main__":
    sys.exit(main())
