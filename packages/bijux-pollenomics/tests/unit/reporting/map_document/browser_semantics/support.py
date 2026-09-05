from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def template_block(start: str, end: str) -> str:
    start_index = MAP_DOCUMENT_TEMPLATE.index(start)
    return MAP_DOCUMENT_TEMPLATE[
        start_index : MAP_DOCUMENT_TEMPLATE.index(end, start_index)
    ]


def run_node_json(source: str) -> Any:
    node = shutil.which("node")
    assert node is not None, "Node.js is required to verify browser semantics"
    result = subprocess.run(
        [node, "-e", source], check=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)


def check_javascript_syntax(source: str, path: Path) -> None:
    node = shutil.which("node")
    assert node is not None, "Node.js is required to verify browser syntax"
    path.write_text(source, encoding="utf-8")
    subprocess.run([node, "--check", str(path)], check=True, capture_output=True)


__all__ = ["check_javascript_syntax", "run_node_json", "template_block"]
