# Conditional local vegetation reconstruction at Bökesjön

This account retains one exposed Swedish development window and three conditional local-reconstruction scenarios. With regional/local compatible-panel abundance-density ratio 0.5, the inferred Betula/Poaceae panel cover is feasible. Ratios 1 and 2 yield negative Poaceae cover and Betula above one. Those signed results are retained as infeasible outcomes; they are not clipped, selected away or presented as measured vegetation.

The saved model passed its 40 source guards and model stage, then its independent numerical oracle failed at finite quadrature depth. An oracle-only successor reused all seven completed model outputs, passed 47 capture/geometry guards, and independently checked four receiving-annulus factors and 48 cover/covariance/SE cells. It did not rerun the model. The original overall failure remains recorded separately from model-stage and successor-oracle acceptance.

## Sources and denominators

The literal parameter panel is **Betula and Poaceae**, not the full LandClim flora. Membership uses the exact named native calibrated-BP point ages in **[100,350)**, with the documented AD1950 datum. Native chronology identities are retained; no historical LandClim chronology equivalence, new calibration, interpolation or repaired bounds is asserted.

| Role and core | Native dataset / collection unit / chronology | Samples | Unknown age bounds | Literal-panel pollen N | All-reported pollen NISP |
| --- | --- | ---: | ---: | ---: | ---: |
| Local BOKE, Bökesjön | 54001 / 39241 / 38422 | 5 | 5 | 707 | 2,663 |
| Regional KRAGMJNY, Krageholmssjön | 23013 / 16622 / 13366 | 9 | 0 | 1,391 | 4,905 |
| Regional BJARE, Bjäresjösjön | 53999 / 39240 / 38421 | 15 | 15 | 5,298 | 20,372 |
| Total | Three source cores | 29 | 20 | 7,396 | 27,940 |

The 20,544 residual reported pollen counts remain outside the parameterized panel. Pollen/NISP coverage does not establish vegetation area or completeness. The nine Krageholm age envelopes are retained even where they extend outside the point window; the other 20 envelopes remain unknown. Individual counts, sample identifiers, depth/age associations and presence masks remain in the external source packet, not these compact products.

Both primary-publication and all-returned-publication dependency groupings exclude the target's whole transitive source group and retain the same two training datasets. This exclusion does not make the already exposed local outcome untouched, and source distinctness does not establish environmental independence.

## Declared regional and local model

For each training core s and taxon i, regional weights pool **unclosed** count/deposition ratios once:

$$U_i=\sum_s\frac{n_{si}}{K_{si}p_i},\qquad r_i=\frac{U_i}{\sum_jU_j}.$$

These are count-weighted source ratios, not an average of individually closed cover vectors or basin-area weighting. The regional proxy includes the 80 m Bjäresjösjön basin; it has not been shown to satisfy the large-lake regional premise or represent a measured homogeneous regional landscape.

The local receiving basin is a static uniform 80 m disk from the selected workbook radius. Local land occupies the annulus 80–1,000 m and regional land 1,000–100,000 m in the scenario. The 1,000 m split is unestimated and is not a measured or fitted RSAP. Compatible land-mask evidence is absent, so both annuli explicitly assume all-terrestrial support. Wind is 3 m/s; fall speeds are 0.024 and 0.035 m/s. The GPM coefficient 0.12 is the source's empirical metre-based coefficient, not SI diffusivity in m²/s; turbulence parameter is 0.25. PPE means are 5.106 and 1, with SD 0.303 and reference SD 0; a fixed reference is not empirical certainty.

Let L_i and R_i be local and regional receiving-annulus responses, p_i the shared PPE, and lambda the **regional/local total compatible panel abundance-density ratio**. Lambda is not inferred from closed pollen, NISP coverage or total biomass integrated over unequal annulus areas. Area weighting is already included in L and R. The scenarios are lambda 0.5, 1 and 2, with 1 the explicitly equal compatible-panel abundance-density assumption.

Set a_i=L_i p_i and b_i=lambda R_i p_i r_i. The declared local/regional affine mixture is

$$q_i=\frac{a_i v_i+b_i}{T},\qquad T=\sum_j(a_jv_j+b_j),\qquad\sum_i v_i=1.$$

For positive a_i and a finite positive denominator, substitute v_i=(Tq_i-b_i)/a_i into the closure constraint:

$$T\sum_i\frac{q_i}{a_i}-\sum_i\frac{b_i}{a_i}=1,\qquad T=\frac{1+\sum_i b_i/a_i}{\sum_i q_i/a_i},\qquad v_i=\frac{Tq_i-b_i}{a_i}.$$

This algebra may produce a signed closed solution outside the simplex. Such a solution is infeasible as ecological cover and remains an explicit negative result. The maintained analytical LOVE adapter uses deterministic adjusted weights n_i/L_i, alpha=p_i and sr_i=b_i/a_i. Those weights are mathematical adjustments, never observed pseudo-counts drawn through a multinomial sampler. A forward roundtrip after fitting the same local pollen is an algebraic consequence, not prediction accuracy.

