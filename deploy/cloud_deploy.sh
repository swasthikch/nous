#!/usr/bin/env bash
# =====================================================================
# NOUS Automated Cloud Server Provisioning & Deployment Script
# Supports: Ubuntu 22.04 / 24.04 LTS, Debian 12, CentOS/RHEL 9
# =====================================================================

set -e

echo "======================================================================"
echo "      NOUS PERSONAL AI ASSISTANT - CLOUD SERVER SETUP"
echo "      'Continuous Minute-to-Minute Autonomous Execution'"
echo "======================================================================"

# 1. Check Root Privileges
if [ "$EUID" -ne 0 ]; then
  echo "[ERROR] Please run this script with sudo or as root: sudo bash deploy/cloud_deploy.sh"
  exit 1
fi

INSTALL_DIR="/opt/nous"
SERVICE_USER="nous"

# 2. Update Operating System packages
echo "\n[STEP 1/6] Updating system packages..."
apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    python3-venv \
    sqlite3 \
    build-essential \
    ufw

# 3. Create Dedicated Service User
echo "\n[STEP 2/6] Configuring dedicated service user '${SERVICE_USER}'..."
if ! id "${SERVICE_USER}" &>/dev/null; then
    useradd --system --shell /bin/false --home-dir "${INSTALL_DIR}" --create-home "${SERVICE_USER}"
fi

# 4. Clone or Sync Codebase to /opt/nous
echo "\n[STEP 3/6] Syncing codebase into ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}"
cp -r . "${INSTALL_DIR}/"
chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}"

# 5. Set Up Python Virtual Environment
echo "\n[STEP 4/6] Creating Python virtual environment & installing dependencies..."
cd "${INSTALL_DIR}"
python3 -m venv .venv
chown -R "${SERVICE_USER}:${SERVICE_USER}" .venv
sudo -u "${SERVICE_USER}" "${INSTALL_DIR}/.venv/bin/pip" install --upgrade pip
sudo -u "${SERVICE_USER}" "${INSTALL_DIR}/.venv/bin/pip" install -r requirements.txt

# 6. Install & Configure Local Ollama Engine
echo "\n[STEP 5/6] Checking Local Ollama Engine..."
if ! command -v ollama &>/dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Ensure Ollama service is enabled and running
systemctl enable ollama
systemctl start ollama
echo "Pulling default local model (qwen2.5:3b)..."
ollama pull qwen2.5:3b || echo "[WARNING] Could not pull model now; daemon will pull on first online connection."

# 7. Configure and Enable Systemd Service
echo "\n[STEP 6/6] Configuring Systemd Auto-Start Service..."
cp "${INSTALL_DIR}/deploy/systemd/nous.service" /etc/systemd/system/nous.service
systemctl daemon-reload
systemctl enable nous.service
systemctl restart nous.service

# Configure Firewall
if command -v ufw &>/dev/null; then
    ufw allow 8000/tcp comment "NOUS Assistant Web" || true
fi

echo "\n======================================================================"
echo "  NOUS CLOUD DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "======================================================================"
echo " - Service Status: systemctl status nous.service"
echo " - Live Dashboard: http://<YOUR_SERVER_IP>:8000/"
echo " - Health Probe:   curl http://127.0.0.1:8000/api/health"
echo " - Minute Daemon:  curl http://127.0.0.1:8000/api/automation/daemon/status"
echo "======================================================================"
