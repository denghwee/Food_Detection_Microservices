FROM python:3.11-slim

WORKDIR /app

# ===== System dependencies =====
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ===== Python deps =====
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ===== App source =====
COPY . .

# ===== Local config =====
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1
ENV SERVICE_PORT=5002

EXPOSE 5002

CMD ["sh", "-c", "python run.py"]
