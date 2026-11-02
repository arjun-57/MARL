"""Tests for Data Loaders and Validators."""

import pytest
import pandas as pd
from pathlib import Path
from data.loaders.ember_loader import EmberPriceLoader
from data.loaders.opsd_loader import OPSDEnergyLoader
from data.loaders.validator import DataValidator


def test_ember_loader(tmp_path):
    raw_file = Path("data/raw/ember/Germany.csv")
    if not raw_file.exists():
        raw_file = tmp_path / "Germany.csv"
        sample_df = pd.DataFrame({
            "Datetime (UTC)": ["2019-01-01 00:00:00", "2019-01-01 01:00:00", "2019-01-01 02:00:00"],
            "Price (EUR/MWhe)": [45.2, 42.1, 39.8]
        })
        sample_df.to_csv(raw_file, index=False)

    loader = EmberPriceLoader(file_path=str(raw_file))
    df = loader.load(start_date="2019-01-01", end_date="2019-01-03")
    assert not df.empty
    assert "price_eur_mwh" in df.columns
    assert df["price_eur_mwh"].isna().sum() == 0


def test_opsd_loader(tmp_path):
    raw_file = Path("data/raw/opsd/time_series_60min_singleindex.csv")
    if not raw_file.exists():
        raw_file = tmp_path / "time_series_60min_singleindex.csv"
        sample_df = pd.DataFrame({
            "utc_timestamp": ["2019-01-01T00:00:00Z", "2019-01-01T01:00:00Z", "2019-01-01T02:00:00Z"],
            "DE_load_actual_entsoe_transparency": [45000.0, 43000.0, 42000.0],
            "DE_solar_generation_actual": [0.0, 0.0, 10.0]
        })
        sample_df.to_csv(raw_file, index=False)

    loader = OPSDEnergyLoader(file_path=str(raw_file))
    df = loader.load(start_date="2019-01-01", end_date="2019-01-03")
    assert not df.empty
    assert "germany_load_mw" in df.columns
    assert "germany_solar_mw" in df.columns
    assert (df["germany_solar_mw"] >= 0).all()


def test_data_validator():
    sample_df = pd.DataFrame({
        "timestamp": pd.date_range("2020-01-01", periods=10, freq="1h", tz="UTC"),
        "load_mw": [50000.0] * 10,
        "solar_mw": [1000.0] * 10,
        "price_eur_mwh": [45.0] * 10
    })
    valid_ts, rep_ts = DataValidator.validate_timestamps(sample_df, "timestamp")
    assert valid_ts

    valid_energy, rep_e = DataValidator.validate_energy_ranges(sample_df)
    assert valid_energy
