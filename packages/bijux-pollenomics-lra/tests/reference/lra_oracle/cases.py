"""Deterministic cases for the independent R/DISQOVER oracle.

The expected arrays in this module are computed by the native Python package.
They are deliberately named *Python expectations*, not R golden files. Actual
R results are generated only by :mod:`parity.run_live_r`.
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from lra_oracle.prospective import load_prospective_optimized_declaration

from bijux_pollenomics_lra.dispersal.kernels import METHODS, DispersalFactorK
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.optimization.solver import ReplayOptimizer
from bijux_pollenomics_lra.reconstruction.analytical import LOVEr, lov
from bijux_pollenomics_lra.reconstruction.optimized import (
    LOVEoptim,
    calK,
    logeuclidean,
    tf,
)
from bijux_pollenomics_lra.reconstruction.regional import REVEALS, REVEALSinR
from bijux_pollenomics_lra.resources.examples import load_dataset, load_love_example


@dataclass(frozen=True, slots=True)
class Case:
    """One R expression and its independently computed Python expectation."""

    name: str
    api: str
    mode: str
    expression: str
    expected: np.ndarray
    rtol: float = 1e-10
    atol: float = 1e-10
    exact_indices: tuple[int, ...] = ()


def r_literal(value: object) -> str:
    """Encode trusted Python data as a non-executable R literal."""
    if isinstance(value, pd.DataFrame):
        columns = ",".join(
            r_literal(value[column].to_numpy()) for column in value.columns
        )
        return (
            "structure(list("
            + columns
            + "),names="
            + r_literal([str(column) for column in value.columns])
            + ',class="data.frame",row.names='
            + r_literal([str(index) for index in value.index])
            + ")"
        )
    if isinstance(value, pd.Series):
        return r_literal(value.to_numpy())
    if isinstance(value, dict):
        return (
            "structure(list("
            + ",".join(r_literal(item) for item in value.values())
            + "),names="
            + r_literal(list(value))
            + ")"
        )
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return r_literal(value.item())
        vector = (
            "c("
            + ",".join(r_literal(item) for item in value.ravel(order="F").tolist())
            + ")"
        )
        return (
            "array(" + vector + ",dim=" + r_literal(list(value.shape)) + ")"
            if value.ndim > 1
            else vector
        )
    if isinstance(value, (list, tuple)):
        if not value:
            return "list()"
        if all(isinstance(item, (str, int, float, bool, np.generic)) for item in value):
            return "c(" + ",".join(r_literal(item) for item in value) + ")"
        return "list(" + ",".join(r_literal(item) for item in value) + ")"
    if isinstance(value, (str, Path)):
        return json.dumps(str(value), ensure_ascii=False)
    if value is None:
        return "NULL"
    if isinstance(value, (bool, np.bool_)):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if np.isnan(number):
            return "NA_real_"
        if np.isposinf(number):
            return "Inf"
        if np.isneginf(number):
            return "-Inf"
        return repr(number)
    raise TypeError(f"Unsupported R literal type: {type(value)!r}")


def flatten(value: object) -> np.ndarray:
    """Flatten nested Python result structures in R list/matrix order."""
    if isinstance(value, dict):
        pieces = [flatten(item) for item in value.values()]
        return np.concatenate(pieces) if pieces else np.empty(0)
    if isinstance(value, (list, tuple)) and any(
        isinstance(item, (dict, np.ndarray, pd.DataFrame, pd.Series)) for item in value
    ):
        pieces = [flatten(item) for item in value if item is not None]
        return np.concatenate(pieces) if pieces else np.empty(0)
    return np.asarray(value).ravel(order="F")


def build_cases(workdir: str | Path) -> tuple[list[str], list[Case]]:
    """Build cases covering every source-compatible public/native LRA API."""
    work = Path(workdir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    setup: list[str] = []
    cases: list[Case] = []

    def variable(name: str, value: object) -> str:
        setup.append(f"{name} <- {r_literal(value)}")
        return name

    def add(
        name: str,
        api: str,
        expression: str,
        expected: object,
        mode: str = "unmodified_function",
        *,
        rtol: float = 1e-10,
        atol: float = 1e-10,
        exact_indices: tuple[int, ...] = (),
    ) -> None:
        cases.append(
            Case(
                name=name,
                api=api,
                mode=mode,
                expression=expression,
                expected=flatten(expected),
                rtol=rtol,
                atol=atol,
                exact_indices=exact_indices,
            )
        )

    # Dispersal coverage includes every model, both basin paths, vectorisation
    # and fall-speed rounding boundaries used by serialized LSM models.
    for method in METHODS:
        for basin in ("peatland", "lake"):
            diameter: float | np.ndarray = (
                np.array([20.0, 100.0, 600.0]) if basin == "peatland" else 60.0
            )
            add(
                f"K_{method.replace(' ', '_')}_{basin}",
                "DispersalFactorK",
                f'F("DispersalFactorK")(.03,{r_literal(basin)},{r_literal(diameter)},{r_literal(method)},1e5)',
                DispersalFactorK(0.03, basin, diameter, method, 100_000),
                atol=3e-10,
            )
    for fall_speed in (0.015, 0.025, 0.045, 0.055, 0.075):
        add(
            f"K_rounding_{fall_speed}",
            "DispersalFactorK",
            f'F("DispersalFactorK")({fall_speed},"peatland",100,"lsm unstable",1e5)',
            DispersalFactorK(fall_speed, "peatland", 100, "lsm unstable", 100_000),
            rtol=0,
            atol=3e-13,
        )

    reveals_data = load_dataset("Tiefer_See")
    regional_pollen = reveals_data["pollenTS"].iloc[:3, :6].copy()
    regional_params = reveals_data["paramsTS"].copy()
    variable("rpollen", regional_pollen)
    variable("rparams", regional_params)
    for draws in (1, 3):
        native = REVEALSinR(
            regional_pollen,
            regional_params,
            "lake",
            100,
            n=draws,
            stochastic=False,
            verbose=False,
        )
        expression = (
            f'fixed_reveals(rpollen,rparams,"lake",100,n={draws},verbose=FALSE)'
        )
        add(
            f"REVEALSinR_deterministic_{draws}",
            "REVEALSinR",
            f"as.matrix(({expression})[,-c(1,2)])",
            native.iloc[:, 2:],
            "sampler_instrumented_wrapper",
        )
    add(
        "REVEALSinR_labels",
        "REVEALSinR",
        'colnames(fixed_reveals(rpollen,rparams,"lake",100,n=3,verbose=FALSE))',
        list(native.columns),
        "sampler_instrumented_wrapper",
    )

    paired_params = pd.DataFrame({"ppe": [1.0, 2.0, 3.0], "ppe.error": [0.1, 0.2, 0.3]})
    paired_ppe = np.array([[1.0, 2.0, 3.0], [2.0, 2.0, 3.0], [1.0, 3.0, 4.0]])
    paired_pollen = np.array(
        [[20.0, 30.0, 50.0], [30.0, 20.0, 50.0], [40.0, 10.0, 50.0]]
    )
    variable("paired_params", paired_params)
    variable("paired_ppe", paired_ppe)
    variable("paired_pollen", paired_pollen)
    paired_native = REVEALS(
        [1.0, 20.0, 30.0, 50.0],
        3,
        paired_params,
        deposition=[0.2, 0.3, 0.5],
        ppe_draws=paired_ppe,
        pollen_draws=paired_pollen,
    )
    add(
        "REVEALS_paired_draws",
        "REVEALS",
        """{ai<-0L;ci<-0L;af<-function(n,mean,sds){ai<<-ai+1L;paired_ppe[ai,]};cf<-function(n,pollen){ci<<-ci+1L;paired_pollen[ci,]};flatten_numeric(F("REVEALS")(c(1,20,30,50),3,paired_params,af,c(.2,.3,.5),cf,FALSE,FALSE))}""",
        paired_native,
        "supplied_random_draws",
    )

    local, regional, love_params, rings = load_love_example()
    love_params = dict(love_params)
    love_params["error"] = False
    variable("lpol", pd.concat([local, regional], axis=0))
    variable("lparams", love_params)
    variable("lrings", rings)
    regional_term = np.linspace(0.01, 0.10, 10)
    variable("sr_test", regional_term)

    add(
        "lov_deterministic",
        "lov",
        'F("lov")(lpol[1,,drop=FALSE],sr_test,lparams)',
        lov(local, regional_term, love_params, stochastic=False),
    )
    add(
        "calK_full",
        "calK",
        'F("calK")(lrings,lparams)',
        calK(rings, love_params),
        atol=3e-10,
    )
    a = np.array([0.2, 0.4, 0.6])
    b = np.array([0.3, 0.5, 0.7])
    add(
        "logeuclidean",
        "logeuclidean",
        f'F("logeuclidean")({r_literal(a)},{r_literal(b)})',
        logeuclidean(a, b),
    )
    candidate = np.linspace(0.1, 0.9, 10)
    regional_deposition = np.linspace(0.02, 0.11, 10)
    local_k = np.vstack([np.linspace(0.1, 0.3, 10), np.linspace(0.2, 0.4, 10)])
    local_fraction = np.array([0.5, 1.0])
    observed = np.linspace(0.03, 0.12, 10)
    ppes = np.linspace(0.5, 2.0, 10)
    add(
        "tf_objective",
        "tf",
        f'F("tf")({r_literal(candidate)},{r_literal(regional_deposition)},{r_literal(local_k)},{r_literal(local_fraction)},{r_literal(observed)},{r_literal(ppes)})',
        tf(candidate, regional_deposition, local_k, local_fraction, observed, ppes),
        atol=3e-10,
    )

    analytical = LOVEr(
        local,
        regional,
        love_params,
        rings,
        10,
        repeats=2,
        stochastic=False,
    )
    analytical_expected = {
        key: analytical[key]
        for key in ("Mean", "Q10", "Q90", "SD", "Outlier", "OutlierQant")
    }
    add(
        "LOVEr_deterministic",
        "LOVEr",
        """flatten_numeric(clone_with("LOVEr",list(REVEALSinR=fixed_reveals))(lpol[1,,drop=FALSE],lpol[2,,drop=FALSE],lparams,lrings,10,repeats=2))""",
        analytical_expected,
        "sampler_instrumented_wrapper",
        atol=3e-10,
    )

    candidates = np.array([np.full(10, 0.5), np.linspace(0.1, 0.9, 10)], dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        optimized = LOVEoptim(
            local,
            regional,
            love_params,
            rings,
            10,
            repeats=2,
            stochastic=False,
            optimizer=ReplayOptimizer(candidates),
        )
    optimized_expected = {
        key: optimized[key] for key in ("cover", "pollenpercentages", "mBestValue")
    }
    add(
        "LOVEoptim_candidate_replay",
        "LOVEoptim",
        """{CANDIDATES<-"""
        + r_literal(candidates)
        + """;with_binding("RcppDE","DEoptim",replay_de,flatten_numeric(clone_with("LOVEoptim",list(REVEALSinR=fixed_reveals,rmultinom=fixed_multinomial))(lpol[1,,drop=FALSE],lpol[2,,drop=FALSE],lparams,lrings,10,repeats=2)))}""",
        optimized_expected,
        "sampler_and_optimizer_replay",
        atol=3e-8,
    )

    declaration = load_prospective_optimized_declaration()
    if tuple(local.columns[1:]) != declaration.taxa:
        raise AssertionError("Prospective taxon axis differs from source resources")
    prospective_k = calK(rings, love_params).to_numpy(dtype=float)
    terrestrial_fraction = rings["terrestrial"].to_numpy(dtype=float) / rings[
        "ring"
    ].to_numpy(dtype=float)
    nominal_ppe = love_params["ppes"]["ppe"].to_numpy(dtype=float)

    for case_index, declared in enumerate(declaration.cases, start=1):
        stem = f"prospective_{case_index}"
        local_case = local.copy()
        regional_case = regional.copy()
        local_case.iloc[0, 1:] = declared.local_counts
        regional_case.iloc[0, 1:] = declared.regional_counts
        variable(f"{stem}_local", local_case)
        variable(f"{stem}_regional", regional_case)
        variable(f"{stem}_candidates", declared.candidates)

        regional_result = REVEALSinR(
            regional_case,
            love_params["ppes"],
            str(np.asarray(love_params["tBasinRegional"]).reshape(-1)[0]),
            int(np.asarray(love_params["dBasinRegional"]).item()),
            dwm=str(np.asarray(love_params["dwm"]).reshape(-1)[0]),
            n=1,
            stochastic=False,
            verbose=False,
        )
        regional_cover = (
            regional_result.filter(regex=r"\.mean$").iloc[0].to_numpy(dtype=float) / 100
        )
        intermediate: list[np.ndarray] = [
            prospective_k.ravel(order="F"),
            regional_cover,
        ]
        observed = declared.local_counts / declared.local_counts.sum()
        for ring_index in range(declared.max_ring_love):
            local_fraction = terrestrial_fraction[: ring_index + 1]
            if local_fraction.sum() <= 0:
                continue
            regional_fraction = terrestrial_fraction[ring_index + 1 :]
            regional_deposition = np.sum(
                prospective_k[ring_index + 1 :]
                * (regional_cover * nominal_ppe)[None, :]
                * regional_fraction[:, None],
                axis=0,
            )
            local_k = prospective_k[: ring_index + 1]
            objectives = np.asarray(
                [
                    tf(
                        candidate,
                        regional_deposition,
                        local_k,
                        local_fraction,
                        observed,
                        nominal_ppe,
                    )
                    for candidate in declared.candidates
                ]
            )
            intermediate.extend((regional_deposition, objectives))
        add(
            f"{declared.case_id}_intermediates",
            "LOVEoptim",
            f"optimized_intermediates({stem}_local,{stem}_regional,lparams,lrings,{declared.max_ring_love},{stem}_candidates)",
            np.concatenate(intermediate),
            "prospective_fixed_input",
            rtol=declaration.rtol,
            atol=declaration.atol,
        )
        add(
            f"{declared.case_id}_taxon_axis",
            "LOVEoptim",
            'colnames(F("calK")(lrings,lparams))',
            list(declaration.taxa),
            "prospective_fixed_input",
            rtol=0,
            atol=0,
        )
        add(
            f"{declared.case_id}_ring_axis",
            "LOVEoptim",
            'as.numeric(rownames(F("calK")(lrings,lparams)))',
            rings["mean"].to_numpy(dtype=float),
            "prospective_fixed_input",
            rtol=declaration.rtol,
            atol=declaration.atol,
            exact_indices=tuple(range(len(rings))),
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            prospective_result = LOVEoptim(
                local_case,
                regional_case,
                love_params,
                rings,
                declared.max_ring_love,
                repeats=1,
                stochastic=False,
                optimizer=ReplayOptimizer(declared.candidates),
            )
        wrapper_expected = {
            key: prospective_result[key]
            for key in ("cover", "pollenpercentages", "mBestValue")
        }
        diagnostic_expected: list[float] = []
        for diagnostic in prospective_result["optimizers"]:
            if (
                diagnostic.nit != 1
                or diagnostic.nfev != len(declared.candidates)
                or not diagnostic.success
            ):
                raise AssertionError(
                    "Replay diagnostics differ from the prospective termination policy"
                )
            selected = np.flatnonzero(
                np.all(declared.candidates == diagnostic.x[None, :], axis=1)
            )
            if len(selected) != 1:
                raise AssertionError(
                    "Replay winner must identify one declared candidate"
                )
            diagnostic_expected.extend(
                (
                    diagnostic.fun,
                    float(diagnostic.nit),
                    float(diagnostic.nfev),
                    float(diagnostic.success),
                    float(selected[0] + 1),
                )
            )
        wrapper_values = [wrapper_expected, np.asarray(diagnostic_expected)]
        wrapper_result_size = len(flatten(wrapper_expected))
        exact_diagnostics = tuple(
            wrapper_result_size + offset + field
            for offset in range(0, len(diagnostic_expected), 5)
            for field in (1, 2, 3, 4)
        )
        wrapper_expression = f"""{{
          REPLAY_TRACE<-list()
          CANDIDATES<-{stem}_candidates
          result<-with_binding(
            "RcppDE","DEoptim",replay_de_traced,
            flatten_numeric(
              clone_with("LOVEoptim",list(REVEALSinR=fixed_reveals,rmultinom=fixed_multinomial))(
                {stem}_local,{stem}_regional,lparams,lrings,
                {declared.max_ring_love},repeats=1
              )
            )
          )
          c(result,unlist(REPLAY_TRACE,use.names=FALSE))
        }}"""
        add(
            f"{declared.case_id}_wrapper_replay",
            "LOVEoptim",
            wrapper_expression,
            wrapper_values,
            "prospective_sampler_and_optimizer_replay",
            rtol=declaration.rtol,
            atol=declaration.atol,
            exact_indices=exact_diagnostics,
        )

        first_active = int(np.flatnonzero(terrestrial_fraction > 0)[0])
        regional_fraction = terrestrial_fraction[first_active + 1 :]
        regional_deposition = np.sum(
            prospective_k[first_active + 1 :]
            * (regional_cover * nominal_ppe)[None, :]
            * regional_fraction[:, None],
            axis=0,
        )
        nonfinite_local_k = prospective_k[: first_active + 1]
        nonfinite_local_fraction = terrestrial_fraction[: first_active + 1]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            zero_objective = tf(
                np.zeros(len(declaration.taxa)),
                regional_deposition,
                nonfinite_local_k,
                nonfinite_local_fraction,
                observed,
                nominal_ppe,
            )
        add(
            f"{declared.case_id}_nonfinite_objective",
            "tf",
            f"optimized_zero_objective({stem}_local,{stem}_regional,lparams,lrings,{stem}_candidates)",
            zero_objective,
            "prospective_nonfinite",
            rtol=declaration.rtol,
            atol=declaration.atol,
        )

        def invalid_objective(
            candidate: np.ndarray,
            regional_input: np.ndarray = regional_deposition,
            local_k_input: np.ndarray = nonfinite_local_k,
            local_fraction_input: np.ndarray = nonfinite_local_fraction,
            observed_input: np.ndarray = observed,
        ) -> float:
            return tf(
                candidate,
                regional_input,
                local_k_input,
                local_fraction_input,
                observed_input,
                nominal_ppe,
            )

        try:
            ReplayOptimizer(np.zeros((2, len(declaration.taxa)))).solve(
                invalid_objective,
                np.zeros(len(declaration.taxa)),
                np.ones(len(declaration.taxa)),
            )
            python_refusal = "accepted"
        except ValidationError as error:
            if str(error) != "Every replay candidate has an undefined objective":
                raise
            python_refusal = "refused: all replay candidates invalid"
        add(
            f"{declared.case_id}_all_nonfinite_refusal",
            "LOVEoptim",
            f"optimized_all_nonfinite_refusal({stem}_local,{stem}_regional,lparams,lrings,{stem}_candidates)",
            python_refusal,
            "prospective_refusal",
            rtol=0,
            atol=0,
        )

    return setup, cases
