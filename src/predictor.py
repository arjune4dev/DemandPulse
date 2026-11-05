
from pathlib import Path

import joblib
import pandas as pd
import numpy as np

from src.feature_builder import (
    load_data,
    build_features,
    get_seven_day_features,
    FEATURE_COLUMNS
)


# ==================================================
# 1. PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "demandpulse_pipeline.pkl"
)


# ==================================================
# 2. LOAD MODEL AND DATA
# ==================================================

print("Loading DemandPulse model...")

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}"
    )

pipeline = joblib.load(MODEL_PATH)

print("Model loaded successfully!")


print("Loading Rossmann dataset...")

try:
    raw_df = load_data()
    print("Generating historical features...")
    df = build_features(raw_df)
    print("Feature generation completed!")
except FileNotFoundError:
    # Keep the web app available so a first-time deployment can accept
    # the local Rossmann CSVs through its setup screen.
    df = None
    print("Rossmann data is not installed yet.")


def _ensure_dataset_loaded():
    global df
    if df is None:
        raw_df = load_data()
        df = build_features(raw_df)
    return df


# ==================================================
# 3. SEVEN-DAY PREDICTION FUNCTION
# ==================================================

def predict_seven_days(store_id, origin_date):

    try:
        forecast_data = _ensure_dataset_loaded()
    except FileNotFoundError as error:
        raise ValueError(
            "Rossmann data is missing. Upload train.csv and store.csv "
            "from the DemandPulse dashboard first."
        ) from error

    store_id = str(store_id)

    origin_date = pd.Timestamp(origin_date)

    # Prepare seven-day forecast features

    forecast_df, X_forecast = get_seven_day_features(
        forecast_data,
        store_id,
        origin_date
    )

    # Initialize predictions

    predictions = np.zeros(len(forecast_df))

    # Only predict for open days

    open_mask = (
        forecast_df["Open"].eq(1).to_numpy()
    )

    X_open = X_forecast.loc[open_mask]

    if len(X_open) > 0:

        open_predictions = pipeline.predict(X_open)

        predictions[open_mask] = open_predictions

    # Build results

    results = []

    for i in range(len(forecast_df)):

        row = forecast_df.iloc[i]

        results.append({

            "date": row["Date"].strftime("%Y-%m-%d"),

            "store_id": int(store_id),

            "open": int(row["Open"]),

            "predicted_sales": round(
                float(predictions[i]), 2
            )

        })

    return results


# ==================================================
# 4. HEALTH CHECK
# ==================================================

def model_status():

    return {
        "model_loaded": pipeline is not None,
        "dataset_loaded": df is not None,
        "number_of_features": len(FEATURE_COLUMNS)
    }
