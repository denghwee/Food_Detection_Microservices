# Base image nhẹ, ổn định cho Flask
FROM python:3.10-slim

# Không tạo file .pyc, log realtime
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Cài các dependency hệ thống cần thiết cho AI / OpenCV (nếu có)
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để cache layer
COPY requirements.txt .

# Cài Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy toàn bộ source code
COPY . .

# Render tự inject PORT, ta map lại
ENV MICRO_HOST=0.0.0.0
ENV MICRO_PORT=10000

# Expose port (Render dùng PORT env, nhưng expose vẫn nên có)
EXPOSE 10000

# Start app
CMD ["python", "run.py"]
