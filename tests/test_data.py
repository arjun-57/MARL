"""Tests for Data Loaders and Validators."""

import pytest
import pandas as pd
from data.loaders.ember_loader import EmberPriceLoader
from data.loaders.opsd_loader import OPSDEnergyLoader
from data.loaders.validator import DataValidator


def test_ember_loader():
    loader = EmberPriceLoader()
    df = loader.load(start_date="2019-01-01", end_date="2019-01-03")
    assert not df.empty
    assert "price_eur_mwh" in df.columns
    assert df["price_eur_mwh"].isna().sum() == 0


def test_opsd_loader():
    loader = OPSDEnergyLoader()
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
