"""Exercise actual Make ordering and profile installed-closure call contracts."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


class WorkspaceMakeCases(unittest.TestCase):
    def test_profile_exports_match_actual_declared_installs(self) -> None:
        repository = Path(__file__).resolve().parents[4]
        products = repository / "artifacts/workspace-audit-make-fixtures"
        products.mkdir(parents=True, exist_ok=True)
        for profile in sorted((repository / "makes/packages").glob("*.mk")):
            with (
                self.subTest(profile=profile.name),
                tempfile.TemporaryDirectory(dir=products) as directory,
            ):
                root = Path(directory)
                text = profile.read_text()
                declared = re.search(
                    r"PACKAGE_INSTALL_SPEC\s*[:?]?=\s*\.\[([^]]+)\]", text
                )
                self.assertIsNotNone(declared)
                assert declared is not None
                extras = declared.group(1).split(",")
                additional = (
                    ["bijux-pollenomics-dev"]
                    if "PACKAGE_INSTALL_PYTHON_PACKAGES" in text
                    else []
                )
                selections = "\n".join(
                    line
                    for line in text.splitlines()
                    if line.startswith("WORKSPACE_AUDIT_")
                )
                interpreter = root / "owned-interpreter"
                interpreter.write_text(
                    "#!"
                    + sys.executable
                    + "\nimport pathlib,json,sys\n"
                    + "root=pathlib.Path("
                    + repr(str(root))
                    + ");args=sys.argv[1:];verified='--verify-installed' in args\n"
                    + "assert (root/'installed').is_file() == verified\n"
                    + "out=pathlib.Path(args[args.index('--output')+1]);out.parent.mkdir(parents=True,exist_ok=True);out.write_text('pip==26.2\\n')\n"
                    + "(root/('argv.json' if verified else 'preparation-argv.json')).write_text(json.dumps(args))\n"
                )
                interpreter.chmod(0o755)
                module = repository / "makes/workspace-dependency-audit.mk"
                makefile = root / "Makefile"
                makefile.write_text(
                    "MONOREPO_ROOT := "
                    + str(repository)
                    + "\nPROJECT_SLUG := "
                    + profile.stem
                    + "\nPYTHON := "
                    + str(interpreter)
                    + "\nPROJECT_ARTIFACTS_DIR := "
                    + str(root / "package-artifacts")
                    + "\nVENV_PYTHON := "
                    + str(interpreter)
                    + "\nUV := uv\n"
                    + "SECURITY_REQS := "
                    + str(root / "requirements.txt")
                    + "\n"
                    + "SECURITY_REPORT_DIR := "
                    + str(root)
                    + "\n"
                    + selections
                    + "\ninclude "
                    + str(module)
                    + "\ninstall:\n\t@touch "
                    + str(root / "installed")
                    + "\n"
                )
                result = subprocess.run(
                    ["make", "-f", str(makefile), "security-locked-inputs"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                argv = json.loads((root / "argv.json").read_text())
                self.assertEqual(
                    argv[0],
                    str(
                        repository
                        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/dependency_audit.py"
                    ),
                )
                actual_extras = [
                    argv[index + 1]
                    for index, flag in enumerate(argv)
                    if flag == "--extra"
                ]
                actual_additional = [
                    argv[index + 1]
                    for index, flag in enumerate(argv)
                    if flag == "--additional-distribution"
                ]
                self.assertEqual(actual_extras, extras)
                self.assertEqual(actual_additional, additional)
                self.assertIn("--verify-installed", argv)
                self.assertNotIn("--prune", argv)
                self.assertEqual(argv[argv.index("--distribution") + 1], profile.stem)


if __name__ == "__main__":
    unittest.main()
