"""Exercise typed refusal, confinement and controller membership without source production."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contracts as c
from runtime import dependency_load_names, expand_dependency


def refused(function: Callable[..., Any], *args: Any) -> None:
    try:
        function(*args)
    except (ValueError, OSError):
        return
    raise AssertionError("Expected refusal")


def main() -> None:
    report = c.load(
        c.ROOT / "docs/report/source-relations/svar/normalized-export/report.json"
    )
    c.validate_scope(report)
    count = 1
    for key, value in [
        ("export_lake_count_claim", 40565.0),
        ("review_source_lake_count_claim", 40565),
        ("review_subset_feature_count", 100),
        ("current_ranked_candidate_count", False),
        ("source_population_reconciled", True),
        ("raw_wfs_capture_bound_to_export", True),
        ("qualified_review_accepted", True),
        ("ranking_admitted", True),
        ("export_generated_on", "2026-09-09"),
    ]:
        bad = deepcopy(report)
        bad[key] = value
        refused(c.validate_scope, bad)
        count += 1
    bad = deepcopy(report)
    bad["inputs"].pop()
    refused(c.validate_scope, bad)
    count += 1
    refused(c.confined_output, c.ROOT / "artifacts/../outside")
    count += 1
    with tempfile.TemporaryDirectory(dir=c.SOURCE / "preflight") as name:
        root = Path(name)
        p = root / "bad.json"
        p.write_text('{"a":1,"a":2}')
        refused(c.load, p)
        count += 1
        p.write_text('{"a":NaN}')
        refused(c.load, p)
        count += 1
        original = c.SOURCE
        c.SOURCE = root
        try:
            c.source_namespace()
            count += 1
            for kind in ["module", "fifo", "alias", "directory"]:
                p = root / ("undeclared.py" if kind == "module" else "undeclared")
                if kind == "module":
                    p.write_text("")
                elif kind == "fifo":
                    os.mkfifo(p)
                elif kind == "alias":
                    p.symlink_to(root / "bad.json")
                else:
                    p.mkdir()
                refused(c.source_namespace)
                count += 1
                if kind == "directory":
                    p.rmdir()
                else:
                    p.unlink()
        finally:
            c.SOURCE = original
        link = root / "alias"
        link.symlink_to(c.ROOT / "artifacts", target_is_directory=True)
        refused(c.confined_output, link / "future")
        count += 1
    with tempfile.TemporaryDirectory(dir=c.SOURCE / "preflight") as name:
        root = Path(name)
        input_file = root / "declared-input"
        input_file.write_bytes(b"reviewed")
        frozen = c.frozen_pin_union([c.pin(input_file), c.pin(input_file)])
        assert len(frozen) == 1
        count += 1
        bad = dict(frozen[0])
        bad["sha256"] = "0" * 64
        refused(c.frozen_pin_union, [frozen[0], bad])
        count += 1
        # Simulate an input changing while the preparer inspects native closure.
        input_file.write_bytes(b"changed-during-census")
        refused(c.verify_frozen_pins, frozen)
        assert frozen[0]["bytes"] == len(b"reviewed")
        count += 1
        output = root / "products"
        output.mkdir()
        (output / "subdirectory").mkdir()
        (output / "regular.json").write_text("{}")
        assert len(c.output_products(output)) == 1
        extra = output / "special"
        os.mkfifo(extra)
        try:
            refused(c.output_products, output)
        finally:
            extra.unlink()
        count += 1
        extra.symlink_to(output / "regular.json")
        try:
            refused(c.output_products, output)
        finally:
            extra.unlink()
        count += 1
    assert expand_dependency(
        "/opt/homebrew/opt/openssl@3/lib/crypto", Path("/lib/foo"), c.BASE
    ) == Path("/opt/homebrew/opt/openssl@3/lib/crypto")
    count += 1
    refused(expand_dependency, "@unsupported/x", Path("/lib/foo"), c.BASE)
    count += 1
    refused(dependency_load_names, "not an image", Path("/image"))
    count += 1
    print(
        json.dumps(
            {
                "source_only_actual_exit": 0,
                "meaningful_guard_groups": count,
                "source_or_preparer_or_native_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
