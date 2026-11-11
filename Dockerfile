FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY gemini_web2api.py ./
COPY gemini_web2api/ ./gemini_web2api/
COPY render_start.py ./

EXPOSE 8081
CMD ["python", "/app/render_start.py"]