[Theuerkauf and Couwenberg (2024), §§2.1–2.3, printed pp.2–3](https://www.mdpi.com/2571-550X/7/2/18) supports additive local-plus-regional deposition from abundance, PPE and distance weighting, followed by pollen closure. The general-T expression above is this account's declared adapter algebra, not a numbered equation quoted from the paper. [Sugita (2007)](https://doi.org/10.1177/0959683607075838) is the original theory reference; its restricted full Equations 6/7 have not been authenticated here. The present receiving-disk split scenario does not establish historical LOVEr workflow compatibility or ecological validity.

## All retained outcomes

Cover and SE below use fractions of the **conditional two-taxon local panel**, not fractions of total landscape vegetation.

| Regional/local compatible-panel abundance-density ratio | Betula cover | Poaceae cover | Marginal SE for either taxon | Simplex / maintained forward |
| ---: | ---: | ---: | ---: | --- |
| 0.5 | 0.77810549 | 0.22189451 | 0.04587493 | Feasible / accepted |
| 1 | 1.00165398 | −0.00165398 | 0.05952186 | Infeasible / negative-cover refusal |
| 2 | 1.44875096 | −0.44875096 | 0.08682644 | Infeasible / negative-cover refusal |

All three marginal matrices use the **same 29 samples and shared PPE vector**. They are not three independent experiments, a cross-scenario joint covariance calculation or a probability-weighted model average. Counting uses separate fixed-N multinomial panel covariances for the pooled site windows. Shared PPE is differentiated through regional and local terms once. Count–PPE cross-covariance is **assumed zero as working independence**, not measured independence. Total conditional covariance is counting plus the once-shared PPE covariance. Each closed two-taxon matrix has negative off-diagonal covariance; the products retain every component and SE.

These delta SEs condition on the chronology points, radius, split, mask, panel and lambda. They are not measured interval coverage and do not include uncertainty in those assumptions. A marginal SE does not rehabilitate negative cover as a valid ecological interval. The independent Decimal50 calculation checks the general inverse and full counting/shared-PPE matrices; scalar circle-lens Simpson integration checks the four actual physical requests at unchanged finite depth and tolerances. The maximum factor difference was approximately 5.71e−12. Quadrature error/convergence estimates remain nonrigorous. None of these numerical checks establishes vegetation accuracy, untouched confirmation, historical reproduction or observational completeness.

## Ratio identifiability under the fixed response

The retained local observation does not jointly identify its local cover and the regional/local compatible-panel abundance-density ratio. Write c_i=R_i p_i r_i, A=sum(q_i/a_i) and B=sum(c_i/a_i). Closure gives the complete affine family

$$v_i(\lambda)=u_i+\lambda d_i,\qquad u_i=\frac{q_i}{a_i A},\qquad d_i=\frac{q_i B/A-c_i}{a_i}.$$

For these exact retained inputs, nonnegative two-taxon cover permits lambda from zero through approximately **0.996300618715**, including both endpoints. Restricting the ratio to positive values excludes zero; zero is only the zero-background limiting control. The upper endpoint has Betula cover one and Poaceae zero. This is a deterministic feasible domain under fixed inputs, not a confidence interval, a ratio probability model or a selected estimate.

Eight declared points retain the three original signed cases and add the zero-background limit, three interior controls and the upper endpoint. Every analytical point has the same closed pollen response, including the signed infeasible original cases. Ratios 1 and 2 retain their separate maintained-model negative-cover refusals; their analytical identity does not make them ecological covers. The free-coordinate response Jacobian on (Betula cover, lambda) has rank one, with the affine slope and ratio direction forming a null direction. An independent exact rational calculation on the serialized source constants verifies closure, the endpoint inequalities, the Jacobian and its null direction. At the serialized binary64 endpoint, the exact rational oracle retains a positive Poaceae remainder of approximately 1.04e−16, while binary64 evaluation returns zero. The mathematical endpoint itself has exactly zero Poaceae. These representations are retained without clipping.

The historical proof continues to name its original writer bytes. Three current helper files differ by specifically reviewed docstrings and import ordering; their separate source identities are qualified in the new source account. The historical hashes are preserved.

This new algebraic consumer executes no model, fit or quadrature and leaves the original report, all three covariance products, source proof and failed overall model envelope unchanged. It adds no cross-scenario covariance. Ratio-compatible physical evidence, measured vegetation and qualified review remain separate requirements. [The derived family](identifiability.json) and [its source account](identifiability-source-account.json) retain the actual scope and independent checks.

## Unresolved geometry provenance

The [CAA2007 paper, printed p.388](https://proceedings.caaconference.org/files/2007/125_Sugita_et_al_CAA2007.pdf) reports Krageholmssjön's area as 186 ha, while the selected workbook scenario uses a radius of 837 m. This is an unresolved cross-source area/radius provenance difference. The documentary evidence is a browser parsed-text review, not a newly authenticated native PDF capture or proof of historical basin geometry. Neither source has silently replaced the frozen radius, and no geometry correction or model rerun is attributed to this comparison.

## Compact source-owned products

`report.json` projects the aggregate denominators, all signed scenarios, covariance components and independent checks. `source-proof.json` binds the exact 14 original external capture members, source descriptor, scientific candidate, failed model envelope, accepted oracle envelope and the projection-module hashes recorded for that publication. The supplied qualified author snapshot uses a dictionary of sorted filename→SHA256 identities and a complete sorted descriptor list. Its manifest is a newly authored transport record; original model/oracle bytes are unchanged.

The original projection authenticates source bytes before parsing and before/after atomic publication. It executes no count acquisition, chronology fitting, physical model or numerical oracle. Raw capture/source masks remain external. Identity transport is not new data-use permission or formal external review; historical workbook restriction flags, author-copy rights and qualified reader/scientific reviews remain separate gates. The declared use is a conditional analytical development result, with no independent vegetation, untouched, full scientific acceptance or release-ready claim.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** The original three conditional scenarios are retained. A new fixed-response affine family shows structural non-identifiability: the same local pollen supports every nonnegative ratio from zero through approximately 0.996300618715; the response Jacobian has rank one. This domain is conditional on the fixed regional proxy, physical responses and literal two-taxon panel.

**Unsupported claim.** Measured vegetation cover, a fitted or measured RSAP, untouched prediction accuracy from a forward roundtrip, historical LOVEr/Sugita-equation reproduction, calibrated uncertainty or biological completeness of the two-taxon panel.

**Actual verification performed.** The actual retained-source consumer passed with 91 independent exact rational scalar comparisons, eight family points, all three original signed-case comparisons, endpoint inequalities and rank/null certificates. Its 27 focused source contracts, strict checks of four files and configured Ruff checks passed. No model, quadrature, acquisition or fit was run. The original overall failed envelope remains distinct from its passed model stage and later accepted oracle-only successor.

**Remaining input or review.** 20 sample-age envelopes remain unknown; static receiving circles, all-terrestrial annuli, the 1,000 m split and regional/local compatible-panel abundance ratio are assumptions. The regional proxy includes a small 80 m basin. Historical source-copy rights, physical applicability and qualified external review remain separate. The later Krageholm static-area sensitivity does not replace this frozen 837 m regional scenario.

**Cause category.** data | assumption | algorithm/numerical | comparability | access/rights | qualified review

**Consequence.** Retain the feasible continuum and both original negative-cover cases. The point observation cannot select local composition and abundance ratio simultaneously. Marginal conditional SEs remain the original products; they do not turn the family into a posterior or give coverage to its feasible domain.

**Precise next acceptance route.** Qualify source-compatible regional/local abundance, land masks, regional support and age-specific basin geometry before a physical/ecological interpretation. Declare cross-scenario uncertainty if needed, and obtain matched vegetation plus external review before accuracy/coverage claims; authenticate original theory equations for a historical-compatibility claim.

**Negative or refused result.** The original ratios 1 and 2 still give negative Poaceae cover and are refused by the maintained forward model. A continuum of feasible covers gives the same pollen, so a forward roundtrip cannot identify the ratio. Exact endpoint checks preserve any signed binary64 rounding difference without clipping. The original overall oracle failure remains retained.

**Matched denominator.** One [100,350) calibrated-BP window; three cores and 29 samples: BOKE 5, KRAG 9 and BJARE 15. The literal Betula/Poaceae panel has 7,396 grains versus 27,940 all-reported NISP, leaving 20,544 residual counts; 20 age bounds remain unknown. Eight deterministic family controls reuse these sources and the fixed shared PPE, including the three unchanged original scenarios. No independent scenario experiments or ratio probabilities are implied.

Qualified authored reader SHA-256: `954442ceccad2fbecd1947d9af0ec91f257add096201a8568051f39767cc7ff2`.

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-conditional-love/report.json](report.json) (SHA-256 `2d52167f4787dc8542f82f2d644933322173998d494017520d7ffeda67362b60`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-conditional-love/source-proof.json](source-proof.json) (SHA-256 `bc4a3b4107b0e738e31852c1dea9933c1e90d1cdb4c7e6f5873cc7d04cfb63dd`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/report.json](../krageholm-static-geometry-sensitivity/report.json) (SHA-256 `07e30b471a0cac2a43ff2877bdbc36469b8ef5f80f6d99cf9501a7c3bb1bb0d7`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-conditional-love/identifiability.json](identifiability.json) (SHA-256 `2541362623d0428ccddd51a9ba4cc6293316c553f02c623d1124ebf768cdff2f`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-conditional-love/identifiability-source-account.json](identifiability-source-account.json) (SHA-256 `0aaaaca4ff820358ddba2b80b6285589fbe52999125d92d80d2c5c40b54d3009`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md) (source SHA-256 `2f61fcbbf6fb36a075790199e81d834dbf8225e426aa7d92dc1ba4cbfb19f1f0`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
