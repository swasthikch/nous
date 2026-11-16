# NOUS — SYSTEM DEVELOPMENT ROADMAP

This roadmap establishes the sequential, phased engineering plan to transform the existing NOUS repository into a full-fledged Personal AI Operating System.

---

## 1. Master Development Tracker

| Phase | Phase Name | Status | Primary Objectives | Deliverables / Files |
| :---: | :--- | :---: | :--- | :--- |
| **0** | **Complete Project Audit** | **COMPLETED** | Comprehensive codebase inspection, security audit, deployment review, architecture definition. | `PROJECT_AUDIT.md`, `ARCHITECTURE.md`, `FEATURE_STATUS.md`, `DEVELOPMENT_ROADMAP.md` |
| **1** | **Central AI Brain** | **COMPLETED** | Central Orchestrator, LLM Provider Abstraction, Real-time Streaming (SSE/WebSocket), Context Builder, Multi-model Routing. | `ai_core/orchestrator.py`, `providers/base.py`, `providers/ollama_provider.py`, `providers/cloud_provider.py`, `api/chat.py` |
| **2** | **Complete Memory Engine** | **COMPLETED** | 5-tier memory taxonomy (Working, Personal, Project, Knowledge, Episodic), Stanford cognitive ranking, conversational extractor, export. | `memory/models.py`, `memory/manager.py`, `memory/ranker.py`, `memory/extractor.py`, `api/memory_api.py` |
| **3** | **Safe Tool Framework** | **COMPLETED** | 5-level permission gate (READ/PREPARE/WRITE/EXTERNAL/SENSITIVE), cryptographic HITL tokens, timeout sandbox, execution logger. | `tools/permissions.py`, `tools/approval.py`, `tools/registry.py`, `tools/logger.py`, `api/tools_api.py` |
| **4** | **Specialized AI Agents** | **COMPLETED** | Research Agent (web/arXiv), Coding Agent (repo analysis/testing), Productivity Agent, Market Agent, File Agent with shared memory. | `agents/base.py`, `agents/research_agent.py`, `agents/coding_agent.py`, `agents/productivity_agent.py`, `agents/file_agent.py`, `agents/market_agent.py`, `agents/coordinator.py`, `api/agents_api.py` |
| **5** | **Voice Assistant System**| **COMPLETED** | Browser Web Speech optimization, speech text formatting, bilingual support (en-US, en-IN, hi-IN), animated waveform, local Whisper hook. | `voice/formatter.py`, `voice/engine.py`, `api/voice_api.py`, `frontend/css/style.css`, `frontend/js/app.js` |
| **6** | **Windows Desktop Companion**| **COMPLETED**| Pure ctypes hardware telemetry (CPU, RAM, Battery, Storage, Ollama), outbound heartbeat, token auth, local Ollama proxy, silent autostart. | `desktop/telemetry.py`, `desktop/companion.py`, `desktop/autostart.py`, `api/desktop_api.py` |
| **7** | **Personal AI OS Modules** | **COMPLETED** | Executive Overview Aggregator, Graphical Workspace File Explorer with traversal defense, Unified Settings with masked API keys. | `backend/app/api/dashboard_api.py`, `backend/tests/test_phase7_dashboard.py`, `frontend/js/app.js`, `frontend/index.html` |
| **8** | **Autonomous AI Agent & Workflows** | **COMPLETED** | Multi-step task decomposition, DAG step evaluation, inter-agent context flow, cryptographic HITL approval pause, pause/resume/cancel/retry controls, SQLite WAL logging. | `workflows/models.py`, `workflows/planner.py`, `workflows/engine.py`, `workflows/db.py`, `api/workflows_api.py` |
| **9** | **Multi-Device Support & Mobile PWA** | **COMPLETED** | PWA Manifest, service worker offline shell, glowing neon app icons, host LAN auto-discovery, 1-click SVG QR mobile pairing, cross-device state sync, push notifications. | `frontend/manifest.json`, `frontend/sw.js`, `api/multidevice_api.py` |
| **10** | **Security Hardening & Production Auth** | **COMPLETED** | PBKDF2-HMAC-SHA256 password cryptography (100k rounds), native HMAC-SHA256 JWT tokens with tamper detection, RBAC roles (admin/user/guest), SQLite WAL persistence (`nous_auth.db`), FastAPI Bearer dependency. | `backend/app/security/auth.py`, `api/auth_api.py` |
| **11** | **Cloud Persistence & Deployment** | **COMPLETED** | WAL Checkpoint flush, automated compressed database snapshot archiving (`latest_snapshot.tar.gz`), container state restoration, free-tier Render keep-alive pinger, zero-budget cloud optimization. | `cloud/persistence.py`, `cloud/keepalive.py`, `api/cloud_api.py` |

