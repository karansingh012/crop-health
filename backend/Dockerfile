FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
# CPU wheels avoid downloading CUDA libraries for the local server.
RUN pip install --no-cache-dir torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/cpu
COPY backend /app/backend
COPY ml /app/ml
COPY shared /app/shared
RUN useradd -m appuser && mkdir -p /app/uploads /app/models && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn","backend.app.main:app","--host","0.0.0.0","--port","8000","--workers","1","--no-proxy-headers"]
