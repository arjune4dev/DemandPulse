
from pathlib import Path

import pandas as pd
import numpy as np
import joblib


# ==================================================
# 1. PATHS AND CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAIN_PATH = PROJECT_ROOT / "data" / "raw" / "train.csv"
STORE_PATH = PROJECT_ROOT / "data" / "raw" / "store.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "demandpulse_pipeline.pkl"


CATEGORICAL_FEATURES = [
    "Store",
    "DayOfWeek",
    "StateHoliday",
    "StoreType",
    "Assortment",
    "PromoInterval"
]

NUMERICAL_FEATURES = [
    "Promo",
    "SchoolHoliday",
    "Year",
    "Month",
    "Day",
    "WeekOfYear",
    "CompetitionDistance",
    "CompetitionOpenSinceMonth",
    "CompetitionOpenSinceYear",
    "Promo2",
    "Promo2SinceWeek",
    "Promo2SinceYear",
    "Sales_lag_7",
    "Sales_lag_14",
    "Sales_lag_28",
    "Sales_rolling_mean_7",
    "Sales_rolling_mean_14",
    "Sales_rolling_mean_28",
    "CompetitionMonthMissing",
    "CompetitionYearMissing",
    "CompetitionDistanceMissing"
]

FEATURE_COLUMNS = (
    CATEGORICAL_FEATURES + NUMERICAL_FEATURES
)


# ==================================================
# 2. LOAD AND MERGE DATA
# ==================================================

def load_data():

    train = pd.read_csv(
        TRAIN_PATH,
        low_memory=False
    )

    store = pd.read_csv(STORE_PATH)

    train["Date"] = pd.to_datetime(train["Date"])

    df = train.merge(
        store,
        on="Store",
        how="left",
        validate="many_to_one"
    )

    df = df.sort_values(
        ["Store", "Date"]
    ).reset_index(drop=True)

    return df


# ==================================================
# 3. GENERATE LAG FEATURES
# ==================================================

def add_lag_features(df):

    history = df[
        ["Store", "Date", "Sales"]
    ].copy()

    for lag in [7, 14, 28]:

        lag_data = history.copy()

        lag_data["Date"] = (
            lag_data["Date"]
            + pd.Timedelta(days=lag)
        )

        lag_data = lag_data.rename(
            columns={
                "Sales": f"Sales_lag_{lag}"
            }
        )

        df = df.merge(
            lag_data,
            on=["Store", "Date"],
            how="left",
            validate="one_to_one"
        )

    return df


# ==================================================
# 4. GENERATE ROLLING FEATURES
# ==================================================

def add_rolling_features(df):

    history = df[
        ["Store", "Date", "Sales"]
    ].copy()

    history = history.set_index(
        ["Store", "Date"]
    ).sort_index()

    for window in [7, 14, 28]:

        rolling_values = []

        for lag in range(7, 7 + window):

            historical_dates = pd.MultiIndex.from_arrays(
                [
                    df["Store"],
                    df["Date"] - pd.Timedelta(days=lag)
                ],
                names=["Store", "Date"]
            )

            values = history.reindex(
                historical_dates
            )["Sales"]

            rolling_values.append(
                values.to_numpy()
            )

        rolling_array = np.column_stack(
            rolling_values
        )

        df[f"Sales_rolling_mean_{window}"] = np.where(
            ~np.isnan(rolling_array).any(axis=1),
            np.mean(rolling_array, axis=1),
            np.nan
        )

    return df


# ==================================================
# 5. CALENDAR FEATURES
# ==================================================

def add_calendar_features(df):

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day

    df["WeekOfYear"] = (
        df["Date"]
        .dt.isocalendar()
        .week.astype(int)
    )

    return df


# ==================================================
# 6. HANDLE MISSING VALUES
# ==================================================

def clean_features(df):

    df["CompetitionMonthMissing"] = (
        df["CompetitionOpenSinceMonth"]
        .isna()
        .astype(int)
    )

    df["CompetitionYearMissing"] = (
        df["CompetitionOpenSinceYear"]
        .isna()
        .astype(int)
    )

    df["CompetitionDistanceMissing"] = (
        df["CompetitionDistance"]
        .isna()
        .astype(int)
    )

    df["CompetitionOpenSinceMonth"] = (
        df["CompetitionOpenSinceMonth"].fillna(0)
    )

    df["CompetitionOpenSinceYear"] = (
        df["CompetitionOpenSinceYear"].fillna(0)
    )

    df["Promo2SinceYear"] = (
        df["Promo2SinceYear"].fillna(0)
    )

    df["Promo2SinceWeek"] = (
        df["Promo2SinceWeek"].fillna(0)
    )

    df["PromoInterval"] = (
        df["PromoInterval"].fillna("None")
    )

    for col in CATEGORICAL_FEATURES:

        df[col] = df[col].astype(str)

    return df


# ==================================================
# 7. COMPLETE FEATURE ENGINEERING
# ==================================================

def build_features(df):

    df = df.copy()

    df = add_lag_features(df)

    df = add_rolling_features(df)

    df = add_calendar_features(df)

    df = clean_features(df)

    return df


# ==================================================
# 8. PREPARE MODEL INPUT
# ==================================================

