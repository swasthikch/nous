# NOUS — COMPLETE PROJECT AUDIT REPORT (PHASE 0)
**Date:** November 16, 2026  
**Auditor:** Senior AI Architect, DevOps & Security Engineering Team  
**Project:** NOUS Personal AI Operating System  
**Repository:** https://github.com/swasthikch/nous  
**Live Cloud Deployment:** https://nous-8k2o.onrender.com  

---

## 1. Executive Summary

NOUS was conceived as a personal AI operating system combining a JARVIS-like assistant, autonomous agent, and centralized AI brain. The project currently has substantial foundational code: an operational FastAPI backend, a responsive cyberpunk/dark-themed single-page application (SPA), 15 automated test suites, 7 SQLite Write-Ahead Logging (WAL) storage databases, an autonomous minute-to-minute daemon, and live deployment on Render.com via Docker.

However, a thorough code-level inspection reveals critical gaps that prevent NOUS from operating as a true personal AI operating system today:
1. **Zero User Authentication or Authorization:** The API has open CORS (`*`), no user accounts, no password hashing, no session tokens, and no JWT authentication. Anyone with the URL can access all databases, files, and tools.
2. **Heuristic/Regex-Only Intent Classification:** The system relies almost entirely on regular expressions to detect intent. It lacks an LLM-driven reasoning and planning engine for complex, multi-turn, multi-step natural language commands.
3. **Disconnected Specialized Capabilities:** Features like Market Intelligence, Research, Email, and Projects exist largely as independent scripts/tools rather than cohesive autonomous agents communicating through a shared orchestrator.
4. **Cloud Storage Ephemerality:** Render's free tier uses ephemeral container storage. All 7 SQLite databases and chat sessions are wiped on container rebuilds or redeployments unless backed by persistent storage or an external database.
5. **No Local-to-Cloud Bridge (Desktop Companion):** While local Ollama is configured for development, the cloud deployment on Render cannot access the user's laptop Ollama or local files without an authenticated outbound desktop agent.
6. **No Real Streaming Responses:** Chat endpoints only support synchronous HTTP POST without WebSockets or Server-Sent Events (SSE) token streaming.

---

## 2. Existing Repository Directory Structure

```
E:\nous\
├── .dockerignore
├── docker-compose.yml
├── Dockerfile
├── fly.toml
├── railway.json
├── render.yaml
├── requirements.txt
├── README.md
├── run_nous.bat
├── start.ps1
│
├── backend\
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   ├── app\
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── api\
│   │   │   ├── automation_api.py
│   │   │   ├── chat.py
│   │   │   ├── diagnostics_api.py
│   │   │   ├── email_api.py
│   │   │   ├── health.py
│   │   │   ├── market_api.py
│   │   │   ├── memory_api.py
│   │   │   ├── projects_api.py
│   │   │   ├── public_apis_api.py
│   │   │   ├── research_api.py
│   │   │   ├── routine_api.py
│   │   │   ├── routing_api.py
│   │   │   ├── security_api.py
│   │   │   ├── sessions_api.py
│   │   │   └── voice_api.py
│   │   ├── automation\
│   │   │   ├── daemon.py
│   │   │   ├── db.py
│   │   │   ├── manager.py
│   │   │   └── security.py
│   │   ├── core\
│   │   │   ├── ai_engine.py
│   │   │   ├── cloud_provider.py
│   │   │   ├── conversation.py
│   │   │   ├── diagnostics.py
│   │   │   ├── intent.py
│   │   │   ├── model_router.py
│   │   │   ├── ollama_client.py
│   │   │   ├── permissions.py
│   │   │   └── tool_registry.py
│   │   ├── email\
│   │   │   ├── analyzer.py
│   │   │   ├── client.py
│   │   │   ├── oauth.py
│   │   │   └── sanitizer.py
│   │   ├── market\
│   │   │   ├── db.py
│   │   │   ├── engine.py
│   │   │   └── fetcher.py
│   │   ├── memory\
│   │   │   ├── db.py
│   │   │   └── manager.py
│   │   ├── projects\
│   │   │   ├── db.py
│   │   │   ├── github_client.py
│   │   │   └── manager.py
│   │   ├── research\
│   │   │   ├── db.py
│   │   │   ├── engine.py
│   │   │   ├── searcher.py
│   │   │   └── summarizer.py
│   │   ├── routine\
│   │   │   ├── db.py
│   │   │   └── manager.py
│   │   ├── security\
│   │   │   ├── db.py
│   │   │   ├── redactor.py
│   │   │   └── vault.py
│   │   ├── services\
│   │   │   └── public_apis.py
│   │   └── voice\
│   │       └── engine.py
│   └── tests\
│       ├── run_all_tests.py
│       ├── test_cloud_daemon.py
│       ├── test_live_server.py
│       ├── test_phase1.py to test_phase15.py
│       └── test_public_apis.py
│
├── frontend\
│   ├── index.html
│   ├── css\style.css
│   └── js\app.js
│
├── data\
│   ├── credentials\
│   ├── database\ (7 SQLite databases)
│   ├── sessions\ (*.json session files)
│   ├── email_drafts.json
│   ├── mailbox_cache.json
│   └── voice_settings.json
│
├── deploy\
│   ├── cloud_deploy.sh
│   ├── start_phone_link.bat
│   ├── cloudflare\
│   ├── systemd\nous.service
│   └── windows\
│
├── docs\
│   ├── ARCHITECTURE.md
│   ├── CLOUDFLARE_TUNNEL.md
│   └── CLOUD_DEPLOYMENT.md
│
└── workspace\
    └── automation_log.txt
```

