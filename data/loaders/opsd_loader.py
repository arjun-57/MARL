"""Loader for Open Power System Data (OPSD) Hourly Time Series."""

import logging
from pathlib import Path
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


class OPSDEnergyLoader:
    """Loads and cleans German load and solar generation from OPSD."""

    def __init__(self, file_path: str = "data/raw/opsd/time_series_60min_singleindex.csv"):
        self.file_path = Path(file_path)

    def load(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Loads OPSD data with actual German demand and actual solar generation."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"OPSD dataset not found at {self.file_path}")

        logger.info(f"Loading OPSD energy data from {self.file_path}")
        target_cols = [
            "utc_timestamp",
            "DE_load_actual_entsoe_transparency",
            "DE_solar_generation_actual"
        ]

        df = pd.read_csv(self.file_path, usecols=target_cols)

        # Rename and parse timestamps
        df.rename(
            columns={
                "utc_timestamp": "timestamp",
                "DE_load_actual_entsoe_transparency": "germany_load_mw",
                "DE_solar_generation_actual": "germany_solar_mw"
            },
            inplace=True
        )

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df.drop_duplicates(subset=["timestamp"], inplace=True)
        df.sort_values("timestamp", inplace=True)
        df.set_index("timestamp", inplace=True)

        if start_date:
            df = df.loc[df.index >= pd.to_datetime(start_date, utc=True)]
        if end_date:
            df = df.loc[df.index <= pd.to_datetime(end_date, utc=True)]

        # Interpolate small missing values
        for col in ["germany_load_mw", "germany_solar_mw"]:
            if df[col].isna().any():
                n_miss = df[col].isna().sum()
                logger.warning(f"Interpolating {n_miss} missing values in {col}")
                df[col] = df[col].interpolate(method="time").bfill().ffill()

        # Physical floor: Solar can't be negative
        df["germany_solar_mw"] = df["germany_solar_mw"].clip(lower=0.0)

        return df
