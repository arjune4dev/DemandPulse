
from src.predictor import predict_seven_days
from src.inventory import simulate_inventory_risk


# Generate forecast
predictions = predict_seven_days(
    store_id=1,
    origin_date="2015-07-24"
)


# Configure synthetic inventory scenario
results, summary = simulate_inventory_risk(

    predictions=predictions,

    initial_stock_units=1000,

    average_revenue_per_unit=100,

    lead_time_days=3,

    safety_stock_days=2

)


print("\nINVENTORY RISK REPORT")

print(results.to_string(index=False))

print("\nINVENTORY SUMMARY")

for key, value in summary.items():

    print(f"{key}: {value}")
