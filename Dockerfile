# AI Boekhouder — productie-image (FastAPI via uvicorn).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Systeem-OCR optioneel: ontcommentarieer om Tesseract (incl. NL) mee te bouwen.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     tesseract-ocr tesseract-ocr-nld && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY boekhouder ./boekhouder
COPY streamlit_app.py ./

# Data (sqlite) op een volume zodat het een herstart overleeft.
ENV BOEKHOUDER_DB_PATH=/data/boekhouder.db
VOLUME ["/data"]
EXPOSE 8000

# 2 workers; verhoog bij meer verkeer. uvicorn-worker voor async FastAPI.
CMD ["gunicorn", "boekhouder.api.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", "--bind", "0.0.0.0:8000", "--timeout", "60"]