---

## 2. Phase-by-Phase Implementation Specifications

### Phase 1: Central AI Brain & Orchestration Upgrade (Immediate Next Step)
- **Goal:** Replace brittle regex-only intent routing with an intelligent central orchestrator capable of multi-step reasoning, dynamic tool selection, and real-time response streaming.
- **Key Deliverables:**
  1. `backend/app/ai_core/orchestrator.py`: Central orchestration engine coordinating input parsing, context budgeting, tool execution, and response synthesis.
  2. `backend/app/providers/base.py`: Abstract LLM provider interface (`generate()`, `stream()`, `embed()`).
  3. `backend/app/providers/ollama.py`: Local Ollama adapter supporting non-streaming and token-by-token streaming.
  4. `backend/app/providers/cloud.py`: OpenAI-compatible cloud client for Groq, OpenRouter, OpenAI, and Gemini.
  5. `backend/app/api/chat.py`: Server-Sent Events (SSE) `/api/chat/stream` endpoint for instant token streaming to the frontend.
  6. Fast-path intent caching: Keep existing regex patterns as a 0ms preliminary cache for standard commands (`time`, `weather`, `calc`), falling back to LLM reasoning for conversational queries.

### Phase 2: Complete 5-Tier Memory Engine
- **Goal:** Implement persistent, categorizable, and semantically retrievable long-term memory that survives restarts and cross-device sessions.
- **Key Deliverables:**
  1. 5-Tier taxonomy: Working, Personal, Project, Knowledge, and Episodic memory tables.
  2. Hybrid Retrieval: Keyword search (BM25) combined with local semantic embeddings.
  3. Passive Extractor: Extracts user preferences, names, and key project decisions from natural chat conversations without requiring explicit "remember that" triggers.
  4. Memory Controls: Export memory to JSON/Markdown, edit memory, and selective wipe.

### Phase 3: Tool-Calling & Safe Permission Framework (COMPLETED)
- **Status:** **Completed & Verified (100% test pass)**
- **Goal:** Create a strict zero-trust tool execution framework that prevents prompt injection and unauthorized system changes.
- **Key Deliverables:**
  1. 5 permission tiers: READ, PREPARE, WRITE, EXTERNAL_ACTION, SENSITIVE_ACTION.
  2. Human-In-The-Loop (HITL) approval tokens: Cryptographically secure (`secrets.token_urlsafe(32)`), time-bounded (300s TTL) single-use verification tokens required before modifying files, executing shell commands, or sending emails. Replay protection guaranteed.
  3. Execution safety timeouts: Asyncio timeouts (`asyncio.wait_for`) applied to all registered tools to prevent infinite blocking.
  4. Immutable Security Audit Logger: Persists execution logs with automated parameter secret/API key redaction to `nous_security.db`.
  5. REST endpoints `/api/tools`, `/api/tools/approvals`, `/api/tools/logs` mounted and operational. Full backward-compatibility with existing 50 tools.

