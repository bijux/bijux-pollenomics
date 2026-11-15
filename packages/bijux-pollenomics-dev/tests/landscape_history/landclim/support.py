"""Small source-spelled fixtures for regional analysis checks."""

from __future__ import annotations

from typing import Any

TAXA = (
    "Abies.alba",
    "Alnus.glutinosa",
    "Amanranthaceae.Chenopodiaceae",
    "Artemisia",
    "Betula",
    "Buxus.sempervirens",
    "Calluna.vulgaris",
    "Carpinus.betulus",
    "Carpinus.orientalis",
    "Castanea",
    "Cerealia.t",
    "Corylus.avellana",
    "Cyperaceae",
    "Ericaceae",
    "Fagus.sylvatica",
    "Filipendula",
    "Fraxinus",
    "Juniperus",
    "Phillyrea",
    "Picea",
    "Pinus",
    "Pistacia",
    "Plantago.lanceolata.type",
    "Poaceae",
    "Quercus.deciduous",
    "Quercus.evergreen",
    "Rumex.acetosa.t",
    "Salix",
    "Secale",
    "Tilia",
    "Ulmus",
)


def means(**amounts: float) -> dict[str, float]:
    """Build source-spelled means with matching cereal and open-land totals."""
    values = dict.fromkeys(TAXA, 0.0)
    values.update(amounts)
    values["AL"] = values["Cerealia.t"] + values["Secale"]
    values["OL"] = sum(
        values[k]
        for k in (
            "Calluna.vulgaris",
            "Amanranthaceae.Chenopodiaceae",
            "Artemisia",
            "Cyperaceae",
            "Filipendula",
            "Plantago.lanceolata.type",
            "Poaceae",
            "Rumex.acetosa.t",
            "Cerealia.t",
            "Secale",
        )
    )
    return values


def cell(
    grid: str,
    lat: float,
    *,
    high: bool = False,
    older: int = 100,
    status: str = "eligible",
    **amounts: float,
) -> Any:
    """Build a cell window with explicit support, quality and source means."""
    from bijux_pollenomics_dev.landscape_history.landclim.inputs import CellWindow

    return CellWindow(
        grid,
        15.5,
        lat,
        0,
        older,
        "high" if high else "low",
        means(**amounts),
        {"OL": 2.0, "AL": 0.3},
        status,
        "" if status == "eligible" else "no_pollen_data",
    )
