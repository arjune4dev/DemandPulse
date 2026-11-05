
import streamlit as st
import pandas as pd
import plotly.express as px
from src.ui import setup_ui, page_header, section_header, plotly_theme

from src.predictor import df, FEATURE_COLUMNS
from src.feature_builder import get_seven_day_features

from src.explainability import (
    get_global_importance,
    plot_global_summary,
    explain_single_prediction,
    get_prediction_contributions
)


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

colors = setup_ui("DemandPulse | Explainability")
chart_theme = plotly_theme(colors)


# ============================================================
# 2. HEADER
# ============================================================

page_header(
    "Model explainability",
    "See which signals shape demand across the model and on a specific forecast day.",
    eyebrow="DEMANDPULSE / MODEL INSIGHTS",
)


# ============================================================
# 3. GLOBAL EXPLAINABILITY
# ============================================================

section_header("Global feature importance", "Explore the strongest drivers across historical open-store observations.")

st.write(
    "This section explains which features have the greatest "
    "influence across a representative sample of historical "
    "open-store observations."
)

if st.button("Generate Global Explanation", type="primary"):

    try:

        with st.spinner("Calculating global SHAP values..."):

            valid_rows = df.loc[
                (df["Open"] == 1)
                & df[FEATURE_COLUMNS].notna().all(axis=1),
                FEATURE_COLUMNS
            ]

            sample = valid_rows.sample(
                n=min(500, len(valid_rows)),
                random_state=42
            )

            importance_df = get_global_importance(
                sample,
                max_samples=500
            )

            st.session_state["global_importance"] = importance_df

            summary_fig = plot_global_summary(
                sample,
                max_samples=500
            )

            st.session_state["global_summary_fig"] = summary_fig

    except Exception as error:

        st.error(f"Global explanation failed: {error}")


