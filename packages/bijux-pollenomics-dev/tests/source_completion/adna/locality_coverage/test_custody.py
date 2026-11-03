"""Independent source/epoch/readset guards over artificial closed exports."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from . import custody
from .fixtures import body, closed_fixture
from .verification import compare_payloads


def _result(products: Path) -> dict[str, Any]:
    return json.loads((products / "result.json").read_bytes())  # type: ignore[no-any-return]


def _save(products: Path, result: dict[str, Any]) -> None:
    result["resources"]["output_bytes"] = sum(
        path.stat().st_size for path in products.iterdir() if path.name != "result.json"
    )
    (products / "result.json").write_bytes(body(result))


def _manifest(
    products: Path, result: dict[str, Any], role: str, value: dict[str, Any]
) -> None:
    path = products / result[role]["path"]
    raw = body(value)
    path.write_bytes(raw)
    result[role] = {
        "path": path.name,
        "bytes": len(raw),
        "sha256": sha256(raw).hexdigest(),
    }
    _save(products, result)


def _bind(
    monkeypatch: pytest.MonkeyPatch, state: dict[str, Any], stash: dict[str, Any]
) -> None:
    monkeypatch.setattr(custody, "code_state", lambda _: deepcopy(state))
    monkeypatch.setattr(custody, "stash_inventory", lambda _: deepcopy(stash))


def test_closed_source_guard_and_external_readset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, protocol, products, state, stash = closed_fixture(tmp_path)
    _bind(monkeypatch, state, stash)
    facts = custody.compare(repository, protocol, products)
    assert facts["status"] == "passed"
    assert facts["product_data_files_checked"] == 4
    assert facts["actual_read_files_checked"] == 5
    assert facts["python_files_checked"] == 1
    assert facts["individual_supports_verified"] == 78
    assert facts["source_guards_passed"] is True


@pytest.mark.parametrize(
    "defect",
    [
        "source_bytes",
        "new_source",
        "pyproject",
        "external",
        "stash",
        "head",
        "index",
        "python_file",
        "protocol",
        "runner",
        "input_inventory",
        "input_python",
        "input_extra",
        "duplicate_read",
        "missing_directory",
        "readset_hash",
        "false_guard",
        "wrong_baseline",
        "rss",
        "elapsed",
        "resource_bytes",
        "extra_product",
        "product_hash",
        "product_parent",
        "product_symlink",
    ],
)
def test_closed_guard_defects_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    repository, protocol, products, state, stash = closed_fixture(tmp_path)
    _bind(monkeypatch, state, stash)
    result = _result(products)
    if defect == "source_bytes":
        (repository / result["baselinepins"]["samples"]["path"]).write_bytes(b"altered")
    elif defect == "new_source":
        (repository / "data/adna/undeclared.txt").write_text("new scientific resource")
    elif defect == "pyproject":
        (repository / "pyproject.toml").write_text("changed environment declaration")
    elif defect == "external":
        (tmp_path / "reference.txt").write_text("mutated external resource")
    elif defect == "stash":
        stash["entries"].append(
            {"path": "new.pdf", "is_file": True, "is_dir": False, "is_symlink": False}
        )
    elif defect in ("head", "index", "python_file"):
        if defect == "head":
            state["head"] = "d" * 40
        elif defect == "index":
            state["index_sha256"] = "d" * 64
        else:
            state["python_files"]["packages/source.py"] = "d" * 64
    elif defect == "protocol":
        protocol.write_bytes(protocol.read_bytes() + b" ")
    elif defect == "runner":
        (repository / result["runner"]["path"]).write_text("changed runner")
    elif defect.startswith("input_"):
        inputs = json.loads((products / result["input_manifest"]["path"]).read_bytes())
        if defect == "input_inventory":
            inputs["product_data_files"].pop()
        elif defect == "input_python":
            inputs["python_files"] = {}
        else:
            inputs["extra_repository_files"].reverse()
        _manifest(products, result, "input_manifest", inputs)
    elif defect in ("duplicate_read", "missing_directory", "readset_hash"):
        readset = json.loads((products / result["readset"]["path"]).read_bytes())
        if defect == "duplicate_read":
            readset["files"].append(readset["files"][0])
        elif defect == "missing_directory":
            readset["directory_discoveries"] = [str(tmp_path / "absent-directory")]
        else:
            readset["files"][0]["sha256"] = "e" * 64
        _manifest(products, result, "readset", readset)
    elif defect == "false_guard":
        result["source_guards_passed"] = False
        _save(products, result)
    elif defect == "wrong_baseline":
        result["baselinepins"]["samples"]["sha256"] = "f" * 64
        _save(products, result)
    elif defect in ("rss", "elapsed", "resource_bytes"):
        if defect == "rss":
            result["resources"]["peak_rss_bytes"] = 1024**3 + 1
        elif defect == "elapsed":
            result["resources"]["elapsed_seconds"] = 61
        else:
            result["resources"]["output_bytes"] += 1
        (products / "result.json").write_bytes(body(result))
    elif defect == "extra_product":
        (products / "unowned.txt").write_text("unexpected member")
    elif defect == "product_hash":
        result["products"]["locality_json"]["sha256"] = "f" * 64
        _save(products, result)
    elif defect == "product_parent":
        result["products"]["locality_json"]["path"] = (
            "../producer/locality_summaries.json"
        )
        _save(products, result)
    else:
        path = products / "locality_summaries.json"
        real = tmp_path / "linked.json"
        path.replace(real)
        path.symlink_to(real)
    with pytest.raises(ValueError):
        custody.compare(repository, protocol, products)


def test_changed_result_after_semantic_comparison_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, protocol, products, state, stash = closed_fixture(tmp_path)
    _bind(monkeypatch, state, stash)
    original = compare_payloads

    def changing(*args: Any) -> dict[str, Any]:
        facts = original(*args)
        path = products / "result.json"
        path.write_bytes(path.read_bytes() + b" ")
        return facts

    monkeypatch.setattr(custody, "compare_payloads", changing)
    with pytest.raises(ValueError):
        custody.compare(repository, protocol, products)


def test_epoch_rechecked_after_semantic_comparison(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, protocol, products, state, stash = closed_fixture(tmp_path)
    _bind(monkeypatch, state, stash)
    original = compare_payloads

    def changing(*args: Any) -> dict[str, Any]:
        facts = original(*args)
        state["index_sha256"] = "e" * 64
        return facts

    monkeypatch.setattr(custody, "compare_payloads", changing)
    with pytest.raises(ValueError):
        custody.compare(repository, protocol, products)


def test_stash_resolution_absence_fallback_and_explicit_root(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    missing = tmp_path / "absent"
    first = custody.discover_stash(repository, "  " + str(missing) + "  ")
    assert first["selected_root"] is None and first["entries"] == []
    assert first["environment_value"] == str(missing)
    fallback = tmp_path / "bijan-references/bijux-pollenomics"
    fallback.mkdir(parents=True)
    (fallback / "nested").mkdir()
    (fallback / "nested/source.pdf").write_bytes(b"contents need not be read")
    second = custody.discover_stash(repository, str(missing))
    assert second["selected_root"] == str(fallback)
    assert second["entries"] == [
        {"path": "nested", "is_file": False, "is_dir": True, "is_symlink": False},
        {
            "path": "nested/source.pdf",
            "is_file": True,
            "is_dir": False,
            "is_symlink": False,
        },
    ]
    explicit = tmp_path / "explicit"
    explicit.mkdir()
    (explicit / "alias.pdf").symlink_to(fallback / "nested/source.pdf")
    third = custody.discover_stash(repository, str(explicit))
    assert third["selected_root"] == str(explicit)
    assert third["entries"] == [
        {"path": "alias.pdf", "is_file": True, "is_dir": False, "is_symlink": True}
    ]


def test_read_pin_rejects_escape_even_when_payload_bytes_match(tmp_path: Path) -> None:
    external = tmp_path / "outside"
    external.write_bytes(b"same bytes")
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(ValueError):
        custody.read_pin(
            base,
            {
                "path": "../outside",
                "bytes": 10,
                "sha256": sha256(b"same bytes").hexdigest(),
            },
            100,
        )


def _runtime_probe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    from types import SimpleNamespace

    prefix = tmp_path / "runtime"
    (prefix / "lib").mkdir(parents=True)
    monkeypatch.setattr(
        custody,
        "sys",
        SimpleNamespace(
            base_prefix=str(prefix), version_info=SimpleNamespace(major=3, minor=11)
        ),
    )
    return prefix / "lib/python311.zip"


def test_absent_runtime_probe_retains_complete_original_attempt_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, protocol, products, state, stash = closed_fixture(tmp_path)
    _bind(monkeypatch, state, stash)
    probe = _runtime_probe(tmp_path, monkeypatch)
    result = _result(products)
    readset = json.loads((products / result["readset"]["path"]).read_bytes())
    readset["directory_discoveries"] = sorted(
        [*readset["directory_discoveries"], str(probe)]
    )
    _manifest(products, result, "readset", readset)
    original = (products / "readset.json").read_bytes()
    facts = custody.compare(repository, protocol, products)
    assert facts["directory_discoveries_recorded"] == 2
    assert (products / "readset.json").read_bytes() == original
    assert not probe.exists() and not probe.is_symlink()


@pytest.mark.parametrize(
    "defect",
    [
        "unknown_missing",
        "wrong_version",
        "dangling_symlink",
        "resolved_dangling_target",
        "regular_file",
        "probe_appears_after_comparison",
    ],
)
def test_no_other_negative_directory_attempt_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    repository, protocol, products, state, stash = closed_fixture(tmp_path)
    _bind(monkeypatch, state, stash)
    probe = _runtime_probe(tmp_path, monkeypatch)
    declared = probe
    if defect == "unknown_missing":
        declared = tmp_path / "absent_scientific_directory"
    elif defect == "wrong_version":
        declared = probe.with_name("python312.zip")
    elif defect in ("dangling_symlink", "resolved_dangling_target"):
        probe.symlink_to(tmp_path / "absent_zip_target")
        if defect == "resolved_dangling_target":
            declared = probe.resolve()
    elif defect == "regular_file":
        probe.write_bytes(b"not a directory and not absent")
    else:
        original = compare_payloads

        def appearing(*args: Any) -> dict[str, Any]:
            facts = original(*args)
            probe.write_bytes(b"runtime discovery changed during observation")
            return facts

        monkeypatch.setattr(custody, "compare_payloads", appearing)
    result = _result(products)
    readset = json.loads((products / result["readset"]["path"]).read_bytes())
    readset["directory_discoveries"] = sorted(
        [*readset["directory_discoveries"], str(declared)]
    )
    _manifest(products, result, "readset", readset)
    with pytest.raises(ValueError):
        custody.compare(repository, protocol, products)
