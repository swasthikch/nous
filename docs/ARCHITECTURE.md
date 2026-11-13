# NOUS Architecture & Engineering Blueprint

> **"Your Intelligence. Your Memory. Your Assistant."**
> Complete architectural guide, subsystem contracts, data schemas, security guardrails, and telemetry specifications.

---

## 1. System Philosophy & Core Design Principles

NOUS (*Greek: νοῦς — mind, intellect, reason*) is engineered as an extensible, JARVIS-inspired personal intelligence system. It is purposefully designed around five foundational tenets:

1. **Local-First & Resource-Calibrated**: 
   Every critical capability (chat, intent classification, memory retrieval, task automation, and routine management) executes locally with zero cloud dependencies on an Intel Core i5 processor and 16 GB shared memory envelope.
2. **Anti-Hallucination Tool Calling**:
   NOUS strictly adheres to ground-truth execution. If a tool fails, returns no rows, or encounters an error, NOUS faithfully reports the real state rather than fabricating hypothetical outputs.
3. **Zero-Trust Security & Indirect Injection Defense**:
   All untrusted input (emails, web pages, external git repositories) is treated as potentially adversarial. Sensitive tokens (`sk-...`, `ghp_...`, `AIzaSy...`, credit cards, passwords) are scrubbed before reaching LLM inference or logs.
4. **Human-In-The-Loop (HITL) Execution Safeguards**:
   Destructive or high-risk actions (sending emails, modifying files outside sandbox, executing OS commands) generate cryptographically random, time-bounded approval tokens requiring explicit user confirmation.
5. **Multi-Subsystem Persistent Storage**:
   State is partitioned across 7 dedicated SQLite databases operating in Write-Ahead Logging (`WAL`) mode to prevent lock contention and guarantee transactional durability.

---

## 2. High-Level Architecture Diagram

```
 +-----------------------------------------------------------------------------------------+
 |                                  FRONTEND CLIENT (SPA)                                  |
 |   Cyberpunk / Dark Minimal UI  |  Vanilla Modern JS  |  CSS3 Variables  |  Audio Synth  |
 +--------------------------------------------+--------------------------------------------+
                                              | HTTP / REST API (Port 8000)
                                              v
 +-----------------------------------------------------------------------------------------+
 |                                 NOUS ORCHESTRATION BACKEND                              |
 |                                      (FastAPI / ASGI)                                   |
 +-----------------------------------------------------------------------------------------+
 |                                                                                         |
 |  [ Semantic Intent Classifier ]  <--->  [ Zero-Trust Sensitive Redactor ]               |
 |                                                                                         |
 |  [ Anti-Hallucination Tool Registry ]  <--->  [ Permission Manager (HITL Tokens) ]      |
 |                                                                                         |
 |  [ Hybrid Model Router ]                                                                |
 |    |                                                                                    |
 |    +---> Offline Lockdown / Local Route ----> Local Ollama Engine (`qwen2.5:3b`)        |
 |    |                                                                                    |
 |    +---> Complex Reasoning Route ----------> Cloud Models (OpenAI / Claude / Gemini)     |
 |                                                                                         |
 +--------------------------------------------+--------------------------------------------+
                                              |
                                              v
 +-----------------------------------------------------------------------------------------+
 |                         PERSISTENT STORAGE TIERS (SQLite WAL)                           |
 +---------------------+----------------------+---------------------+----------------------+
 | 1. Memory DB        | 2. Routine DB        | 3. Projects DB      | 4. Market DB         |
 |    `nous_memory.db` |    `nous_routine.db` |    `nous_projects.db|    `nous_market.db`  |
 +---------------------+----------------------+---------------------+----------------------+
 | 5. Research DB      | 6. Automation DB     | 7. Security Vault   | 8. Session State     |
 |    `nous_research.db|    `nous_autom.db`   |    `nous_sec.db`    |    `sessions.json`   |
 +---------------------+----------------------+---------------------+----------------------+
```

---

## 3. Subsystem Breakdown (Phases 1 through 15)

### Phase 1 & 2: Core Brain, Session Persistence & Intent Engine
- **Files**: `backend/app/core/ai_engine.py`, `backend/app/core/intent.py`, `backend/app/core/sessions.py`
- **Capabilities**:
  - Regex-boosted semantic classifier matching 30+ intent archetypes with zero latency.
  - Multi-turn conversation sessions persisted with JSON storage and token usage tracking.
  - Anti-hallucination tool call contract enforcing ground-truth verification before user answers.

