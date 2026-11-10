"""Check that tests import only public names and that every public name is imported.

Usage: python3 scripts/check_interface_coverage.py --prompt PROMPT_FILE --tests DIR_OR_FILE
           [--package NAME ...] [--lang auto|python|js]
Exit 0 on pass, 1 on findings, 2 on usage error.
Each finding prints as: ERROR <path>:<line>: <text> or WARN <path>:<line>: <text>
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

IGNORED_MODULES = {"pytest", "unittest", "hypothesis", "mock"}
PY_EXT = {".py"}
JS_EXT = {".js", ".jsx", ".ts", ".tsx"}
SKIP_DIRS = {"node_modules", "__pycache__", ".git", ".venv", "venv"}

_FALLBACK_STDLIB = {
    "abc", "argparse", "array", "ast", "asyncio", "base64", "bisect", "builtins", "calendar", "collections",
    "concurrent", "configparser", "contextlib", "copy", "csv", "ctypes", "dataclasses", "datetime", "decimal",
    "difflib", "email", "enum", "errno", "fnmatch", "fractions", "functools", "gc", "getpass", "glob", "gzip",
    "hashlib", "heapq", "hmac", "html", "http", "importlib", "inspect", "io", "ipaddress", "itertools", "json",
    "logging", "math", "mimetypes", "multiprocessing", "numbers", "operator", "os", "pathlib", "pickle",
    "platform", "pprint", "queue", "random", "re", "secrets", "select", "shlex", "shutil", "signal", "socket",
    "sqlite3", "ssl", "stat", "statistics", "string", "struct", "subprocess", "sys", "tempfile", "textwrap",
    "threading", "time", "timeit", "tokenize", "traceback", "types", "typing", "unicodedata", "unittest",
    "urllib", "uuid", "warnings", "weakref", "xml", "zipfile", "zlib", "__future__", "copyreg", "sched",
    "selectors", "tarfile", "tomllib", "venv", "zoneinfo", "graphlib", "bz2", "lzma", "codecs", "locale",
}
STDLIB = set(getattr(sys, "stdlib_module_names", _FALLBACK_STDLIB))

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
NAME_RE = re.compile(r"^-\s+Name:\s*(.*?)\s*$")


NOT_IMPORTABLE_TYPES = {"endpoint", "command"}
TYPE_RE = re.compile(r"^-\s+Type:\s*(.*?)\s*$")


def parse_interface(text):
    """Return (public, importable) name sets, or None when Expected Interface is missing.

    Entries of Type endpoint or command are public but not importable.
    """
    entries = []  # each: {"names": set, "type": str}
    seen_section = [False]
    in_section = False
    fence = False
    for line in text.splitlines():
        s = line.lstrip()
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence
            continue
        if fence:
            continue
        m = HEADING_RE.match(line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            if level == 2:
                in_section = title == "Expected Interface"
                if in_section:
                    seen_section[0] = True
                continue
            if in_section and level >= 3:
                entries.append({"names": {title.split(".")[0].strip()}, "type": ""})
            continue
        if in_section and entries:
            nm = NAME_RE.match(line)
            if nm and nm.group(1):
                entries[-1]["names"].add(nm.group(1).split(".")[0].strip())
                continue
            tm = TYPE_RE.match(line)
            if tm:
                entries[-1]["type"] = tm.group(1)
    if not seen_section[0]:
        return None
    public, importable = set(), set()
    for e in entries:
        public |= e["names"]
        if e["type"] not in NOT_IMPORTABLE_TYPES:
            importable |= e["names"]
    public.discard("")
    importable.discard("")
    return public, importable


def parse_public_names(text):
    """Return the set of public names, or None when Expected Interface is missing."""
    got = parse_interface(text)
    return None if got is None else got[0]


def _join(base, name):
    return base + name if base.endswith(".") else base + "." + name


def _is_private(segment):
    return segment.startswith("_") and not (segment.startswith("__") and segment.endswith("__"))


def _attribute_chains(tree):
    """Yield (root_name, [attrs], lineno) for each maximal Name.attr.attr chain."""
    inner = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute):
            inner.add(id(node.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and id(node) not in inner:
            attrs = []
            cur = node
            while isinstance(cur, ast.Attribute):
                attrs.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                yield cur.id, list(reversed(attrs)), node.lineno


def python_imports(source, packages):
    """Return [(name, line)] of project names used by Python test source.

    A project import is a relative import, or an absolute import whose top-level
    package is in `packages`. Module imports are not reported; attribute uses on a
    module binding are reported by the attribute name. Private path segments are
    reported by their own name.
    """
    tree = ast.parse(source)
    out = []
    modules = set()      # dotted module paths seen in project imports (every prefix)
    froms = []           # (node, base) for project from-imports
    bindings = {}        # local name -> dotted module path

    def add_prefixes(path):
        parts = path.split(".")
        for i in range(1, len(parts) + 1):
            modules.add(".".join(parts[:i]))

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            top = (node.module or "").split(".")[0]
            if node.level > 0:
                base = "." * node.level + (node.module or "")
            elif top in packages:
                base = node.module
            else:
                continue
            froms.append((node, base))
            if node.module:
                add_prefixes(node.module if node.level == 0 else base.lstrip(".") or base)
                if node.level > 0:
                    modules.add(base)
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in packages:
                    add_prefixes(a.name)
                    segs = a.name.split(".")[1:]
                    for seg in segs:
                        if _is_private(seg):
                            out.append((seg, node.lineno))
                    if a.asname:
                        bindings[a.asname] = a.name
                    else:
                        bindings[a.name.split(".")[0]] = a.name.split(".")[0]
    chains = list(_attribute_chains(tree))
    attr_bases = {root for root, _, _ in chains}
    for node, base in froms:
        for seg in (node.module or "").split(".")[1:] if node.level == 0 else (node.module or "").split("."):
            if seg and _is_private(seg):
                out.append((seg, node.lineno))
        for a in node.names:
            if a.name == "*":
                continue
            candidate = _join(base, a.name) if base else a.name
            is_module = (not _is_private(a.name) and not a.name.startswith("_")
                         and (candidate in modules or (a.name[:1].islower() and (a.asname or a.name) in attr_bases)))
            if is_module:
                bindings[a.asname or a.name] = candidate
                modules.add(candidate)
            else:
                out.append((a.name, node.lineno))
    for root, attrs, line in chains:
        if root not in bindings:
            continue
        path = bindings[root]
        for attr in attrs:
            if _is_private(attr):
                out.append((attr, line))
                break
            nxt = _join(path, attr)
            if nxt in modules:
                path = nxt
                continue
            out.append((attr, line))
            break
    out.sort(key=lambda t: t[1])
    return out


_JS_IMPORT = re.compile(r"""\bimport\s+(?:type\s+)?([^'";]*?)\s*from\s*['"]([^'"]+)['"]""", re.S)
_JS_REQUIRE = re.compile(
    r"""(?:\b(?:const|let|var)\s+([A-Za-z_$][\w$]*|\{[^}]*\})\s*=\s*)?\brequire\(\s*['"]([^'"]+)['"]\s*\)""", re.S)


def _is_project_module(mod, packages):
    if mod.startswith("."):
        return True
    for p in packages:
        if mod == p or mod.startswith(p + "/"):
            return True
    return False


def _named_list(block):
    names = []
    for part in block.split(","):
        part = part.strip()
        if not part:
            continue
        part = re.sub(r"^type\s+", "", part)
        names.append(re.split(r"\s+as\s+|\s*:\s*", part)[0].strip())
    return names


def _line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def js_imports(source, packages):
    """Return [(name, line)] of project names imported by JS or TS test source."""
    out = []
    for m in _JS_IMPORT.finditer(source):
        clause, mod = m.group(1).strip(), m.group(2)
        if not _is_project_module(mod, packages):
            continue
        line = _line_of(source, m.start())
        brace = re.search(r"\{([^}]*)\}", clause, re.S)
        default = re.sub(r"\{[^}]*\}", "", clause).strip().strip(",").strip()
        if default and not default.startswith("*"):
            out.append((default.split(",")[0].strip(), line))
        if brace:
            out.extend((n, line) for n in _named_list(brace.group(1)))
    for m in _JS_REQUIRE.finditer(source):
        target, mod = m.group(1), m.group(2)
        if not _is_project_module(mod, packages) or not target:
            continue
        line = _line_of(source, m.start())
        if target.startswith("{"):
            out.extend((n, line) for n in _named_list(target[1:-1]))
        else:
            out.append((target, line))
    out.sort(key=lambda t: t[1])
    return out


def find_test_files(target, lang):
    exts = set()
    if lang in ("auto", "python"):
        exts |= PY_EXT
    if lang in ("auto", "js"):
        exts |= JS_EXT
    if target.is_file():
        return [target] if target.suffix in exts else []
    files = []
    for p in sorted(target.rglob("*")):
        if p.is_file() and p.suffix in exts and not (set(p.parts) & SKIP_DIRS):
            files.append(p)
    return files


def check(prompt_text, files, packages, prompt_label="PROMPT.md"):
    """Return findings as (level, path, line, text)."""
    findings = []
    parsed = parse_interface(prompt_text)
    if parsed is None:
        return [("ERROR", prompt_label, 0, "Expected Interface section not found")]
    public, importable = parsed
    if not files:
        return [("ERROR", prompt_label, 0, "no test files found")]
    imported = set()
    for f in files:
        src = f.read_text(encoding="utf-8")
        try:
            pairs = python_imports(src, packages) if f.suffix in PY_EXT else js_imports(src, packages)
        except SyntaxError as exc:
            findings.append(("ERROR", str(f), exc.lineno or 0, "cannot parse test file: %s" % exc.msg))
            continue
        for name, line in pairs:
            imported.add(name)
            if name in public:
                continue
            if _is_private(name):
                findings.append(("WARN", str(f), line, "test imports private name %s" % name))
            else:
                findings.append(("WARN", str(f), line, "test imports %s, which is not in Expected Interface" % name))
    for name in sorted(importable - imported):
        findings.append(("WARN", prompt_label, 0, "public name %s has no test that imports it" % name))
    if not packages:
        findings.append(("WARN", prompt_label, 0, "pass --package NAME to check imports"))
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check test imports against the Expected Interface of a PROMPT.md.")
    ap.add_argument("--prompt", required=True, help="path to PROMPT.md")
    ap.add_argument("--tests", required=True, help="test directory or file")
    ap.add_argument("--package", action="append", default=[], help="project package name (repeatable)")
    ap.add_argument("--lang", choices=["auto", "python", "js"], default="auto")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    prompt = Path(args.prompt)
    tests = Path(args.tests)
    if not prompt.is_file():
        print("usage error: not a file: %s" % prompt, file=sys.stderr)
        return 2
    if not tests.exists():
        print("usage error: not found: %s" % tests, file=sys.stderr)
        return 2
    files = find_test_files(tests, args.lang)
    findings = check(prompt.read_text(encoding="utf-8"), files, args.package, str(prompt))
    for level, path, line, msg in findings:
        print("%s %s:%d: %s" % (level, path, line, msg))
    ne = sum(1 for f in findings if f[0] == "ERROR")
    print("%d errors, %d warnings" % (ne, len(findings) - ne))
    return 1 if ne else 0


if __name__ == "__main__":
    sys.exit(main())
