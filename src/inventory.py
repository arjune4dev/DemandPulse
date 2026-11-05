
import math
import pandas as pd


def simulate_inventory_risk(
    predictions,
    initial_stock_units,
    average_revenue_per_unit,
    lead_time_days,
    safety_stock_days
):
    """
    Simulate store-level inventory risk using forecast sales.

    IMPORTANT:
    Rossmann Sales represents sales value, not physical units.
    We estimate synthetic demand units using an assumed
    average revenue per unit.

    This is a configurable simulation, not actual stockout
    prediction or SKU-level inventory forecasting.
    """

    # -----------------------------------------
    # 1. VALIDATE INPUTS
    # -----------------------------------------

    if initial_stock_units < 0:
        raise ValueError("Initial stock cannot be negative.")

    if average_revenue_per_unit <= 0:
        raise ValueError(
            "Average revenue per unit must be greater than zero."
        )

    if lead_time_days < 0:
        raise ValueError("Lead time cannot be negative.")

    if safety_stock_days < 0:
        raise ValueError("Safety stock days cannot be negative.")

    if not predictions:
        raise ValueError("Forecast predictions are empty.")

    # -----------------------------------------
    # 2. CONVERT FORECAST SALES TO SYNTHETIC UNITS
    # -----------------------------------------

    forecast = pd.DataFrame(predictions)

    forecast["estimated_demand_units"] = (
        forecast["predicted_sales"]
        .apply(
            lambda sales: math.ceil(
                max(0, sales) / average_revenue_per_unit
            )
        )
    )

    # Closed stores have no demand in this simulation
    forecast.loc[
        forecast["open"] == 0,
        "estimated_demand_units"
    ] = 0

    # -----------------------------------------
    # 3. CALCULATE AVERAGE DAILY DEMAND
    # -----------------------------------------

    open_days = forecast[
        forecast["open"] == 1
    ]

    if open_days.empty:
        raise ValueError("No open days in the forecast period.")

    average_daily_demand = (
        open_days["estimated_demand_units"].mean()
    )

    # Reorder point includes lead time and safety stock
    reorder_point = math.ceil(
        average_daily_demand
        * (lead_time_days + safety_stock_days)
    )

    # -----------------------------------------
    # 4. SIMULATE DAILY INVENTORY
    # -----------------------------------------

    current_stock = int(initial_stock_units)

    results = []

    for _, row in forecast.iterrows():

        demand = int(row["estimated_demand_units"])

        opening_stock = current_stock

        fulfilled_demand = min(
            opening_stock,
            demand
        )

        unmet_demand = max(
            0,
            demand - opening_stock
        )

        current_stock = max(
            0,
            opening_stock - demand
        )

        closing_stock = current_stock

        # -------------------------------------
        # 5. CLASSIFY INVENTORY RISK
        # -------------------------------------

        if unmet_demand > 0:

            risk = "Stockout"

        elif closing_stock <= reorder_point:

            risk = "High"

        elif closing_stock <= reorder_point * 1.5:

            risk = "Medium"

        else:

            risk = "Low"

        reorder_required = (
            closing_stock <= reorder_point
        )

        results.append({

            "date": row["date"],

            "open": int(row["open"]),

            "forecast_sales": round(
                float(row["predicted_sales"]), 2
            ),

            "estimated_demand_units": demand,

            "opening_stock": opening_stock,

            "fulfilled_demand": fulfilled_demand,

            "unmet_demand": unmet_demand,

            "closing_stock": closing_stock,

            "risk_level": risk,

            "reorder_required": reorder_required

        })

    # -----------------------------------------
    # 6. BUILD FINAL RESULTS
    # -----------------------------------------

    result_df = pd.DataFrame(results)

    summary = {

        "initial_stock_units": int(initial_stock_units),

        "ending_stock_units": int(current_stock),

        "average_daily_demand_units": round(
            float(average_daily_demand), 2
        ),

        "reorder_point_units": int(reorder_point),

        "total_estimated_demand_units": int(
            result_df["estimated_demand_units"].sum()
        ),

        "total_unmet_demand_units": int(
            result_df["unmet_demand"].sum()
        ),

        "stockout_days": int(
            (result_df["risk_level"] == "Stockout").sum()
        ),

        "high_risk_days": int(
            (result_df["risk_level"] == "High").sum()
        )

    }

    return result_df, summary
