
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by XGBoost
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY pages/ ./pages/
COPY dashboard.py .
COPY README.md .
COPY models/ ./models/
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/render_start.sh /app/render_start.sh

# Create directories used by the application
RUN mkdir -p /app/data/raw /app/models /app/reports

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
EXPOSE 8501
EXPOSE 10000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
