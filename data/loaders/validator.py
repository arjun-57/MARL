"""Data Validation and Quality Assurance Utilities."""

import logging
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates raw and processed energy time-series data."""

    @staticmethod
    def validate_timestamps(df: pd.DataFrame, time_col: str, expected_freq: str = "1h") -> Tuple[bool, Dict[str, Any]]:
        """Verify chronological ordering, duplicates, and missing timestamps."""
        if time_col not in df.columns:
            return False, {"error": f"Missing column: {time_col}"}

        series = pd.to_datetime(df[time_col], utc=True)
        is_monotonic = series.is_monotonic_increasing
        duplicates = series.duplicated().sum()

        full_range = pd.date_range(start=series.min(), end=series.max(), freq=expected_freq, tz="UTC")
        missing_count = len(full_range) - len(series)

        report = {
            "is_monotonic": bool(is_monotonic),
            "duplicates": int(duplicates),
            "start": str(series.min()),
            "end": str(series.max()),
            "total_rows": len(series),
            "missing_timestamps": int(missing_count)
        }
        valid = is_monotonic and (duplicates == 0) and (missing_count >= 0)
        return valid, report

    @staticmethod
    def validate_energy_ranges(
        df: pd.DataFrame,
        load_col: str = "load_mw",
        solar_col: str = "solar_mw",
        price_col: str = "price_eur_mwh"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Validate physical sanity checks for German electrical figures."""
        issues = []
        metrics = {}

        if load_col in df.columns:
            load = df[load_col].dropna()
            metrics["load_min"] = float(load.min())
            metrics["load_max"] = float(load.max())
            metrics["load_nan_count"] = int(df[load_col].isna().sum())
            if (load < 0).any():
                issues.append("Negative load detected")
            if (load > 120000).any():  # German peak is ~80 GW
                issues.append("Unrealistically high German load (>120 GW)")

        if solar_col in df.columns:
            solar = df[solar_col].dropna()
            metrics["solar_min"] = float(solar.min())
            metrics["solar_max"] = float(solar.max())
            metrics["solar_nan_count"] = int(df[solar_col].isna().sum())
            if (solar < -1e-3).any():
                issues.append("Negative solar generation detected")

        if price_col in df.columns:
            price = df[price_col].dropna()
            metrics["price_min"] = float(price.min())
            metrics["price_max"] = float(price.max())
            metrics["price_nan_count"] = int(df[price_col].isna().sum())
            # Negative electricity prices happen in Germany (curtailment/surplus), but extreme bounds check:
            if (price < -500).any() or (price > 4000).any():
                issues.append("Electricity price out of normal physical market bounds (-500 to +4000 EUR/MWh)")

        metrics["issues"] = issues
        return len(issues) == 0, metrics
