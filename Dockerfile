# Используем Python 3.12, так как зависимости требуют его
FROM python:3.12-slim

# Устанавливаем системные библиотеки (обязательно для ML!)
# В Debian Trixie libgl1-mesa-glx переименован в libgl1
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

CMD ["python", "main.py"]