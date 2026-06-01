#!/usr/bin/env bash
# ==============================================================================
# SPEMS NVIDIA JETSON DEPLOYMENT & DAEMONIZER SCRIPT
# Target OS: Ubuntu 20.04/22.04 LTS (JetPack 5.1 / 6.0)
# ==============================================================================

set -euo pipefail

echo "=================================================="
echo "🕉️  SPEMS - NVIDIA JETSON PROVISIONING ENGINE  🕉️"
echo "=================================================="

# 1. Update system dependencies and install CUDA-capable binaries
echo "[Step 1] Syncing system package registry..."
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    python3-pip \
    python3-dev \
    python3-virtualenv \
    sqlite3 \
    ffmpeg \
    libjpeg-dev \
    zlib1g-dev \
    curl

# 2. Setup Virtual Environment
echo "[Step 2] Creating sandboxed Python virtual environment..."
WORKDIR="/opt/spems/edge"
sudo mkdir -p "${WORKDIR}"
sudo chown -R "${USER}:${USER}" "/opt/spems"

python3 -m virtualenv "${WORKDIR}/venv"
source "${WORKDIR}/venv/bin/activate"

# 3. Install PyTorch & TensorRT Python bindings compatible with JetPack
echo "[Step 3] Installing JetPack-compatible Python modules..."
pip install --upgrade pip
pip install numpy opencv-python-headless pyyaml requests ultralytics

# Note: JetPack uses pre-configured PyTorch wheels mapped to Jetson CUDA architectures
# Refer to NVIDIA PyTorch for Jetson index pages for customized installations.

# 4. Create failsafe buffer structures
echo "[Step 4] Configuring offline database cache..."
mkdir -p "${WORKDIR}/database"
mkdir -p "${WORKDIR}/evidence/violations"
sqlite3 "${WORKDIR}/database/buffer.db" "VACUUM;"

# 5. Create Systemd Service File
echo "[Step 5] Creating SPEMS Supervisor systemd daemon..."
cat <<EOF | sudo tee /etc/systemd/system/spems-edge.service
[Unit]
Description=Smart Pilgrimage Environmental Monitoring System (SPEMS) Edge Supervisor
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${WORKDIR}
Environment="PYTHONUNBUFFERED=1"
ExecStart=${WORKDIR}/venv/bin/python ${WORKDIR}/main_edge.py --config ${WORKDIR}/config.yaml
Restart=always
RestartSec=10
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# 6. Enable and Start Daemon
echo "[Step 6] Activating systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable spems-edge.service
# sudo systemctl start spems-edge.service

echo "=================================================="
echo "RESULT: NVIDIA Jetson provisioning complete."
echo "Service is registered. To launch, execute:"
echo "  sudo systemctl start spems-edge"
echo "=================================================="
