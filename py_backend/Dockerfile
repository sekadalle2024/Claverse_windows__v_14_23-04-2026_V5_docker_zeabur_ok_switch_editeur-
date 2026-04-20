FROM python:3.11-slim

# Add labels for the image
LABEL org.opencontainers.image.title="Clara Backend"
LABEL org.opencontainers.image.description="Clara AI Assistant Backend Service"
LABEL org.opencontainers.image.authors="Clara Team"
LABEL org.opencontainers.image.source="https://github.com/clara17verse/clara"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="Clara"
LABEL org.opencontainers.image.version="1.0.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies directly with pip (faster than uv for Hugging Face)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Set environment variables (Zeabur uses port 8080)
ENV HOST="0.0.0.0" \
    PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port (Zeabur uses 8080)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"] 