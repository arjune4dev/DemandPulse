
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from src.ui import setup_ui, page_header, section_header, plotly_theme

from src.monitoring import LOG_PATH


colors = setup_ui("DemandPulse | Monitoring")
chart_theme = plotly_theme(colors)
page_header(
    "Model monitoring",
    "Track prediction activity, evaluate observed forecasts and inspect error patterns.",
    eyebrow="DEMANDPULSE / MODEL HEALTH",
)


# --------------------------------------------------
# LOAD PREDICTION LOGS
# --------------------------------------------------

@st.cache_data(ttl=10)
def load_logs():
    if not Path(LOG_PATH).exists():
        return pd.DataFrame()

    data = pd.read_csv(LOG_PATH)

    if data.empty:
        return data

    data["forecast_date"] = pd.to_datetime(
        data["forecast_date"],
        errors="coerce"
    )

    data["forecast_generated_at"] = pd.to_datetime(
        data["forecast_generated_at"],
        errors="coerce"
    )

    data["store_id"] = pd.to_numeric(
        data["store_id"],
        errors="coerce"
    )

    data["predicted_sales"] = pd.to_numeric(
        data["predicted_sales"],
        errors="coerce"
    )

    data["actual_sales"] = pd.to_numeric(
        data["actual_sales"],
        errors="coerce"
    )

    data["is_open"] = pd.to_numeric(
        data["is_open"],
        errors="coerce"
    )

    return data


if st.button("Refresh Monitoring Data"):
    st.cache_data.clear()
    st.rerun()


logs = load_logs()


if logs.empty:
    st.warning(
        "No prediction logs found. Generate a forecast "
        "using the API first."
    )
    st.stop()


# --------------------------------------------------
# PREPARE DATA
# --------------------------------------------------

evaluated = logs.dropna(
    subset=["actual_sales", "predicted_sales"]
).copy()

errors = (
    evaluated["actual_sales"]
    - evaluated["predicted_sales"]
)

if not evaluated.empty:
    evaluated["absolute_error"] = errors.abs()
    evaluated["squared_error"] = errors ** 2


# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------

total_predictions = len(logs)

evaluated_count = len(evaluated)

pending_count = logs["actual_sales"].isna().sum()

if evaluated_count > 0:
    mae = evaluated["absolute_error"].mean()

    rmse = np.sqrt(
        evaluated["squared_error"].mean()
    )

    total_actual = evaluated["actual_sales"].sum()

    wape = (
        evaluated["absolute_error"].sum()
        / total_actual * 100
        if total_actual != 0
        else np.nan
    )
else:
    mae = np.nan
    rmse = np.nan
    wape = np.nan


section_header("Monitoring overview", "Current activity and evaluation metrics from the prediction log.")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Predictions",
    f"{total_predictions:,}"
)

col2.metric(
    "Evaluated Predictions",
    f"{evaluated_count:,}"
)

col3.metric(
    "Pending Actuals",
    f"{pending_count:,}"
)

col4.metric(
    "MAE",
    f"{mae:,.2f}" if pd.notna(mae) else "N/A"
)


col5, col6 = st.columns(2)

col5.metric(
    "RMSE",
    f"{rmse:,.2f}" if pd.notna(rmse) else "N/A"
)

col6.metric(
    "WAPE",
    f"{wape:.2f}%" if pd.notna(wape) else "N/A"
)


st.divider()


# --------------------------------------------------
# DATA QUALITY NOTICE
# --------------------------------------------------

st.subheader("Evaluation Data Quality")

st.info(
    "The current prediction log may contain synthetic test "
    "records from test_monitoring.py alongside API-generated "
    "forecasts. These records are not yet separately labelled. "
    "Therefore, the metrics below are descriptive of the log "
    "contents and should not be presented as production model "
    "performance."
)


# --------------------------------------------------
# ACTUAL VS PREDICTED
# --------------------------------------------------

st.subheader("Actual vs Predicted Sales")

if evaluated.empty:
    st.info(
        "No evaluated predictions available yet. "
        "Add actual sales to the prediction log to see this chart."
    )
else:
    comparison = evaluated.sort_values("forecast_date")

    fig = px.line(
        comparison,
        x="forecast_date",
        y=["actual_sales", "predicted_sales"],
        markers=True,
        title="Actual Sales vs Predicted Sales",
        labels={
            "forecast_date": "Forecast Date",
            "value": "Sales",
            "variable": "Metric",
        },
    )
    fig.update_layout(**chart_theme, height=360)

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# --------------------------------------------------
# ERROR ANALYSIS
# --------------------------------------------------

st.subheader("Prediction Error Analysis")

if evaluated.empty:
    st.info("Error analysis will appear once actual sales are available.")
else:
    error_col1, error_col2 = st.columns(2)

    with error_col1:
        fig_error = px.bar(
            evaluated.sort_values("forecast_date"),
            x="forecast_date",
            y="absolute_error",
            title="Absolute Prediction Error",
            labels={
                "forecast_date": "Forecast Date",
                "absolute_error": "Absolute Error",
            },
        )
        fig_error.update_layout(**chart_theme, height=340)

        st.plotly_chart(
            fig_error,
            use_container_width=True
        )

    with error_col2:
        fig_scatter = px.scatter(
            evaluated,
            x="actual_sales",
            y="predicted_sales",
            title="Predicted vs Actual Relationship",
            labels={
                "actual_sales": "Actual Sales",
                "predicted_sales": "Predicted Sales",
            },
        )
        fig_scatter.update_layout(**chart_theme, height=340)

        st.plotly_chart(
            fig_scatter,
            use_container_width=True
        )


# --------------------------------------------------
# STORE-WISE PERFORMANCE
# --------------------------------------------------

st.subheader("Store-wise Performance")

if evaluated.empty:
    st.info("Store-wise metrics require actual sales.")
else:
    store_metrics = (
        evaluated.groupby("store_id")
        .apply(
            lambda group: pd.Series({
                "Evaluated Predictions": len(group),
                "MAE": (
                    group["actual_sales"]
                    - group["predicted_sales"]
                ).abs().mean(),
                "WAPE": (
                    (
                        group["actual_sales"]
                        - group["predicted_sales"]
                    ).abs().sum()
                    / group["actual_sales"].sum() * 100
                    if group["actual_sales"].sum() != 0
                    else np.nan
                ),
            }),
            include_groups=False,
        )
        .reset_index()
    )

    st.dataframe(
        store_metrics.round(2),
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# PREDICTION HISTORY
# --------------------------------------------------

st.subheader("Prediction History")

store_options = sorted(
    logs["store_id"].dropna().unique().tolist()
)

selected_store = st.selectbox(
    "Filter by Store",
    ["All Stores"] + store_options,
)

filtered_logs = logs.copy()

if selected_store != "All Stores":
    filtered_logs = filtered_logs[
        filtered_logs["store_id"] == selected_store
    ]


st.dataframe(
    filtered_logs.sort_values(
        "forecast_generated_at",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True,
)


# --------------------------------------------------
# DOWNLOAD REPORT
# --------------------------------------------------

st.subheader("Export Monitoring Report")

csv_data = filtered_logs.to_csv(index=False)

st.download_button(
    label="Download Monitoring CSV",
    data=csv_data,
    file_name="demandpulse_monitoring_report.csv",
    mime="text/csv",
)

st.caption(
    "DemandPulse | Store-level sales forecasting "
    "and model monitoring"
)