---

## 3. Comprehensive Feature Inventory & Status

Each feature has been audited against the physical codebase and categorized into one of five statuses:
- **Working:** Complete, tested, operational.
- **Partially Working:** Basic functionality works, but key architectural pieces are simulated or incomplete.
- **Broken:** Code exists but fails under real conditions or is fundamentally blocked.
- **Not Implemented:** Missing entirely from the system.
- **Needs Security Improvement:** Serious security, injection, or permission risks.

| Subsystem / Feature | Location | Status | Technical Details & Limitations |
| :--- | :--- | :--- | :--- |
| **User Authentication & RBAC** | `backend/app/api/` | **Not Implemented** | No signup/login routes, no user DB table, no password hashing (bcrypt/argon2), no JWT session tokens. |
| **CORS Configuration** | `backend/app/main.py:69` | **Needs Security Improvement** | `allow_origins=["*"]` allows any website to make authenticated/cross-origin requests against the local or cloud backend. |
| **Central AI Orchestrator** | `backend/app/core/ai_engine.py` | **Partially Working** | Orchestrates tool execution before LLM call, but lacks true planning loops, multi-agent communication, and reflection. |
| **Response Streaming** | `backend/app/api/chat.py` | **Not Implemented** | Only blocking `POST /api/chat` exists. No SSE (`text/event-stream`) or WebSockets (`ws://`) for token-by-token streaming. |
| **Intent Recognition** | `backend/app/core/intent.py` | **Partially Working** | 48 intent types detected, but 100% heuristic regex-based. Fails when natural phrasing deviates from regex patterns. |
| **Model Routing (Local/Cloud)** | `backend/app/core/model_router.py` | **Working** | Clean routing between local Ollama and OpenAI-compatible cloud endpoints with offline lockdown enforcement. |
| **Anti-Hallucination Tool Registry** | `backend/app/core/tool_registry.py` | **Working** | 48 registered tools with schema validation, risk classification, and observation formatting. |
| **Tool Permission & Approvals** | `backend/app/core/permissions.py` | **Partially Working** | Risk levels (LOW, MEDIUM, HIGH) and approval tokens exist, but token generation is unauthenticated; any client can trigger execution. |
| **Persistent Long-Term Memory** | `backend/app/memory/manager.py` | **Partially Working** | Stores key-value memories in SQLite with keyword search. Missing vector embeddings, semantic search, and memory decay/ranking. |
| **Ephemeral Container Storage** | Dockerfile / Render | **Needs Security & Infra Improvement** | Databases stored in container filesystem. Any container restart or redeploy erases all user memories and conversation sessions. |
| **Voice Interaction (STT / TTS)** | `frontend/js/app.js:1020` | **Partially Working** | Uses browser Web Speech API (`webkitSpeechRecognition` & `speechSynthesis`). No backend STT (Whisper) or offline TTS fallback. Fails in non-secure HTTP contexts. |
| **Daily Planner & Routine** | `backend/app/routine/manager.py` | **Working** | Complete SQLite CRUD, schedule generation, missed-activity rescheduling, and completion rate calculations. |
| **Email Intelligence & Sanitizer** | `backend/app/email/` | **Partially Working** | OAuth2 client and prompt injection sanitizer work, but fallback mailbox is purely mocked `mailbox_cache.json`. |
| **Project Intelligence & Git** | `backend/app/projects/` | **Working** | GitHub REST client fetches real commits/PRs; local milestone and task tracking with percentage calculation works. |
| **Market Intelligence Engine** | `backend/app/market/` | **Working** | Live NSE/BSE and Yahoo Finance quotes with RSS news correlation, 20-factor causal reasoning, and offline baselines. |
| **Web Research Engine** | `backend/app/research/` | **Working** | Multi-source aggregator (DuckDuckGo, Wikipedia, arXiv, curated fallbacks) with 8-part structured report generator. |
| **Autonomous Minute Daemon** | `backend/app/automation/daemon.py` | **Working** | Ticks every 60s, performs non-blocking network checks, logs heartbeats in SQLite WAL even when offline. |
| **Computer & Safe Automation** | `backend/app/automation/manager.py` | **Needs Security Improvement** | Executes PowerShell/bash commands inside `workspace/`. Substring blacklist (`rm -rf`, `format`) is bypassable via obfuscation. |
| **Sensitive Redaction & Vault** | `backend/app/security/` | **Working** | Regex masks API keys, bearer tokens, private keys, credit cards, and passwords before prompt injection and audit logging. |
| **Public APIs (Weather, Lexical, etc.)** | `backend/app/services/public_apis.py` | **Working** | Open-Meteo, Free Dictionary, Frankfurter ECB currency, and Official Joke API with offline fallbacks. |
| **Windows Desktop Companion** | `deploy/` | **Partially Working** | Windows batch scripts exist for autostart, lid power, and cloudflared tunnel, but no unified companion app linking laptop Ollama to cloud. |
| **Frontend UI / UX** | `frontend/` | **Partially Working** | Sleek dark UI with responsive mobile drawer, but lacks a central Overview Dashboard, dedicated File Explorer, and Unified Settings panel. |

