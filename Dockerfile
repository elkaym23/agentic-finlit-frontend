# ---- Agentic FinLit Frontend (Streamlit) ----
FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# System deps (build-essential sometimes needed for deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire repo (no 'src/' in your structure)
COPY . /app

# Streamlit will bind to 0.0.0.0:7860 on Spaces
EXPOSE 7860
CMD ["bash", "-lc", "streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=7860"]
