"""Check both complete final source admission gates on physical artificial copies."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any

SOURCE = Path(__file__).absolute().parent


def extracted(path: Path, names: set[str], context: dict[str, Any]) -> dict[str, Any]:
    tree = ast.parse(path.read_bytes())
    nodes: list[ast.stmt] = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    assert len(nodes) == len(names)
    exec(
        compile(
            ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
            str(path),
            "exec",
        ),
        context,
    )
    return context


def main() -> None:
    manifest_path = SOURCE / "prepared-source-manifest.json"
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    assert manifest["source_only"] is True
    root = SOURCE / "preflight/complete-held-copy"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir()
    copied = deepcopy(manifest)
    for row in copied["files"]:
        original = Path(row["path"])
        relative = original.relative_to(SOURCE)
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = original.read_bytes()
        assert (
            len(data) == row["bytes"]
            and hashlib.sha256(data).hexdigest() == row["sha256"]
        )
        target.write_bytes(data)
        row["path"] = str(target)

    def publish(document: dict[str, Any]) -> None:
        data = (json.dumps(document, indent=2) + "\n").encode()
        (root / "prepared-source-manifest.json").write_bytes(data)
        (root / "independent-source-review.json").write_text(
            json.dumps(
                {
                    "approved": True,
                    "source_manifest_sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        )

    publish(copied)
    context: dict[str, Any] = {
        "Path": Path,
        "hashlib": hashlib,
        "json": json,
        "Any": Any,
    }
    extracted(SOURCE / "entry.py", {"verify"}, context)
    extracted(
        SOURCE / "source_inputs.py",
        {"pin", "normalize_row", "incoming_rows", "exact_union", "verify_rows"},
        context,
    )
    context["Iterable"] = __import__("collections.abc", fromlist=["Iterable"]).Iterable
    context["verify_namespace"] = context["verify"]
    extracted(SOURCE / "source_admission.py", {"reviewed_controls"}, context)
    gates = [context["verify"], context["reviewed_controls"]]
    cases = []

    def both(label: str, expected: bool) -> None:
        for index, gate in enumerate(gates):
            try:
                gate(root)
            except (ValueError, TypeError, KeyError, OSError):
                assert not expected, label
            else:
                assert expected, label
            cases.append(label + ":gate" + str(index))

    both("complete_final_schema_positive", True)
    for name in (
        "country-authority.json",
        "saved-authority.json",
        "declared-inputs.json",
        "members.py",
    ):
        target = root / name
        content = target.read_bytes()
        target.unlink()
        altered = deepcopy(copied)
        altered["files"] = [
            row for row in altered["files"] if Path(row["path"]) != target
        ]
        publish(altered)
        both("mandatory_role_omitted_" + name, False)
        target.write_bytes(content)
        publish(copied)
    altered = deepcopy(copied)
    altered["files"][0]["path"] = Path(altered["files"][0]["path"]).name
    publish(altered)
    both("relative_member_refused", False)
    publish(copied)
    target = root / "members.py"
    content = target.read_bytes()
    target.write_bytes(content + b"\n# artificial tamper\n")
    both("helper_tamper", False)
    target.write_bytes(content)
    unknown = root / "contracts.so"
    unknown.write_bytes(b"ARTIFICIAL")
    both("native_import_shadow", False)
    unknown.unlink()
    unknown = root / "unreviewed"
    unknown.mkdir()
    both("unknown_import_directory", False)
    unknown.rmdir()
    target.unlink()
    os.mkfifo(target)
    both("FIFO_source", False)
    target.unlink()
    target.write_bytes(content)
    alias = root / "contracts_alias.py"
    alias.symlink_to(root / "contracts.py")
    both("source_alias", False)
    alias.unlink()
    altered = deepcopy(copied)
    altered["files"].append(deepcopy(altered["files"][0]))
    publish(altered)
    both("duplicate_manifest_member", False)
    publish(copied)
    both("restored_complete_schema_positive", True)
    receipt = {
        "actual_exit": 0,
        "held_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "case_count": len(cases),
        "cases": cases,
        "scope": "Actual complete final entry.verify and reviewed_controls over controlled source copies only; no real runtime, preparation or packet assembly.",
    }
    (SOURCE / "preflight/final-admission-proof.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "actual_exit": 0,
                "case_count": len(cases),
                "source_manifest_sha256": receipt["held_manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
