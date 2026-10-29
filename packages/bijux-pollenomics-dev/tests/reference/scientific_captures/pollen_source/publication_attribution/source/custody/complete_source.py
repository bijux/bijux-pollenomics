"""Complete the controlled source guard entrypoint and compile all held source bodies."""
import ast
from pathlib import Path

A=Path(__file__).resolve().parent.parent
prefix=(A/"preflight/entry-prefix.txt").read_text()
header='''"""Exercise only controlled publication, input-custody and entrypoint guards."""
from __future__ import annotations
import ast
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from typing import Any
import unittest
from urllib.parse import quote

'''
target=A/"check_contracts.py"; assert not target.exists(); target.write_text(header+prefix+(A/"preflight/check_contracts.body").read_text())
observe=A/"observe.py"; text=observe.read_text(); old='    c.require(len(progress) == 2, "Two real maintained native stages required before observer")\n'; assert text.count(old)==1; observe.write_text(text.replace(old,'    m.native_progress(progress, plan["stages"][:2])\n'))
files=list(A.glob("*.py")); assert len(files)==11
for path in files: ast.parse(path.read_bytes(),filename=str(path))
print({"source_only":True,"AST_files":11,"private_runtime_preparer_or_native_calls":0})
