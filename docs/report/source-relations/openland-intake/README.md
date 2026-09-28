# OpenLand member intake decision

The existing private `LandCover_OpenLand.zip` has SHA-256 `7ed602f3b480a995cd2e1ff6dc445e994442100b1f626a953185849305e2434b`. The [member ledger](members.csv) records its 51 ZIP directory entries and one role, rights posture, source route, and decision for each. The [report](report.json) binds the archive identity, this consumer's source, the existing OpenLand authority, the local LandClim receipt, and the [pinned upstream tree metadata](upstream-tree.json). No archive member was copied into this report.

The primary upstream source is [Behnaz Pirzamanbein's pinned repository](https://github.com/BehnazP/SpatioCompo_entireHolocene_EU/tree/894d44d58f66bb5c273491d98c3ec23a35e6a796), associated with [Githumbi et al. (2022)](https://doi.org/10.3389/fevo.2022.795794). The [source README](https://github.com/BehnazP/SpatioCompo_entireHolocene_EU/blob/894d44d58f66bb5c273491d98c3ec23a35e6a796/README.md) identifies the 25 CSV slices, their coniferous, broadleaved, and unforested/open modeled columns, attribution requirement, and CC BY-SA 4.0 data terms. The upstream [LICENSE](https://github.com/BehnazP/SpatioCompo_entireHolocene_EU/blob/894d44d58f66bb5c273491d98c3ec23a35e6a796/LICENSE) states GPL 3.0 for upstream code. The source archive's own local R script is not an upstream Git member; its rights are unresolved.

All 25 modeled CSV members and the PDF are byte identical to pinned upstream Git blobs. The CSVs route to the existing OpenLand source authority for **private modeled-source review only**. The PDF is a reference with unresolved member-specific rights. The archive also contains one local interpolated GeoPackage, one local script, one project configuration file, 14 private editor-state files, and eight directories. The GeoPackage has no pinned upstream member identity and is excluded. The ZIP directory and full archive hash were checked; the large GeoPackage and private editor-state contents were not extracted or executed.

The [primary paper](https://doi.org/10.3389/fevo.2022.795794) describes spatial statistical reconstructions based on pollen-derived REVEALS estimates and KK10 covariates. It cites PANGAEA `931856` for REVEALS inputs, while the local LandClim II authority identifies PANGAEA `937075`. [Primary DOI metadata](doi-lineage.md) now confirms that `931856` was obsoleted by `937075`; the former has restricted access and unknown licensing terms, while the successor is CC BY 4.0. This establishes dataset lineage, not exact row or input identity or transferred rights. The ledger therefore counts **zero independent vegetation benchmarks** and does not create a second LandClim authority. Raw pollen counts are absent from the admitted CSV role. Member-level public redistribution, map display, export, propagation, and scientific benchmark use remain unapproved.

Reproduce the decision with the development package environment and an explicitly supplied private archive:

```sh
python -m bijux_pollenomics_dev.source_completion.openland_intake \
  --repository . \
  --archive <private-source-store>/LandCover_OpenLand.zip \
  --upstream-tree docs/report/source-relations/openland-intake/upstream-tree.json \
  --output artifacts/jobs/openland-intake/replay-check
```

The command requires an absent output directory and the exact pinned archive SHA-256. The retained local execution is `artifacts/jobs/openland-intake/replay-final/`; its CSV and JSON are byte identical to this report. Default focused tests use only the tracked upstream metadata and synthetic member decisions. They do not require a private archive.
