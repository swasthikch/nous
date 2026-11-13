# NOUS — Advanced Personal AI Assistant

> **"Your Intelligence. Your Memory. Your Assistant."**

NOUS is an advanced, JARVIS-inspired personal AI assistant built with a **hybrid local/cloud architecture**. It combines strict zero-trust security guardrails, multi-subsystem persistent storage across 7 SQLite WAL databases, anti-hallucination tool calling, hands-free voice engine, email intelligence with indirect prompt-injection defenses, financial market causal reasoning, web research note-taking, sandboxed computer automation, and real-time hardware telemetry.

---

## 🖥️ System Hardware Profile

NOUS is calibrated and optimized for local edge performance on:

- **Operating System:** Windows 11 (64-bit AMD64)
- **Processor:** 13th Gen Intel(R) Core(TM) i5-1334U (10 Cores [2 P-cores + 8 E-cores], 12 Threads)
- **Memory (RAM):** 16 GB DDR4/DDR5 (Shared unified memory ceiling)
- **Graphics:** Intel(R) Iris(R) Xe Graphics (Integrated GPU)
- **Local AI Engine:** Ollama (`http://127.0.0.1:11434`)
- **Active Local Model:** `qwen2.5:3b` (Quantized GGUF `Q4_K_M`, ~1.9 GB footprint)

---

## 🚀 One-Click Quickstart (Production)

### Option 1: Double-Click Windows Script (Easiest)
Simply double-click **`run_nous.bat`** in the project root:
1. Automatically activates the virtual environment (`.venv`).
2. Confirms Ollama local engine status.
3. Automatically opens your default web browser to `http://127.0.0.1:8000/`.
4. Starts the fast Uvicorn ASGI server with live reload.

### Option 2: PowerShell Console
```powershell
.\start.ps1
```