### Phase 3 & 4: Model Router & Dual Execution Engine
- **Files**: `backend/app/core/model_router.py`, `backend/app/core/ollama_client.py`
- **Capabilities**:
  - Automatically assesses reasoning complexity, query length, and token load.
  - Routes standard queries to local Ollama (`qwen2.5:3b`, ~1.9 GB footprint) in < 800ms.
  - Escalates deep analytical questions to cloud models when keys are available and lockdown is disabled.

### Phase 5 & 6: Persistent Long-Term Memory & Hands-Free Voice Engine
- **Files**: `backend/app/memory/manager.py`, `backend/app/api/voice_api.py`
- **Capabilities**:
  - SQLite WAL database `data/database/nous_memory.db` with categories (`user_profile`, `personal_info`, `project`, `routine`, `conversation`).
  - Web Speech API synthesis & recognition with wake-word detection ("Hey Nous", "Jarvis").

### Phase 7 & 8: Routine Intelligence & Email Intelligence
- **Files**: `backend/app/routine/manager.py`, `backend/app/email/client.py`, `backend/app/email/analyzer.py`
- **Capabilities**:
  - Chronological schedule management with overlap conflict detection and free-slot rollover.
  - Google OAuth 2.0 integration with least-privilege scopes.
  - `EmailSanitizer` defending against indirect prompt injection by isolating untrusted emails in `<untrusted_email_data>` sandboxes.
  - Draft creation requiring strict Human-In-The-Loop approval before dispatch.

### Phase 9 & 10: Project Intelligence & GitHub Telemetry
- **Files**: `backend/app/projects/manager.py`, `backend/app/projects/github_client.py`
- **Capabilities**:
  - Project milestone tracking, tech stack logging, and proactive inactivity audits.
  - Real-time GitHub commit, PR, and issue telemetry with in-memory caching.

### Phase 11: Financial Market Intelligence & 20-Factor Causal Reasoning
- **Files**: `backend/app/market/data_fetcher.py`, `backend/app/market/engine.py`
- **Capabilities**:
  - Live NSE/BSE & global index tracking via Yahoo Finance (`yfinance`).
  - 20-factor causal reasoning engine analyzing macro yields, crude oil, USD/INR, FII/DII institutional flows, and news sentiment.

### Phase 12: Web Research Engine & Knowledge Notebook
- **Files**: `backend/app/research/searcher.py`, `backend/app/research/summarizer.py`, `backend/app/research/engine.py`
- **Capabilities**:
  - Live web search and deep synthesis without requiring paid search APIs.
  - Knowledge notebook storing tagged markdown reports and research takeaways in SQLite WAL.

### Phase 13: Computer & Task Automation
- **Files**: `backend/app/automation/security.py`, `backend/app/automation/manager.py`, `backend/app/automation/db.py`
- **Capabilities**:
  - Strict path traversal prevention ensuring file CRUD operations never escape the designated workspace directory.
  - Command risk categorization (`SAFE`, `REQUIRES_APPROVAL`, `BLOCKED`).
  - Human-In-The-Loop confirmation tokens with 5-minute expiry windows.
  - SQLite WAL scheduler executing periodic tasks and recording execution history.

### Phase 14: Security Vault, Privacy Controls & Audit Trail
- **Files**: `backend/app/security/redactor.py`, `backend/app/security/vault.py`, `backend/app/security/db.py`
- **Capabilities**:
  - `SensitiveDataRedactor` masking API keys (OpenAI, Google, Anthropic, GitHub), bearer tokens, private keys, credit cards, and passwords.
  - Offline Lockdown switch enforcing 100% local Ollama inference and blocking all outbound cloud traffic.
  - Memory Retention Pause freezing long-term memory updates during confidential sessions.
  - Immutable audit trail recording every tool execution, risk level, and actor decision.

### Phase 15: System Diagnostics & Startup Automation
- **Files**: `backend/app/core/diagnostics.py`, `backend/app/api/diagnostics_api.py`, `run_nous.bat`, `start.ps1`
- **Capabilities**:
  - Real-time hardware telemetry (RAM load with 16 GB ceiling, CPU core metrics, disk free space).
  - SQLite database integrity verifier running `PRAGMA integrity_check` across all 7 databases.
  - Interactive diagnostics dashboard with in-process smoke testing.
  - One-click Windows startup scripts.

