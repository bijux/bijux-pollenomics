"""Fail-closed publication reconciliation for animal sample chronology."""

from .service import (
    build_animal_chronology_publication as build_animal_chronology_publication,
)

build_animal_chronology_publication.__module__ = __name__

__all__ = ["build_animal_chronology_publication"]
