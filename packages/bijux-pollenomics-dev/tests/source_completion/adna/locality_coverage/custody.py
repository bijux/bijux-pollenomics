"""Frozen product/source custody for the single-species display-label comparison."""

from __future__ import annotations

from decimal import Decimal
from hashlib import file_digest, sha256
import os
from pathlib import Path
import stat
import subprocess
from typing import Any

from .verification import compare_payloads, decode, require, same

EXTRA_FILES = ("pyproject.toml", "packages/bijux-pollenomics/pyproject.toml")
PRODUCT_FILES = {
    "locality_json": "locality_summaries.json",
    "locality_csv": "locality_summaries.csv",
    "bundle": "normalization_bundle.json",
}


def file_pin(path: Path, base: Path | None = None) -> dict[str, Any]:
    require(path.is_file(), "consumed regular file exists")
    if base is not None:
        require(
            path.is_relative_to(base)
            and not any(p.is_symlink() for p in (path, *path.parents)),
            "ordinary repository file",
        )
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), "regular input descriptor")
        digest = file_digest(stream, "sha256").hexdigest()
        after = os.fstat(stream.fileno())
    current = path.stat()
    require(
        all(
            getattr(before, k) == getattr(after, k) == getattr(current, k)
            for k in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        ),
        "consumed file changed while hashing",
    )
    return {
        "path": str(path.relative_to(base)) if base is not None else str(path),
        "bytes": current.st_size,
        "sha256": digest,
    }


def read_pin(base: Path, pin: dict[str, Any], maximum: int) -> bytes:
    require(
        type(pin) is dict
        and set(pin) == {"path", "bytes", "sha256"}
        and type(pin["path"]) is str
        and type(pin["bytes"]) is int
        and 0 <= pin["bytes"] <= maximum,
        "closed bounded product identity",
    )
    relative = Path(pin["path"])
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "relative ordinary product locator",
    )
    path = base / relative
    same(file_pin(path, base), pin)
    result = path.read_bytes()
    require(
        len(result) == pin["bytes"] and sha256(result).hexdigest() == pin["sha256"],
        "read product bytes differ",
    )
    same(file_pin(path, base), pin)
    return result


def code_state(repository: Path) -> dict[str, Any]:
    names = (
        subprocess.check_output(
            ["git", "ls-files", "-z", "--", "packages"], cwd=repository, timeout=10
        )
        .decode()
        .split("\0")
    )
    return {
        "head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repository, text=True, timeout=10
        ).strip(),
        "index_sha256": file_pin(repository / ".git/index", repository)["sha256"],
        "python_files": {
            name: file_pin(repository / name, repository)["sha256"]
            for name in names
            if name.endswith(".py")
        },
    }


def data_inventory(repository: Path) -> list[dict[str, Any]]:
    return [
        file_pin(path, repository)
        for path in sorted((repository / "data/adna").rglob("*"))
        if path.is_file()
    ]


def discover_stash(repository: Path, configured: str) -> dict[str, Any]:
    """Reproduce discovery metadata without opening private reference contents."""
    configured = configured.strip()
    candidates = ([Path(configured)] if configured else []) + [
        repository.parent / "bijan-references/bijux-pollenomics"
    ]
    candidates = [path.absolute() for path in candidates]
    selected = next((path for path in candidates if path.is_dir()), None)
    return {
        "environment_value": configured,
        "candidates": [
            {
                "path": str(path),
                "is_dir": path.is_dir(),
                "is_symlink": path.is_symlink(),
            }
            for path in candidates
        ],
        "selected_root": str(selected) if selected else None,
        "entries": [
            {
                "path": str(path.relative_to(selected)),
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "is_symlink": path.is_symlink(),
            }
            for path in sorted(selected.rglob("*"))
        ]
        if selected
        else [],
    }


def stash_inventory(repository: Path) -> dict[str, Any]:
    return discover_stash(
        repository, os.environ.get("BIJUX_POLLENOMICS_REFERENCE_STASH_ROOT", "")
    )


