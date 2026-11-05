
from pathlib import Path
import os

import numpy as np
import pandas as pd


REPORTS_DIR = Path(
    os.environ.get("DEMANDPULSE_REPORTS_DIR", "reports")
)
LOG_PATH = REPORTS_DIR / "prediction_logs.csv"

LOG_COLUMNS = [
    "forecast_generated_at",
    "store_id",
    "forecast_date",
    "is_open",
    "predicted_sales",
    "actual_sales",
]


def log_predictions(predictions):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    generated_at = pd.Timestamp.now()

    for prediction in predictions:
        rows.append({
            "forecast_generated_at": generated_at,
            "store_id": prediction["store_id"],
            "forecast_date": prediction["date"],
            "is_open": prediction["open"],
            "predicted_sales": prediction["predicted_sales"],
            "actual_sales": np.nan,
        })

    new_logs = pd.DataFrame(rows, columns=LOG_COLUMNS)

    if LOG_PATH.exists():
        existing_logs = pd.read_csv(LOG_PATH)
        updated_logs = pd.concat(
            [existing_logs, new_logs],
            ignore_index=True
        )
    else:
        updated_logs = new_logs

    updated_logs.to_csv(LOG_PATH, index=False)

    return updated_logs


def update_actual_sales(actual_data):
    if not LOG_PATH.exists():
        raise FileNotFoundError("Prediction log does not exist.")

    logs = pd.read_csv(LOG_PATH)

    actual_data = actual_data.copy()

    actual_data["forecast_date"] = pd.to_datetime(
        actual_data["forecast_date"]
    )

    logs["forecast_date"] = pd.to_datetime(
        logs["forecast_date"]
    )

    logs["store_id"] = logs["store_id"].astype(int)
    actual_data["store_id"] = actual_data["store_id"].astype(int)

    actual_lookup = actual_data.set_index(
        ["store_id", "forecast_date"]
    )["actual_sales"]

    for index, row in logs.iterrows():
        key = (row["store_id"], row["forecast_date"])

        if key in actual_lookup.index:
            logs.loc[index, "actual_sales"] = actual_lookup.loc[key]

    logs.to_csv(LOG_PATH, index=False)

    return logs


def calculate_monitoring_metrics():
    if not LOG_PATH.exists():
        raise FileNotFoundError("Prediction log does not exist.")

    logs = pd.read_csv(LOG_PATH)

    evaluated = logs.dropna(
        subset=["actual_sales", "predicted_sales"]
    )

    if evaluated.empty:
        raise ValueError("No actual sales available for evaluation.")

    errors = (
        evaluated["actual_sales"] - evaluated["predicted_sales"]
    )

    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors ** 2))

    total_actual = evaluated["actual_sales"].sum()

    wape = (
        np.sum(np.abs(errors)) / total_actual * 100
        if total_actual != 0
        else np.nan
    )

    return {
        "evaluated_predictions": len(evaluated),
        "MAE": round(float(mae), 2),
        "RMSE": round(float(rmse), 2),
        "WAPE": round(float(wape), 2),
    }
