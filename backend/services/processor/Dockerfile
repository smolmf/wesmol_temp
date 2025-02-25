FROM python:3.9-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY backend/services/processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy indexer package
COPY backend/indexer /app/backend/indexer

# Install the indexer package
RUN pip install -e /app/backend/indexer

# Copy processor service code
COPY backend/services/processor /app/backend/services/processor

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the processor service
CMD ["python", "/app/backend/services/processor/server/main.py"]