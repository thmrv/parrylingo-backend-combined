FROM python:3.11-slim

# Устанавливаем зависимости системы и ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY requirements.txt ./

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем приложение
COPY . .
