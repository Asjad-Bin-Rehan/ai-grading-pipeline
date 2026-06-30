FROM python:3.12-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \ 
    poppler-utils \
    tesseract-ocr \
    libgl1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /workspace
EXPOSE 8000
