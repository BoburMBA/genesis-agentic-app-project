FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl gcc g++ wget && \
    rm -rf /var/lib/apt/lists/*

# Install setuptools first (required for editable install)
RUN pip install --no-cache-dir setuptools>=70.0

# Install dependencies first (better layer caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Pre-download the sentence transformer model so it's baked into the image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/system/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
