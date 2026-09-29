FROM nvidia/cuda:12.8.1-devel-ubuntu22.04
WORKDIR /app
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-pip python3-dev python-is-python3 blender git build-essential ca-certificates xvfb libgl1-mesa-dri libegl1 libgl1 && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN git clone --depth 1 https://github.com/VAST-AI-Research/TripoSR.git /opt/TripoSR
RUN pip install --no-cache-dir --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128
RUN sed -e '/torchmcubes/d' -e '/torch/d' /opt/TripoSR/requirements.txt > /tmp/triposr-requirements.txt \
    && pip install --no-cache-dir -r /tmp/triposr-requirements.txt
RUN pip install --no-cache-dir onnxruntime-gpu
RUN pip install --no-cache-dir scikit-build-core ninja cmake pybind11
RUN git clone --depth 1 https://github.com/tatsy/torchmcubes.git /tmp/torchmcubes \
    && sed -i 's/torch==2.6.\*/torch>=2.6/' /tmp/torchmcubes/pyproject.toml \
    && sed -i 's/lerp(/lerp_ts(/g' /tmp/torchmcubes/cxx/helper_math.h \
    && pip install --no-cache-dir --no-build-isolation /tmp/torchmcubes
COPY app ./app
ENV GPU_NAME="NVIDIA GeForce RTX 5070 Ti"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
