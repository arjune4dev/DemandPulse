FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi==0.162.0 uvicorn==0.54.0

COPY src/data_store.py ./data_store.py

ENV PYTHONUNBUFFERED=1

EXPOSE 10000

CMD ["uvicorn", "data_store:app", "--host", "0.0.0.0", "--port", "10000"]
