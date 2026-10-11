"""Build source-locked scientific PDF briefings from the repository root."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "presentation"
LOCK = HERE / "source-lock.json"
DECKS = ("big-picture", "developer", "scientific-evidence")


def main() -> int:
    if len(sys.argv) != 1:
        print("usage: python presentation/build.py", file=sys.stderr)
        return 2
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if lock["decks"] != list(DECKS):
        print("Deck identity differs from source lock", file=sys.stderr)
        return 1
    for relative, expected in lock["sources"].items():
        path = ROOT / relative
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            print(
                f"Review changed presentation source before rebuilding: {relative}",
                file=sys.stderr,
            )
            return 1
    latexmk = shutil.which("latexmk")
    if latexmk is None:
        print("latexmk is required to build the PDFs", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = str(lock["source_date_epoch"])
    for name in DECKS:
        output = ROOT / "artifacts" / "jobs" / "presentation" / name
        output.mkdir(parents=True, exist_ok=True)
        with subprocess.Popen(
            [
                latexmk,
                "-pdf",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-file-line-error",
                f"-outdir={output}",
                str(HERE / f"{name}.tex"),
            ],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        ) as process:
            try:
                transcript, _ = process.communicate(timeout=180)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                transcript, _ = process.communicate()
                (output / "build.log").write_text(
                    transcript + "\nBuild refused: compiler exceeded 180 seconds.\n",
                    encoding="utf-8",
                )
                print(
                    f"{name}: compiler timeout; inspect {output / 'build.log'}",
                    file=sys.stderr,
                )
                return 124
        (output / "build.log").write_text(transcript, encoding="utf-8")
        if process.returncode:
            print(f"{name}: LaTeX failed; see {output / 'build.log'}", file=sys.stderr)
            return process.returncode
        pdf = output / f"{name}.pdf"
        if not pdf.is_file() or pdf.stat().st_size < 1000:
            print(f"{name}: PDF missing or empty", file=sys.stderr)
            return 1
        shutil.copyfile(pdf, HERE / pdf.name)
        print(f"{name}: {pdf.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
