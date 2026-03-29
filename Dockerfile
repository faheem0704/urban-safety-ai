FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .

# Step 1: Install CPU-only PyTorch + torchvision (avoids ~2 GB of CUDA packages)
RUN pip install --no-cache-dir torch==2.5.1+cpu torchvision==0.20.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Step 2: Pin the CPU torch versions so ultralytics can't upgrade to CUDA
RUN pip freeze | grep -E "^(torch|torchvision)==" > /tmp/constraints.txt

# Step 3: Install everything else, constrained to keep CPU torch
RUN pip install --no-cache-dir -r requirements.txt -c /tmp/constraints.txt

COPY . .
RUN mkdir -p temp outputs models database
EXPOSE 8080
CMD ["python", "start.py"]
