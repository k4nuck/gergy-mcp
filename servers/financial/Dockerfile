FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.minimal.txt .
RUN pip install --no-cache-dir -r requirements.minimal.txt

# Copy source code
COPY shared/ shared/
COPY servers/financial/ servers/financial/

# Set environment variables
ENV PYTHONPATH=/app
ENV DOMAIN_NAME=financial

# Expose port (if needed for health checks)
EXPOSE 8000

# Run the server
CMD ["python", "servers/financial/server.py"]