def prepare_model_features(df):

    missing_columns = [
        col for col in FEATURE_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing model features: {missing_columns}"
        )

    return df[FEATURE_COLUMNS].copy()


# ==================================================
# 9. FIND LATEST VALID FORECAST ORIGIN
# ==================================================

def find_latest_valid_origin(df, store_id):

    store_id = str(store_id)

    store_data = df[
        df["Store"] == store_id
    ]

    if store_data.empty:

        raise ValueError(
            f"Store {store_id} does not exist."
        )

    available_dates = set(
        store_data["Date"]
    )

    min_date = store_data["Date"].min()
    max_date = store_data["Date"].max()

    latest_possible_origin = (
        max_date - pd.Timedelta(days=7)
    )

    for origin in pd.date_range(
        start=min_date,
        end=latest_possible_origin,
        freq="D"
    )[::-1]:

        forecast_dates = pd.date_range(
            start=origin + pd.Timedelta(days=1),
            periods=7,
            freq="D"
        )

        if all(
            date in available_dates
            for date in forecast_dates
        ):

            return origin

    raise ValueError(
        f"No complete seven-day forecast window found "
        f"for Store {store_id}."
    )


# ==================================================
# 10. PREPARE SEVEN-DAY FORECAST FEATURES
# ==================================================

def get_seven_day_features(
    df,
    store_id,
    origin_date
):

    store_id = str(store_id)

    origin_date = pd.Timestamp(origin_date)

    forecast_dates = pd.date_range(
        start=origin_date + pd.Timedelta(days=1),
        periods=7,
        freq="D"
    )

    store_data = df[
        df["Store"] == store_id
    ]

    available_dates = set(
        store_data["Date"]
    )

    missing_dates = [
        date for date in forecast_dates
        if date not in available_dates
    ]

    if missing_dates:

        raise ValueError(
            f"Missing calendar records for Store {store_id}: "
            f"{missing_dates}"
        )

    forecast_df = store_data[
        store_data["Date"].isin(forecast_dates)
    ].copy()

    forecast_df = forecast_df.sort_values(
        "Date"
    ).reset_index(drop=True)

    X_forecast = prepare_model_features(
        forecast_df
    )

    return forecast_df, X_forecast


# ==================================================
# 11. LOAD SAVED MODEL
# ==================================================

def load_model():

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}"
        )

    pipeline = joblib.load(MODEL_PATH)

    return pipeline


# ==================================================
# 12. GENERATE SEVEN-DAY PREDICTIONS
# ==================================================

def predict_seven_days(
    pipeline,
    forecast_df,
    X_forecast
):

    predictions = np.zeros(len(forecast_df))

    open_mask = (
        forecast_df["Open"].eq(1).to_numpy()
    )

    X_open = X_forecast.loc[open_mask]

    if len(X_open) > 0:

        open_predictions = pipeline.predict(X_open)

        predictions[open_mask] = open_predictions

    result = pd.DataFrame({

        "Date": forecast_df["Date"],

        "Open": forecast_df["Open"],

        "Actual_Sales": forecast_df["Sales"],

        "Predicted_Sales": np.round(predictions, 2)

    })

    result["Absolute_Error"] = np.round(
        np.abs(
            result["Actual_Sales"]
            - result["Predicted_Sales"]
        ),
        2
    )

    return result


# ==================================================
# 13. MAIN EXECUTION
# ==================================================

if __name__ == "__main__":

    print("\nLoading datasets...")

    df = load_data()

    print("Original dataset shape:", df.shape)

    print("\nGenerating historical features...")

    df = build_features(df)

    print("Feature engineering completed!")

    print("Updated dataset shape:", df.shape)

    # Select store
    store_id = 1

    # Find a valid historical forecast window
    origin_date = find_latest_valid_origin(
        df,
        store_id
    )

    print("\nForecast origin:", origin_date.date())

    # Prepare features
    forecast_df, X_forecast = get_seven_day_features(
        df,
        store_id,
        origin_date
    )

    print("\nModel input shape:", X_forecast.shape)

    print("\nLoading trained XGBoost pipeline...")

    pipeline = load_model()

    print("Model loaded successfully!")

    # Generate predictions
    print("\nGenerating seven-day predictions...")

    forecast_results = predict_seven_days(
        pipeline,
        forecast_df,
        X_forecast
    )

    print("\nSEVEN-DAY SALES FORECAST")

    print(
        forecast_results.to_string(index=False)
    )

    # Calculate metrics for this seven-day replay
    open_results = forecast_results[
        forecast_results["Open"] == 1
    ]

    if not open_results.empty:

        mae = np.mean(
            open_results["Absolute_Error"]
        )

        wape = (
            open_results["Absolute_Error"].sum()
            / open_results["Actual_Sales"].sum()
        ) * 100

        print("\nSeven-day replay metrics (open days only):")

        print(f"MAE: {mae:.2f}")

        print(f"WAPE: {wape:.2f}%")

    # Save forecast
    output_path = (
        PROJECT_ROOT
        / "reports"
        / "seven_day_forecast.csv"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    forecast_results.to_csv(
        output_path,
        index=False
    )

    print("\nForecast saved to:", output_path)

    print("\nDemandPulse prediction completed!")
