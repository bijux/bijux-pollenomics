"""Own source identities and mocked Git transport for capsule boundary controls."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.retained_source import generated, objects
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import index as retained

NATIVE = "a" * 40
STORAGE = "b" * 40
ROOT_HEAD = "c" * 40
PREFIX = "data/atlas/own-chronology-capture"
RUNTIME_PATH = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
)
RUNTIME_MEMBER = "runtime/" + RUNTIME_PATH


def sha(raw: bytes) -> str:
    """Return the SHA256 identity of an owned synthetic fixture."""
    return hashlib.sha256(raw).hexdigest()


def oid(raw: bytes) -> str:
    """Return the Git blob identity of an owned synthetic body."""
    return hashlib.sha1(
        f"blob {len(raw)}\0".encode() + raw, usedforsecurity=False
    ).hexdigest()


def encoded(value: object) -> bytes:
    """Encode a deterministic synthetic JSON body."""
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write(path: Path, raw: bytes) -> None:
    """Write an owned synthetic JSON fixture beneath its parent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


@dataclass
class GitTransport:
    """Replace only external Git IO while actual custody parsing and hashing execute."""

    repository: Path
    bodies: dict[str, bytes]
    fault: str | None = None
    body_reads: int = 0

    def query(
        self,
        repository: Path,
        args: list[str],
        limit: int,
        deadline: float,
        executable: Path,
    ) -> bytes:
        """Emulate bounded Git metadata queries for synthetic bodies."""
        assert repository == self.repository
        assert executable == Path(sys.executable).resolve()
        assert limit >= 0 and deadline > 0
        if args[:2] == ["cat-file", "-t"]:
            assert args[2] == STORAGE
            return b"missing\n" if self.fault == "revision" else b"commit\n"
        if args[:2] == ["merge-base", "--is-ancestor"]:
            assert args[2:] == [STORAGE, "HEAD"]
            if self.fault == "ancestor":
                raise ValueError("own source ancestor absent")
            return b""
        assert args[:5] == ["ls-tree", "-r", "-z", STORAGE, "--"]
        rows: list[bytes] = []
        for name in args[5:]:
            if self.fault == "missing_member" and not rows:
                continue
            mode = "120000" if self.fault == "mode" else "100644"
            kind = "tree" if self.fault == "kind" else "blob"
            rows.append(f"{mode} {kind} {oid(self.bodies[name])}\t{name}\0".encode())
        if self.fault == "extra_member":
            rows.append(b"100644 blob " + b"0" * 40 + b"\textra.py\0")
        if self.fault == "duplicate_member" and rows:
            rows.append(rows[0])
        return b"".join(rows)


class GitPipe:
    """Supply exact own batch bytes through the maintained Git stream interface."""

    def __init__(self, state: GitTransport) -> None:
        """Bind the synthetic blob pipe to its owned transport state."""
        self.state = state
        self.stdin = self
        self.header = b""
        self.buffer = b""

    def write(self, request: bytes) -> int:
        """Queue the exact synthetic blob requested by the decoder."""
        revision, name = request.decode().strip().split(":", 1)
        assert revision == STORAGE
        original = self.state.bodies[name]
        body = original + b"!" if self.state.fault == "body" else original
        self.header = f"{oid(original)} blob {len(original)}".encode()
        self.buffer = body + (b"?" if self.state.fault == "terminator" else b"\n")
        self.state.body_reads += 1
        return len(request)

    def flush(self) -> None:
        """Complete the synthetic input flush without external I/O."""

    def line(self) -> bytes:
        """Return the queued synthetic Git blob header."""
        return self.header

    def exact(self, size: int) -> bytes:
        """Consume the requested bytes from the synthetic blob stream."""
        body, self.buffer = self.buffer[:size], self.buffer[size:]
        return body

    def finish(self) -> None:
        """Require the synthetic stream to be fully consumed."""
        assert not self.buffer

    def close(self) -> None:
        """Close the synthetic pipe without external resources."""


