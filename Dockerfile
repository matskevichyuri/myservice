FROM nvidia/cuda:12.4.1-devel-ubuntu22.04
WORKDIR /app
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-pip python3-dev python-is-python3 blender git build-essential ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN git clone --depth 1 https://github.com/VAST-AI-Research/TripoSR.git /opt/TripoSR \
    && pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu124 \
    && sed '/torchmcubes/d' /opt/TripoSR/requirements.txt > /tmp/triposr-requirements.txt \
    && pip install --no-cache-dir -r /tmp/triposr-requirements.txt \
    && pip install --no-cache-dir scikit-build-core ninja cmake pybind11 \
    && git clone --depth 1 https://github.com/tatsy/torchmcubes.git /tmp/torchmcubes \
    && sed -i 's/\\blerp(/lerp_ts(/g' /tmp/torchmcubes/cxx/helper_math.h \
    && pip install --no-cache-dir --no-build-isolation /tmp/torchmcubes
COPY app ./app
ENV GPU_NAME="NVIDIA GeForce RTX 5070 Ti"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
