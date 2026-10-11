"""Exercise constraint publication before inherited installers and audit equality."""

from __future__ import annotations

import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class InstallConstraintCases(unittest.TestCase):
    def test_installer_and_fallback_custody_and_failure_ordering(self) -> None:
        repository = Path(__file__).resolve().parents[4]
        products = repository / "artifacts/workspace-install-constraint-fixtures"
        products.mkdir(parents=True, exist_ok=True)
        fixture_env = {
            name: value
            for name, value in os.environ.items()
            if name not in {"MAKEFLAGS", "MFLAGS", "MAKEOVERRIDES"}
        }
        module = repository / "makes/workspace-dependency-audit.mk"
        for outcome, stamped in itertools.product(
            ("valid", "export-fails", "audit-differs"), (False, True)
        ):
            with (
                self.subTest(outcome=outcome, stamped=stamped),
                tempfile.TemporaryDirectory(dir=products) as directory,
            ):
                root = Path(directory)
                source = root / "source"
                source.mkdir()
                lock = source / "uv.lock"
                lock.write_text("fixture locked inputs\n")
                stamp = root / "install.stamp"
                interpreter = root / "owned-python"
                interpreter.write_text(
                    "#!"
                    + sys.executable
                    + "\nimport pathlib,json,sys,os\n"
                    + "root=pathlib.Path("
                    + repr(str(root))
                    + ");args=sys.argv[1:]\n"
                    + "verified='--verify-installed' in args\n"
                    + "assert not verified or (root/'installed').exists()\n"
                    + "if not verified and "
                    + repr(outcome)
                    + "=='export-fails':raise SystemExit(2)\n"
                    + "out=pathlib.Path(args[args.index('--output')+1]);out.parent.mkdir(parents=True,exist_ok=True)\n"
                    + "version='26.2.1' if verified and "
                    + repr(outcome)
                    + "=='audit-differs' else '26.2'\n"
                    + "out.write_text('pip=='+version+'\\n')\n"
                    + "(root/('audit-argv.json' if verified else 'export-argv.json')).write_text(json.dumps(args))\n"
                )
                interpreter.chmod(0o755)
                installer = root / "installer.py"
                installer.write_text(
                    "import pathlib,json,os\nroot=pathlib.Path("
                    + repr(str(root))
                    + ")\n"
                    + "assert (root/'venv-ready').is_file()\n"
                    + "a=pathlib.Path(os.environ['UV_CONSTRAINT']);b=pathlib.Path(os.environ['PIP_CONSTRAINT'])\n"
                    + "assert a==b and a.is_relative_to(root);assert a.read_text()=='pip==26.2\\n'\n"
                    + "(root/'installed').write_text(json.dumps({'uv_constraint':str(a),'pip_constraint':str(b),'selected_version':'26.2'}))\n"
                    + "count=root/'installer-count';count.write_text(str(int(count.read_text())+1) if count.exists() else '1')\n"
                )
                makefile = root / "Makefile"
                makefile.write_text(
                    "MONOREPO_ROOT := "
                    + str(source)
                    + "\nPROJECT_SLUG := fixture\n"
                    + "PROJECT_ARTIFACTS_DIR := "
                    + str(root / "artifacts")
                    + "\n"
                    + "PYTHON := "
                    + str(interpreter)
                    + "\nVENV_PYTHON := "
                    + str(interpreter)
                    + "\n"
                    + "SECURITY_REQS := "
                    + str(root / "audit/requirements.txt")
                    + "\n"
                    + "SECURITY_REPORT_DIR := "
                    + str(root / "audit")
                    + "\nUV := fixture-uv\n"
                    + (
                        "PACKAGE_INSTALL_STAMP := " + str(stamp) + "\n"
                        if stamped
                        else ""
                    )
                    + "include "
                    + str(module)
                    + "\ninstall: "
                    + (str(stamp) if stamped else str(root / "venv-ready"))
                    + "\n"
                    + (
                        str(stamp) + ": " + str(root / "venv-ready") + "\n"
                        if stamped
                        else ""
                    )
                    + "\t@"
                    + sys.executable
                    + " "
                    + str(installer)
                    + "\n"
                    + ("\t@touch " + str(stamp) + "\n" if stamped else "")
                    + str(root / "venv-ready")
                    + ":\n\t@touch "
                    + str(root / "venv-ready")
                    + "\n"
                )
                result = subprocess.run(
                    ["make", "-j2", "-f", str(makefile), "security-locked-inputs"],
                    cwd=root,
                    env=fixture_env,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                self.assertEqual(
                    result.returncode, 0 if outcome == "valid" else 2, result.stderr
                )
                if outcome == "export-fails":
                    self.assertFalse((root / "installed").exists())
                    self.assertFalse((root / "audit-argv.json").exists())
                    continue
                if outcome == "valid" and stamped:
                    argv = [
                        "make",
                        "-j2",
                        "-f",
                        str(makefile),
                        "security-locked-inputs",
                    ]
                    cached = subprocess.run(
                        argv,
                        cwd=root,
                        env=fixture_env,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=10,
                    )
                    self.assertEqual(cached.returncode, 0, cached.stderr)
                    self.assertEqual((root / "installer-count").read_text(), "1")
                    # A lock newer than the accepted stamp requires the ordinary installer.
                    newer = stamp.stat().st_mtime_ns + 1_000_000_000
                    os.utime(lock, ns=(newer, newer))
                    changed = subprocess.run(
                        argv,
                        cwd=root,
                        env=fixture_env,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=10,
                    )
                    self.assertEqual(changed.returncode, 0, changed.stderr)
                    self.assertEqual((root / "installer-count").read_text(), "2")
                receipt = json.loads((root / "installed").read_text())
                self.assertEqual(receipt["uv_constraint"], receipt["pip_constraint"])
                self.assertEqual(receipt["selected_version"], "26.2")
                before = json.loads((root / "export-argv.json").read_text())
                after = json.loads((root / "audit-argv.json").read_text())
                self.assertNotIn("--verify-installed", before)
                self.assertIn("--verify-installed", after)
                self.assertEqual(
                    before[before.index("--distribution") + 1],
                    after[after.index("--distribution") + 1],
                )


if __name__ == "__main__":
    unittest.main()
