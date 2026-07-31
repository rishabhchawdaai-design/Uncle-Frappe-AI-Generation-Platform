FROM python:3.12-slim

WORKDIR /app

# Platform is pure Python (stdlib + pytest for tests); no build deps required.
COPY . .

ENV PYTHONPATH=/app

CMD ["python", "-m", "ai_generation.cli", "--help"]
