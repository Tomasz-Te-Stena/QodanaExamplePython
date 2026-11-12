FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Debian security updates that are newer than the base image
# (the pipeline builds with --pull, so this layer is rebuilt each run).
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Numeric, non-root user: works with --read-only and --cap-drop ALL.
RUN useradd --uid 10001 --create-home appuser
USER 10001

EXPOSE 5000

# The slim image has no curl, so the check uses Python itself.
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/CurrentTime', timeout=2)"]

# Bind to 0.0.0.0 so the app is reachable from outside the container.
CMD ["flask", "--app", "app", "run", "--host", "0.0.0.0", "--port", "5000"]
