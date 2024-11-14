FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    libcairo2 \
    libcairo2-dev \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libpango-1.0-0 \
    libffi-dev \
    shared-mime-info && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
