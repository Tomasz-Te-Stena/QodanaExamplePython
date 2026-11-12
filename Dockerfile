FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

# Bind to 0.0.0.0 so the app is reachable from outside the container.
CMD ["flask", "--app", "app", "run", "--host", "0.0.0.0", "--port", "5000"]
