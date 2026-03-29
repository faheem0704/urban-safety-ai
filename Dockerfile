FROM python:3.10-slim
WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libxcb1 \
    libxcb-shm0 \
    libxcb-xfixes0 \
    libx11-6 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only PyTorch + torchvision (avoids ~2 GB of CUDA packages)
RUN pip install --no-cache-dir torch==2.5.1+cpu torchvision==0.20.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Pin CPU torch so ultralytics can't upgrade to CUDA
RUN pip freeze | grep -E "^(torch|torchvision)==" > /tmp/constraints.txt

# Install everything else, constrained to keep CPU torch
RUN pip install --no-cache-dir -r requirements.txt -c /tmp/constraints.txt

COPY . .
RUN mkdir -p temp outputs models database

EXPOSE 8080
CMD ["python", "start.py"]
