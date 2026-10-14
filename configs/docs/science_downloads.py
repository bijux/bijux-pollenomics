"""Expose reviewed scientific PDFs without copying them into the source tree."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import runpy
import subprocess
import tomllib
from typing import Any, cast

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "reports/exports/site-downloads.json"
DECKS = ("big-picture", "developer", "scientific-evidence")
RETAINED_CONTEXT_PATH = "presentation/retained-source-context.json"
RETAINED_CONTEXT_SHA256 = (
    "14f1d06e8f1470e5810865f4ae6d56b8d7cd08e30f3b73ad07d43fdda9bd0818"
)
RETAINED_CONTEXT = {
    "schema": "retained-deck-source-context.v1",
    "source_revision": "11079034b7dc0c1a0d94d26c97c70ec59fcf27f7",
    "source_lock_sha256": "42fc24dc8c0a4f43bb754d4176f8259bb93a61133fa73ee00a9c20e27b2cad5b",
    "security_metadata": {
        "revision": "5f3fe303ef3e5cf1f4cf2b5e29da2b934844a331",
        "path": "pyproject.toml",
        "historical_sha256": "9cc54d64c3f76f62bf16e7d2552d02c390d99c82387f0617782c880ba92acecd",
        "current_sha256": "a3d3d57eceaba706062cc94626bbc9f41c4bc0894f574d29b098d9abd332af04",
        "toml_path": ["tool", "bandit", "skips"],
        "historical_value": ["B404", "B311"],
        "current_value": [],
    },
}


def _read(root: Path, relative: str) -> bytes:
    path = PurePosixPath(relative)
    if (
        not isinstance(relative, str)
        or path.is_absolute()
        or ".." in path.parts
        or not path.parts
        or path.as_posix() != relative
        or any(character in relative for character in "\\\n\r\0")
    ):
        raise ValueError(f"Unsafe scientific download path: {relative}")
    source = root / relative
    if (
        not source.is_file()
        or source.stat().st_nlink != 1
        or not source.resolve().is_relative_to(root.resolve())
        or any(
            part.is_symlink()
            for part in (source, *source.parents)
            if part.is_relative_to(root)
        )
    ):
        raise ValueError(f"Scientific download source unavailable: {relative}")
    return source.read_bytes()


def _git(root: Path, *arguments: str, request: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "--no-replace-objects", "-C", str(root), *arguments],
        input=request,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout


def _committed_inputs(root: Path, revision: str, paths: list[str]) -> dict[str, bytes]:
    """Read exact regular Git blobs; no filesystem value substitutes for history."""
    if len(revision) != 40 or any(
        character not in "0123456789abcdef" for character in revision
    ):
        raise ValueError("Retained deck history requires an exact revision")
    if not paths or len(paths) != len(set(paths)) or len(paths) > 128:
        raise ValueError("Retained deck source population is ambiguous")
    for name in paths:
        path = PurePosixPath(name)
        if (
            not path.parts
            or path.is_absolute()
            or path.as_posix() != name
            or ".." in path.parts
            or any(character in name for character in "\\\n\r\0")
        ):
            raise ValueError("Retained deck history requires canonical source paths")
    tree = _git(root, "ls-tree", "-r", "-z", revision, "--", *paths)
    owned = {}
    for record in tree.split(b"\0"):
        if not record:
            continue
        metadata, encoded_name = record.split(b"\t", 1)
        mode, kind, _ = metadata.split()
        if mode not in {b"100644", b"100755"} or kind != b"blob":
            raise ValueError("Retained deck history requires regular source blobs")
        owned[encoded_name.decode()] = mode
    if set(owned) != set(paths):
        raise ValueError("Retained deck history is missing an exact source")
    request = "".join(f"{revision}:{path}\n" for path in paths).encode()
    stream = io.BytesIO(_git(root, "cat-file", "--batch", request=request))
    result = {}
    for relative in paths:
        header = stream.readline().split()
        if len(header) != 3 or header[1] != b"blob":
            raise ValueError("Retained deck history requires complete source blobs")
        result[relative] = stream.read(int(header[2]))
        if stream.read(1) != b"\n":
            raise ValueError("Retained deck history stream is incomplete")
    if stream.read():
        raise ValueError("Retained deck history stream has unexpected records")
    return result


def _json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Scientific download JSON has duplicate source keys")
        result[key] = value
    return result


def _previous_deck_sources(root: Path) -> dict[str, object]:
    """Keep original deck context and one reviewed security metadata delta distinct."""
    context_bytes = _read(root, RETAINED_CONTEXT_PATH)
    context = json.loads(context_bytes, object_pairs_hook=_json_object)
    if hashlib.sha256(context_bytes).hexdigest() != RETAINED_CONTEXT_SHA256:
        raise ValueError(
            "Retained deck raw context differs from reviewed source authority"
        )
    if context != RETAINED_CONTEXT:
        raise ValueError("Retained deck context differs from reviewed source authority")
    security = context["security_metadata"]
    historical_revision = context["source_revision"]
    security_revision = security["revision"]
    for revision in (historical_revision, security_revision):
        _git(root, "merge-base", "--is-ancestor", revision, "HEAD")
    lock_bytes = _read(root, "presentation/source-lock.json")
    if hashlib.sha256(lock_bytes).hexdigest() != context["source_lock_sha256"]:
        raise ValueError("Retained deck original source lock changed")
    lock = json.loads(lock_bytes, object_pairs_hook=_json_object)
    if lock["decks"] != list(DECKS) or len(lock["sources"]) != 98:
        raise ValueError("Retained deck original source population changed")
    paths = sorted(lock["sources"])
    historical = _committed_inputs(
        root, historical_revision, paths + ["presentation/source-lock.json"]
    )
    if historical["presentation/source-lock.json"] != lock_bytes:
        raise ValueError("Retained deck source lock differs from original Git context")
    current_revision = _git(root, "rev-parse", "--verify", "HEAD").decode().strip()
    current_committed = _committed_inputs(root, current_revision, paths)
    current_modes = _git(root, "ls-tree", "-r", "-z", current_revision, "--", *paths)
    for record in current_modes.split(b"\0"):
        if record:
            metadata, encoded_name = record.split(b"\t", 1)
            mode = metadata.split()[0]
            physical_mode = (
                b"100755"
                if (root / encoded_name.decode()).stat().st_mode & 0o100
                else b"100644"
            )
            if physical_mode != mode:
                raise ValueError(
                    "Retained deck physical mode differs from committed source"
                )
    security_parent = (
        _git(root, "rev-parse", "--verify", security_revision + "^").decode().strip()
    )
    security_before = _committed_inputs(root, security_parent, [security["path"]])
    security_after = _committed_inputs(root, security_revision, [security["path"]])
    old = historical[security["path"]]
    new = _read(root, security["path"])
    if (
        hashlib.sha256(old).hexdigest() != security["historical_sha256"]
        or hashlib.sha256(new).hexdigest() != security["current_sha256"]
        or security_before[security["path"]] != old
        or security_after[security["path"]] != new
    ):
        raise ValueError(
            "Retained deck security metadata differs from reviewed history"
        )
    old_line = b'skips = ["B404", "B311"]'
    if old.count(old_line) != 1 or old.replace(old_line, b"skips = []", 1) != new:
        raise ValueError(
            "Retained deck compatibility requires the exact raw security delta"
        )
    old_toml, new_toml = tomllib.loads(old.decode()), tomllib.loads(new.decode())
    if (
        old_toml["tool"]["bandit"]["skips"] != security["historical_value"]
        or new_toml["tool"]["bandit"]["skips"] != security["current_value"]
    ):
        raise ValueError(
            "Retained deck compatibility requires the reviewed Bandit values"
        )
    old_toml["tool"]["bandit"]["skips"] = security["current_value"]
    if old_toml != new_toml:
        raise ValueError("Retained deck compatibility changed another TOML field")
    historical_inputs, current_inputs = [], []
    for relative in paths:
        original = historical[relative]
        current = _read(root, relative)
        if hashlib.sha256(original).hexdigest() != lock["sources"][relative]:
            raise ValueError(f"Retained deck historical source changed: {relative}")
        if current != current_committed[relative]:
            raise ValueError(
                f"Retained deck source differs from committed input: {relative}"
            )
        if relative != security["path"] and current != original:
            raise ValueError(
                f"Retained deck source changed outside security metadata: {relative}"
            )
        historical_inputs.append(
            {"path": relative, "sha256": hashlib.sha256(original).hexdigest()}
        )
        current_inputs.append(
            {"path": relative, "sha256": hashlib.sha256(current).hexdigest()}
        )
    return {
        "context": context,
        "historical_inputs": historical_inputs,
        "current_inputs": current_inputs,
    }


CURRENT_DECK_CONTEXT_PATH = "presentation/retained-build-source-context.json"
CURRENT_DECK_CONTEXT_SCHEMA = "retained-deck-current-source-correspondence.v1"
CURRENT_DECK_BUILD = {
    "accepted_revision": "4ec5f1f614ba2e0e1c8b16f3e9b3aa1abd73c3c3",
    "source_revision": "2f526aee907574df061318ef2982af11012626e4",
    "source_lock_path": "presentation/source-lock.json",
    "source_lock_sha256": "e5f3ccf408cbea0b3961c5ca9abf2b11edeaa2710d1587b62f60d5145bdd696e",
    "source_count": 121,
    "native_terminal_sha256": "6e018822b26df4db52f844ae923fbfd5c328796d8f64e601c2a6eeeeff33d31b",
    "pdf_sha256": {
        "presentation/big-picture.pdf": "d1c924e807c77c79c98fe64ad29c1b7bac3df41f6862cbd006591655f129e739",
        "presentation/developer.pdf": "ddb85077744cf4a9cefd2223280572e0c534bb51d8d1336c1083a4495738fde6",
        "presentation/scientific-evidence.pdf": "7a9ec3066a0a577b5b4775a937ddae6df3e50cafd6049adc6a48778df7478031",
    },
    "scope": "Three retained actual native PDF builds; original121-source lock and PDF bytes remain unchanged. Current source correspondence does not rerun slides or scientific models.",
}
CURRENT_DECK_PREVIOUS_EPOCH = {
    "context_path": "presentation/retained-source-context.json",
    "context_sha256": "14f1d06e8f1470e5810865f4ae6d56b8d7cd08e30f3b73ad07d43fdda9bd0818",
    "source_revision": "11079034b7dc0c1a0d94d26c97c70ec59fcf27f7",
    "source_lock_sha256": "42fc24dc8c0a4f43bb754d4176f8259bb93a61133fa73ee00a9c20e27b2cad5b",
    "source_count": 98,
    "scope": "Original deck epoch remains historical; it is not the source lock of the later121-source PDFs.",
}
CURRENT_DECK_SOURCE_LOCK_SHA256 = (
    "e5f3ccf408cbea0b3961c5ca9abf2b11edeaa2710d1587b62f60d5145bdd696e"
)
CURRENT_DECK_ACCEPTED_REVISION = "4ec5f1f614ba2e0e1c8b16f3e9b3aa1abd73c3c3"


def _validated_current_deck_context(raw: bytes) -> dict[str, Any]:
    """Validate a finite source-owned review manifest; prose grants no admission."""
    context = json.loads(raw, object_pairs_hook=_json_object)
    if (
        not isinstance(context, dict)
        or set(context)
        != {
            "schema_version",
            "retained_build",
            "previous_deck_epoch",
            "current_source_sha256",
            "reviewed_deltas",
            "qualification",
        }
        or context["schema_version"] != CURRENT_DECK_CONTEXT_SCHEMA
        or json.dumps(context["retained_build"], sort_keys=True)
        != json.dumps(CURRENT_DECK_BUILD, sort_keys=True)
        or json.dumps(context["previous_deck_epoch"], sort_keys=True)
        != json.dumps(CURRENT_DECK_PREVIOUS_EPOCH, sort_keys=True)
        or not isinstance(context["current_source_sha256"], dict)
        or not isinstance(context["reviewed_deltas"], list)
        or not isinstance(context["qualification"], str)
        or len(context["qualification"].strip()) < 20
    ):
        raise ValueError(
            "Retained deck committed source context manifest schema differs"
        )
    current = context["current_source_sha256"]

    def source_hash(value: object) -> bool:
        return (
            isinstance(value, str)
            and len(value) == 64
            and all(c in "0123456789abcdef" for c in value)
        )

    for name, value in current.items():
        path = PurePosixPath(name)
        if (
            path.is_absolute()
            or path.as_posix() != name
            or ".." in path.parts
            or any(c in name for c in "\\\n\r\0")
            or not source_hash(value)
        ):
            raise ValueError("Retained deck source context path/hash differs")
    deltas = context["reviewed_deltas"]
    for row in deltas:
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "retained_sha256", "current_sha256", "review"}
            or not isinstance(row["path"], str)
            or row["path"] not in current
            or not source_hash(row["retained_sha256"])
            or not source_hash(row["current_sha256"])
            or row["current_sha256"] != current[row["path"]]
            or not isinstance(row["review"], str)
            or len(row["review"].strip()) < 20
        ):
            raise ValueError(
                "Retained deck source context reviewed delta schema differs"
            )
    names = [row["path"] for row in deltas]
    if names != sorted(set(names)):
        raise ValueError("Retained deck source context delta ordering differs")
    return cast(dict[str, Any], context)


def _current_deck_sources(root: Path) -> dict[str, object]:
    """Authenticate retained slide inputs and separately reviewed current bytes."""
    raw = _read(root, CURRENT_DECK_CONTEXT_PATH)
    context = _validated_current_deck_context(raw)
    previous_raw = _read(root, RETAINED_CONTEXT_PATH)
    previous_context = json.loads(previous_raw, object_pairs_hook=_json_object)
    if (
        hashlib.sha256(previous_raw).hexdigest() != RETAINED_CONTEXT_SHA256
        or previous_context != RETAINED_CONTEXT
    ):
        raise ValueError("Retained deck original context differs")
    previous_revision = previous_context["source_revision"]
    for revision in (previous_revision, CURRENT_DECK_ACCEPTED_REVISION):
        _git(root, "merge-base", "--is-ancestor", revision, "HEAD")
    previous_lock_raw = _committed_inputs(
        root, previous_revision, ["presentation/source-lock.json"]
    )["presentation/source-lock.json"]
    if (
        hashlib.sha256(previous_lock_raw).hexdigest()
        != RETAINED_CONTEXT["source_lock_sha256"]
    ):
        raise ValueError("Retained deck original source lock differs")
    previous_lock = json.loads(previous_lock_raw, object_pairs_hook=_json_object)
    if previous_lock["decks"] != list(DECKS) or len(previous_lock["sources"]) != 98:
        raise ValueError("Retained deck original source population differs")
    source_lock_raw = _read(root, "presentation/source-lock.json")
    if hashlib.sha256(source_lock_raw).hexdigest() != CURRENT_DECK_SOURCE_LOCK_SHA256:
        raise ValueError("Retained deck source lock changed")
    lock = json.loads(source_lock_raw, object_pairs_hook=_json_object)
    paths = sorted(lock["sources"])
    if lock["decks"] != list(DECKS) or len(paths) != 121:
        raise ValueError("Retained deck source population differs")
    historical = _committed_inputs(
        root, CURRENT_DECK_ACCEPTED_REVISION, paths + ["presentation/source-lock.json"]
    )
    if historical["presentation/source-lock.json"] != source_lock_raw:
        raise ValueError("Retained deck source lock differs from accepted build")
    expected_current = context["current_source_sha256"]
    if set(expected_current) != set(paths):
        raise ValueError("Retained deck reviewed current population differs")
    current_revision = _git(root, "rev-parse", "--verify", "HEAD").decode().strip()
    current_committed = _committed_inputs(
        root, current_revision, [*paths, CURRENT_DECK_CONTEXT_PATH]
    )
    if current_committed[CURRENT_DECK_CONTEXT_PATH] != raw:
        raise ValueError(
            "Retained deck source context manifest differs from current committed source"
        )
    modes = _git(
        root,
        "ls-tree",
        "-r",
        "-z",
        current_revision,
        "--",
        *paths,
        CURRENT_DECK_CONTEXT_PATH,
    )
    for record in modes.split(b"\0"):
        if record:
            metadata, encoded_name = record.split(b"\t", 1)
            physical = (
                b"100755"
                if (root / encoded_name.decode()).stat().st_mode & 0o100
                else b"100644"
            )
            if metadata.split()[0] != physical:
                raise ValueError("Retained deck physical mode differs")
    historical_inputs, current_inputs, differences = [], [], []
    for relative in paths:
        original = historical[relative]
        current = _read(root, relative)
        original_hash, current_hash = (
            hashlib.sha256(original).hexdigest(),
            hashlib.sha256(current).hexdigest(),
        )
        if original_hash != lock["sources"][relative]:
            raise ValueError("Retained deck historical source changed")
        if (
            current_hash != expected_current[relative]
            or current != current_committed[relative]
        ):
            raise ValueError(
                f"Retained deck reviewed current source changed: {relative}"
            )
        historical_inputs.append({"path": relative, "sha256": original_hash})
        current_inputs.append({"path": relative, "sha256": current_hash})
        if original != current:
            differences.append(relative)
    deltas = context["reviewed_deltas"]
    if any(
        not isinstance(row, dict)
        or set(row) != {"path", "retained_sha256", "current_sha256", "review"}
        or not isinstance(row["path"], str)
        or row["path"] not in lock["sources"]
        or row["retained_sha256"] != lock["sources"][row["path"]]
        or row["current_sha256"] != expected_current[row["path"]]
        or not isinstance(row["review"], str)
        or len(row["review"].strip()) < 20
        for row in deltas
    ) or differences != [row["path"] for row in deltas]:
        raise ValueError("Retained deck reviewed delta population differs")
    if (
        _git(root, "rev-parse", "--verify", "HEAD").decode().strip() != current_revision
        or _read(root, CURRENT_DECK_CONTEXT_PATH) != raw
    ):
        raise ValueError(
            "Retained deck committed source context changed during validation"
        )
    for relative, expected in context["retained_build"]["pdf_sha256"].items():
        if hashlib.sha256(_read(root, relative)).hexdigest() != expected:
            raise ValueError("Retained deck original PDF changed")
    return {
        "context": context,
        "historical_inputs": historical_inputs,
        "current_inputs": current_inputs,
    }


def retained_deck_sources(root: Path) -> dict[str, object]:
    """Keep the original and later retained deck epochs distinct."""
    source_lock = _read(root, "presentation/source-lock.json")
    if hashlib.sha256(source_lock).hexdigest() == CURRENT_DECK_SOURCE_LOCK_SHA256:
        return _current_deck_sources(root)
    return _previous_deck_sources(root)


def download_bytes(root: Path) -> dict[str, bytes]:
    """Validate the exact population and freeze its bytes before site rendering."""
    manifest = json.loads(_read(root, MANIFEST), object_pairs_hook=_json_object)
    if manifest.get("schema_version") != "scientific-reader-downloads.v1":
        raise ValueError("Unknown scientific download manifest")
    inventory = list(
        csv.DictReader(
            _read(root, "reports/science/paper-accounts.csv").decode().splitlines()
        )
    )
    expected = {
        f"reports/exports/papers/{row['paper_id']}.pdf": (
            f"assets/science/papers/{row['paper_id']}.pdf",
            row["canonical_report"],
        )
        for row in inventory
    }
    expected.update(
        {
            f"presentation/{name}.pdf": (
                f"assets/science/presentations/{name}.pdf",
                f"presentation/{name}.tex",
            )
            for name in DECKS
        }
    )
    rows = manifest["files"]
    if len(inventory) != 9 or len(rows) != 12 or len(expected) != 12:
        raise ValueError("Scientific download population changed")
    if {row["path"] for row in rows} != set(expected):
        raise ValueError("Scientific download membership differs")
    for relative, digest in manifest["inputs"].items():
        if hashlib.sha256(_read(root, relative)).hexdigest() != digest:
            raise ValueError(f"Scientific download input changed: {relative}")
    required_inputs = {
        "reports/science/paper-accounts.csv",
        "reports/exports/papers/manifest.json",
        "reports/exports/papers/visual-review.json",
        "presentation/source-lock.json",
    }
    if not required_inputs <= set(manifest["inputs"]):
        raise ValueError("Scientific download input closure incomplete")
    deck_lock = json.loads(
        _read(root, "presentation/source-lock.json"), object_pairs_hook=_json_object
    )
    if deck_lock["decks"] != list(DECKS):
        raise ValueError("Scientific download deck identity differs")
    retained_deck_sources(root)
    frozen = {}
    for row in rows:
        uri, source = expected[row["path"]]
        if row["site_uri"] != uri or row["canonical_source"] != source:
            raise ValueError("Scientific download route or canonical source differs")
        content = _read(root, row["path"])
        if (
            not content.startswith(b"%PDF-")
            or len(content) != row["bytes"]
            or hashlib.sha256(content).hexdigest() != row["sha256"]
            or hashlib.sha256(_read(root, source)).hexdigest() != row["source_sha256"]
        ):
            raise ValueError(f"Scientific download identity changed: {row['path']}")
        frozen[uri] = content
    return frozen


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Require canonical export verification before inserting virtual PDF files."""
    runpy.run_path(str(ROOT / "reports/exports/papers/verify.py"), run_name="__main__")
    frozen = download_bytes(ROOT)
    if set(frozen) & {file.src_uri for file in files}:
        raise ValueError("Scientific download route collides with a docs source")
    for uri, content in frozen.items():
        files.append(File.generated(config, uri, content=content))
    return files
