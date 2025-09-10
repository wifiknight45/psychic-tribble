# =========================
# Stage 1: Build dependencies
# =========================
FROM python:3.11.8-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY requirements.txt .

# Install Python dependencies globally
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt


# =========================
# Stage 2: Final runtime image
# =========================
FROM python:3.11.8-slim

# Set working directory
WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTT_ENV=production \
    PORT=8000 \
    PATH=/usr/local/bin:$PATH

# Install only runtime dependencies (including curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod 755 /app/entrypoint.sh

# Copy application code
COPY . .

# Create non-root user and set ownership (including the entrypoint script)
RUN useradd -m appuser && chown -R appuser:appuser /app && chmod 755 /app/entrypoint.sh
USER appuser

# Expose application port
EXPOSE $PORT

# Healthcheck using curl
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Use entrypoint script to handle migrations and start uvicorn
CMD ["/app/entrypoint.sh"]
