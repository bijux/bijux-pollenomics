# Recovered SMHI SVAR normalized export

The [custody receipt](report.json) identifies a 261,041,034-byte normalized
Sweden lake GeoJSON export preserved in the private source store under
`svar/normalized-export-2026-09-08/`. The export SHA-256 is
`d9a1943d1a35e7ab6d48e06156fef625e7c62c8bc410cecf9d8f592ccb07dfd8`.
Its associated manifest and summary were copied byte-for-byte with it. The
receipt SHA-256 is
`ab082b7899ce947b7bef8c0f8c58fc030aed79b54ee14edf50c81bf5e18f9baf`.
This is a preserved normalized export, not a newly acquired provider capture.
The original raw WFS pages are not retained with it.

The export manifest and summary claim **40,565 lakes** on 8 September 2026.
The current governed candidate review instead cites **40,523** source lakes
and contains 99 derived features. The current
[lake report](../../../countries/sweden/sweden_lake_evidence_richness_v66.md)
admits **zero** candidates because its governing normalized registry is absent.
The source populations differ by 42; the receipt does not identify why. Neither
the recovered export nor the 99-feature subset is promoted to the governed
registry. Qualified source, identity and publication review remains outstanding.

To replay the byte and refusal checks, supply the private source-store root and
write a disposable receipt under `artifacts/`, then compare the resulting JSON
with the governed receipt:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/svar/normalized-export/verify.py \
  --repository . --source-root /path/to/bijux-pollenomics-data \
  --output artifacts/svar-normalized-export/replay
cmp docs/report/source-relations/svar/normalized-export/report.json \
  artifacts/svar-normalized-export/replay/report.json
```

The next admissible action is to recover the source capture or a new official
registry with version and rights, reconcile its lake identities with the
candidate subset, and obtain qualified review. Until that happens, the public
[Sweden lake page](../../../../public/nordic-atlas/sweden-lake-priorities/index.md)
must show the current zero-candidate refusal rather than old rank values.
