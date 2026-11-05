
import pandas as pd

from src.monitoring import (
    log_predictions,
    update_actual_sales,
    calculate_monitoring_metrics,
)


predictions = [
    {
        "store_id": 1,
        "date": "2015-07-25",
        "open": 1,
        "predicted_sales": 4000,
    },
    {
        "store_id": 1,
        "date": "2015-07-26",
        "open": 0,
        "predicted_sales": 0,
    },
    {
        "store_id": 1,
        "date": "2015-07-27",
        "open": 1,
        "predicted_sales": 5000,
    },
]

log_predictions(predictions)

actual_data = pd.DataFrame([
    {
        "store_id": 1,
        "forecast_date": "2015-07-25",
        "actual_sales": 4200,
    },
    {
        "store_id": 1,
        "forecast_date": "2015-07-26",
        "actual_sales": 0,
    },
    {
        "store_id": 1,
        "forecast_date": "2015-07-27",
        "actual_sales": 4800,
    },
])

update_actual_sales(actual_data)

metrics = calculate_monitoring_metrics()

print("\nMONITORING RESULTS")
for metric, value in metrics.items():
    print(f"{metric}: {value}")
