# SEAD source-key portability

The retained `sead-full-evidence-39bfff6a-ce80714e` capture produced identical
source-key reports before and after an exclusive relocation of its complete input
capsule on 17 November 2026. The two maintained CLI calls exited successfully.
This qualifies source identity, receipts, country bindings and portability for
this exact snapshot. It does not admit a dated ecological event or measure
scientific accuracy.

[summary.json](summary.json) and [tables.csv](tables.csv) are the exact accepted
outputs, without a new rendering or numerical calculation. The
[source input index](source-inputs.json) identifies the 188 required Git blobs,
their relative capsule paths, sizes and SHA-256 values. No local machine paths or
source payloads are embedded in this account.

| Reconciled population | Result | Meaning |
| --- | ---: | --- |
| captured tables | 61 | all 61 receipts complete; eight tables empty |
| table-qualified primary keys | 522,270 | zero duplicates within a table; a key is `(table, primary key)` |
| country-decision sites | 2,195 | 2,069 assigned, 103 review, 23 unassigned |
| assigned sites | 2,069 | SE 1,925; DK 59; NO 45; FI 40 |
| capsule files / logical bytes | 188 / 709,625,669 | raw 128, normalized 54, historical boundary six |

Source keys are not counts of observations, samples, dates or independent events.
A complete empty table differs from an unqueried or partial table. Country
membership here uses the pinned boundary decision, not a native country field or
a bounding-box inference. The 126 review/unassigned sites retain their source
identities outside the assigned-country population; this replay does not establish
their downstream sample or chronology coverage.

## What the closed replay checked

The original and relocated capsules retained the same 188 physical file stamps
and directory identities. The existing owner moved the capsule exclusively;
it did not reacquire it or hydrate a second copy. The maintained reader verified
the full normalized file closure even though the selected exported document was
`source_key_ledger.json`. The reports were byte-identical after relocation:

| Product | Bytes | SHA-256 |
| --- | ---: | --- |
| `summary.json` | 2,450 | `f9ce173a33dc76c39b56a8d79a61054c7b3c718d5e4d00557e0575589d72173b` |
| `tables.csv` | 12,157 | `89ee2b92ff3f1a29207e9b5a907b346b554df6439972eb47aecdc991e8437c8d` |

The calls took 59.94 and 59.59 seconds in the observed environment. Each recorded
633 source opens and 2,211,602,857 conservative reserved bytes. These are the
reader's accounting quantities, not measured physical disk I/O or a transferable
performance guarantee. The closed retained operation took 124.65 seconds; it
excludes earlier bootstrap refusals and initial Git hydration. No provider query,
SQL query or model was run by these two CLI observations.

The actual producer revision was
`011263729c1b138cc85460090fbb89cdcab4d412`. Raw and normalized input blobs come
from `5d087b5e1548c26dc4669ba08b03194a8ee672c2`; the six original boundary files
come from `4e9b4306ea450e618c370d3d5b7dcc4e0febae0f`. Retaining that boundary
snapshot is necessary to reproduce the original admission. Substituting the
later Åland-aware boundary would change the authority being checked.

The closed-output freeze SHA-256 is
`b6b9ce5378cf68aae78b7d2349b872622f5b63a6fd993c3f121f91758ef8bfa1`.
The separate closed-result review SHA-256 is
`4f2fff9ab24d31a26d5645b6f0068a644dc5e53ff067f19311c4f92d8944f576`.
That reviewer checked the finite saved products and control evidence without
reopening the native capsule. The input index records these provenance pins;
it does not replace the source admission or its validators.

## Recorded admission versus current derived evidence

`summary.json` deliberately preserves the original raw admission's
`refused` / `*_not_materialized` fields. They are historical recorded metadata,
not a fresh finding that chronology or observations are absent. The governed
normalized snapshot already contained 25,109 typed chronology claims and
177,763 source-native observations. This operation authenticated that closure;
it did not reconstruct each chronology interpretation or observation relation,
rebuild all eleven derived products, or reassess ecological-event eligibility.

In particular, a country-assigned site is not an analysis-owned date, an
observation is not a propagation event, and integrity of a stored semantic result
is not a new semantic validation. This report neither turns the historical
strings into repository-wide missing-work claims nor clears the recorded
scientific refusals. Continue to the
[SEAD source guidance](../../../../../docs/public/pollenomics-data/sources/sead.md)
for chronology, analysis-unit and publication meaning.

## Reproduce the selected source-key export

Use the maintained development CLI in an installed environment containing the
host and development packages. The interface is
`bijux_pollenomics_dev.source_completion.sead_relations`; the observed producer
revision above identifies the actual run. Its source-key workflow is unchanged
in the account's base revision `5d0ac62327d2578a3959ac938ca0820e4bda4aba`.

Prepare a fresh capsule under the repository's `artifacts/` directory using only
the indexed Git objects. This recipe needs the referenced objects already present
in the local Git object store. Missing objects refuse; it does not fetch from a
provider, check out the entire data tree or repair source claims by hand.

```python
from hashlib import sha1, sha256
import json
import os
from pathlib import Path
import subprocess

from bijux_pollenomics.core.filesystem import OwnedTreeWriter

account = Path("reports/science/source-integrity/sead/source-key-portability")
index = json.loads((account / "source-inputs.json").read_text())
capsule = Path("artifacts/sead-source-key-replay/capsule")  # must be absent
assert index["file_count"] == 188 and index["logical_bytes"] == 709625669
ids = "".join(row["git_blob_oid"] + "\n" for row in index["files"]).encode()
with subprocess.Popen(
    ["git", "cat-file", "--batch"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    env={**os.environ, "GIT_NO_LAZY_FETCH": "1", "GIT_OPTIONAL_LOCKS": "0"},
) as process:
    assert process.stdin is not None and process.stdout is not None
    process.stdin.write(ids)
    process.stdin.close()
    with OwnedTreeWriter(capsule, max_bytes=709625669, max_files=188) as writer:
        for row in index["files"]:
            header = process.stdout.readline(128).decode().rstrip("\n").split(" ")
            assert header == [row["git_blob_oid"], "blob", str(row["bytes"])]
            raw = process.stdout.read(row["bytes"])
            assert len(raw) == row["bytes"] and process.stdout.read(1) == b"\n"
            assert sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == row["git_blob_oid"]
            assert sha256(raw).hexdigest() == row["sha256"]
            writer.write_bytes(row["capsule_path"], raw)
        assert process.stdout.read(1) == b""
        writer.validate_attachment()
    assert process.wait(timeout=180) == 0
```

The manifest and the historical boundary files must remain byte-exact. Run:

```sh
python -I -B -m bijux_pollenomics_dev.source_completion.sead_relations \
  --data-root artifacts/sead-source-key-replay/capsule \
  --output artifacts/sead-source-key-replay/before
```

The output must be absent before the call. Compare both output hashes with the
table above. To repeat the portability check, exclusively move the complete
closed capsule to a fresh sibling on the same filesystem, retain its file and
directory identities, and invoke the same CLI with the relocated data root and a
fresh `after` output. Compare the two output files byte-for-byte. Do not merge
another boundary epoch, reuse a partial destination or reinterpret an admission
refusal to make the comparison pass. The native input reader and existing owned
publication remain the validators; this recipe does not introduce a second
scientific engine or qualify a different snapshot.