### Phase 4: Specialized AI Agents (COMPLETED)
- **Status:** **Completed & Verified (100% test pass)**
- **Goal:** Build goal-directed agents that communicate through the central brain and share memory.
- **Key Deliverables:**
  1. Base Agent Framework: Polymorphic `BaseAgent` integrated with `memory_manager` and `safe_tool_registry`.
  2. Research Agent: Deep multi-source web investigations (DuckDuckGo, Wikipedia, arXiv), evidence-backed synthesis, citations, auto-indexes into Memory Tier `KNOWLEDGE`.
  3. Coding Agent: Local repository inspection (`git status`), Python syntax verification (`py_compile`), architecture recording in Memory Tier `PROJECT`.
  4. Productivity Agent: Schedule coordination, Eisenhower briefing, missed activity rescheduling, auto-indexes into Memory Tier `EPISODIC`.
  5. File Agent: Bounded workspace navigation, document reading, directory traversal security sandbox, auto-indexes into Memory Tier `KNOWLEDGE`.
  6. Market Agent: Benchmark quote monitoring, FII/DII institutional flows, 20-factor causal reasoning, mandatory educational disclaimer, and strict Zero-Trading safety gate.
  7. Agent Coordinator & REST APIs: Dynamic intent routing and `/api/agents` endpoints.

### Phase 5: Voice Assistant & Speech Pipeline (COMPLETED)
- **Status:** **Completed & Verified (100% test pass)**
- **Goal:** Provide responsive, natural voice interaction with hands-free operation and bilingual design.
- **Key Deliverables:**
  1. Frontend Web Speech optimization with animated voice frequency waveform rendering.
  2. Speech interruption handling: Speech synthesis stops immediately when the user taps or speaks (barge-in support).
  3. Bilingual support: English (US/India) and Hindi (`hi-IN`) language selection and Devanagari/Hinglish detection.
  4. Hands-free Conversational Loop: Automatic continuous listening turn-taking.
  5. Conversational Spoken Formatter: Strips complex markdown tables, code blocks, URLs, and citations into clean, concise spoken dialogue.
  6. Architectural hook for local Whisper STT payloads via `/api/voice/transcribe-audio`.

### Phase 6: Windows Desktop Companion (COMPLETED)
- **Status:** **Completed & Verified (100% test pass)**
- **Goal:** Bridge the user's Windows 11 laptop hardware (local Ollama, local files) to the 24/7 cloud service without exposing open ports to the internet.
- **Key Deliverables:**
  1. `desktop/telemetry.py`: Pure ctypes Windows 11 kernel API telemetry (CPU, RAM, Battery, Storage, Ollama) with 0 third-party pip dependencies.
  2. `desktop/companion.py`: Lightweight Python desktop background client with periodic outbound heartbeats and latency tracking.
  3. Cryptographic authentication: Secure shared token (`nous_desk_...`) for laptop-server authorization.
  4. Local Ollama proxy relay: Allows cloud instance to forward heavy inference to local laptop Ollama for free execution.
  5. `desktop/autostart.py`: Silent VBScript autostart launcher and batch runner for Windows 11 logon without visible CMD windows.
  6. REST endpoints `/api/desktop/heartbeat`, `/api/desktop/status`, `/api/desktop/autostart`.

### Phase 7: Integrated Dashboard, Workspace & Settings (COMPLETED)
- **Status:** **Completed & Verified (100% test pass via `test_phase7_dashboard.py`)**
- **Goal:** Deliver a unified operating system experience across productivity, files, executive overview, and system configuration.
- **Key Deliverables:**
  1. `backend/app/api/dashboard_api.py`: Comprehensive `/api/dashboard/overview` aggregating native hardware telemetry, 5-tier memory distributions, pending HITL authorization tokens, active agents, today's schedule, and market flows.
  2. Workspace File Explorer: Endpoints `/api/dashboard/files`, `/read`, `/write`, `/delete` with strict path traversal boundary verification (`_resolve_safe_path`) preventing directory escape attacks (`403 Forbidden`).
  3. Unified Settings & Zero-Leak Credential Masking: Endpoints `/api/dashboard/settings` with masked API keys (`sk-••••••••`, `ghp_••••••••`), persistent voice parameters, and privacy lock switches.
  4. Frontend Integration: Real-time native Windows 11 hardware telemetry (CPU, RAM free/total %, Battery status) and active counter badges dynamically rendered on the sidebar.

