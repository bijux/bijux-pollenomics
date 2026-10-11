# Original Solsø core and basin evidence

The full [Odgaard (1994) published study](https://pure.au.dk/portal/en/publications/the-holocene-vegetation-history-of-northern-west-jutland/)
was inspected as the [Aarhus University PDF](https://pure.au.dk/ws/files/39023242/Odgaard_1994_combined.pdf)
(12,519,377 bytes; SHA-256
`f6959549f955a5bf17540f41ca6c295f11f584c88e550627718fc555a9c3dadd`).
The source PDF is retained in the private external source store at
`landclim/solsoe/odgaard-1994.pdf`, not republished here. The
[source-bound comparison](report.json) has SHA-256
`8456bf919423c4b57ed202704cc43d04b891ba98069b9ad9e0765192abf533a6`.

Figure 30 and its text (printed pages 35–36; PDF pages 32–33) map a Solsø
basin reconstruction for **9000 BC** from 51 corings. They mark the 1981 and
1983 cores at local coordinates (−33 m east, 64 m north) and (−50 m east,
70 m north), about **18.03 m apart**. The local figure has no georeferenced
origin. The paper says a 1.5 m fall in water level from 41.30 to 39.80 m
above sea level would halve the reconstructed lake area and volume. At the
1981/1983 corings it reports a water level of 40.80 m and only about
40 × 30 m of open water (printed page 34; PDF page 31). These are distinct
time and water-level claims; neither supplies a universal 89 m radius for
all pollen samples.

The paper explicitly uses the **1981 core** for 9700–5260 BC and 1540 BC–AD
1981, and the **1983 core** for 5230–1750 BC (printed page 42; PDF page 39).
It explains that a 1981 hiatus near 480–470 cm requires the 1983 core to
complete the Holocene record. Its seven 1983 radiocarbon controls in Table 17
(printed page 45; PDF page 42) match **all seven** distinct Neotoma controls
exactly by laboratory identifier, depth, radiocarbon age, one-sigma error and
δ¹³C. Neotoma represents each control in two chronology views, yielding 14
rows. This is an independent primary-source match for the 1983 core lineage.

Applying the paper's calendar interval boundaries as `BC + 1950 = BP` to
Neotoma's **92 calibrated sample ages** yields a **conditional** selection of
**76** samples: 56 from the 1981 core and 20 from the 1983 core. Restricting
that selection to LandClim II's published 10–11659 BP span yields **74**.
Both differ from LandClim II's **79** reported Solsø pollen samples. The
paper's chronology is not Neotoma's calibrated chronology, and the author
sequence's actual input rows are not published in this source. The comparison
therefore narrows core selection and confirms the original seven dates, but
does not identify the 79 samples or their full 31-target denominator. The
9000 BC basin figure cannot be assigned to every sample age, so **zero Solsø
LRA samples are admitted**.

Replay against the retained Neotoma relations and private source PDF:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/replay.py \
  --repository . --paper /path/to/landclim/solsoe/odgaard-1994.pdf \
  --output artifacts/jobs/solsoe-original-study/replay
cmp docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/report.json \
  artifacts/jobs/solsoe-original-study/replay/report.json
```
