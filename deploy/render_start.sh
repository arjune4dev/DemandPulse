#!/bin/sh
set -eu

mkdir -p "${DEMANDPULSE_DATA_DIR:-/var/data/raw}"
mkdir -p "${DEMANDPULSE_REPORTS_DIR:-/var/data/reports}"

streamlit run dashboard.py \
  --server.address 127.0.0.1 \
  --server.port 8501 \
  --server.enableCORS false \
  --server.enableXsrfProtection false &

uvicorn src.main:app --host 127.0.0.1 --port 8000 &

exec nginx -g 'daemon off;'
