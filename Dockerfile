# Використовуємо офіційний Python образ
FROM python:3.10

# Встановлюємо робочий каталог у контейнері
WORKDIR /app

# Копіюємо всі файли в контейнер
COPY . /app

# Встановлюємо залежності
RUN pip install -r requirements.txt

# Команда для запуску додатку
CMD ["python", "app.py"]
