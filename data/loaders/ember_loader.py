"""Loader for Ember Day-Ahead Electricity Wholesale Prices."""

import logging
from pathlib import Path
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


class EmberPriceLoader:
    """Loads and cleans Ember hourly German day-ahead electricity prices."""

    def __init__(self, file_path: str = "data/raw/ember/Germany.csv"):
        self.file_path = Path(file_path)

    def load(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Loads price data, enforces UTC DatetimeIndex, and cleans duplicates/nans."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Ember dataset not found at {self.file_path}")

        logger.info(f"Loading Ember price data from {self.file_path}")
        df = pd.read_csv(self.file_path)

        # Parse UTC timestamp
        df["timestamp"] = pd.to_datetime(df["Datetime (UTC)"], utc=True)
        df["price_eur_mwh"] = pd.to_numeric(df["Price (EUR/MWhe)"], errors="coerce")

        # Keep relevant columns and sort
        df = df[["timestamp", "price_eur_mwh"]].drop_duplicates(subset=["timestamp"]).sort_values("timestamp")

        # Set index
        df.set_index("timestamp", inplace=True)

        # Filter by date if specified
        if start_date:
            df = df.loc[df.index >= pd.to_datetime(start_date, utc=True)]
        if end_date:
            df = df.loc[df.index <= pd.to_datetime(end_date, utc=True)]

        # Handle missing prices via time interpolation
        if df["price_eur_mwh"].isna().any():
            missing = df["price_eur_mwh"].isna().sum()
            logger.warning(f"Interpolating {missing} missing price values")
            df["price_eur_mwh"] = df["price_eur_mwh"].interpolate(method="time").bfill().ffill()

        return df