---

## 4. Database Schema Specifications

All databases reside in `data/database/` and run in SQLite `WAL` mode:

| Database File | Primary Tables | Primary Responsibilities |
|---|---|---|
| `nous_memory.db` | `memories`, `memory_audit_log` | Facts, user preferences, long-term memory |
| `nous_routine.db` | `routine_activities`, `activity_logs`, `routine_summaries` | Daily time-blocks, status tracking, evening reviews |
| `nous_projects.db` | `projects`, `project_milestones`, `project_notes`, `github_commits_cache` | Codebase tracking, milestones, git activity |
| `nous_market.db` | `watchlist_items`, `price_alerts`, `market_snapshots`, `alert_history` | Stocks, indices, price thresholds, alerts |
| `nous_research.db` | `research_notes`, `deep_reports`, `search_cache` | Synthesized web articles, literature notes |
| `nous_automation.db` | `scheduled_tasks`, `execution_history` | Cron jobs, shell audit logs, execution timing |
| `nous_security.db` | `audit_events`, `privacy_settings` | Immutable security audit log, lockdown policies |

---

## 5. Security & Isolation Matrix

```
+-----------------------------------+---------------------------------------------------------+
| Risk Boundary                     | Mitigation Mechanism                                    |
+-----------------------------------+---------------------------------------------------------+
| Path Traversal (`../`, root C:\)  | Absolute path canonicalization vs. workspace root path. |
| Dangerous CLI (`rmdir /s`, `del`)| Regex blocklist with instantaneous rejection.            |
| Sensitive Key Exfiltration       | Zero-trust redaction before prompts reach any LLM.      |
| Indirect Prompt Injection (Email) | Isolation in `<untrusted_email_data>` passive tags.     |
| Unauthorized File Overwrite       | Explicit overwrite checkbox requirement in API/UI.      |
| Accidental Cloud Egress           | Offline Lockdown toggle forcing local Ollama execution. |
+-----------------------------------+---------------------------------------------------------+
```

---

## 6. How to Run NOUS in Production

### Option A: Windows Double-Click (Recommended)
Double-click `run_nous.bat` in the project root:
- Activates Python `.venv`
- Verifies local Ollama server status
- Opens default web browser to `http://127.0.0.1:8000`
- Starts the production Uvicorn server

### Option B: PowerShell Console
```powershell
.\start.ps1
```

### Option C: Manual CLI
```bash
# 1. Activate Virtual Environment
.venv\Scripts\activate

# 2. Start Backend Server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 7. Curated Public APIs Integration (`public-apis/public-apis`)

To extend NOUS with real-time global utility without requiring paid accounts or API keys, NOUS integrates selected keyless, HTTPS, CORS-enabled endpoints from the [public-apis/public-apis](https://github.com/public-apis/public-apis) directory:

```
+---------------------+------------------------------------------------+----------------------------+
| Domain              | Provider & Public Endpoint                     | Anti-Hallucination Tool    |
+---------------------+------------------------------------------------+----------------------------+
| Weather & Climate   | Open-Meteo (`api.open-meteo.com`) & wttr.in    | `get_weather_forecast`     |
| Lexicon & Language  | Free Dictionary API (`api.dictionaryapi.dev`)  | `lookup_dictionary_definition` |
| Currency Exchange   | Frankfurter API (`api.frankfurter.dev`) / ECB   | `convert_currency`         |
| Humor & Jokes       | Official Joke API (`official-joke-api.appspot`)| `get_random_joke`          |
+---------------------+------------------------------------------------+----------------------------+
```

### Architectural Guarantees:
1. **Zero-Setup & Free Access**: All providers require no personal token, credit card, or authentication header.
2. **Deterministic Offline Fallbacks**: If external networks are unreachable or offline lockdown is active, each service automatically falls back to verified cached benchmark datasets with `is_offline_fallback=True` without failing.
3. **Anti-Hallucination Verification**: The `AIEngine` intercepts weather, definition, currency, and joke intents at the heuristic classifier layer, executes the verified tool, and injects verified facts into the prompt before the model synthesizes the user-facing response.

