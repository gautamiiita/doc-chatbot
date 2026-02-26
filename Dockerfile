FROM python:3.11-slim

WORKDIR /app

# Set pip to have no cache and disable version check
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONUNBUFFERED=1

# Copy requirements
COPY requirements.txt .

# Install dependencies with pip cache optimization
# Using --no-deps-build to skip unnecessary compilation
RUN pip install --no-cache-dir \
    --only-binary=:all: \
    -r requirements.txt || pip install -r requirements.txt

# Copy only essential application files
COPY backend.py .
COPY public.html .

# Create embeddings directory (will be auto-populated at runtime)
RUN mkdir -p /app/.embeddings

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "backend.py"]
