"""Tests for scripts/check_interface_coverage.py. Run: python3 assets/tests/test_check_interface_coverage.py"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_interface_coverage as cic  # noqa: E402


def entry(name, kind="public function"):
    return ("### %s\n- Path: src/m.py\n- Name: %s\n- Type: %s\n- Input: N/A\n- Output: N/A\n"
            "- Description: Does a thing.\n" % (name, name, kind))


def prompt(*names):
    return "## Title\nT\n## Description\nD\n## Expected Interface\n" + "".join(entry(n) for n in names)


class PublicNames(unittest.TestCase):
    def test_headings_and_name_field(self):
        self.assertEqual(cic.parse_public_names(prompt("alpha", "Beta")), {"alpha", "Beta"})

    def test_dotted_first_segment(self):
        self.assertEqual(cic.parse_public_names(prompt("Store.save")), {"Store"})

    def test_no_section(self):
        self.assertIsNone(cic.parse_public_names("## Title\nT\n"))

    def test_stops_at_next_section(self):
        text = prompt("alpha") + "## Deliverables\n### other\n"
        self.assertEqual(cic.parse_public_names(text), {"alpha"})


class ImportableNames(unittest.TestCase):
    def test_endpoint_and_command_not_importable(self):
        text = ("## Title\nT\n## Description\nD\n## Expected Interface\n" + entry("alpha")
                + entry("GET_items", "endpoint") + entry("run_cli", "command"))
        public, importable = cic.parse_interface(text)
        self.assertEqual(public, {"alpha", "GET_items", "run_cli"})
        self.assertEqual(importable, {"alpha"})

    def test_missing_section(self):
        self.assertIsNone(cic.parse_interface("## Title\nT\n"))


class PythonParsing(unittest.TestCase):
    def test_from_import_with_alias(self):
        src = "import os\nfrom pkg.mod import alpha as a, _hidden\nfrom json import loads\n"
        got = cic.python_imports(src, ["pkg"])
        self.assertEqual(got, [("alpha", 2), ("_hidden", 2)])

    def test_relative_import(self):
        got = cic.python_imports("from . import alpha\nfrom ..x import beta\n", [])
        self.assertEqual(got, [("alpha", 1), ("beta", 2)])

    def test_ignored_modules(self):
        src = "import pytest\nfrom unittest import mock\nfrom unittest.mock import patch\nfrom hypothesis import given\n"
        self.assertEqual(cic.python_imports(src, []), [])

    def test_import_package_attributes(self):
        src = "import mypkg\nimport mypkg as m\nmypkg.alpha()\nm.beta\nother.gamma\n"
        got = cic.python_imports(src, ["mypkg"])
        self.assertEqual(sorted(got), [("alpha", 3), ("beta", 4)])

    def test_import_without_package_ignored(self):
        self.assertEqual(cic.python_imports("import mypkg\nmypkg.alpha()\n", []), [])

    def test_star_skipped(self):
        self.assertEqual(cic.python_imports("from pkg import *\n", []), [])

    def test_syntax_error_raises(self):
        with self.assertRaises(SyntaxError):
            cic.python_imports("def (:\n", [])

    def test_third_party_import_ignored(self):
        src = "from fastapi import FastAPI\nimport requests\nfrom requests import get\n"
        self.assertEqual(cic.python_imports(src, []), [])
        self.assertEqual(cic.python_imports(src, ["pkg"]), [])

    def test_absolute_import_needs_package(self):
        src = "from pkg.mod import alpha\n"
        self.assertEqual(cic.python_imports(src, []), [])
        self.assertEqual(cic.python_imports(src, ["pkg"]), [("alpha", 1)])

    def test_import_dotted_private_segment(self):
        self.assertEqual(cic.python_imports("import pkg.core._x\n", ["pkg"]), [("_x", 1)])

    def test_from_module_private_segment(self):
        self.assertEqual(cic.python_imports("from pkg._impl import alpha\n", ["pkg"]),
                         [("_impl", 1), ("alpha", 1)])

    def test_module_import_not_reported(self):
        self.assertEqual(cic.python_imports("import pkg.core\n", ["pkg"]), [])
        self.assertEqual(cic.python_imports("import pkg.core as c\n", ["pkg"]), [])
        src = "from pkg import core\ncore.run()\n"
        self.assertEqual(cic.python_imports(src, ["pkg"]), [("run", 2)])
        src = "import pkg.core\nfrom pkg import core\n"
        self.assertEqual(cic.python_imports(src, ["pkg"]), [])

    def test_class_attribute_use_is_still_a_name(self):
        src = "from pkg import Store\nStore.create()\n"
        self.assertEqual(cic.python_imports(src, ["pkg"]), [("Store", 1)])

    def test_attribute_chain_counts_final_name(self):
        src = "import pkg.core\npkg.core.NAME()\n"
        self.assertEqual(cic.python_imports(src, ["pkg"]), [("NAME", 2)])
        src = "import pkg.core as c\nc.NAME\n"
        self.assertEqual(cic.python_imports(src, ["pkg"]), [("NAME", 2)])

    def test_attribute_chain_private_segment(self):
        src = "import pkg.core\npkg.core._x()\n"
        self.assertEqual(cic.python_imports(src, ["pkg"]), [("_x", 2)])

    def test_dunder_segment_is_not_private(self):
        self.assertEqual(cic.python_imports("import pkg.__main__\n", ["pkg"]), [])


class JsParsing(unittest.TestCase):
    def test_named_and_default(self):
        src = "import Def, { a, b as c } from './mod';\nimport x from 'lodash';\n"
        got = cic.js_imports(src, [])
        self.assertEqual(got, [("Def", 1), ("a", 1), ("b", 1)])

    def test_multiline_import_line(self):
        src = "\nimport {\n  a,\n  b,\n} from '../src/mod'\n"
        self.assertEqual(cic.js_imports(src, []), [("a", 2), ("b", 2)])

    def test_package_import(self):
        src = "import { run } from 'mypkg/core';\nimport { z } from 'other';\n"
        self.assertEqual(cic.js_imports(src, ["mypkg"]), [("run", 1)])

    def test_require_destructure(self):
        src = "const { a, b: c } = require('./mod');\nconst d = require('./other');\nconst e = require('fs');\n"
        self.assertEqual(cic.js_imports(src, []), [("a", 1), ("b", 1), ("d", 2)])

    def test_type_import(self):
        self.assertEqual(cic.js_imports("import type { T } from './t';\n", []), [("T", 1)])

    def test_namespace_and_side_effect_skipped(self):
        src = "import * as ns from './m';\nimport './setup';\n"
        self.assertEqual(cic.js_imports(src, []), [])


class Coverage(unittest.TestCase):
    def make(self, files, prompt_text):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        root = Path(d.name)
        (root / "PROMPT.md").write_text(prompt_text, encoding="utf-8")
        (root / "tests").mkdir()
        for name, body in files.items():
            (root / "tests" / name).write_text(body, encoding="utf-8")
        return root

    def run_cli(self, root, *extra):
        return subprocess.run([sys.executable, str(SCRIPTS / "check_interface_coverage.py"),
                               "--prompt", str(root / "PROMPT.md"), "--tests", str(root / "tests")] + list(extra),
                              capture_output=True, text=True, encoding="utf-8")

    def test_clean_python(self):
        root = self.make({"test_a.py": "from src.m import alpha\n"}, prompt("alpha"))
        r = self.run_cli(root, "--package", "src")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("WARN", r.stdout)

    def test_no_package_warns(self):
        root = self.make({"test_a.py": "from src.m import alpha\n"}, prompt("alpha"))
        r = self.run_cli(root)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("pass --package NAME to check imports", r.stdout)

    def test_third_party_ignored_cli(self):
        root = self.make({"test_a.py": "from fastapi import FastAPI\nfrom src.m import alpha\n"}, prompt("alpha"))
        r = self.run_cli(root, "--package", "src")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("FastAPI", r.stdout)

    def test_relative_import_counts_cli(self):
        root = self.make({"test_a.py": "from .m import alpha, helper\n"}, prompt("alpha"))
        r = self.run_cli(root, "--package", "src")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertRegex(r.stdout, r"WARN .*test_a\.py:1: test imports helper, which is not in Expected Interface")

    def test_private_import_is_warn(self):
        root = self.make({"test_a.py": "from src.m import alpha, _helper\n"}, prompt("alpha"))
        r = self.run_cli(root, "--package", "src")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("test imports private name _helper", r.stdout)
        self.assertRegex(r.stdout, r"WARN .*test_a\.py:1: ")
        self.assertNotIn("ERROR", r.stdout)

    def test_non_public_import_is_warn(self):
        root = self.make({"test_a.py": "from src.m import alpha, helper\n"}, prompt("alpha"))
        r = self.run_cli(root, "--package", "src")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARN", r.stdout)
        self.assertIn("test imports helper, which is not in Expected Interface", r.stdout)

    def test_dunder_import_is_not_private(self):
        root = self.make({"test_a.py": "from src import __version__\n"}, prompt("alpha"))
        r = self.run_cli(root, "--package", "src")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("test imports __version__, which is not in Expected Interface", r.stdout)
        self.assertNotIn("private name", r.stdout)

    def test_private_chain_is_warn(self):
        root = self.make({"test_a.py": "import src.core\nsrc.core.alpha()\nsrc.core._x()\n"}, prompt("alpha"))
        r = self.run_cli(root, "--package", "src")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertRegex(r.stdout, r"WARN .*test_a\.py:3: test imports private name _x")

    def test_unimported_public_is_warn(self):
        root = self.make({"test_a.py": "from src.m import alpha\n"}, prompt("alpha", "beta"))
        r = self.run_cli(root, "--package", "src")
        self.assertEqual(r.returncode, 0)
        self.assertIn("WARN", r.stdout)
        self.assertIn("public name beta has no test that imports it", r.stdout)

    def test_endpoint_and_command_never_warn(self):
        text = ("## Title\nT\n## Description\nD\n## Expected Interface\n" + entry("alpha")
                + entry("GET_items", "endpoint") + entry("run_cli", "command"))
        root = self.make({"test_a.py": "from src.m import alpha\n"}, text)
        r = self.run_cli(root, "--package", "src")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("has no test", r.stdout)

    def test_missing_section(self):
        root = self.make({"test_a.py": "from src.m import alpha\n"}, "## Title\nT\n")
        r = self.run_cli(root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Expected Interface", r.stdout)

    def test_no_test_files(self):
        root = self.make({"notes.txt": "x"}, prompt("alpha"))
        r = self.run_cli(root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no test files", r.stdout)

    def test_js_private_and_lang(self):
        root = self.make({"a.test.js": "import { alpha, _h } from '../src/m';\n", "t.py": "from x import zzz\n"},
                         prompt("alpha"))
        r = self.run_cli(root, "--lang", "js")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertRegex(r.stdout, r"WARN .*private name _h")
        self.assertNotIn("zzz", r.stdout)

    def test_ts_auto(self):
        root = self.make({"a.spec.ts": "import { alpha } from './m';\n"}, prompt("alpha"))
        self.assertEqual(self.run_cli(root).returncode, 0)

    def test_package_flag_names_count(self):
        root = self.make({"test_a.py": "import mypkg\nmypkg.alpha()\nmypkg.nope()\n"}, prompt("alpha"))
        r = self.run_cli(root, "--package", "mypkg")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("test imports nope", r.stdout)
        self.assertNotIn("pass --package", r.stdout)

    def test_dotted_public(self):
        root = self.make({"test_a.py": "from src.m import Store\n"}, prompt("Store.save"))
        self.assertEqual(self.run_cli(root, "--package", "src").returncode, 0)

    def test_single_file_target(self):
        root = self.make({"test_a.py": "from src.m import alpha\n"}, prompt("alpha"))
        r = subprocess.run([sys.executable, str(SCRIPTS / "check_interface_coverage.py"), "--prompt",
                            str(root / "PROMPT.md"), "--tests", str(root / "tests" / "test_a.py"),
                            "--package", "src"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_usage_and_help(self):
        r = subprocess.run([sys.executable, str(SCRIPTS / "check_interface_coverage.py")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        r = subprocess.run([sys.executable, str(SCRIPTS / "check_interface_coverage.py"), "--help"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
