
from datetime import date

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.predictor import predict_seven_days
from src.monitoring import (
    log_predictions,
    calculate_monitoring_metrics,
    LOG_PATH,
)


app = FastAPI(
    title="DemandPulse API",
    description="Seven-day store sales forecasting and monitoring API",
    version="1.0.0",
)


class PredictionRequest(BaseModel):
    store_id: int = Field(gt=0)
    origin_date: date


@app.get("/")
def home():
    return {
        "message": "Welcome to DemandPulse API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "DemandPulse",
    }


@app.post("/predict")
def predict(request: PredictionRequest):
    try:
        predictions = predict_seven_days(
            request.store_id,
            request.origin_date,
        )

        log_predictions(predictions)

        return {
            "store_id": request.store_id,
            "origin_date": request.origin_date,
            "forecast": predictions,
            "monitoring": "Predictions logged successfully",
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.get("/monitoring")
def monitoring():
    try:
        metrics = calculate_monitoring_metrics()

        return {
            "status": "success",
            "monitoring_metrics": metrics,
        }

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@app.get("/monitoring/logs")
def monitoring_logs():
    if not LOG_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No prediction logs found.",
        )

    try:
        logs = pd.read_csv(LOG_PATH)

        # Convert missing values (NaN) to JSON-compatible None
        logs = logs.astype(object).where(
            pd.notna(logs),
            None
        )

        return {
            "total_records": len(logs),
            "logs": logs.to_dict(orient="records"),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve prediction logs: {str(error)}",
        )
