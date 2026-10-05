# Joint conditional covariance of reused counts and shared PPE

This calculation propagates a fixed count model and shared parameter covariance through closed literal-panel compositions. It does not estimate chronology, geography, ecological transfer or empirical error coverage.

For result r, let the positive fixed factor be K_ri and shared positive PPE be p_i. With nonnegative observed counts n_i and positive panel total N, define a_ri = 1/(K_ri p_i), w_ri = a_ri n_i, W_r = sum_i w_ri, and c_ri = w_ri/W_r. The closure Jacobian is B_r = I − c_r 1ᵀ. Differentiation gives the count derivative J_r = B_r diag(a_r)/W_r and the PPE derivative H_r = −B_r diag(c_r/p). Parameter columns are embedded by their exact shared native row identity, including parameters absent from a particular panel.

One authenticated native collection-unit/dataset/chronology/window/count-support identity defines one latent count vector. Reusing those observations with alternative receiving geometries does not create another independent observation. Under the conditional fixed-N multinomial model, C_ng = N_g[diag(f_g) − f_g f_gᵀ], where f_g = n_g/N_g. Stack each result's count derivative into G_g at that group's columns. Let H stack the PPE derivatives. Then

`C_joint = sum_g G_g C_ng G_gᵀ + H C_P Hᵀ`.

This sum assumes zero count–PPE cross-covariance. Count-correlated or endogenous PPE requires the omitted cross terms. Distinct native units and nonoverlapping fixed-point windows are independent count groups only under the separately declared working assumptions. Native identifiers establish distinct supports, not empirical temporal or environmental independence. Overlapping observations and alternate same-unit chronology/dataset projections are refused because their count cross-covariance is not supplied. Within the Nordic profile, C_P is the diagonal of eight literal native parameter-row SD² values, shared across every applicable result; unknown PPE off-diagonal correlation is not estimated.

Each C_ng is positive semidefinite by the multinomial variance identity. If C_P is positive semidefinite, every linear image in the sum is positive semidefinite. Also 1ᵀB_r = 0, so the covariance annihilates each panel's closure direction. Singular tangent covariance is expected. For a same-count geometry difference, a selector A places +I at the first result and −I at the second. Its covariance A C_joint Aᵀ equals C_rr + C_tt − C_rt − C_tr and remains positive semidefinite. Identical geometries have zero contrast variance because both count and PPE errors are shared.

An independently expressed route uses the panel fractions directly. Its derivative L_r = B_r diag(a_r)/sum_i(a_ri f_i) equals N J_r, and C_fg = [diag(f_g) − f_g f_gᵀ]/N_g. Consequently L_r C_fg L_tᵀ = J_r C_ng J_tᵀ. The retained independent Decimal50 consumer uses this fraction route and quotient differentiation for PPE, rather than calling the producer's count derivative implementation.

These are first-order conditional delta covariances at the observed plug-in fractions. Positive semidefiniteness, closure and scalar parity do not establish a calibrated confidence interval, joint posterior, empirical coverage, independent vegetation accuracy or historical reconstruction. A zero boundary plug-in covariance is not proof of absence.