if "global_importance" in st.session_state:

    importance_df = st.session_state["global_importance"]

    st.subheader("Top 20 Influential Features")

    top_features = importance_df.head(20).sort_values(
        "Mean Absolute SHAP",
        ascending=True
    )

    fig_importance = px.bar(
        top_features,
        x="Mean Absolute SHAP",
        y="Feature",
        orientation="h",
        title="Mean Absolute SHAP Values"
    )

    fig_importance.update_layout(
        **chart_theme,
        xaxis_title="Mean Absolute SHAP Value",
        yaxis_title="Feature",
        height=650
    )

    st.plotly_chart(
        fig_importance,
        use_container_width=True
    )

    st.subheader("SHAP Summary Plot")

    st.pyplot(
        st.session_state["global_summary_fig"],
        clear_figure=False
    )

    st.caption(
        "Higher mean absolute SHAP values indicate greater "
        "average influence on model predictions. They do not "
        "indicate whether a feature increases or decreases sales."
    )

    with st.expander("View feature importance table"):

        st.dataframe(
            importance_df.head(20),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 4. INDIVIDUAL FORECAST EXPLANATION
# ============================================================

st.markdown("---")

section_header("Explain an individual forecast", "Choose a store and forecast date to inspect the factors behind one prediction.")

st.write(
    "Choose a store and forecast origin. DemandPulse will "
    "generate seven-day features and explain the selected "
    "open day's prediction."
)


# ============================================================
# 5. FORECAST INPUTS
# ============================================================

available_stores = sorted(
    df["Store"].astype(int).unique().tolist()
)

col1, col2 = st.columns(2)

with col1:

    selected_store = st.selectbox(
        "Select Store",
        available_stores,
        key="explanation_store"
    )

with col2:

    selected_origin = st.date_input(
        "Forecast Origin",
        value=pd.Timestamp("2015-07-24").date(),
        min_value=pd.Timestamp("2013-01-01").date(),
        max_value=pd.Timestamp("2015-07-24").date(),
        key="explanation_origin"
    )


# ============================================================
# 6. GENERATE FEATURES FOR THE SELECTED STORE
# ============================================================

if st.button("Load Forecast Days"):

    try:

        with st.spinner("Preparing forecast features..."):

            forecast_df, X_forecast = get_seven_day_features(
                df,
                str(selected_store),
                selected_origin
            )

            open_mask = (
                forecast_df["Open"].eq(1).to_numpy()
            )

            open_positions = [
                i for i, is_open in enumerate(open_mask)
                if is_open
            ]

            if not open_positions:

                st.warning("No open days in this forecast window.")

            else:

                X_open = X_forecast.iloc[
                    open_positions
                ].copy()

                open_forecast = forecast_df.iloc[
                    open_positions
                ].copy()

                st.session_state["explain_forecast"] = open_forecast

                st.session_state["explain_features"] = X_open

                st.success(
                    f"Loaded {len(open_positions)} open forecast days."
                )

    except Exception as error:

        st.error(f"Unable to load forecast features: {error}")


# ============================================================
# 7. SELECT A DAY TO EXPLAIN
# ============================================================

if "explain_features" in st.session_state:

    X_open = st.session_state["explain_features"]

    open_forecast = st.session_state["explain_forecast"]

    date_options = [
        pd.Timestamp(value).strftime("%Y-%m-%d")
        for value in open_forecast["Date"]
    ]

    selected_day = st.selectbox(
        "Select a forecast day to explain",
        date_options
    )

    row_index = date_options.index(selected_day)

    st.divider()

    st.subheader(
        f"Explanation for {selected_day}"
    )

    # ----------------------------------------
    # MODEL PREDICTION
    # ----------------------------------------

    from src.predictor import pipeline

    selected_features = X_open.iloc[
        [row_index]
    ]

    predicted_sales = float(
        pipeline.predict(selected_features)[0]
    )

    st.metric(
        "Predicted Sales",
        f"₹{predicted_sales:,.2f}"
    )

    # ----------------------------------------
    # SHAP CONTRIBUTIONS
    # ----------------------------------------

    if st.button("Explain This Prediction", type="primary"):

        try:

            with st.spinner("Calculating individual SHAP values..."):

                contributions = get_prediction_contributions(
                    X_open,
                    row_index=row_index,
                    top_n=15
                )

                waterfall_fig = explain_single_prediction(
                    X_open,
                    row_index=row_index,
                    max_display=15
                )

                st.session_state["individual_contributions"] = (
                    contributions
                )

                st.session_state["individual_waterfall"] = (
                    waterfall_fig
                )

        except Exception as error:

            st.error(f"Individual explanation failed: {error}")


# ============================================================
# 8. DISPLAY INDIVIDUAL EXPLANATION
# ============================================================

if "individual_contributions" in st.session_state:

    contributions = st.session_state[
        "individual_contributions"
    ]

    st.subheader("Feature Contributions")

    fig_contributions = px.bar(
        contributions.sort_values(
            "SHAP Value",
            ascending=True
        ),
        x="SHAP Value",
        y="Feature",
        color="Impact",
        orientation="h",
        title="Features Increasing or Decreasing Prediction"
    )

    fig_contributions.update_layout(
        height=650,
        xaxis_title="SHAP Contribution",
        yaxis_title="Feature"
    )

    st.plotly_chart(
        fig_contributions,
        use_container_width=True
    )

    st.subheader("SHAP Waterfall Plot")

    st.pyplot(
        st.session_state["individual_waterfall"],
        clear_figure=False
    )

    st.subheader("Contribution Details")

    st.dataframe(
        contributions[
            [
                "Feature",
                "SHAP Value",
                "Impact"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Positive SHAP values push the prediction above the "
        "model's expected value. Negative values push it below."
    )


# ============================================================
# 9. FOOTER
# ============================================================

st.divider()

st.caption(
    "DemandPulse | SHAP Explainability | XGBoost"
)
