# Published southern Swedish vegetation comparison

[Gaillard et al. (2010), Figure 6](https://cp.copernicus.org/articles/6/483/2010/) reproduces the southern Swedish REVEALS validation by Hellman et al. (2008). It prints rounded whole-percent values for pollen, REVEALS and independently compiled observed vegetation in Skåne and Småland. The figure shows 26 taxa, but names values only when they reach at least 2% in a panel. The [transcription](printed-labels.csv) keeps the **nine region/taxon pairs named in all three panels**; it does not fill unlabeled values with zeros.

| Published regional subset | Matched named taxa | Pollen mean absolute error | REVEALS mean absolute error |
| --- | ---: | ---: | ---: |
| Skåne | 5 | 14.8 percentage points | 4.2 percentage points |
| Småland | 4 | 20.5 percentage points | 6.25 percentage points |
| Pooled named subset | 9 | 17.33 percentage points | 5.11 percentage points |

The paired [calculation](report.json) uses the printed integer labels only. It shows that published REVEALS values lie closer to the figure's observed vegetation than raw pollen percentages **on this selected set**, with Skåne Poaceae an individual exception. The result cannot estimate 26-taxon skill, uncertainty, or the performance of any predictor in this repository. The two regions are not nine independent validation landscapes, and selection by printed labels favors abundant taxa. The underlying ten-lake source counts, measured vegetation compilation, exact unrounded percentages and original REVEALS run identities remain necessary to reproduce the full study or admit an independent matched validation cohort here.

The CC BY 3.0 article PDF is held in the private source store and pinned by SHA-256 in `report.json`. Values in the CSV were transcribed from page 490 of that PDF; the producer verifies the PDF bytes and calculates scores from the declared transcription. To replay from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/vegetation-reference/southern-sweden-figure/compare.py \
  --source-pdf /path/to/private/reference-sources/southern-sweden-vegetation-validation/gaillard-2010.pdf \
  --output artifacts/jobs/southern-sweden-published-figure/replayed
```
