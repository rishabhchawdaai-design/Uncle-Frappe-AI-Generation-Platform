FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tesseract-ocr poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY platform/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY platform/ ./platform/
COPY sections/ ./sections/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "platform.api:app", "--host", "0.0.0.0", "--port", "8000"]
