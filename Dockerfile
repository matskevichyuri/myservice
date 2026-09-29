FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends blender git build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN git clone --depth 1 https://github.com/VAST-AI-Research/TripoSR.git /opt/TripoSR \
    && pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu124 \
    && sed '/torchmcubes/d' /opt/TripoSR/requirements.txt > /tmp/triposr-requirements.txt \
    && pip install --no-cache-dir -r /tmp/triposr-requirements.txt \
    && pip install --no-cache-dir scikit-build-core ninja cmake pybind11 \
    && pip install --no-cache-dir --no-build-isolation git+https://github.com/tatsy/torchmcubes.git
COPY app ./app
ENV GPU_NAME="NVIDIA GeForce RTX 5070 Ti"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
