"""Build aligned processed datasets from raw Ember and OPSD sources."""

import logging
from pathlib import Path
import pandas as pd
import numpy as np

from data.loaders.ember_loader import EmberPriceLoader
from data.loaders.opsd_loader import OPSDEnergyLoader
from data.loaders.validator import DataValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def build_aligned_dataset(
    ember_path: str = "data/raw/ember/Germany.csv",
    opsd_path: str = "data/raw/opsd/time_series_60min_singleindex.csv",
    output_dir: str = "data/processed",
    start_date: str = "2015-01-01 00:00:00",
    end_date: str = "2020-09-30 23:00:00",
) -> pd.DataFrame:
    """Loads, validates, aligns, and saves processed energy datasets."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Load raw data
    ember_loader = EmberPriceLoader(ember_path)
    opsd_loader = OPSDEnergyLoader(opsd_path)

    df_price = ember_loader.load(start_date=start_date, end_date=end_date)
    df_energy = opsd_loader.load(start_date=start_date, end_date=end_date)

    logger.info(f"Loaded Ember prices: {len(df_price)} rows")
    logger.info(f"Loaded OPSD load/solar: {len(df_energy)} rows")

    # 2. Align timestamps via inner join on DatetimeIndex
    aligned_df = df_price.join(df_energy, how="inner")
    logger.info(f"Aligned dataset contains {len(aligned_df)} hourly timesteps")

    # 3. Add temporal features for agents and forecasting
    aligned_df["hour"] = aligned_df.index.hour
    aligned_df["day_of_week"] = aligned_df.index.dayofweek
    aligned_df["day_of_year"] = aligned_df.index.dayofyear
    aligned_df["is_weekend"] = (aligned_df["day_of_week"] >= 5).astype(int)

    # Cyclical hour encoding (useful for ML forecasters)
    aligned_df["hour_sin"] = np.sin(2 * np.pi * aligned_df["hour"] / 24.0)
    aligned_df["hour_cos"] = np.cos(2 * np.pi * aligned_df["hour"] / 24.0)

    # 4. Normalized profiles for IEEE 33-bus scaling
    # Normalizing German load: L_t / L_ref (where reference load is the 95th percentile or mean reference)
    ref_load = float(aligned_df["germany_load_mw"].quantile(0.95))
    ref_solar = float(aligned_df["germany_solar_mw"].quantile(0.999))

    aligned_df["normalized_load_profile"] = (aligned_df["germany_load_mw"] / ref_load).clip(0.1, 1.5)
    aligned_df["normalized_solar_profile"] = (aligned_df["germany_solar_mw"] / ref_solar).clip(0.0, 1.2)

    # Price normalization (standard score and min-max)
    p_mean = aligned_df["price_eur_mwh"].mean()
    p_std = aligned_df["price_eur_mwh"].std()
    aligned_df["price_zscore"] = (aligned_df["price_eur_mwh"] - p_mean) / (p_std + 1e-6)

    # 5. Validation check
    val_ok, report = DataValidator.validate_energy_ranges(
        aligned_df,
        load_col="germany_load_mw",
        solar_col="germany_solar_mw",
        price_col="price_eur_mwh"
    )
    logger.info(f"Validation report: {report}")
    if not val_ok:
        logger.warning(f"Validation issues found: {report.get('issues')}")

    # 6. Save individual and master processed datasets
    aligned_file = out_path / "aligned_energy_data.csv"
    price_file = out_path / "germany_price.csv"
    load_file = out_path / "germany_load.csv"
    solar_file = out_path / "germany_solar.csv"

    aligned_df.to_csv(aligned_file)
    aligned_df[["price_eur_mwh", "price_zscore"]].to_csv(price_file)
    aligned_df[["germany_load_mw", "normalized_load_profile"]].to_csv(load_file)
    aligned_df[["germany_solar_mw", "normalized_solar_profile"]].to_csv(solar_file)

    logger.info(f"Saved master aligned dataset to {aligned_file}")
    logger.info(f"Saved component datasets to {price_file}, {load_file}, {solar_file}")
    return aligned_df


if __name__ == "__main__":
    build_aligned_dataset()
