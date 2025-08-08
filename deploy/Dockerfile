FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY api/requirements.txt /app/api/

# Install Python dependencies
RUN pip install --no-cache-dir -r api/requirements.txt

# Copy the entire repository (needed for yt_dlp imports)
COPY . /app/

# Create download directory
RUN mkdir -p /tmp/downloads

# Environment variables
ENV FLASK_APP=api/app.py
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application with gunicorn for production with enhanced logging
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "--workers", "2", "--threads", "4", "--worker-class", "gthread", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "--capture-output", "api.app:app"]