def _readset(repository: Path, readset: dict[str, Any]) -> None:
    require(set(readset) == {"files", "directory_discoveries"}, "closed actual readset")
    identities = []
    for record in readset["files"]:
        require(
            set(record) == {"path", "bytes", "sha256", "storage"}
            and record["storage"] in ("repository", "external"),
            "actual consumed file identity",
        )
        pin = {key: record[key] for key in ("path", "bytes", "sha256")}
        path = Path(pin["path"])
        if record["storage"] == "repository":
            require(
                not path.is_absolute() and ".." not in path.parts,
                "readset repository locator",
            )
            same(file_pin(repository / path, repository), pin)
        else:
            require(
                path.is_absolute() and not path.is_relative_to(repository),
                "external resource locator",
            )
            same(file_pin(path), pin)
        identities.append((record["storage"], record["path"]))
    require(identities == sorted(set(identities)), "ordered unique actual readset")
    directories = readset["directory_discoveries"]
    require(
        type(directories) is list
        and directories == sorted(set(directories))
        and all(
            type(name) is str and Path(name).is_absolute() and Path(name).is_dir()
            for name in directories
        ),
        "actual directory discoveries retained",
    )


def compare(repository: Path, protocol_path: Path, products: Path) -> dict[str, Any]:
    """Authenticate frozen custody, then execute only literal JSON/CSV comparison."""
    repository = repository.resolve(strict=True)
    products = products if products.is_absolute() else repository / products
    protocol_path = (
        protocol_path if protocol_path.is_absolute() else repository / protocol_path
    )
    require(
        ".." not in products.parts
        and products.is_dir()
        and products.resolve().is_relative_to(repository / "artifacts")
        and not any(p.is_symlink() for p in (products, *products.parents)),
        "ordinary closed artifact directory",
    )
    require(
        ".." not in protocol_path.parts
        and protocol_path.is_file()
        and protocol_path.is_relative_to(repository)
        and not any(p.is_symlink() for p in (protocol_path, *protocol_path.parents)),
        "ordinary repository protocol",
    )
    state = code_state(repository)
    raw_protocol = protocol_path.read_bytes()
    protocol = decode(raw_protocol)
    require(
        protocol["schema_version"] == "adna-locality-support-protocol.v1"
        and protocol["input_guards"]["product_data_root"] == "data/adna",
        "locality support protocol",
    )
    limits = protocol["limits"]
    same(
        limits,
        {
            "producer_wall_seconds": 60,
            "producer_max_rss_bytes": 1024**3,
            "producer_max_output_bytes": 16 * 1024**2,
            "observer_wall_seconds": 60,
            "observer_max_rss_bytes": 512 * 1024**2,
            "observer_max_output_bytes": 8 * 1024**2,
        },
    )
    require(len(raw_protocol) <= 1024**2, "bounded protocol")
    result_path = products / "result.json"
    require(
        result_path.is_file()
        and not result_path.is_symlink()
        and result_path.stat().st_size <= 1024**2,
        "bounded ordinary result",
    )
    result_raw = result_path.read_bytes()
    result = decode(result_raw)
    require(
        set(result)
        == {
            "schema_version",
            "status",
            "source_commit",
            "index_sha256",
            "python_files_checked",
            "protocol_sha256",
            "source_guards_passed",
            "products",
            "baselinepins",
            "runner",
            "input_manifest",
            "readset",
            "reference_stash",
            "resources",
        }
        and result["schema_version"] == "adna-locality-support-result.v1"
        and result["status"] == "produced_awaiting_independent_verification",
        "closed producer result",
    )
    require(
        result["source_commit"] == state["head"]
        and result["index_sha256"] == state["index_sha256"]
        and type(result["python_files_checked"]) is int
        and result["python_files_checked"] == len(state["python_files"])
        and result["source_guards_passed"] is True
        and result["protocol_sha256"] == sha256(raw_protocol).hexdigest(),
        "frozen producer and observer epoch",
    )
    maximum = limits["producer_max_output_bytes"]
    snapshots = {}
    for role, filename in (
        ("input_manifest", "input-manifest.json"),
        ("readset", "readset.json"),
        ("reference_stash", "reference-stash.json"),
    ):
        require(result[role]["path"] == filename, "owned direct guard manifest")
        snapshots[role] = decode(read_pin(products, result[role], maximum))
    inputs, readset, stash = (
        snapshots[k] for k in ("input_manifest", "readset", "reference_stash")
    )
    require(
        set(inputs) == {"product_data_files", "python_files", "extra_repository_files"},
        "complete input manifest fields",
    )
    initial_data = data_inventory(repository)
    initial_extra = [file_pin(repository / name, repository) for name in EXTRA_FILES]
    same(inputs["product_data_files"], initial_data)
    same(inputs["python_files"], state["python_files"])
    same(inputs["extra_repository_files"], initial_extra)
    same(stash_inventory(repository), stash)
    _readset(repository, readset)
    runner_body = read_pin(repository, result["runner"], 1024**2)
    require(
        Path(result["runner"]["path"]).is_relative_to("artifacts"),
        "artifact-local maintained-call runner",
    )
    normalization = protocol["normalization"]
    baselinepins = {
        **normalization["baseline_products"],
        "samples": normalization["canonical_samples"],
    }
    same(result["baselinepins"], baselinepins)
    require(
        set(result["products"]) == set(PRODUCT_FILES),
        "three maintained candidate products",
    )
    baseline = {
        role: read_pin(repository, pin, maximum)
        for role, pin in normalization["baseline_products"].items()
    }
    candidate = {}
    for role, filename in PRODUCT_FILES.items():
        require(
            result["products"][role]["path"] == filename,
            "owned direct candidate product",
        )
        candidate[role] = read_pin(products, result["products"][role], maximum)
    canonical = read_pin(repository, normalization["canonical_samples"], maximum)
    facts = compare_payloads(normalization, baseline, candidate, canonical)
    names = {
        "result.json",
        *PRODUCT_FILES.values(),
        "input-manifest.json",
        "readset.json",
        "reference-stash.json",
    }
    require(
        {p.name for p in products.iterdir()} == names
        and all(p.is_file() and not p.is_symlink() for p in products.iterdir()),
        "closed seven-member result inventory",
    )
    output_bytes = sum(p.stat().st_size for p in products.iterdir())
    used = result["resources"]
    require(
        set(used) == {"elapsed_seconds", "peak_rss_bytes", "output_bytes"}
        and type(used["elapsed_seconds"]) in (Decimal, int)
        and 0 <= used["elapsed_seconds"] <= 60
        and type(used["peak_rss_bytes"]) is int
        and 0 < used["peak_rss_bytes"] <= 1024**3
        and type(used["output_bytes"]) is int
        and used["output_bytes"] == output_bytes - len(result_raw)
        and output_bytes <= maximum,
        "complete producer resource accounting",
    )
    same(data_inventory(repository), initial_data)
    same(
        [file_pin(repository / name, repository) for name in EXTRA_FILES], initial_extra
    )
    same(stash_inventory(repository), stash)
    _readset(repository, readset)
    same(code_state(repository), state)
    require(
        protocol_path.read_bytes() == raw_protocol
        and result_path.read_bytes() == result_raw
        and read_pin(repository, result["runner"], 1024**2) == runner_body,
        "protocol/result/runner changed",
    )
    for role, pin in result["products"].items():
        require(
            read_pin(products, pin, maximum) == candidate[role],
            "closed candidate changed",
        )
    for role in ("input_manifest", "readset", "reference_stash"):
        read_pin(products, result[role], maximum)
    return {
        "schema_version": "adna-locality-support-verification.v1",
        **facts,
        "source_commit": state["head"],
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "source_guards_passed": True,
        "product_data_files_checked": len(initial_data),
        "actual_read_files_checked": len(readset["files"]),
        "directory_discoveries_recorded": len(readset["directory_discoveries"]),
        "reference_stash_entries_checked": len(stash["entries"]),
        "runner_authenticated": True,
        "protocol_sha256": sha256(raw_protocol).hexdigest(),
        "producer_result_sha256": sha256(result_raw).hexdigest(),
        "producer_output_bytes": output_bytes,
    }
