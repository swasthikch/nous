# NOUS Cloud Server Deployment & Offline Minute-to-Minute Execution Guide

> **"Your Intelligence. Your Memory. Your Assistant."**

This document details how to host NOUS on cloud servers (VPS, Docker, Render, Fly.io, Railway) and how its **Autonomous Minute Daemon** maintains continuous, minute-to-minute operation even in the complete absence of network connectivity.

---

## 1. The Minute-to-Minute Autonomous Engine Architecture

NOUS includes an integrated, zero-crash background worker (`AutonomousMinuteDaemon` in [`backend/app/automation/daemon.py`](file:///e:/nous/backend/app/automation/daemon.py)) that ticks every 60 seconds.

### 🌐 Network Presence & Zero-Network Fault-Tolerance

```
                      +-----------------------------+
                      |   60-Second Minute Clock    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Non-Blocking Network Probe |
                      |  (0.8s socket DNS check)    |
                      +--------------+--------------+
                                     |
                     +---------------+---------------+
                     |                               |
              [Network Available]             [Network Absent]
                     |                               |
                     v                               v
             +---------------+               +---------------+
             | ONLINE STATE  |               | OFFLINE STATE |
             +-------+-------+               +-------+-------+
                     |                               |
                     |--- Execute Scheduled Tasks ---| (Local tasks only)
                     |--- Check Routine Schedule  ---| (Read SQLite WAL)
                     |--- Check Milestone Deadlines--| (Read SQLite WAL)
                     |--- SQLite WAL Checkpointing---| (Zero-lock PASSIVE)
                     |--- Log Minute Heartbeat    ---| (Persist to DB)
                     |                               |
                     +---------------+---------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Heartbeat Audit Entry in   |
                      |     nous_automation.db      |
                      +-----------------------------+
```

### Key Guarantees During Network Absence:
1. **Zero Unhandled Exceptions**: Socket connection drops, DNS failures, or air-gapped environments are caught cleanly within 0.8s.
2. **Local Task Continuance**: Routine reminders, schedule verification, project milestone tracking, and local file operations continue unaffected.
3. **Audit Trail Persistence**: Every tick writes a timestamped record to `execution_history` in `data/database/nous_automation.db`.
4. **Local LLM Conversing**: By pairing with an in-cluster or host-level Ollama service, NOUS answers user queries using local models (`qwen2.5:3b`) without requiring internet access.

---

## 2. Cloud Deployment Option A: Docker Compose (Recommended)

Deploy the full stack (NOUS Brain + Local Ollama Engine + Persistent Volumes):

```bash
# 1. Clone repository on your cloud server
git clone https://github.com/nous-assistant/core.git /opt/nous
cd /opt/nous

# 2. Build and launch container stack in detached mode
docker compose up -d --build

# 3. Pull the local AI model inside the container
docker compose exec ollama ollama pull qwen2.5:3b

# 4. Check live container status
docker compose ps
```

The stack automatically sets `restart: always` so any host reboot or process crash will auto-recover within 5 seconds.

---

## 3. Cloud Deployment Option B: Ubuntu / Debian Linux VPS

For native bare-metal or cloud VPS (AWS EC2, DigitalOcean Droplet, Linode, Hetzner, GCP Compute Engine):

### Automated 1-Command Script
```bash
sudo bash deploy/cloud_deploy.sh
```

### Manual Step-by-Step Setup
1. **Install System Packages**:
   ```bash
   sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip curl git sqlite3
   ```
2. **Install Local Ollama**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull qwen2.5:3b
   ```
3. **Configure Systemd Unit**:
   ```bash
   sudo cp deploy/systemd/nous.service /etc/systemd/system/nous.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now nous.service
   ```
4. **Verify Service Health**:
   ```bash
   sudo systemctl status nous.service
   curl http://127.0.0.1:8000/api/health
   curl http://127.0.0.1:8000/api/automation/daemon/status
   ```

---

## 4. Cloud Deployment Option C: Managed Cloud PaaS

### Render.com
1. Connect your Git repository to Render.
2. Select **Web Service** using Docker runtime.
3. Attach a **Persistent Disk** mounted at `/app/data` (10 GB recommended).
4. Render automatically detects `render.yaml` and deploys.

### Fly.io
```bash
# 1. Launch app
fly launch --no-deploy

# 2. Create persistent volume for SQLite databases
fly volumes create nous_data --size 10 --region iad

# 3. Deploy
fly deploy
```

### Railway.app
1. Create a new Railway project from GitHub.
2. Railway detects `Dockerfile` and `railway.json`.
3. Set environment variable `PORT=8000` and attach a volume at `/app/data`.

---

## 5. Live Minute-to-Minute Diagnostics & API Endpoints

| HTTP Method | Route | Description |
|---|---|---|
| `GET` | `/api/health` | Comprehensive server and Ollama connectivity status |
| `GET` | `/api/automation/daemon/status` | Live minute daemon status, tick counts, and uptime |
| `POST` | `/api/automation/daemon/tick-now` | Force an immediate tick (supports `?force_offline=true`) |
| `GET` | `/api/automation/history` | Historical audit logs including minute heartbeat records |
