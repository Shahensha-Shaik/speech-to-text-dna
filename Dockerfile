FROM python:3.10-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg wget unzip && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt
# Download Vosk small English model
ENV VOSK_MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
RUN mkdir -p /app/model || true
RUN wget -O /tmp/model.zip "$VOSK_MODEL_URL" || true
RUN if [ -f /tmp/model.zip ]; then unzip /tmp/model.zip -d /app && mv /app/vosk-model-small-en-us-0.15 /app/model || true; fi
COPY backend /app
RUN mkdir -p /app/uploads
EXPOSE 5000
ENV PORT 5000
CMD ["gunicorn","--bind","0.0.0.0:5000","app:app","--workers=1"]