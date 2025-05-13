FROM python:3.11-slim

WORKDIR /app

# Combine RUN commands to reduce layers and clean up in the same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libcairo2 \
    libcairo2-dev \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libpango-1.0-0 \
    libffi-dev \
    shared-mime-info && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask-cors watchdog

# Don't copy code here - we'll use a volume mount instead

EXPOSE 8080

# For development, run with hot reloading
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080", "--debug"]