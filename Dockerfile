# Multi-stage build for optimal size and security
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Download and setup Stockfish
RUN wget -q https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64-avx2.tar \
    && tar -xf stockfish-ubuntu-x86-64-avx2.tar \
    && mkdir -p /engines \
    && cp stockfish/stockfish-ubuntu-x86-64-avx2 /engines/stockfish \
    && chmod +x /engines/stockfish

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash lichess

# Set working directory
WORKDIR /app

# Copy engine from builder stage
COPY --from=builder /engines /app/engines

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p books logs \
    && touch books/bullet.bin books/blitz.bin books/rapid.bin books/classical.bin

# Change ownership to non-root user
RUN chown -R lichess:lichess /app

# Switch to non-root user
USER lichess

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://lichess.org/api/account', timeout=5)" || exit 1

# Default command
CMD ["python", "user_interface.py", "-u"]