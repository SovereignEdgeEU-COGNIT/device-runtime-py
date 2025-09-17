FROM python:3.10.15-slim-bookworm

# Set work directory (auto-creates if missing)
WORKDIR /cognit

# Copy repository inside the image
COPY . .

# Install dependencies with no cache and build/install package directly to avoid leftover artifacts
RUN pip install --upgrade --no-cache-dir pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir .

# Create non-root user for better security
RUN useradd -m app && chown -R app /cognit
USER app

# Run python example script when the image is executed
ENTRYPOINT ["python", "examples/minimal_offload_sync.py"]