---

## 4. Architectural Analysis & Code Smells

1. **Fragmentation of 7 Separate SQLite Databases:**
   The application maintains 7 independent `.db` files:
   - `nous_memory.db`
   - `nous_routine.db`
   - `nous_projects.db`
   - `nous_market.db`
   - `nous_research.db`
   - `nous_automation.db`
   - `nous_security.db`
   *Impact:* Relational integrity across subsystems is impossible without complex multi-database attachments. Migrating to a production-grade external database (PostgreSQL / Supabase / Neon) requires 7 migrations instead of 1 coherent schema.

2. **Heuristic-Only Decision Making:**
   `intent.py` has over 700 lines of regex patterns. If the user says:
   *"Can you look into why our revenue dropped last Tuesday and summarize the top three emails about it?"*
   The regex classifier will fail to decompose this multi-step requirement into sub-tasks. A true AI Operating System requires an **LLM Reasoning & Task Decomposition Loop** (ReAct / Plan-and-Solve).

3. **In-Memory and File-Based State Coupling:**
   Chat sessions are stored in raw JSON files in `data/sessions/`, while other data is in SQLite. This creates a split brain where session state cannot be easily queried, joined, or backed up alongside memories.

4. **Lack of Agent Identity & Communication Protocol:**
   Currently, "Agents" (Research, Projects, Market) are simply utility classes invoked directly by the monolithic `tool_registry.py`. They lack independent memory views, goals, reflection loops, and a message bus for inter-agent delegation.

