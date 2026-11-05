
import pandas as pd
import pytest

from fastapi.testclient import TestClient

from src import main


client = TestClient(main.app)


@pytest.fixture
def sample_predictions():
    return [
        {
            "store_id": 1,
            "date": "2015-07-25",
            "open": 1,
            "predicted_sales": 4000.0,
        },
        {
            "store_id": 1,
            "date": "2015-07-26",
            "open": 0,
            "predicted_sales": 0.0,
        },
    ]


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_prediction_endpoint(
    monkeypatch,
    sample_predictions,
):
    logged_predictions = []

    def mock_predict(store_id, origin_date):
        return sample_predictions

    def mock_log(predictions):
        logged_predictions.extend(predictions)

    monkeypatch.setattr(
        main,
        "predict_seven_days",
        mock_predict,
    )

    monkeypatch.setattr(
        main,
        "log_predictions",
        mock_log,
    )

    response = client.post(
        "/predict",
        json={
            "store_id": 1,
            "origin_date": "2015-07-24",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["store_id"] == 1
    assert len(result["forecast"]) == 2

    assert (
        result["monitoring"]
        == "Predictions logged successfully"
    )

    assert len(logged_predictions) == 2


def test_invalid_prediction_request():
    response = client.post(
        "/predict",
        json={
            "store_id": -1,
            "origin_date": "2015-07-24",
        },
    )

    assert response.status_code == 422


def test_monitoring_endpoint(monkeypatch):
    mock_metrics = {
        "evaluated_predictions": 10,
        "MAE": 120.5,
        "RMSE": 160.2,
        "WAPE": 4.5,
    }

    monkeypatch.setattr(
        main,
        "calculate_monitoring_metrics",
        lambda: mock_metrics,
    )

    response = client.get("/monitoring")

    assert response.status_code == 200

    result = response.json()

    assert result["status"] == "success"

    assert (
        result["monitoring_metrics"]["MAE"]
        == 120.5
    )


def test_monitoring_logs_endpoint(
    monkeypatch,
    tmp_path,
):
    log_file = tmp_path / "prediction_logs.csv"

    sample_logs = pd.DataFrame([
        {
            "store_id": 1,
            "forecast_date": "2015-07-25",
            "is_open": 1,
            "predicted_sales": 4000.0,
            "actual_sales": None,
            "forecast_generated_at": "2026-11-01 10:00:00",
        }
    ])

    sample_logs.to_csv(
        log_file,
        index=False,
    )

    monkeypatch.setattr(
        main,
        "LOG_PATH",
        log_file,
    )

    response = client.get("/monitoring/logs")

    assert response.status_code == 200

    result = response.json()

    assert result["total_records"] == 1
    assert len(result["logs"]) == 1

    assert result["logs"][0]["store_id"] == 1
    assert result["logs"][0]["actual_sales"] is None
