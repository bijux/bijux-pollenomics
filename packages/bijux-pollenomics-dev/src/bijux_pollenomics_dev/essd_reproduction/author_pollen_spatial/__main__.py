"""Run the author spatial-block prediction or its separate scoring step."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .prediction import predict_block
from .scoring import score_blocks
from .source import GRIDS, _study


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("predict", "score"))
    parser.add_argument("--author", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target-grid", choices=GRIDS)
    parser.add_argument("--prediction-512", type=Path)
    parser.add_argument("--prediction-562", type=Path)
    parser.add_argument("--local-scores", type=Path)
    args = parser.parse_args()
    study = _study(args.author, args.reference)
    if args.operation == "predict":
        if args.target_grid is None:
            raise ValueError("Prediction needs a target grid")
        result = predict_block(study, args.target_grid, args.output)
        print(
            json.dumps(
                {
                    "grid": args.target_grid,
                    "predicted_bins": result["predicted_target_bins_without_outcomes"],
                }
            )
        )
    else:
        if (
            args.prediction_512 is None
            or args.prediction_562 is None
            or args.local_scores is None
        ):
            raise ValueError("Scoring needs both persisted blocks and local baseline")
        result = score_blocks(
            study,
            (args.prediction_512, args.prediction_562),
            args.output,
            args.local_scores,
        )
        print(
            json.dumps(
                {
                    key: result[key]
                    for key in (
                        "attempted_observed_site_bins",
                        "scored_site_bins",
                        "refused_no_training_site_bins",
                        "site_macro_mae_fraction",
                    )
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
