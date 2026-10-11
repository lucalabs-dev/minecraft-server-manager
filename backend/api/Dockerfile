FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update && \
    apt-get install -y openjdk-25-jre-headless && \
    rm -rf /var/lib/apt/lists/*

COPY services/ ./services/

CMD ["uvicorn", "services.main:app", "--host", "0.0.0.0", "--port", "3000"]