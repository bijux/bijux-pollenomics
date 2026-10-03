import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize(
    "corruption",
    ["inventory", "duplicate_paper", "pdf", "review", "page_coverage"],
)
def test_library_refuses_a_corrupted_source_pdf_or_review(
    corruption: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = ROOT / "reports/exports/papers/verify.py"
    spec = importlib.util.spec_from_file_location("paper_library", path)
    assert spec is not None and spec.loader is not None
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    manifest = json.loads(path.with_name("manifest.json").read_text())
    review = json.loads(path.with_name("visual-review.json").read_text())
    if corruption == "inventory":
        manifest["inventory_sha256"] = "0" * 64
    elif corruption == "duplicate_paper":
        manifest["papers"].append(copy.deepcopy(manifest["papers"][0]))
    elif corruption == "pdf":
        manifest["papers"][0]["pdf_sha256"] = "0" * 64
    elif corruption == "review":
        review["input_receipt_sha256"] = "0" * 64
    else:
        review["papers"][0]["pages"].pop()
    inputs = iter([manifest, review])
    monkeypatch.setattr(verifier, "json", SimpleNamespace(loads=lambda _: next(inputs)))
    with pytest.raises(ValueError):
        verifier.main()
