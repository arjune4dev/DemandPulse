import os

import pandas as pd
import requests


def _api_base_url():
    hostport = os.environ.get("API_SERVICE_HOSTPORT")
    if hostport:
        return f"http://{hostport.rstrip('/')}"

    explicit_url = os.environ.get("API_BASE_URL")
    return explicit_url.rstrip("/") if explicit_url else None


def predict_forecast(store_id, origin_date):
    base_url = _api_base_url()
    if not base_url:
        from src.predictor import predict_seven_days

        return predict_seven_days(store_id, origin_date)

    response = requests.post(
        f"{base_url}/predict",
        json={
            "store_id": int(store_id),
            "origin_date": str(origin_date),
        },
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["forecast"]


def get_prediction_logs():
    base_url = _api_base_url()
    if not base_url:
        return None

    response = requests.get(f"{base_url}/monitoring/logs", timeout=60)
    if response.status_code == 404:
        return pd.DataFrame()
    response.raise_for_status()
    return pd.DataFrame(response.json().get("logs", []))
