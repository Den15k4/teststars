FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Добавляем директорию в PYTHONPATH
ENV PYTHONPATH=/app

# Запуск бота
CMD ["python", "main.py"]