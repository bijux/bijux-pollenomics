# English development design and retained-score ledger

The source is the previously opened English author-prepared pollen search: 17
author site IDs, 31 taxa, three whole-site folds and 12 historical candidates.
The candidates comprise training mean, nearest site, inverse-distance-squared
interpolation and nine CLR radial-basis fits with training-distance quantiles
0.25, 0.50 and 0.75 crossed with ridge penalties 0.001, 0.01 and 0.1.

This packet freezes a **new retained-score audit**. It declares matched taxon,
site-fold and author-bin support, metrics, the existing common-support selection
rule and a finite resource budget before its fresh audit attempts. It preserves
the original completed design and its selected candidate separately. It does
not retroactively freeze the historical fitting search or make its exposed
outer outcomes untouched test data.

Each fresh candidate/fold audit reserves a content-addressed ledger record
before consuming its retained scores. It independently checks all scored
31-taxon predictions against their original observed-count denominator and
recomputes MAE and Hellinger distance. Every original bin outcome remains in
the packet: 2,208 attempts, comprising 2,100 scored rows and 108 refusals. The
refusals comprise 90 insufficient-training-site fitted-model cases and 18
missing-training-bin baseline cases. An audit terminal describes execution of
these checks; individual refused source bins remain explicitly refused.

The admission profile explicitly means **prior-exposed development only**.
The production reviewed evaluation cohort contract continues to require its
own reviewed receipt and unopened-outcome declaration. The development binding
refuses changes to its admission class, target, source, split or support digest.
The append-only ledger preserves completed, refused, failed and unfinished
attempts and refuses replacement of an existing run.

The packet also retains 36 earlier fresh launches that failed before score
consumption: copying the interpreter into the ledger directory lost its
environment dependency roots. Their failed records remain separate. The
successor declares and checks source and dependency roots, records installed
distribution identities, and passes an actual copied-interpreter import check
before launching its audit attempts. Successful successor runs do not erase
those earlier failures.

The historical selection rule ranks candidates by common-support site-macro
MAE subject to at least 80% own scored-bin coverage, then prefers greater own
coverage and candidate ID. This audit reconciles retained exposed results; it
performs no new fit or model selection. Temporal support is the retained author
window/bin labeling; it does not authenticate historical chronology or
cross-database site aliases. No independent measured vegetation target is
present. These results support local development custody and reproducibility,
not confirmatory accuracy, ecological interpretation, interval coverage,
physical development sweeps or release certification.

The maintained producer prepares an absent declaration directory and executes
its fixed attempt plans. Use a repository environment with the locked package
dependencies installed:

```sh
python -m bijux_pollenomics_dev.lra_validation.retained_development prepare \
  --repository "$PWD" --output "$PWD/artifacts/english-score-ledger" \
  --source-candidate "$(git rev-parse HEAD)"
python -m bijux_pollenomics_dev.lra_validation.retained_development run \
  --output "$PWD/artifacts/english-score-ledger"
```

A new declaration records the actual interpreter and source paths for that
execution. It does not replace the immutable historical packet. The maintained
`development_evidence` reader verifies the packet manifest and all members,
then writes a retained account without fitting, predicting or scoring again:

```sh
python -m bijux_pollenomics_dev.lra_validation.development_evidence \
  --repository "$PWD" --output "$PWD/artifacts/english-development-evidence.json"
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Previously exposed English retained-score ledger, not new fitting or untouched confirmation.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md) (source SHA-256 `2f61fcbbf6fb36a075790199e81d834dbf8225e426aa7d92dc1ba4cbfb19f1f0`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
