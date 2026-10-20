FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home demo && mkdir /state && chown demo:demo /state
COPY --chown=demo:demo . .
USER demo
ENV DEMO_STATE_DIR=/state
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "webdemo.app:app", "--host", "0.0.0.0", "--port", "8080"]
