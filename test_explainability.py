
import pandas as pd

from src.predictor import df, FEATURE_COLUMNS

from src.explainability import (
    get_global_importance,
    plot_global_summary,
    explain_single_prediction,
    get_prediction_contributions
)


# Select open historical rows with available features
sample = df.loc[
    (df["Open"] == 1)
    & df[FEATURE_COLUMNS].notna().all(axis=1),
    FEATURE_COLUMNS
].sample(
    n=200,
    random_state=42
)


# Global feature importance
importance = get_global_importance(sample)

print("\nTOP 15 IMPORTANT FEATURES")

print(importance.head(15).to_string(index=False))


# Individual prediction contributions
print("\nINDIVIDUAL PREDICTION EXPLANATION")

contributions = get_prediction_contributions(
    sample,
    row_index=0,
    top_n=10
)

print(contributions.to_string(index=False))


# Global SHAP plot
fig1 = plot_global_summary(sample)

fig1.savefig(
    "reports/shap_summary.png",
    dpi=200,
    bbox_inches="tight"
)


# Individual SHAP waterfall plot
fig2 = explain_single_prediction(
    sample,
    row_index=0
)

fig2.savefig(
    "reports/shap_individual.png",
    dpi=200,
    bbox_inches="tight"
)

print("\nSHAP testing completed successfully!")
