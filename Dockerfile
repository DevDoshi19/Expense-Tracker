FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY config.py .
COPY syn_for_local.py .

# Copy resources
COPY prompts/ ./prompts/
COPY resources/ ./resources/

# Create data directory for databases
RUN mkdir -p data

# Expose port (for documentation, actual port is from environment)
EXPOSE 8000

# Set default environment variables
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV MCP_ENV=production
ENV ENABLE_LOGGING=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; print('OK')" || exit 1

# Run the server
CMD ["python", "main.py"]
