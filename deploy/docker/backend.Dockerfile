FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

RUN useradd --create-home --uid 10001 cloudrag

COPY backend/requirements.txt .
# The API performs embeddings on CPU. Install the CPU-only PyTorch wheel first
# so pip does not pull NVIDIA CUDA runtime packages into the Docker image.
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.13.0+cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
RUN mkdir -p /app/data && chown -R cloudrag:cloudrag /app

USER cloudrag

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
