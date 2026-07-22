FROM python:3.12.1-slim

WORKDIR /app

# System deps for tgcrypto build (gcc alone isn't enough - needs libc headers like stdint.h)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
