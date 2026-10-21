FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update && \
    apt-get install -y openjdk-25-jre-headless && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 minecraft && \
    useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin minecraft

COPY services/ ./services/

USER minecraft

CMD ["uvicorn", "services.main:app", "--host", "0.0.0.0", "--port", "3000"]