### Phase 8: Autonomous Workflows & Execution Engine (COMPLETED)
- **Status:** **Completed & Verified (100% test pass via `test_phase8_workflows.py`)**
- **Goal:** Enable multi-step autonomous tasks with strict safety limits and human oversight.
- **Key Deliverables:**
  1. `backend/app/workflows/models.py`: DAG step dependencies (`depends_on`), execution status tracking (`PLANNING`, `RUNNING`, `PAUSED_APPROVAL`, `PAUSED_USER`, `COMPLETED`, `FAILED`, `CANCELLED`).
  2. `backend/app/workflows/planner.py`: Plan-and-Solve task decomposition routing to specialized agents with write/external risk detection.
  3. `backend/app/workflows/engine.py`: Sequential execution engine with context data propagation, single-use cryptographic HITL approval token pauses, and full lifecycle controls (`start`, `pause`, `resume`, `cancel`, `retry`).
  4. `backend/app/workflows/db.py`: SQLite Write-Ahead Logging (WAL) mode persistence and immutable step execution audit logs.
  5. `backend/app/api/workflows_api.py`: Complete REST API endpoints (`POST /plan`, `GET /`, `GET /{id}`, `POST /start`, `/pause`, `/resume`, `/cancel`, `/retry`).

### Phase 9: Multi-Device Synchronization & Mobile PWA (COMPLETED)
- **Status:** **Completed & Verified (100% test pass via `test_phase9_multidevice.py`)**
- **Goal:** Seamless continuity between laptop and mobile phone.
- **Key Deliverables:**
  1. `frontend/manifest.json`: Full PWA manifest (`standalone` mode, `#00d4ff` theme color, dark background `#0a0c10`).
  2. `frontend/sw.js`: Service worker implementing offline shell pre-caching, fetch cache-first with network fallback, and push notification handling.
  3. `frontend/icons/`: High-resolution standalone PWA icons (`icon-192.png`, `icon-512.png`).
  4. `backend/app/api/multidevice_api.py`:
     - `/api/multidevice/network-info`: Discovers host LAN IP (`192.168.x.x`), generates mobile access URL (`http://<LAN_IP>:8000/`), and produces zero-dependency SVG QR pairing code for 1-click mobile phone camera linking.
     - `/api/multidevice/sync`: Cross-device state synchronizer delivering pending approval requests, active chat state, and queued notifications.
     - `/api/multidevice/notify`: Web push notification dispatcher for autonomous alerts.

### Phase 10: Security Hardening & Production Authentication (COMPLETED)
- **Status:** **Completed & Verified (100% test pass via `test_phase10_security_auth.py`)**
- **Goal:** Enterprise-grade security review, zero-dependency password cryptography, and token-based RBAC.
- **Key Deliverables:**
  1. `backend/app/security/auth.py`: Pure Python PBKDF2-HMAC-SHA256 password hashing (100,000 rounds, 32-byte salt) and native HMAC-SHA256 JWT token generation, signature tamper validation, and expiry enforcement.
  2. User Persistence & RBAC: SQLite WAL database `nous_auth.db` with roles (`admin`, `user`, `guest`).
  3. `backend/app/api/auth_api.py`: REST endpoints `/api/auth/register`, `/login`, `/me`, `/logout` with FastAPI Bearer token dependency (`get_current_user`, `require_role`).

### Phase 11: Cloud Persistence & Deployment (COMPLETED)
- **Status:** **Completed & Verified (100% test pass via `test_phase11_cloud_deploy.py`)**
- **Goal:** Keep the entire operating system running 24/7 at zero cost with automated backups and sleep prevention.
- **Key Deliverables:**
  1. `backend/app/cloud/persistence.py`: Automatic SQLite WAL checkpointing (`PRAGMA wal_checkpoint(FULL);`) and compressed tar.gz state snapshot creation (`data/backups/latest_snapshot.tar.gz`) with container state restoration.
  2. `backend/app/cloud/keepalive.py`: Autonomous keep-alive health pinger preventing free-tier container sleep during active hours.
  3. `backend/app/api/cloud_api.py`: Cloud persistence and pinger control endpoints (`/api/cloud/status`, `/snapshot`, `/restore`, `/keepalive/ping`, `/keepalive/toggle`).
