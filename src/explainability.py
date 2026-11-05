
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt

from scipy import sparse


# ============================================================
# 1. LOAD TRAINED PIPELINE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = PROJECT_ROOT / "models" / "demandpulse_pipeline.pkl"

pipeline = joblib.load(MODEL_PATH)

preprocessor = pipeline.named_steps["preprocessor"]
model = pipeline.named_steps["model"]


# ============================================================
# 2. GET FEATURE NAMES AFTER PREPROCESSING
# ============================================================

FEATURE_NAMES = preprocessor.get_feature_names_out()


# ============================================================
# 3. CREATE SHAP EXPLAINER
# ============================================================

explainer = shap.TreeExplainer(model)


# ============================================================
# 4. PREPARE INPUT DATA
# ============================================================

def prepare_features(features):

    if not isinstance(features, pd.DataFrame):
        features = pd.DataFrame(features)

    missing_columns = [
        col for col in preprocessor.feature_names_in_
        if col not in features.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing model features: {missing_columns}"
        )

    features = features[
        preprocessor.feature_names_in_
    ].copy()

    transformed = preprocessor.transform(features)

    if sparse.issparse(transformed):
        transformed = transformed.toarray()

    return transformed


# ============================================================
# 5. CALCULATE SHAP VALUES
# ============================================================

def calculate_shap_values(features):

    transformed = prepare_features(features)

    shap_values = explainer(
        transformed,
        check_additivity=False
    )

    return shap_values


# ============================================================
# 6. GLOBAL FEATURE IMPORTANCE
# ============================================================

def get_global_importance(
    features,
    max_samples=500
):

    sample = features.sample(
        n=min(len(features), max_samples),
        random_state=42
    )

    shap_values = calculate_shap_values(sample)

    importance = np.abs(
        shap_values.values
    ).mean(axis=0)

    importance_df = pd.DataFrame({
        "Feature": FEATURE_NAMES,
        "Mean Absolute SHAP": importance
    })

    importance_df = importance_df.sort_values(
        "Mean Absolute SHAP",
        ascending=False
    )

    return importance_df


# ============================================================
# 7. GLOBAL SHAP SUMMARY PLOT
# ============================================================

def plot_global_summary(
    features,
    max_samples=500
):

    sample = features.sample(
        n=min(len(features), max_samples),
        random_state=42
    )

    shap_values = calculate_shap_values(sample)

    fig, ax = plt.subplots(figsize=(11, 8))

    shap.plots.beeswarm(
        shap_values,
        max_display=20,
        show=False
    )

    fig = plt.gcf()

    plt.tight_layout()

    return fig


# ============================================================
# 8. INDIVIDUAL PREDICTION EXPLANATION
# ============================================================

def explain_single_prediction(
    features,
    row_index=0,
    max_display=15
):

    if row_index < 0 or row_index >= len(features):
        raise IndexError("Invalid row index.")

    single_row = features.iloc[
        [row_index]
    ].copy()

    shap_values = calculate_shap_values(
        single_row
    )

    explanation = shap_values[0]

    fig = plt.figure(figsize=(11, 7))

    shap.plots.waterfall(
        explanation,
        max_display=max_display,
        show=False
    )

    plt.tight_layout()

    return fig


# ============================================================
# 9. TOP POSITIVE AND NEGATIVE CONTRIBUTIONS
# ============================================================

def get_prediction_contributions(
    features,
    row_index=0,
    top_n=10
):

    if row_index < 0 or row_index >= len(features):
        raise IndexError("Invalid row index.")

    single_row = features.iloc[
        [row_index]
    ].copy()

    shap_values = calculate_shap_values(
        single_row
    )

    values = shap_values.values[0]

    contributions = pd.DataFrame({
        "Feature": FEATURE_NAMES,
        "SHAP Value": values
    })

    contributions["Impact"] = np.where(
        contributions["SHAP Value"] > 0,
        "Increases prediction",
        "Decreases prediction"
    )

    contributions["Absolute Impact"] = (
        contributions["SHAP Value"].abs()
    )

    contributions = contributions.sort_values(
        "Absolute Impact",
        ascending=False
    )

    return contributions.head(top_n)


# ============================================================
# 10. MODEL EXPLANATION SUMMARY
# ============================================================

def get_model_explanation(features):

    importance_df = get_global_importance(
        features
    )

    return {
        "model": "XGBoost",
        "explainer": "SHAP TreeExplainer",
        "number_of_features": len(FEATURE_NAMES),
        "top_features": importance_df.head(10)
    }


print("DemandPulse SHAP Explainability loaded successfully!")
print("Model:", type(model).__name__)
print("Encoded features:", len(FEATURE_NAMES))
