from datetime import date
import importlib

import pandas as pd
import plotly.express as px
import streamlit as st

from src.predictor import predict_seven_days, df
import src.predictor as predictor_module
from src.feature_builder import TRAIN_PATH, STORE_PATH
from src.inventory import simulate_inventory_risk
from src.ui import setup_ui, page_header, section_header, plotly_theme


# ------------------------------------------------------------
# PAGE SETUP
# ------------------------------------------------------------

colors = setup_ui("DemandPulse | Overview")
chart_theme = plotly_theme(colors)


# First-run setup for deployments where the source data is kept off GitHub.
if df is None:
    page_header(
        "Set up your workspace",
        "Add the Rossmann source files once to unlock forecasts, explainability, and monitoring.",
        eyebrow="DEMANDPULSE / DATA SETUP",
    )
    st.markdown(
        """
        <div class="dp-next-step">
          <span class="dp-next-step-icon">↥</span>
          <div><strong>Your data stays with this deployment</strong><br><span>Both CSV files are saved to the app’s data volume and aren’t added to the GitHub repository.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")
    upload_col, details_col = st.columns([1.2, 0.8], gap="large")
    with upload_col:
        uploaded_train = st.file_uploader(
            "Rossmann train.csv",
            type=["csv"],
            help="The historical store sales data used to build the forecasting features.",
        )
        uploaded_store = st.file_uploader(
            "Rossmann store.csv",
            type=["csv"],
            help="Store metadata used by the forecasting model.",
        )
        if st.button(
            "Save data and prepare workspace",
            type="primary",
            use_container_width=True,
            disabled=not (uploaded_train and uploaded_store),
        ):
            try:
                with st.spinner("Saving files and preparing store features…"):
                    TRAIN_PATH.parent.mkdir(parents=True, exist_ok=True)
                    TRAIN_PATH.write_bytes(uploaded_train.getvalue())
                    STORE_PATH.write_bytes(uploaded_store.getvalue())
                    importlib.reload(predictor_module)
                st.success("Data loaded. Opening your forecast workspace…")
                st.rerun()
            except Exception as error:
                st.error(f"Unable to prepare the data: {error}")
    with details_col:
        st.markdown(
            f"""
            <div class="dp-card dp-setup-card">
              <div class="dp-card-top"><span class="dp-card-icon">i</span><span class="dp-card-label">BEFORE YOU UPLOAD</span></div>
              <div class="dp-card-value">Two files, one time</div>
              <div class="dp-card-foot">Use the Rossmann Store Sales <code>train.csv</code> and <code>store.csv</code> files. Keep their original column headers.</div>
              <div class="dp-card-meta">SAVED TO <span>{TRAIN_PATH.parent}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.stop()


# ------------------------------------------------------------
# SIDEBAR CONFIGURATION
# ------------------------------------------------------------

st.sidebar.markdown("---")
st.sidebar.markdown("### Forecast configuration")

available_stores = sorted(df["Store"].astype(int).unique().tolist())

selected_store = st.sidebar.selectbox(
    "Select Store",
    options=available_stores,
)

selected_date = st.sidebar.date_input(
    "Forecast origin date",
    value=date(2015, 7, 24),
    min_value=date(2013, 1, 1),
    max_value=date(2015, 7, 24),
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Inventory scenario")

initial_stock = st.sidebar.number_input(
    "Initial stock (units)",
    min_value=0,
    max_value=1_000_000,
    value=1000,
    step=100,
)

average_revenue = st.sidebar.number_input(
    "Assumed revenue per unit (₹)",
    min_value=1.0,
    max_value=100_000.0,
    value=100.0,
    step=10.0,
)

lead_time = st.sidebar.number_input(
    "Supplier lead time (days)",
    min_value=0,
    max_value=90,
    value=3,
)

safety_stock_days = st.sidebar.number_input(
    "Safety stock (days)",
    min_value=0,
    max_value=90,
    value=2,
)

st.sidebar.markdown("---")

generate_button = st.sidebar.button(
    "Generate forecast",
    type="primary",
    use_container_width=True,
)


# ------------------------------------------------------------
# PAGE HEADER
# ------------------------------------------------------------

page_header(
    "Retail Intelligence Overview",
    "Forecast store-level sales and explore inventory decisions with machine learning.",
)

st.markdown(
    """
    <div class="dp-hero">
        <div class="dp-hero-layout">
          <div class="dp-hero-content">
            <div class="dp-hero-tag"><span class="dp-live-dot"></span> RETAIL INTELLIGENCE WORKSPACE</div>
            <div class="dp-hero-title">See demand clearly.<br>Plan with confidence.</div>
            <div class="dp-hero-copy">
                Turn store-level sales signals into a clear seven-day outlook
                and practical inventory scenarios.
            </div>
          </div>
          <div class="dp-hero-aside">
            <div class="dp-hero-aside-label">YOUR DECISION WINDOW</div>
            <div class="dp-hero-aside-value">7 <span>days</span></div>
            <div class="dp-hero-aside-rule"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
            <div class="dp-hero-aside-foot">Forecast · Explain · Plan</div>
          </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# GENERATE FORECAST
# ------------------------------------------------------------

if generate_button:
    try:
        with st.spinner("Generating forecast and inventory scenario..."):

            predictions = predict_seven_days(
                store_id=selected_store,
                origin_date=selected_date,
            )

            forecast_df = pd.DataFrame(predictions)
            forecast_df["date"] = pd.to_datetime(forecast_df["date"])

            # Retrieve actual historical sales for comparison.
            actual_df = df[
                df["Store"].astype(str) == str(selected_store)
            ][["Date", "Sales"]].copy()

            actual_df["Date"] = pd.to_datetime(actual_df["Date"])

            forecast_df = forecast_df.merge(
                actual_df,
                left_on="date",
                right_on="Date",
                how="left",
            )

            forecast_df = forecast_df.rename(
                columns={"Sales": "actual_sales"}
            )

            forecast_df["absolute_error"] = (
                forecast_df["actual_sales"] -
                forecast_df["predicted_sales"]
            ).abs()

            # Run the synthetic inventory simulation.
            inventory_df, inventory_summary = simulate_inventory_risk(
                predictions=predictions,
                initial_stock_units=initial_stock,
                average_revenue_per_unit=average_revenue,
                lead_time_days=lead_time,
                safety_stock_days=safety_stock_days,
            )

            inventory_df["date"] = pd.to_datetime(inventory_df["date"])

            # Store results in Streamlit session state.
            st.session_state["forecast_df"] = forecast_df
            st.session_state["inventory_df"] = inventory_df
            st.session_state["inventory_summary"] = inventory_summary
            st.session_state["forecast_store"] = selected_store
            st.session_state["forecast_origin"] = selected_date

            st.session_state["scenario"] = {
                "initial_stock": initial_stock,
                "average_revenue": average_revenue,
                "lead_time": lead_time,
                "safety_stock_days": safety_stock_days,
            }

        st.success("Forecast generated successfully.")

    except Exception as error:
        st.error(f"Unable to generate results: {error}")


# ------------------------------------------------------------
# EMPTY STATE
# ------------------------------------------------------------

if "forecast_df" not in st.session_state:

    st.markdown("")

    section_header(
        "Your analytics workspace",
        "Configure a store and generate a forecast to populate your dashboard.",
    )

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown(
            """
            <div class="dp-card">
                <div class="dp-card-top"><span class="dp-card-icon">↗</span><span class="dp-card-label">FORECASTING</span></div>
                <div class="dp-card-value">Know what’s next</div>
                <div class="dp-card-foot">
                    Predict store-level sales for the next seven days.
                </div>
                <div class="dp-card-meta">7 DAY HORIZON <span>→</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="dp-card">
                <div class="dp-card-top"><span class="dp-card-icon">▤</span><span class="dp-card-label">PLANNING</span></div>
                <div class="dp-card-value">Plan with context</div>
                <div class="dp-card-foot">
                    Explore inventory scenarios using configurable assumptions.
                </div>
                <div class="dp-card-meta">INVENTORY SCENARIOS <span>→</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="dp-card">
                <div class="dp-card-top"><span class="dp-card-icon">⌁</span><span class="dp-card-label">MODEL INSIGHTS</span></div>
                <div class="dp-card-value">Understand the why</div>
                <div class="dp-card-foot">
                    Compare predictions with historical observed sales.
                </div>
                <div class="dp-card-meta">EXPLAINABILITY & HEALTH <span>→</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="dp-next-step">
          <span class="dp-next-step-icon">✦</span>
          <div><strong>Your next step</strong><br><span>Choose a store and forecast date in the left panel, then generate your first outlook.</span></div>
          <span class="dp-next-step-hint">START IN THE SIDEBAR&nbsp; →</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="dp-footer">
            DEMANDPULSE · STORE-LEVEL SALES FORECASTING ·
            INVENTORY RISK IS A SYNTHETIC SCENARIO
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()


# ------------------------------------------------------------
# LOAD RESULTS
# ------------------------------------------------------------

forecast_df = st.session_state["forecast_df"].copy()
inventory_df = st.session_state["inventory_df"].copy()
summary = st.session_state["inventory_summary"]

forecast_store = st.session_state["forecast_store"]
forecast_origin = st.session_state["forecast_origin"]
scenario = st.session_state["scenario"]


# ------------------------------------------------------------
# FORECAST STATUS
# ------------------------------------------------------------

st.markdown(
    f"""
    <span class="dp-status">FORECAST GENERATED</span>
    &nbsp;&nbsp;
    <span style="color:{colors["muted"]};font-size:12px;">
        Store {forecast_store}
        &nbsp;·&nbsp;
        Origin {forecast_origin}
        &nbsp;·&nbsp;
        Seven-day horizon
    </span>
    """,
    unsafe_allow_html=True,
)

st.markdown("")


# ------------------------------------------------------------
# SALES FORECAST OVERVIEW
# ------------------------------------------------------------

section_header(
    "Sales forecast",
    "Predicted store-level sales across the seven-day forecast horizon.",
)

total_sales = forecast_df["predicted_sales"].sum()

open_forecast = forecast_df[forecast_df["open"] == 1]

average_sales = (
    open_forecast["predicted_sales"].mean()
    if not open_forecast.empty
    else 0
)

open_days = int((forecast_df["open"] == 1).sum())
closed_days = int((forecast_df["open"] == 0).sum())

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Forecasted sales",
    f"₹{total_sales:,.0f}",
)

k2.metric(
    "Average / open day",
    f"₹{average_sales:,.0f}",
)

k3.metric(
    "Open days",
    open_days,
)

k4.metric(
    "Closed days",
    closed_days,
)


# ------------------------------------------------------------
# SALES CHART
# ------------------------------------------------------------

section_header("Sales trend", "Predicted sales compared with observed historical sales.")

sales_chart = forecast_df.melt(
    id_vars=["date"],
    value_vars=["predicted_sales", "actual_sales"],
    var_name="Sales type",
    value_name="Sales",
)

sales_chart["Sales type"] = sales_chart["Sales type"].replace({
    "predicted_sales": "Predicted sales",
    "actual_sales": "Actual sales",
})

fig_sales = px.line(
    sales_chart,
    x="date",
    y="Sales",
    color="Sales type",
    markers=True,
    color_discrete_map={
        "Predicted sales": colors["accent"],
        "Actual sales": colors["success"],
    },
)

fig_sales.update_layout(
    **chart_theme,
    xaxis_title="Forecast date",
    yaxis_title="Sales (₹)",
    height=370,
)

fig_sales.update_traces(
    line=dict(width=3),
    marker=dict(size=7),
)

st.plotly_chart(
    fig_sales,
    use_container_width=True,
    config={"displayModeBar": False},
)


# ------------------------------------------------------------
# SALES FORECAST TABLE
# ------------------------------------------------------------

with st.expander("View detailed seven-day forecast"):

    sales_display = forecast_df[
        [
            "date",
            "open",
            "predicted_sales",
            "actual_sales",
            "absolute_error",
        ]
    ].copy()

    sales_display.columns = [
        "Date",
        "Open",
        "Predicted sales",
        "Actual sales",
        "Absolute error",
    ]

    sales_display["Date"] = pd.to_datetime(
        sales_display["Date"]
    ).dt.strftime("%Y-%m-%d")

    for column in [
        "Predicted sales",
        "Actual sales",
        "Absolute error",
    ]:
        sales_display[column] = sales_display[column].round(2)

    st.dataframe(
        sales_display,
        use_container_width=True,
        hide_index=True,
    )


# ------------------------------------------------------------
# INVENTORY RISK ANALYSIS
# ------------------------------------------------------------

st.markdown("---")

section_header(
    "Inventory risk analysis",
    "A configurable simulation derived from forecasted sales and assumed revenue per unit.",
)

st.warning(
    "This is a synthetic inventory scenario, not actual stock data or "
    "a real stockout prediction. Rossmann provides store-level sales, "
    "not SKU-level inventory records."
)


# ------------------------------------------------------------
# INVENTORY KPIs
# ------------------------------------------------------------

i1, i2, i3, i4 = st.columns(4)

i1.metric(
    "Initial stock",
    f"{summary['initial_stock_units']:,} units",
)

i2.metric(
    "Ending stock",
    f"{summary['ending_stock_units']:,} units",
)

i3.metric(
    "Estimated demand",
    f"{summary['total_estimated_demand_units']:,} units",
)

i4.metric(
    "Unmet demand",
    f"{summary['total_unmet_demand_units']:,} units",
)

i5, i6, i7 = st.columns(3)

i5.metric(
    "Reorder point",
    f"{summary['reorder_point_units']:,} units",
)

i6.metric(
    "Stockout days",
    summary["stockout_days"],
)

i7.metric(
    "High-risk days",
    summary["high_risk_days"],
)


# ------------------------------------------------------------
# INVENTORY CHART
# ------------------------------------------------------------

section_header(
    "Inventory projection",
    "Projected closing inventory against the calculated reorder point.",
)

fig_inventory = px.line(
    inventory_df,
    x="date",
    y="closing_stock",
    markers=True,
)

fig_inventory.add_hline(
    y=summary["reorder_point_units"],
    line_dash="dash",
    line_color=colors["warning"],
    annotation_text="Reorder point",
    annotation_font_color=colors["warning"],
)

fig_inventory.update_traces(
    line=dict(color=colors["accent"], width=3),
    marker=dict(size=7),
)

fig_inventory.update_layout(
    **chart_theme,
    xaxis_title="Date",
    yaxis_title="Remaining stock (units)",
    height=350,
)

st.plotly_chart(
    fig_inventory,
    use_container_width=True,
    config={"displayModeBar": False},
)


# ------------------------------------------------------------
# INVENTORY RISK TABLE
# ------------------------------------------------------------

with st.expander("View daily inventory risk report"):

    inventory_display = inventory_df[
        [
            "date",
            "estimated_demand_units",
            "opening_stock",
            "fulfilled_demand",
            "unmet_demand",
            "closing_stock",
            "risk_level",
            "reorder_required",
        ]
    ].copy()

    inventory_display.columns = [
        "Date",
        "Estimated demand",
        "Opening stock",
        "Fulfilled demand",
        "Unmet demand",
        "Closing stock",
        "Risk level",
        "Reorder required",
    ]

    inventory_display["Date"] = pd.to_datetime(
        inventory_display["Date"]
    ).dt.strftime("%Y-%m-%d")

    st.dataframe(
        inventory_display,
        use_container_width=True,
        hide_index=True,
    )


# ------------------------------------------------------------
# INVENTORY RECOMMENDATIONS
# ------------------------------------------------------------

section_header("Scenario recommendations")

if summary["stockout_days"] > 0:
    st.error(
        "Stockout risk detected under this scenario. "
        "Review starting inventory and replenishment assumptions."
    )

elif summary["high_risk_days"] > 0:
    st.warning(
        "Inventory reaches the high-risk threshold under this scenario. "
        "Consider replenishment."
    )

else:
    st.success(
        "No stockout occurred under the selected synthetic scenario."
    )

r1, r2, r3 = st.columns(3)

r1.metric(
    "Average daily demand",
    f"{summary['average_daily_demand_units']:.2f} units",
)

r2.metric(
    "Supplier lead time",
    f"{scenario['lead_time']} days",
)

r3.metric(
    "Safety stock",
    f"{scenario['safety_stock_days']} days",
)


# ------------------------------------------------------------
# HISTORICAL REPLAY EVALUATION
# ------------------------------------------------------------

st.markdown("---")

section_header(
    "Historical replay evaluation",
    "Evaluation against actual observed sales for the selected historical forecast window.",
)

evaluation_df = forecast_df[
    (forecast_df["open"] == 1)
    & forecast_df["actual_sales"].notna()
].copy()

if not evaluation_df.empty:

    mae = evaluation_df["absolute_error"].mean()

    actual_total = evaluation_df["actual_sales"].sum()

    wape = (
        evaluation_df["absolute_error"].sum() / actual_total * 100
        if actual_total > 0
        else None
    )

    e1, e2, e3 = st.columns(3)

    e1.metric(
        "Mean absolute error",
        f"₹{mae:,.2f}",
    )

    e2.metric(
        "Weighted absolute percentage error",
        f"{wape:.2f}%" if wape is not None else "N/A",
    )

    e3.metric(
        "Evaluated open days",
        len(evaluation_df),
    )

    st.caption(
        "These are historical replay metrics for the selected window. "
        "They are not live future forecast accuracy."
    )

else:
    st.info(
        "Actual sales are unavailable for this forecast window, "
        "so historical replay metrics cannot be calculated."
    )


# ------------------------------------------------------------
# DOWNLOAD REPORTS
# ------------------------------------------------------------

st.markdown("---")

section_header(
    "Export reports",
    "Download the forecast and synthetic inventory scenario for further analysis.",
)

download1, download2 = st.columns(2)

sales_csv = forecast_df.to_csv(index=False).encode("utf-8")
inventory_csv = inventory_df.to_csv(index=False).encode("utf-8")

with download1:
    st.download_button(
        label="Download sales forecast CSV",
        data=sales_csv,
        file_name=f"demandpulse_sales_store_{forecast_store}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with download2:
    st.download_button(
        label="Download inventory scenario CSV",
        data=inventory_csv,
        file_name=f"demandpulse_inventory_store_{forecast_store}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------

st.markdown(
    """
    <div class="dp-footer">
        DEMANDPULSE · RETAIL INTELLIGENCE PLATFORM<br>
        STORE-LEVEL SALES FORECASTING · SEVEN-DAY HORIZON ·
        SYNTHETIC INVENTORY SCENARIOS
    </div>
    """,
    unsafe_allow_html=True,
)
