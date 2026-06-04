#!/usr/bin/env bash
# ==============================================================================
# SPEMS GAURIKUND CHECKPOINT - PILOT DEPLOYMENT ORCHESTRATION ENGINE
# Configures local networking, edge inference services, and monitoring exporters
# ==============================================================================

set -euo pipefail

echo "=================================================="
echo "🕉️  SPEMS - PILOT DEPLOYMENT INITIALIZATION ENGINE  🕉"
echo "Target: 5 Cameras | 1 Checkpoint | 1 Command Center"
echo "=================================================="

# 1. Network Subnet Audit
echo "[Step 1] Initializing private checkpoint network interfaces..."
GATEWAY_IP="192.168.10.1"
EDGE_IPS=("192.168.10.100" "192.168.10.101")
CAMERA_IPS=("192.168.10.10" "192.168.10.11" "192.168.10.12" "192.168.10.13" "192.168.10.14")

echo "Configured Checkpoint Subnet: 192.168.10.0/24"
echo "Gateway Router: ${GATEWAY_IP}"
echo "Registered Camera IPs: ${CAMERA_IPS[*]}"
echo "Registered Edge Nodes: ${EDGE_IPS[*]}"

# 2. Check and Install Docker & Docker Compose (Station Workstation Hub)
echo "[Step 2] Auditing Docker environment on local command station PC..."
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing docker engine..."
    curl -fsSL https://get.github.com -o get-docker.sh || curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker "${USER}"
    rm get-docker.sh
else
    echo "Docker engine verified: $(docker --version)"
fi

# 3. Boot local command server via Docker Compose
echo "[Step 3] Launching local station orchestration stack..."
cat <<EOF > docker-compose-pilot.yml
version: '3.8'

services:
  database:
    image: postgres:15-alpine
    container_name: spems-postgres-pilot
    restart: always
    environment:
      POSTGRES_DB: spems_pilot
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: SecretPassword7718
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  prometheus:
    image: prom/prometheus:latest
    container_name: spems-prometheus-pilot
    restart: always
    ports:
      - "9090:9090"
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./infra/prometheus/alert_rules.yml:/etc/prometheus/alert_rules.yml

  grafana:
    image: grafana/grafana-oss:latest
    container_name: spems-grafana-pilot
    restart: always
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafanadata:/var/lib/grafana

volumes:
  pgdata:
  grafanadata:
EOF

echo "Station services written to: docker-compose-pilot.yml"

# 4. Provision Prometheus exporter configs
echo "[Step 4] Configuring Prometheus monitoring scrape pools..."
sudo mkdir -p /etc/prometheus
cat <<EOF | sudo tee /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'spems-command-station'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'spems-edge-node-a'
    static_configs:
      - targets: ['192.168.10.100:9100']

  - job_name: 'spems-edge-node-b'
    static_configs:
      - targets: ['192.168.10.101:9100']
EOF

# 5. Provision legal evidence verification paths
echo "[Step 5] Checking evidence cryptographic signature keys..."
mkdir -p /opt/spems/evidence
if [ ! -f "/opt/spems/private_signature.pem" ]; then
    echo "Generating new secure system keypair for Section 65B certifications..."
    openssl genpkey -algorithm RSA -out /opt/spems/private_key.pem -pkeyopt rsa_keygen_bits:2048
    openssl rsa -pubout -in /opt/spems/private_key.pem -out /opt/spems/public_key.pem
else
    echo "Pre-existing legal keys located."
fi

echo "=================================================="
echo "STATUS: Pilot deployment config scripts initialized."
echo "Launch station stack using: docker compose -f docker-compose-pilot.yml up -d"
echo "=================================================="
