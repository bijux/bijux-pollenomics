"""Materialize guarded source entrypoints without importing or invoking their consumers."""
from pathlib import Path

A=Path(__file__).resolve().parent.parent
prefix=(A/"preflight/entry-prefix.txt").read_text()
headers={
    "prepare": '"""Prepare current publication source custody; native consumers require registration."""\nfrom __future__ import annotations\nimport argparse\nimport hashlib\nfrom pathlib import Path\nimport shutil\nimport sys\nfrom typing import Any\n\n',
    "execute_source": '"""Execute an unchanged maintained publication CLI and retain truthful exits/origins."""\nfrom __future__ import annotations\nimport argparse\nfrom collections.abc import Callable\nimport json\nfrom pathlib import Path\nimport runpy\nimport sys\nimport traceback\nfrom typing import Any\n\n',
    "observe": '"""Independently join exact raw metadata to both genuine maintained publications."""\nfrom __future__ import annotations\nimport argparse\nimport json\nfrom pathlib import Path\nimport re\nimport sys\nfrom typing import Any\n\n',
}
for name,header in headers.items():
    target=A/(name+".py"); assert not target.exists(); target.write_text(header+prefix+(A/"preflight"/(name+".body")).read_text())
print({"source_entrypoints_authored":3,"private_or_runtime_or_native_consumer_calls":0})
