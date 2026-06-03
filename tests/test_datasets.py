"""Tests for the cached, analysis-ready clean reservoir dataset (Phase 1 output)."""

from __future__ import annotations

from pathlib import Path

from geothermal.datasets import clean_reservoir_dataset

_FINAL_COLUMNS = {
    "well_id",
    "x",
    "y",
    "ah_m",
    "depth_tvd_m",
    "porosity_final",
    "porosity_source",
    "permeability_md",
}


def test_clean_dataset_has_analysis_columns_and_no_gaps(tmp_path: Path) -> None:
    df = clean_reservoir_dataset(refresh=True, cache_path=tmp_path / "clean.parquet")
    assert set(df.columns) >= _FINAL_COLUMNS
    assert df["depth_tvd_m"].notna().to_numpy().all()
    assert df["porosity_final"].notna().to_numpy().all()
    assert df["permeability_md"].notna().to_numpy().all()
    assert len(df) == 3455


def test_cache_round_trips(tmp_path: Path) -> None:
    cache = tmp_path / "clean.parquet"
    built = clean_reservoir_dataset(refresh=True, cache_path=cache)
    assert cache.exists()
    loaded = clean_reservoir_dataset(cache_path=cache)  # served from cache
    assert len(loaded) == len(built)
    assert list(loaded.columns) == list(built.columns)