### Option 3: Manual Command Line
```powershell
.\.venv\Scripts\activate
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🏛️ Comprehensive Architecture (All 15 Phases)

| Phase | Subsystem | Core Features & Implementation |
|---|---|---|
| **Phase 1 & 2** | **Core Brain & Anti-Hallucination** | Regex-boosted 0ms intent classifier, multi-turn session persistence in JSON, strictly verified tool calling. |
| **Phase 3 & 4** | **Hybrid Model Router & Ollama** | Dynamic routing assessing query complexity. Local execution on `qwen2.5:3b` in <800ms with cloud fallback. |
| **Phase 5 & 6** | **Persistent Memory & JARVIS Voice** | SQLite WAL `nous_memory.db` with relevance scoring. Web Speech API bidirectional voice orb with wake-word. |
| **Phase 7** | **Daily Life & Routine Manager** | Chronological schedule tracking, conflict detection, intelligent rescheduling, and evening reviews. |
| **Phase 8** | **Email Intelligence & Injection Defense** | Google OAuth 2.0, `EmailSanitizer` defending against prompt injection attacks, HITL draft approval gates. |
| **Phase 9 & 10** | **Projects & GitHub Telemetry** | Milestone management, inactivity audits, live GitHub commit/PR/issue tracking with cache. |
| **Phase 11** | **Market Intelligence & Causal Engine** | Real-time NSE/BSE & global stock tracking, 20-factor causal reasoning analyzing yields, crude, and FII flows. |
| **Phase 12** | **Web Research & Knowledge Notebook** | Live search without paid API keys, automated synthesis, and persistent Markdown research notes in SQLite. |
| **Phase 13** | **Computer & Task Automation** | Path traversal prevention, dangerous command blocklist, HITL 5-minute approval tokens, background scheduler. |
| **Phase 14** | **Security Vault & Privacy Controls** | Zero-trust credential redactor, Offline Lockdown switch, Memory Retention Pause, immutable audit trail. |
| **Phase 15** | **System Diagnostics & Polish** | Hardware load telemetry (16GB shared limit), database integrity checks across all 7 DBs, in-process smoke test. |
| **Public APIs** | **Open Keyless API Integrations** | Curated from `public-apis/public-apis`: Open-Meteo Weather, Free Dictionary API, Frankfurter ECB Currency, Official Joke API with offline fallback. |
| **Cloud & Daemon**| **Autonomous Minute-to-Minute Worker** | 24/7 background daemon ticking every 60s, 100% offline-resilient, Docker container, Systemd unit, zero-crash network probe. |

---

## 💾 The 7 Persistent SQLite Storage Engines

All databases operate in Write-Ahead Logging (`WAL`) mode in `data/database/`:

1. **`nous_memory.db`**: User profile, personal info, project facts, routine habits, and conversation takeaways.
2. **`nous_routine.db`**: Scheduled activities, completion tracking, time-block conflict logs, and daily debriefs.
3. **`nous_projects.db`**: Codebase projects, milestone roadmaps, architectural notes, and GitHub telemetry cache.
4. **`nous_market.db`**: Watchlist instruments, price alert thresholds, market snapshots, and alert history.
5. **`nous_research.db`**: Investigated topics, deep synthesis reports, and persistent knowledge notebook entries.
6. **`nous_automation.db`**: Scheduled automation tasks, shell execution history, and command latency metrics.
7. **`nous_security.db`**: Immutable security audit trail, offline lockdown state, and privacy policy configurations.

---

## 🛡️ Security, Privacy & Zero-Trust Architecture

- **Offline Lockdown**: With one toggle, NOUS disconnects all external cloud APIs and guarantees 100% on-device inference via local Ollama.
- **Sensitive Data Redaction**: Automatic regex masking intercepts and scrubs OpenAI keys, Google API keys, GitHub PATs, JWT tokens, credit card numbers, URL passwords, and private keys before text reaches any LLM or log file.
- **Human-In-The-Loop (HITL)**: Actions that send emails, write files, or execute shell commands require explicit user verification tokens with 5-minute expiration windows.
- **Workspace Containment**: Computer automation is strictly locked to `workspace/`. Path traversal sequences (`../`, absolute drive roots) are permanently blocked.

---

## ☁️ Cloud Deployment & Minute-to-Minute Offline Resilience

NOUS is containerized and cloud-ready for continuous 24/7 background operation:

- **Autonomous Minute Daemon**: Automatically ticks every 60 seconds. Performs non-blocking network presence probes (`0.8s` timeout).
- **Zero-Network Fault-Tolerance**: If the cloud host or local machine loses internet connectivity, the daemon seamlessly switches into Autonomous Offline Mode without crashing. It evaluates local routine schedules, maintains SQLite WAL journals, and records persistent heartbeat logs.
- **Docker & Docker Compose**: Multi-container stack (`Dockerfile`, `docker-compose.yml`) pairing NOUS with an internal Ollama container and persistent SQLite volumes.
- **Linux Systemd Service**: Auto-restart unit `deploy/systemd/nous.service` ensures automatic recovery within 5 seconds if a host crashes or reboots.
- **Cloudflare Tunnel (100% Free Remote Gateway)**: Launch [`deploy/cloudflare/start_cloudflare_tunnel.bat`](deploy/cloudflare/start_cloudflare_tunnel.bat) to expose NOUS over a free, encrypted Cloudflare HTTPS URL (`https://xxxx.trycloudflare.com`) accessible from any phone worldwide.
- *Detailed instructions for Docker, Cloudflare, Ubuntu VPS, Render, Fly.io, and Railway are in [`docs/CLOUD_DEPLOYMENT.md`](docs/CLOUD_DEPLOYMENT.md) and [`docs/CLOUDFLARE_TUNNEL.md`](docs/CLOUDFLARE_TUNNEL.md).*

---

## 🧪 Comprehensive Verification Suite

Run all verification test suites directly in PowerShell:

```powershell
# Execute the Master Runner (All 15 Suites)
.\.venv\Scripts\python.exe backend/tests/run_all_tests.py

# Or run individual verification suites:
.\.venv\Scripts\python.exe backend/tests/test_phase1.py
.\.venv\Scripts\python.exe backend/tests/test_phase2.py
.\.venv\Scripts\python.exe backend/tests/test_phase5.py
.\.venv\Scripts\python.exe backend/tests/test_phase6.py
.\.venv\Scripts\python.exe backend/tests/test_phase7.py
.\.venv\Scripts\python.exe backend/tests/test_phase8.py
.\.venv\Scripts\python.exe backend/tests/test_phase9.py
.\.venv\Scripts\python.exe backend/tests/test_phase11.py
.\.venv\Scripts\python.exe backend/tests/test_phase12.py
.\.venv\Scripts\python.exe backend/tests/test_phase13.py
.\.venv\Scripts\python.exe backend/tests/test_phase14.py
.\.venv\Scripts\python.exe backend/tests/test_phase15.py
.\.venv\Scripts\python.exe backend/tests/test_public_apis.py
.\.venv\Scripts\python.exe backend/tests/test_cloud_daemon.py
.\.venv\Scripts\python.exe backend/tests/test_live_server.py
```

*For detailed architectural explanations, schema diagrams, and subsystem contracts, refer to [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).*
