"""Bind an admitted local site to exact accepted source and a bounded browser."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
from typing import Any

from ..atlas_media.process_execution import run_bounded_argv
from .contracts import (
    DATA,
    ENTRY,
    LIMIT,
    ROUTES,
    SITE,
    SITE_URL,
    download_records,
    identity,
    read_regular,
    require,
    verify_receipt,
)


def git_bytes(root: Path, *args: str) -> bytes:
    """Read Git through the existing bounded argv executor."""
    result = run_bounded_argv(
        ("git", "--no-replace-objects", "-C", str(root), *args),
        cwd=root,
        timeout_seconds=30,
        max_output_bytes=LIMIT,
    )
    require(
        not result.timed_out and result.returncode == 0,
        "bounded Git source read failed",
    )
    return result.stdout


def git(root: Path, *args: str) -> str:
    """Read one bounded source identity without invoking a shell."""
    return git_bytes(root, *args).decode().strip()


def prepare(root: Path, accepted: str, browser: Path) -> dict[str, Any]:
    """Authenticate the existing build checkpoint and selected owning download bytes."""
    require(
        len(accepted) == 40 and all(c in "0123456789abcdef" for c in accepted),
        "exact accepted commit required",
    )
    require(
        git(root, "rev-parse", "HEAD") == accepted
        and not git(root, "status", "--porcelain", "--untracked-files=no"),
        "candidate source is changed",
    )
    tree = git(root, "rev-parse", "HEAD^{tree}")
    checkpoint_raw = read_regular(
        root, "artifacts/website-security/source-identity.json"
    )
    checkpoint = json.loads(checkpoint_raw)
    require(
        checkpoint["repository_source"] == {"sha": accepted, "tree": tree}
        and checkpoint["site_url"] == SITE_URL
        and checkpoint["site_dir"] == SITE,
        "admitted site source or production destination differs",
    )
    standard = read_regular(root, ".github/standards/bijux-docs.sha").decode().strip()
    require(checkpoint["standard"]["sha"] == standard, "admitted standard pin differs")
    publication_path = "artifacts/website-security/publication.json"
    publication_raw = read_regular(root, publication_path)
    publication = json.loads(publication_raw)
    require(
        publication.get("schema") == 2
        and publication.get("repository_source_sha") == accepted
        and publication.get("standard_sha") == standard
        and publication.get("site_url") == SITE_URL
        and publication.get("site_dir") == SITE
        and publication["qualification"]["source"]["sha256"]
        == identity(checkpoint_raw)["sha256"]
        and publication["qualification"]["source"]["receipt"] == checkpoint,
        "qualified publication manifest does not bind this exact source checkpoint",
    )
    public_files = {
        row["path"]: {k: row[k] for k in ("bytes", "sha256")}
        for row in publication["files"]
    }
    require(
        len(public_files) == len(publication["files"]),
        "qualified site members are duplicated",
    )
    manifest_raw = read_regular(root, "reports/exports/site-downloads.json")
    manifest = json.loads(manifest_raw)
    rows = download_records(manifest)
    downloads = []
    site = root / SITE
    for row in rows:
        content = read_regular(root, row["path"])
        require(
            content.startswith(b"%PDF-")
            and identity(content) == {k: row[k] for k in ("bytes", "sha256")},
            "PDF owner source differs",
        )
        downloads.append(
            {
                "path": row["site_uri"],
                **identity(content),
                "page": "public/pollenomics/science/downloads/",
                "source": row["path"],
            }
        )
    for path in DATA:
        content = read_regular(root, "docs/" + path)
        downloads.append(
            {
                "path": path,
                **identity(content),
                "page": "public/pollenomics/science/sources/",
                "source": "docs/" + path,
            }
        )
    for row in downloads:
        source = row["source"]
        committed = git_bytes(root, "show", accepted + ":" + source)
        require(
            identity(committed) == {k: row[k] for k in ("bytes", "sha256")},
            "download is not the accepted Git source",
        )
        require(
            identity(read_regular(site, row["path"])) == identity(committed),
            "admitted download differs from source",
        )
    selected = [
        ENTRY + "index.html",
        *(path + "index.html" for path in ROUTES),
        *(row["path"] for row in downloads),
    ]
    selected_identity = {path: identity(read_regular(site, path)) for path in selected}
    require(
        all(
            public_files.get(path) == value for path, value in selected_identity.items()
        ),
        "reader files differ from the qualified publication",
    )
    return {
        "schema": "scientific-reading-verification.v1",
        "candidate": {"sha": accepted, "tree": tree, "standard": standard},
        "site_url": SITE_URL,
        "site_directory": str(site),
        "browser_binary": str(browser),
        "source_checkpoint": identity(checkpoint_raw),
        "publication_manifest": identity(publication_raw),
        "publication_manifest_path": str(root / publication_path),
        "download_owner": identity(manifest_raw),
        "entry": ENTRY,
        "routes": list(ROUTES),
        "downloads": downloads,
        "selected_site": selected_identity,
    }


def run(root: Path, accepted: str, browser: Path, output: Path) -> dict[str, Any]:
    """Keep failure evidence and require unchanged source/site after browser shutdown."""
    require(
        output.resolve() == output
        and output.is_relative_to(root / "artifacts")
        and not any(parent.is_symlink() for parent in (output, *output.parents))
        and not output.exists(),
        "fresh owned artifact output required",
    )
    output.mkdir(parents=True)
    summary: dict[str, Any] = {
        "status": "FAIL",
        "claim": "local nonpublishing scientific reading route",
    }
    try:
        plan = prepare(root, accepted, browser)
        plan["output_directory"] = str(output)
        plan_path = output / "plan.json"
        plan_path.write_text(json.dumps(plan, indent=2) + "\n")
        node = shutil.which("node")
        require(node, "Node.js unavailable")
        script = Path(__file__).with_name("browser.mjs")
        process = run_bounded_argv(
            (str(node), str(script), str(plan_path)),
            cwd=root,
            timeout_seconds=180,
            max_output_bytes=LIMIT,
        )
        (output / "stdout.log").write_bytes(process.stdout)
        (output / "stderr.log").write_bytes(process.stderr)
        summary["process"] = {
            "returncode": process.returncode,
            "seconds": process.duration_seconds,
            "timed_out": process.timed_out,
            "termination": process.termination,
        }
        require(
            not process.timed_out and process.returncode == 0,
            "browser process refused or exhausted its 180-second limit",
        )
        receipt = json.loads(read_regular(output, "browser.json"))
        verify_receipt(plan, receipt)
        publication = json.loads(
            read_regular(root, "artifacts/website-security/publication.json")
        )
        qualified = {
            row["path"]: {k: row[k] for k in ("bytes", "sha256")}
            for row in publication["files"]
        }
        served = receipt.get("served", [])
        require(
            bool(served)
            and all(
                qualified.get(row["path"]) == {k: row[k] for k in ("bytes", "sha256")}
                for row in served
            ),
            "served resource differs from admitted publication bytes",
        )
        require(
            prepare(root, accepted, browser)
            == {k: v for k, v in plan.items() if k != "output_directory"},
            "consumed site or source changed",
        )
        summary.update(
            status="PASS",
            candidate=plan["candidate"],
            browser=receipt["browser"],
            receipt=identity(read_regular(output, "browser.json")),
            scope="Local admitted-site reading/download behavior only; no hosted, human comprehension, scientific accuracy or publication acceptance",
        )
    except Exception as error:
        summary["error"] = str(error)
        raise
    finally:
        for profile in output.glob("browser-profile-*"):
            if profile.is_dir() and not profile.is_symlink():
                shutil.rmtree(profile)
        (output / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    """Verify accepted scientific reading through the admitted local-site owner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--accepted-commit", required=True)
    parser.add_argument("--browser", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.environ["TMPDIR"] = str(
        args.repository.resolve() / "artifacts/scientific-reading/tmp"
    )
    Path(os.environ["TMPDIR"]).mkdir(parents=True, exist_ok=True)
    run(
        args.repository.resolve(),
        args.accepted_commit,
        args.browser.resolve(),
        args.output.resolve(),
    )


if __name__ == "__main__":
    main()
