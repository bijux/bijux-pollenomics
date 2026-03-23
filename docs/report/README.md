# AADR Country Reports

This directory stores generated country-level reports derived from local AADR metadata.

Run the Sweden report from the repository root with:

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Sweden --version v62.0
```

That command writes the Sweden outputs into `docs/report/sweden/`, including a standalone interactive HTML map with zoom controls and distance-selection circles.
