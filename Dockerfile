# Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Cài dependency hệ thống (nếu có opencv, torch, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để cache
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code
COPY . .

# Expose port (Render dùng PORT env)
EXPOSE 5000

# Render sẽ set PORT, nên ta dùng gunicorn
CMD gunicorn run:app --bind 0.0.0.0:${PORT:-5000}
