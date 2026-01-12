FROM node:20-slim

# Set environment variables
ENV NODE_ENV=production \
    ENVIRONMENT=workstation

WORKDIR /app

# Install system dependencies for canvas (chartjs-node-canvas) and faiss-node
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    librsvg2-dev \
    libgomp1 \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Copy package files for layer caching
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code and build assets
COPY tsconfig.json tsup.config.ts ./
COPY src ./src

# Build the application
RUN npm run build

# Prune dev dependencies after build
RUN npm prune --production

# Copy FAISS index (if present in build context)
COPY src/faiss_index_fundfacts ./src/faiss_index_fundfacts

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD node -e "fetch('http://localhost:8080/health').then(r => process.exit(r.ok ? 0 : 1))" || exit 1

# Run the application
CMD ["node", "./dist/server.js"]
