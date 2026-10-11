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

Let L_i and R_i be local and regional receiving-annulus responses, p_i the shared PPE, and lambda the **regional/local total compatible panel abundance-density ratio**. Lambda is not inferred from closed pollen, NISP coverage or total biomass integrated over unequal annulus areas. Area weighting is already included in L and R. The scenarios are lambda 0.5, 1 and 2, with 1 the explicitly equal-panel-mass assumption.

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

## Unresolved geometry provenance

The [CAA2007 paper, printed p.388](https://proceedings.caaconference.org/files/2007/125_Sugita_et_al_CAA2007.pdf) reports Krageholmssjön's area as 186 ha, while the selected workbook scenario uses a radius of 837 m. This is an unresolved cross-source area/radius provenance difference. The documentary evidence is a browser parsed-text review, not a newly authenticated native PDF capture or proof of historical basin geometry. Neither source has silently replaced the frozen radius, and no geometry correction or model rerun is attributed to this comparison.

## Compact source-owned products

`report.json` projects the aggregate denominators, all signed scenarios, covariance components and independent checks. `source-proof.json` binds the exact 14 original external capture members, source descriptor, scientific candidate, failed model envelope, accepted oracle envelope and current projection-module hashes. The supplied qualified author snapshot uses a dictionary of sorted filename→SHA256 identities and a complete sorted descriptor list. Its manifest is a newly authored transport record; original model/oracle bytes are unchanged.

The projection authenticates source bytes before parsing and before/after atomic publication. It executes no count acquisition, chronology fitting, physical model or numerical oracle. Raw capture/source masks remain external. Identity transport is not new data-use permission or formal external review; historical workbook restriction flags, author-copy rights and qualified reader/scientific reviews remain separate gates. The declared use is a conditional analytical development result, with no independent vegetation, untouched, full scientific acceptance or release-ready claim.