@dataclass
class Catalogue:
    """Own full-cardinality logical catalogue; browser/native semantics are not admitted."""

    repository: Path
    document: dict[str, Any]
    descriptor: dict[str, Any]
    state: GitTransport
    own_runtime: bytes
    payloads: dict[str, bytes]

    @property
    def directory(self) -> Path:
        """Return the owned synthetic packet directory."""
        return self.repository / PREFIX

    def refresh(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Pin an intentionally modified fixture authority through existing parser seams."""
        raw = encoded(self.document)
        write(self.directory / "capture.json", raw)
        self.descriptor["capture"] = {
            "name": "capture.json",
            "bytes": len(raw),
            "sha256": sha(raw),
        }
        descriptor = encoded(self.descriptor)
        write(self.directory / "source-transport.json", descriptor)
        registry = {
            "schema_version": "retained-source-index.v1",
            "capsules": {
                PREFIX: {
                    "descriptor": "source-transport.json",
                    "bytes": len(descriptor),
                    "sha256": sha(descriptor),
                }
            },
            "source_revisions": {NATIVE: STORAGE},
        }
        index = encoded(registry)
        write(self.repository / retained.INDEX_PATH, index)
        monkeypatch.setattr(retained, "INDEX_SHA256", sha(index))
        monkeypatch.setattr(retained, "INDEX_BYTES", len(index))

    def validate(self, *, indexed: bool = False) -> retained.SourceCapsule:
        """Validate the synthetic capsule through real decoder checks."""
        authority = (
            {}
            if indexed
            else {
                "descriptor_name": "source-transport.json",
                "descriptor_bytes": len(encoded(self.descriptor)),
                "descriptor_sha256": sha(encoded(self.descriptor)),
            }
        )
        return retained.validated_descriptor(
            self.repository, PREFIX, self.document["files"], **authority
        )


@pytest.fixture
def catalogue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Catalogue:
    """Create 300 tiny own payloads; 1171 programs and the runtime stay byte buffers."""
    repository = tmp_path / "repository"
    write(repository / ".git/HEAD", (ROOT_HEAD + "\n").encode())
    bodies = {
        f"packages/own/chronology_{i:04d}.py": f"# Own program {i}\n".encode()
        for i in range(1162)
    }
    bodies.update(
        {
            f"packages/own/verifier_{i:02d}.mjs": f"// Own verifier {i}\n".encode()
            for i in range(9)
        }
    )
    payloads = {
        f"source/data/own/source_{i:03d}.json": encoded({"own_source": i})
        for i in range(55)
    }
    payloads.update(
        {f"evidence/own_{i:03d}.json": encoded({"own_evidence": i}) for i in range(245)}
    )
    own_runtime = generated.serialize("0.0.0.own0000", (0, 0, 0, "own0000"))
    assert len(own_runtime) == 539
    files: list[dict[str, Any]] = [
        {
            "path": "source/" + name,
            "bytes": len(raw),
            "sha256": sha(raw),
            "kind": "captured-source-input",
        }
        for name, raw in sorted(bodies.items())
    ]
    files += [
        {
            "path": name,
            "bytes": len(raw),
            "sha256": sha(raw),
            "kind": "captured-source-input"
            if name.startswith("source/")
            else "own-evidence",
        }
        for name, raw in sorted(payloads.items())
    ]
    files.append(
        {
            "path": RUNTIME_MEMBER,
            "bytes": len(own_runtime),
            "sha256": sha(own_runtime),
            "kind": "runtime-resource",
        }
    )
    source_members = {
        name.removeprefix("source/"): name
        for name in [x["path"] for x in files]
        if name.startswith("source/")
    }
    footprint = {
        name.removeprefix("source/"): row["sha256"]
        for row in files
        if (name := row["path"]).startswith("source/")
    }
    generations = {
        f"own_generation_{i}": f"evidence/own_{i:03d}.json" for i in range(5)
    }
    document = {
        "schema_version": "atlas-sample-chronology-source-capture.v2",
        "source_candidate": NATIVE,
        "source_context": {
            "not_a_clean_git_tree": True,
            "scope": "Own fixture, not native evidence",
        },
        "scientific_admission": False,
        "sample_chronology_admission": False,
        "numerical_execution": False,
        "files": sorted(files, key=lambda row: row["path"]),
        "source_footprint": footprint,
        "source_members": source_members,
        "runtime_resources": {
            RUNTIME_PATH: {
                "member": RUNTIME_MEMBER,
                "sha256": sha(own_runtime),
                "generated_by": "vcs-versioning",
            }
        },
        "generations": generations,
        "cases": [
            {
                "case_id": f"own_case_{i}",
                "generation": list(generations.values())[i % 5],
                "receipt": f"evidence/own_{i + 5:03d}.json",
            }
            for i in range(9)
        ],
        "products": [
            {
                "owner_id": f"own_owner_{i % 12}",
                "output_path": f"atlas/own/output_{i:02d}.json",
                "source": "evidence/own_000.json",
            }
            for i in range(43)
        ],
    }
    mapping = [[name, oid(raw)] for name, raw in sorted(bodies.items())]
    descriptor = {
        "schema_version": "git-retained-source.v1",
        "capture": {},
        "historical_native_epochs": [NATIVE],
        "source_revision_correspondence": [
            {"historical_source_commit": NATIVE, "source_revision": STORAGE}
        ],
        "git_groups": [
            {
                "historical_source_commit": NATIVE,
                "source_revision": STORAGE,
                "member_count": 1171,
                "git_entries_sha256": sha(
                    json.dumps(
                        mapping, separators=(",", ":"), ensure_ascii=True
                    ).encode()
                ),
                "prefixes": {
                    "member_prefix": "source/packages/",
                    "repository_prefix": "packages/",
                },
            }
        ],
        "generated_members": [
            {
                "member": RUNTIME_MEMBER,
                "generator": {
                    "provider": generated.PROVIDER,
                    "sha256": generated.GENERATOR_SHA256,
                    "bytes": generated.GENERATOR_BYTES,
                },
                "scalars": {
                    "version": "0.0.0.own0000",
                    "version_tuple": [0, 0, 0, "own0000"],
                    "short_node": None,
                },
                "original_generator_execution_claimed": False,
                "original_version_derivation_claimed": False,
            }
        ],
        "rewritten_source_epoch_executed": False,
    }
    state = GitTransport(repository, bodies)
    monkeypatch.setattr(objects, "query", state.query)
    monkeypatch.setattr(
        objects, "git_executable", lambda: Path(sys.executable).resolve()
    )

    def pipe(root: Path, args: list[str], deadline: float, executable: Path) -> GitPipe:
        assert root == repository and args == ["cat-file", "--batch"] and deadline > 0
        assert executable == Path(sys.executable).resolve()
        return GitPipe(state)

    monkeypatch.setattr(objects, "GitPipe", pipe)
    for name, raw in payloads.items():
        write(repository / PREFIX / name, raw)
    result = Catalogue(repository, document, descriptor, state, own_runtime, payloads)
    result.refresh(monkeypatch)
    return result
