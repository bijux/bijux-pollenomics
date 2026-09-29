"""Write a read-only source audit to a caller-selected new artifact file."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile

from .audit import build_source_audit, summarize_source_audit
from .evidence import digest
from .intake_custody import build_intake_custody_report
from .intakes import audit_intakes, find_hyde_candidates


def _write_new_json(path: Path, payload: dict[str, object]) -> None:
    """Publish a content-bound result only at an absent destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        try:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            os.link(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def main() -> int:
    """Write one content-addressed source audit to the requested new path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path)
    parser.add_argument("--intake-root", type=Path)
    parser.add_argument("--private-source-root", type=Path)
    parser.add_argument("--hyde-search-root", type=Path, action="append", default=[])
    args = parser.parse_args()
    result = build_source_audit(args.root)
    if args.intake_root is not None:
        result["external_intake_receipts"] = audit_intakes(args.intake_root)
    if args.private_source_root is not None:
        result["external_intake_custody"] = build_intake_custody_report(
            args.root, args.private_source_root
        )
    result["hyde_name_discovery"] = find_hyde_candidates(args.hyde_search_root)
    result["audit_sha256"] = digest(
        {key: value for key, value in result.items() if key != "audit_sha256"}
    )
    _write_new_json(args.output, result)
    if args.summary_output is not None:
        _write_new_json(args.summary_output, summarize_source_audit(result))
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "source_count",
                    "country_cell_count",
                    "accounting_checks_pass",
                    "audit_sha256",
                )
            },
            sort_keys=True,
        )
    )
    return 0 if result["accounting_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
