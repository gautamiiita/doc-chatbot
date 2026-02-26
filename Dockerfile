FROM python:3.11-slim

WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies (skip cache to reduce image size)
RUN pip install --no-cache-dir -r requirements.txt

# Copy only essential application files
COPY backend.py .
COPY public.html .

# Create embeddings directory (will be populated at runtime)
RUN mkdir -p /app/.embeddings

# Expose port
EXPOSE 8000

# Set environment for Python
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "backend.py"]
