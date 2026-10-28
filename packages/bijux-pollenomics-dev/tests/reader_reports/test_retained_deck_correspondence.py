"""Keep historical deck input custody separate from maintained current readers."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[4]


class _Fixture:
    def __init__(self, root: Path, scope: dict[str, Any]) -> None:
        self.scope = scope
        self.root = root
        paths = (
            ["reports/needed/README.md"]
            + [f"readers/reader-{i}.md" for i in range(56)]
            + [f"measurements/value-{i}.json" for i in range(42)]
            + [f"measurements/table-{i}.csv" for i in range(12)]
            + [f"presentation/source-{i}.tex" for i in range(4)]
            + [f"code/source-{i}.py" for i in range(3)]
            + [f"config/source-{i}.toml" for i in range(2)]
            + ["uv.lock"]
        )
        assert len(paths) == 121
        self.historical = {p: ("historical " + p).encode() for p in paths}
        self.current = dict(self.historical)
        self.current.pop("reports/needed/README.md")
        self.previous_lock = json.dumps(
            {"decks": ["a", "b", "c"], "sources": {str(i): "a" * 64 for i in range(98)}}
        ).encode()
        self.previous = {
            "source_revision": "a" * 40,
            "source_lock_sha256": self.sha(self.previous_lock),
        }
        self.previous_raw = json.dumps(self.previous).encode()
        self.lock = json.dumps(
            {
                "decks": ["a", "b", "c"],
                "sources": {p: self.sha(v) for p, v in self.historical.items()},
            }
        ).encode()
        self.pdfs = {
            f"presentation/{name}.pdf": ("%PDF-" + name).encode()
            for name in ("a", "b", "c")
        }
        self.context = {
            "current_source_sha256": {
                p: self.sha(v) for p, v in self.historical.items()
            },
            "retained_build": {
                "pdf_sha256": {p: self.sha(v) for p, v in self.pdfs.items()}
            },
        }
        self.context_raw = json.dumps(self.context).encode()
        self.witness_lock = self.lock
        self.witness = "b" * 40
        self.head = "c" * 40
        self.mode_changed = False
        self.history_missing = False
        for p, v in {
            **self.current,
            **self.pdfs,
            "presentation/retained-build-source-context.json": self.context_raw,
            "presentation/retained-source-context.json": self.previous_raw,
            "presentation/source-lock.json": self.lock,
        }.items():
            target = root / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(v)
        self.scope.update(
            RETAINED_BUILD_CONTEXT_PATH="presentation/retained-build-source-context.json",
            RETAINED_BUILD_CONTEXT_SHA256=self.sha(self.context_raw),
            RETAINED_BUILD_LOCK_SHA256=self.sha(self.lock),
            RETAINED_BUILD_WITNESS=self.witness,
            RETIRED_DECK_REGISTER="reports/needed/README.md",
            RETAINED_CONTEXT_PATH="presentation/retained-source-context.json",
            RETAINED_CONTEXT_SHA256=self.sha(self.previous_raw),
            RETAINED_CONTEXT=self.previous,
            DECKS=("a", "b", "c"),
            _committed_inputs=self.committed,
            _git=self.git,
        )

    @staticmethod
    def sha(v: bytes) -> str:
        return hashlib.sha256(v).hexdigest()

    def committed(
        self, root: Path, revision: str, paths: list[str]
    ) -> dict[str, bytes]:
        if revision == self.previous["source_revision"]:
            return {"presentation/source-lock.json": self.previous_lock}
        if revision == self.witness:
            return {
                p: self.witness_lock
                if p == "presentation/source-lock.json"
                else self.historical[p]
                for p in paths
            }
        assert revision == self.head
        return {p: self.current[p] for p in paths}

    def git(self, root: Path, *args: str) -> bytes:
        if args[0] == "merge-base":
            if self.history_missing:
                raise subprocess.CalledProcessError(1, ["git", *args])
            return b""
        if args[0] == "rev-parse":
            return self.head.encode() + b"\n"
        assert args[0] == "ls-tree"
        return b"".join(
            (
                ("100755" if self.mode_changed and i == 0 else "100644")
                + " blob "
                + ("d" * 40)
                + "\t"
                + p
                + "\0"
            ).encode()
            for i, p in enumerate(args[args.index("--") + 1 :])
        )

    def call(self) -> dict[str, Any]:
        return cast(dict[str, Any], self.scope["_retained_build_sources"](self.root))


@pytest.fixture
def deck(tmp_path: Path) -> _Fixture:
    spec = importlib.util.spec_from_file_location(
        "bijux_deck_correspondence", ROOT / "configs/docs/science_downloads.py"
    )
    assert spec is not None and spec.loader is not None
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    return _Fixture(tmp_path, vars(hook))


@pytest.mark.parametrize(
    "relative",
    [
        None,
        "readers/reader-0.md",
        "code/source-0.py",
        "config/source-0.toml",
        "uv.lock",
        "presentation/source-0.tex",
    ],
)
def test_committed_maintained_sources_are_not_historical_body_pins(
    deck: _Fixture, relative: str | None
) -> None:
    if relative is not None:
        deck.current[relative] += b"\nmaintained current source"
        (deck.root / relative).write_bytes(deck.current[relative])
    result = deck.call()
    assert len(result["historical_inputs"]) == 121
    assert len(result["current_inputs"]) == 120
    assert result["historical_only_inputs"] == ["reports/needed/README.md"]
    assert result["context"] == deck.context
    assert result["source_witness_revision"] == deck.witness


@pytest.mark.parametrize(
    "mutation",
    [
        "json",
        "csv",
        "uncommitted",
        "historical_blob",
        "revived_register",
        "mode",
        "missing_witness",
        "context",
        "lock",
        "pdf",
        "symlink",
        "hardlink",
    ],
)
def test_historical_machine_and_physical_custody_refuse_substitution(
    deck: _Fixture, mutation: str
) -> None:
    if mutation in {"json", "csv"}:
        relative = (
            "measurements/value-0.json"
            if mutation == "json"
            else "measurements/table-0.csv"
        )
        deck.current[relative] += b"changed scientific input"
        (deck.root / relative).write_bytes(deck.current[relative])
    elif mutation == "uncommitted":
        (deck.root / "readers/reader-0.md").write_bytes(b"uncommitted reader")
    elif mutation == "historical_blob":
        deck.historical["readers/reader-0.md"] = b"wrong historical blob"
    elif mutation == "revived_register":
        source = deck.root / "reports/needed/README.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b"revived current register")
    elif mutation == "mode":
        deck.mode_changed = True
    elif mutation == "missing_witness":
        deck.history_missing = True
    elif mutation in {"context", "lock", "pdf"}:
        relative = {
            "context": "presentation/retained-build-source-context.json",
            "lock": "presentation/source-lock.json",
            "pdf": "presentation/a.pdf",
        }[mutation]
        (deck.root / relative).write_bytes(b"changed immutable artifact")
    elif mutation == "symlink":
        source = deck.root / "readers/reader-0.md"
        source.unlink()
        source.symlink_to(deck.root / "readers/reader-1.md")
    else:
        (deck.root / "hardlink").hardlink_to(deck.root / "readers/reader-0.md")
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        deck.call()


@pytest.mark.parametrize(
    "mutation", ["missing", "unknown", "revision", "reviewed_machine_hash", "duplicate"]
)
def test_retained_build_context_custody_is_independent_of_current_dispatch(
    deck: _Fixture, mutation: str
) -> None:
    path = deck.root / "presentation/retained-build-source-context.json"
    if mutation == "missing":
        path.unlink()
    elif mutation == "duplicate":
        raw = deck.context_raw.replace(b"{", b'{"current_source_sha256":{},', 1)
        path.write_bytes(raw)
        # Isolate the duplicate-object contract after byte authentication.
        deck.scope["RETAINED_BUILD_CONTEXT_SHA256"] = deck.sha(raw)
    else:
        changed = json.loads(deck.context_raw)
        if mutation == "unknown":
            changed["unreviewed"] = True
        elif mutation == "revision":
            changed["retained_build"]["accepted_revision"] = "0" * 40
        else:
            changed["current_source_sha256"]["measurements/value-0.json"] = "0" * 64
        path.write_text(json.dumps(changed))
    with pytest.raises(ValueError):
        deck.call()


@pytest.mark.parametrize("mutation", ["missing", "unknown", "revision", "duplicate"])
def test_previous_deck_context_remains_immutable_history(
    deck: _Fixture, mutation: str
) -> None:
    path = deck.root / "presentation/retained-source-context.json"
    if mutation == "missing":
        path.unlink()
    elif mutation == "duplicate":
        raw = deck.previous_raw.replace(b"{", b'{"source_revision":"duplicate",', 1)
        path.write_bytes(raw)
        deck.scope["RETAINED_CONTEXT_SHA256"] = deck.sha(raw)
    else:
        changed = json.loads(deck.previous_raw)
        if mutation == "unknown":
            changed["unreviewed"] = True
        else:
            changed["source_revision"] = "0" * 40
        path.write_text(json.dumps(changed))
    with pytest.raises(ValueError):
        deck.call()


@pytest.mark.parametrize(
    "mutation", ["original_lock", "witness_lock", "machine_population"]
)
def test_original_and_build_source_locks_preserve_exact_population(
    deck: _Fixture, mutation: str
) -> None:
    if mutation == "original_lock":
        deck.previous_lock += b"changed original lock"
    elif mutation == "witness_lock":
        deck.witness_lock += b"changed witnessed lock"
    else:
        changed = json.loads(deck.lock)
        del changed["sources"]["measurements/value-0.json"]
        deck.lock = json.dumps(changed).encode()
        (deck.root / "presentation/source-lock.json").write_bytes(deck.lock)
        deck.scope["RETAINED_BUILD_LOCK_SHA256"] = deck.sha(deck.lock)
    with pytest.raises(ValueError):
        deck.call()
