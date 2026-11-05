
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by XGBoost
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
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

# Create directories used by the application
RUN mkdir -p /app/data/raw /app/models /app/reports

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
EXPOSE 8501

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
