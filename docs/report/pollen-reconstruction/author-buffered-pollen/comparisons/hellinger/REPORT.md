# Hellinger distance for buffered observed-pollen predictions

The retained author-prepared pollen predictions from two adjacent English grids are rescored on the identical 148/184 observed site-bin support. Hellinger distance is between zero and one and uses all 31 named taxa and exact retained observed counts. Each site has equal weight; the 36 bins without buffered same-bin training remain refusals.

| Method | Site-macro Hellinger | Difference from training mean |
| --- | ---: | ---: |
| training_mean | 0.357926 | +0.000000 |
| nearest_site | 0.362546 | +0.004620 |
| inverse_distance_squared | 0.356682 | -0.001245 |

| Grid | Sites | Scored bins | Training mean | Nearest site | Inverse distance squared |
| --- | ---: | ---: | ---: | ---: | ---: |
| 512 | 9 | 69 | 0.349775 | 0.349331 | 0.346817 |
| 562 | 8 | 79 | 0.367096 | 0.377412 | 0.367780 |

The full per-bin distances and per-site means are in scores.csv and report.json. This is a descriptive development comparison on two adjacent blocks. It does not select a method or establish Swedish LRA skill, long-distance transfer, independent vegetation accuracy or publication rights. The source denominator is the author's prepared 31-taxon count axis, not a certified full raw-core denominator.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
