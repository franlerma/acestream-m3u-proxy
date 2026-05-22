# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files  
COPY pyproject.toml .
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir uv
RUN uv pip install --system --no-cache-dir -e .

# Copy environment file (if exists)
COPY .env .env

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "src.acestream_proxy.main:app", "--host", "0.0.0.0", "--port", "8000"]