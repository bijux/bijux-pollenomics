from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics.provenance import gates as gate_module


def _digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _json_digest(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _digest(payload)


def _gate_producer_source_files() -> list[dict[str, object]]:
    package_root = Path(gate_module.__file__).parent
    source_files: list[dict[str, object]] = []
    for path in sorted(
        package_root.rglob("*.py"),
        key=lambda item: item.relative_to(package_root).as_posix(),
    ):
        relative = path.relative_to(package_root)
        components = list(relative.parts)
        if components[-1] == "__init__.py":
            components.pop()
        else:
            components[-1] = path.stem
        payload = path.read_bytes()
        source_files.append(
            {
                "module": ".".join(("bijux_pollenomics.provenance.gates", *components)),
                "sha256": _digest(payload),
                "byte_count": len(payload),
            }
        )
    return source_files


def _input(root: Path) -> None:
    path = root / "inputs/source.txt"
    path.parent.mkdir(parents=True)
    path.write_text("immutable input\n", encoding="utf-8")
