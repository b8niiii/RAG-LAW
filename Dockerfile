FROM python:3.11-slim AS ui

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements-ui.txt ./
RUN python -m pip install --no-cache-dir --timeout 60 -r requirements-ui.txt
COPY ui/ ui/
COPY .streamlit/ .streamlit/

EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "ui/main.py", "--server.address=0.0.0.0", "--server.headless=true"]

FROM python:3.11-slim AS api

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_DISABLE_XET=1 \
    HF_HUB_DOWNLOAD_TIMEOUT=180 \
    HF_HOME=/opt/model-cache

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements-api.txt ./
RUN python -m pip install --no-cache-dir --timeout 60 -r requirements-api.txt
COPY api/ api/
COPY modules/ modules/
COPY examples/ examples/
COPY scripts/ scripts/
RUN python -c "from modules.encoder import model_files; model_files()"

ARG RAGLAW_BUILD_CORPUS=examples/italian_demo.json
COPY ${RAGLAW_BUILD_CORPUS} /app/${RAGLAW_BUILD_CORPUS}
RUN python -m scripts.build_index --corpus "${RAGLAW_BUILD_CORPUS}" --output /opt/raglaw-index

ENV HF_HUB_OFFLINE=1 RAGLAW_INDEX_PATH=/opt/raglaw-index

EXPOSE 8080
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
