# api-server/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && pip install flask pymssql \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY app.py /app/app.py

CMD ["python", "app.py"]
