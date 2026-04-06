FROM python:3.11-slim

WORKDIR /app

COPY endpoint/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY relay /app/relay
COPY endpoint /app/endpoint
COPY shared /app/shared

CMD ["uvicorn", "endpoint.main:app", "--host", "0.0.0.0", "--port", "8001"]