---

## 5. Security & Threat Assessment

| Threat Vector | Severity | Finding | Remediation Required |
| :--- | :--- | :--- | :--- |
| **Unauthenticated API Access** | **CRITICAL** | Any client on the local network or internet can execute commands, read all emails, and delete memory without credentials. | Implement JWT Bearer authentication, user registration, bcrypt password hashing, and route protection. |
| **Unrestricted CORS** | **HIGH** | `allow_origins=["*"]` allows malicious third-party websites visited in the user's browser to send requests to `localhost:8000` or `nous-8k2o.onrender.com`. | Restrict CORS to explicit trusted origins (e.g., the deployed domain and local development host). |
| **Arbitrary Command Execution Bypass** | **HIGH** | Command safety relies on substring blacklist in `backend/app/automation/security.py`. In PowerShell, malicious commands can be easily obfuscated (e.g. `iex ([char]... )`). | Sandbox command execution strictly, enforce AST inspection or replace shell commands with predefined Python actions. |
| **Cloud Ephemeral Data Loss** | **HIGH** | SQLite files stored on Render container disk will vanish on next deploy or container restart. | Support cloud database adapters (PostgreSQL / Turso SQLite over HTTP) with automatic environment detection. |
| **Indirect Prompt Injection** | **MEDIUM** | Email sanitizer does basic regex stripping, but LLM context can still be poisoned by adversarial text in web pages or documents. | Enforce strict role-delimited observation wrapping with defensive system prompts. |

---

## 6. Deployment & Environment Assessment

### Local Development Environment:
- **OS:** Windows 11
- **Hardware:** Intel Core i5 (8 logical cores), 16 GB RAM, Integrated GPU.
- **Python:** 3.14 / 3.12 virtual environment (`.venv`).
- **Ollama Status:** Configured for `qwen2.5:3b`. Model fits within ~2.0 GB VRAM/RAM envelope and runs at 15–25 tokens/second on CPU.

### Cloud Deployment (Render.com):
- **URL:** `https://nous-8k2o.onrender.com`
- **Instance Type:** Free Web Service (0.1 CPU, 512 MB RAM).
- **Runtime:** Linux Docker container (`python:3.12-slim-bookworm`).
- **Spin-Down Constraint:** Container sleeps after 15 minutes of inactivity; initial wakeup latency is ~30–50 seconds.
- **RAM Constraint:** 512 MB RAM **cannot run a 3B+ parameter local LLM**. In the cloud, NOUS must route inference to a free/paid cloud API (OpenAI, Groq, OpenRouter, Gemini) or connect back to the user's laptop via the Desktop Companion.

---

## 7. Migration Plan & Priority Sequence

To transform NOUS into a production-grade personal AI operating system without breaking existing functionality:
1. **Preserve All Working Tools & Subsystems:** Do not delete or rewrite working code in `services/`, `market/`, `research/`, `projects/`, or `routine/`.
2. **Phase 1 Priority:** Upgrade the Central AI Brain with dynamic LLM planning, model provider abstractions, and token-streaming WebSockets while maintaining the existing regex classification as a fast-path cache (0ms latency for common queries).
3. **Database Unification (Phase 2):** Unify the SQLite schemas into a single migration-managed database structure with clean table names, paving the way for seamless PostgreSQL transitions.
4. **Security Hardening (Phase 3 & 10):** Add JWT authentication, origin validation, and authenticated desktop tunneling.
5. **Desktop Companion Bridge (Phase 6):** Create a secure, authenticated bridge allowing the Render cloud app to leverage the user's laptop Ollama when the laptop is on, falling back to cloud providers when the laptop is closed.
