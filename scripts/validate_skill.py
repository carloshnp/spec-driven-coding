"""Validate a skill directory against the build contract (checks 1 to 12).

Usage: python3 scripts/validate_skill.py SKILL_DIR
On Windows use: python scripts/validate_skill.py SKILL_DIR
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HELP = """usage: validate_skill.py SKILL_DIR

Validate a skill directory. Runs 12 checks: frontmatter, required keys, name,
description, SKILL.md size, referenced paths, flat references, forbidden files,
stdlib-only scripts, cross-reference scan, dash scan, eval JSON parsing.

Prints one line per finding: ERROR <path>:<line>: <text> or WARN <path>:<line>: <text>,
then a summary line: N errors, M warnings.

Exit codes: 0 no errors, 1 errors found, 2 usage error.
"""

REQUIRED_KEYS = ("name", "description", "license", "compatibility", "metadata")
FORBIDDEN_NAMES = ("README.md", "CHANGELOG.md", "install.sh", ".env", ".env.example", ".gitignore")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SLASH_RE = re.compile(r"(?<![\w/.:])/[A-Za-z][\w-]*")
PATH_RE = re.compile(r"\b(?:references|templates|scripts|assets)/[\w./*<>{}-]*")
SOURCES_REL = "references/16-sources.md"

# Denylist stored as word parts so this file does not match its own scan.
_DENY_PARTS = [
    ("writing", "plans"), ("subagent", "driven", "development"), ("grill", "ing"),
    ("grill", "me"), ("grill", "with", "docs"), ("domain", "modeling"),
    ("to", "tickets"), ("to", "spec"), ("td", "d"), ("implement", "spec"),
    ("sa", "ga"), ("tlc", "spec", "driven"), ("tech", "leads", "club"),
    ("multi", "agent", "review"), ("writing", "for", "agents"),
    ("writing", "great", "skills"), ("spec", "driven", "development"),
    ("incremental", "implementation"), ("planning", "and", "task", "breakdown"),
    ("test", "driven", "development"), ("api", "and", "interface", "design"),
    ("context", "engineering"), ("using", "agent", "skills"), ("interview", "me"),
    ("source", "driven", "development"), ("matt", "pocock"), ("addy", "osmani"),
    ("warp", "dot", "dev"), ("riek", "elt"), ("way", "finder"),
    ("setup", "matt", "pocock", "skills"), ("diagnosing", "bugs"),
    ("codebase", "design"), ("improve", "codebase", "architecture"),
]
# Two entries are single words in the contract; rejoin them without hyphens.
_NO_HYPHEN = {("riek", "elt"), ("matt", "pocock"), ("addy", "osmani"), ("warp", "dot", "dev"), ("way", "finder"),
              ("td", "d"), ("sa", "ga"), ("grill", "ing")}
DENYLIST: List[str] = []
for _p in _DENY_PARTS:
    DENYLIST.append("".join(_p) if _p in _NO_HYPHEN else "-".join(_p))
DENY_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(w) for w in sorted(DENYLIST, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
DASHES = (chr(0x2013), chr(0x2014))

_FALLBACK_STDLIB = frozenset("""
__future__ abc argparse array ast asyncio base64 bisect builtins bz2 calendar collections
configparser contextlib copy csv ctypes dataclasses datetime decimal difflib dis email enum
errno fnmatch fractions ftplib functools gc getopt getpass glob gzip hashlib heapq hmac html
http importlib inspect io itertools json keyword linecache locale logging lzma math mimetypes
multiprocessing numbers operator os pathlib pickle pkgutil platform pprint queue random re
sched secrets select shlex shutil signal socket sqlite3 ssl stat statistics string struct
subprocess sys sysconfig tarfile tempfile textwrap threading time timeit token tokenize
traceback types typing unicodedata unittest urllib uuid venv warnings weakref xml zipfile zlib
zoneinfo
""".split())
STDLIB = getattr(sys, "stdlib_module_names", None) or _FALLBACK_STDLIB


class Report:
    def __init__(self) -> None:
        self.errors = 0
        self.warnings = 0

    def error(self, path: str, line: int, text: str) -> None:
        self.errors += 1
        print("ERROR %s:%d: %s" % (path, line, text))

    def warn(self, path: str, line: int, text: str) -> None:
        self.warnings += 1
        print("WARN %s:%d: %s" % (path, line, text))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(lines: List[str]) -> Optional[Dict[str, object]]:
    """Return keys parsed from the block after the first '---', or None if unclosed."""
    data: Dict[str, object] = {}
    current_block: Optional[str] = None
    for raw in lines[1:]:
        if raw.strip() == "---":
            return data
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  ") and current_block is not None:
            m = re.match(r"^\s+([^:\s][^:]*):\s*(.*)$", raw)
            if m:
                block = data[current_block]
                assert isinstance(block, dict)
                block[m.group(1).strip()] = unquote(m.group(2))
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if value.strip() == "":
            data[key] = {}
            current_block = key
        else:
            data[key] = unquote(value)
            current_block = None
    return None


def check_frontmatter(root: Path, rep: Report) -> None:
    skill = root / "SKILL.md"
    if not skill.is_file():
        rep.error("SKILL.md", 0, "SKILL.md does not exist")
        return
    text = read(skill)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        rep.error("SKILL.md", 1, 'first line must be "---"')
        return
    fm = parse_frontmatter(lines)
    if fm is None:
        rep.error("SKILL.md", 1, "frontmatter is not closed by a second ---")
        return
    for key in REQUIRED_KEYS:
        if key not in fm:
            rep.error("SKILL.md", 1, "missing required key: " + key)
    name = fm.get("name")
    if isinstance(name, str):
        if name != root.resolve().name:
            rep.error("SKILL.md", 1, "name %r does not equal the directory name %r" % (name, root.resolve().name))
        if not NAME_RE.match(name):
            rep.error("SKILL.md", 1, "name %r does not match the pattern ^[a-z0-9]+(-[a-z0-9]+)*$" % name)
        if not 1 <= len(name) <= 64:
            rep.error("SKILL.md", 1, "name length %d is outside 1 to 64" % len(name))
    desc = fm.get("description")
    if isinstance(desc, str):
        if len(desc) > 60:
            rep.error("SKILL.md", 1, "description is %d characters, at most 60 allowed" % len(desc))
        if not desc.endswith("."):
            rep.error("SKILL.md", 1, "description must end with a period")
        if re.search(r"\.\s", desc):
            rep.error("SKILL.md", 1, "description must be exactly one sentence")
        if not desc.startswith("Use"):
            rep.error("SKILL.md", 1, 'description must start with "Use"')


def check_size(root: Path, rep: Report) -> None:
    skill = root / "SKILL.md"
    if not skill.is_file():
        return
    text = read(skill)
    n = len(text.splitlines())
    if n > 200:
        rep.error("SKILL.md", 0, "SKILL.md has %d lines, at most 200 allowed" % n)
    if len(text) > 24000:
        rep.error("SKILL.md", 0, "SKILL.md has %d characters, at most 24000 allowed" % len(text))


def check_paths(root: Path, rep: Report) -> None:
    skill = root / "SKILL.md"
    if not skill.is_file():
        return
    for i, line in enumerate(read(skill).splitlines(), 1):
        for m in PATH_RE.finditer(line):
            p = m.group(0)
            if any(c in p for c in "*<>{}") or "NN" in p:
                continue  # placeholder pattern, not a concrete path
            p = p.rstrip(".,;:")
            if not (root / p).exists():
                rep.error("SKILL.md", i, "referenced path does not exist: " + p)


def check_references(root: Path, rep: Report) -> None:
    refs = root / "references"
    if not refs.is_dir():
        return
    for child in sorted(refs.iterdir()):
        rel = "references/" + child.name
        if child.is_dir():
            rep.error(rel, 0, "references/ must be flat, found subdirectory")
            continue
        lines = read(child).splitlines()
        if len(lines) > 150:
            rep.error(rel, 0, "file has %d lines, at most 150 allowed" % len(lines))
        if len(lines) > 100 and not any(l.strip() == "## Contents" for l in lines):
            rep.error(rel, 0, "file over 100 lines needs a line ## Contents")


def all_files(root: Path) -> List[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".git" not in p.parts)


def rel_of(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def check_forbidden(root: Path, files: List[Path], rep: Report) -> None:
    for p in files:
        rel = rel_of(root, p)
        if p.name in FORBIDDEN_NAMES:
            rep.error(rel, 0, "forbidden file name: " + p.name)
        if p.name == "SKILL.md" and rel != "SKILL.md":
            rep.error(rel, 0, "nested SKILL.md is forbidden")


def check_scripts(root: Path, rep: Report) -> None:
    sdir = root / "scripts"
    if not sdir.is_dir():
        return
    for child in sorted(sdir.iterdir()):
        rel = "scripts/" + child.name
        if child.is_dir():
            if child.name != "__pycache__":
                rep.error(rel, 0, "scripts/ must be flat, found subdirectory")
            continue
        if child.suffix != ".py":
            continue
        try:
            tree = ast.parse(read(child), filename=rel)
        except SyntaxError as exc:
            rep.error(rel, exc.lineno or 0, "syntax error: %s" % exc.msg)
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in STDLIB:
                        rep.error(rel, node.lineno, "import of non-stdlib module: " + top)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    rep.error(rel, node.lineno, "relative import is forbidden in scripts")
                elif node.module:
                    top = node.module.split(".")[0]
                    if top not in STDLIB:
                        rep.error(rel, node.lineno, "import of non-stdlib module: " + top)


def check_text_scans(root: Path, files: List[Path], rep: Report) -> None:
    for p in files:
        rel = rel_of(root, p)
        if p.suffix not in (".md", ".py", ".json"):
            # dash scan still applies to every file, but only if it decodes as text
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            scan_cross = False
        else:
            text = read(p)
            scan_cross = rel != SOURCES_REL
        for i, line in enumerate(text.splitlines(), 1):
            if scan_cross:
                for m in DENY_RE.finditer(line):
                    rep.error(rel, i, "cross-reference to a forbidden name: " + m.group(0))
                for m in SLASH_RE.finditer(line):
                    rep.error(rel, i, "slash-command token: " + m.group(0))
            for d in DASHES:
                if d in line:
                    rep.error(rel, i, "em or en dash (U+%04X) found; use a hyphen or colon" % ord(d))


def check_json(root: Path, rep: Report) -> None:
    evals = root / "assets" / "evals"
    if not evals.is_dir():
        return
    for p in sorted(evals.glob("*.json")):
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            rep.error(rel_of(root, p), 0, "invalid JSON: %s" % exc)


def main(argv: List[str]) -> int:
    if any(a in ("-h", "--help") for a in argv):
        print(HELP)
        return 0
    if len(argv) != 1:
        print("usage: validate_skill.py SKILL_DIR", file=sys.stderr)
        return 2
    root = Path(argv[0])
    if not root.is_dir():
        print("error: not a directory: %s" % argv[0], file=sys.stderr)
        return 2
    rep = Report()
    files = all_files(root)
    check_frontmatter(root, rep)      # checks 1 to 4
    check_size(root, rep)             # 5
    check_paths(root, rep)            # 6
    check_references(root, rep)       # 7
    check_forbidden(root, files, rep) # 8
    check_scripts(root, rep)          # 9
    check_text_scans(root, files, rep)  # 10 and 11
    check_json(root, rep)             # 12
    print("%d errors, %d warnings" % (rep.errors, rep.warnings))
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
