FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends blender git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN git clone --depth 1 https://github.com/VAST-AI-Research/TripoSR.git /opt/TripoSR \
    && pip install --no-cache-dir -r /opt/TripoSR/requirements.txt \
    && pip install --no-cache-dir git+https://github.com/tatsy/torchmcubes.git
COPY app ./app
ENV GPU_NAME="NVIDIA GeForce RTX 5070 Ti"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
