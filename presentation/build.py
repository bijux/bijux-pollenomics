"""Build scientific briefings from committed TeX and preserve their Git identity."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "presentation"
MANIFEST = ROOT / "reports/exports/site-downloads.json"
DECKS = ("big-picture", "developer", "scientific-evidence")
COMPILED_INPUTS = (
    *(f"presentation/{name}.tex" for name in DECKS),
    "presentation/shared.tex",
    "presentation/build.py",
)
FLAGS = (
    "-pdf",
    "-g",
    "-recorder",
    "-interaction=nonstopmode",
    "-halt-on-error",
    "-file-line-error",
)


def _git(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", "--no-replace-objects", "-C", str(ROOT), *arguments],
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout


def _physical(path: Path) -> None:
    if (
        path.resolve(strict=True) != path
        or not path.is_file()
        or path.stat().st_nlink != 1
    ):
        raise ValueError(f"Physical regular deck input required: {path}")


def source_identity(revision: str | None = None) -> tuple[str, int]:
    """Require the actual five input blobs, independent of unrelated HEAD changes."""
    revision = revision or _git("rev-parse", "--verify", "HEAD").decode().strip()
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("Exact deck source revision required")
    _git("merge-base", "--is-ancestor", revision, "HEAD")
    for name in COMPILED_INPUTS:
        path = ROOT / name
        _physical(path)
        row = _git("ls-tree", revision, "--", name).split()
        if len(row) != 4 or row[0] not in {b"100644", b"100755"} or row[1] != b"blob":
            raise ValueError(f"Tracked regular deck input required: {name}")
        mode = b"100755" if path.stat().st_mode & 0o100 else b"100644"
        if row[0] != mode or _git("show", f"{revision}:{name}") != path.read_bytes():
            raise ValueError(
                f"Review uncommitted or changed compiled deck input: {name}"
            )
    epoch = int(_git("show", "-s", "--format=%ct", revision))
    if epoch < 0:
        raise ValueError("Nonnegative source date epoch required")
    return revision, epoch


def check_compiled_inputs(name: str, output: Path) -> None:
    """Refuse undeclared repository inputs in the compiler's existing recorder."""
    recorder = output / f"{name}.fls"
    _physical(recorder)
    if recorder.stat().st_size > 4 * 1024**2:
        raise ValueError("Deck compiler recorder exceeds four MiB")
    expected = {HERE / f"{name}.tex", HERE / "shared.tex"}
    generated = {
        output / f"{name}.{suffix}"
        for suffix in ("aux", "out", "toc", "nav", "snm", "vrb")
    }
    observed = set()
    for line in recorder.read_text(encoding="utf-8").splitlines():
        if not line.startswith("INPUT "):
            continue
        value = Path(line[6:])
        path = value if value.is_absolute() else ROOT / value
        resolved = path.resolve(strict=True)
        if path.is_relative_to(ROOT) or resolved.is_relative_to(ROOT):
            _physical(path)
            if path in expected:
                observed.add(path)
            elif path not in generated:
                raise ValueError(f"Undeclared repository deck compiler input: {path}")
    if observed != expected:
        raise ValueError("Deck compiler did not record its authored/shared TeX inputs")


def main() -> int:
    if len(sys.argv) != 1:
        print("usage: python presentation/build.py", file=sys.stderr)
        return 2
    try:
        revision, epoch = source_identity()
        _physical(MANIFEST)
        manifest_raw = MANIFEST.read_bytes()
        manifest = json.loads(manifest_raw)
        if (
            not isinstance(manifest, dict)
            or not isinstance(manifest.get("files"), list)
            or not isinstance(manifest.get("inputs"), dict)
            or any(
                not isinstance(row, dict) or not isinstance(row.get("path"), str)
                for row in manifest["files"]
            )
        ):
            raise ValueError("Existing structured download inventory required")
        paths = {f"presentation/{name}.pdf" for name in DECKS}
        rows = [row for row in manifest["files"] if row["path"] in paths]
        if (
            manifest.get("schema_version") != "scientific-reader-downloads.v1"
            or len(rows) != 3
            or {row["path"] for row in rows} != paths
        ):
            raise ValueError("Existing three-deck download inventory required")
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if shutil.which("latexmk") is None:
        print("latexmk is required to build the PDFs", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = str(epoch)
    compilers = []
    products = []
    for name in DECKS:
        output = ROOT / "artifacts" / "jobs" / "presentation" / name
        output.mkdir(parents=True, exist_ok=True)
        if output.resolve(strict=True) != output:
            print("Physical compiler output directory required", file=sys.stderr)
            return 1
        argv = [
            "latexmk",
            *FLAGS,
            f"-outdir=artifacts/jobs/presentation/{name}",
            f"presentation/{name}.tex",
        ]
        with subprocess.Popen(
            argv,
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
        if type(process.returncode) is not int or process.returncode != 0:
            print(f"{name}: LaTeX failed; see {output / 'build.log'}", file=sys.stderr)
            return process.returncode if type(process.returncode) is int else 1
        pdf = output / f"{name}.pdf"
        try:
            _physical(pdf)
            if (
                not 1000 <= pdf.stat().st_size <= 8 * 1024** 2
                or not pdf.read_bytes().startswith(b"%PDF-")
            ):
                raise ValueError(f"{name}: PDF missing, malformed or exceeds eight MiB")
            check_compiled_inputs(name, output)
        except (ValueError, OSError) as error:
            print(str(error), file=sys.stderr)
            return 1
        products.append(pdf)
        compilers.append({"deck": name, "argv": argv, "actual_exit": 0})
    try:
        if source_identity(revision) != (revision, epoch):
            raise ValueError("Compiled deck inputs changed during build")
        for name in DECKS:
            _physical(HERE / f"{name}.pdf")
        _physical(MANIFEST)
        if MANIFEST.read_bytes() != manifest_raw:
            raise ValueError("Download inventory changed during deck compilation")
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    for pdf in products:
        shutil.copyfile(pdf, HERE / pdf.name)
        print(f"{pdf.stem}: {pdf.stat().st_size} bytes")
    for row in rows:
        raw = (ROOT / row["path"]).read_bytes()
        row.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        row.pop("source_sha256", None)
    for name in (
        "presentation/source-lock.json",
        "presentation/retained-source-context.json",
        "presentation/retained-build-source-context.json",
        "presentation/current-build-export-context.json",
        "configs/docs/publication/deck_exports.py",
    ):
        manifest["inputs"].pop(name, None)
    manifest["deck_build"] = {
        "schema_version": "git-compiled-deck-inputs.v1",
        "source_revision": revision,
        "source_date_epoch": epoch,
        "inputs": list(COMPILED_INPUTS),
        "compilers": compilers,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
