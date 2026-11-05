# DemandPulse

DemandPulse is a retail demand forecasting workspace. It combines a seven-day store sales forecast, configurable inventory scenario simulation, SHAP explanations, and prediction monitoring.

## Run with Docker Compose

Docker is the recommended deployment path. The dashboard and API run as separate services from the same image:

```bash
docker compose up --build
```

- Dashboard: <http://localhost:8501>
- API docs: <http://localhost:8000/docs>
- API health: <http://localhost:8000/health>

The compose file mounts `data/`, `models/`, and `reports/` from this project into the containers. Keep the Rossmann source files at `data/raw/train.csv` and `data/raw/store.csv`; the trained pipeline is `models/demandpulse_pipeline.pkl`. The model files are also copied into the image. Dataset files are intentionally excluded from the image and source control, so supply the two CSVs when deploying to a new machine.

To stop the services, run `docker compose down`.

## Run locally

Use Python 3.11, install dependencies, then start the two processes:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run dashboard.py
```

In a second terminal, run the API:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

The app requires the trained model and Rossmann `train.csv` and `store.csv` files at the paths described above. The dashboard uses the Python forecasting pipeline directly; the API is available for integrations and logs API forecasts for monitoring.

## Deploy to Render

The repository includes a Render Blueprint in `render.yaml`. In Render, choose **New → Blueprint**, connect `arjune4dev/DemandPulse` on `main`, and review the proposed service before applying it. The Blueprint runs the dashboard and API behind one web service and attaches a 1 GB persistent disk for the Rossmann files and prediction log. After the first deploy, open the service URL and upload `train.csv` and `store.csv` on the setup screen; the files stay on the disk across deploys.

This Render setup uses the paid Standard web service plan because the forecasting feature build needs more memory than Render's free plan provides. Render also requires a paid service for persistent disks. Review Render's current [compute pricing](https://render.com/pricing) and [persistent disk requirements](https://render.com/docs/disks) before applying the Blueprint. The local Docker Compose setup remains available at no additional hosting cost.

## Product areas

- **Overview** — forecast store sales for seven days, compare with available observed sales, and explore inventory assumptions.
- **Explainability** — inspect global feature importance and SHAP contributions for an individual forecast.
- **Monitoring** — review API prediction logs and evaluation metrics when actual sales are available.

Inventory outputs are a synthetic scenario based on forecast sales and assumed revenue per unit. The Rossmann dataset does not contain SKU-level inventory records, so these values are planning illustrations rather than observed stock or stockout predictions.

## Project layout

- `dashboard.py`, `pages/` — Streamlit application
- `src/` — forecasting, API, inventory, monitoring, and explanation logic
- `models/` — serialized trained models
- `data/raw/` — local Rossmann source data (not committed)
- `reports/` — generated charts, evaluation outputs, and prediction logs
- `notebooks/` — exploration and model development
