# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# copy repo first (requirements.txt should be at repo root)
COPY . /app

# ensure system deps for some python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# remove conflicting PyPI package named "telegram" if present, then install requirements
RUN pip uninstall -y telegram || true
RUN if [ -f "/app/requirements.txt" ]; then pip install --no-cache-dir -r /app/requirements.txt; fi

# make entrypoint executable
RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/app/entrypoint.sh"]
