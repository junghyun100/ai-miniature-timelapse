# Reference-Frame Relay v2.0 Execution Guide

This document defines the step-by-step operational instructions for local execution, proxy boot, and QA/smoke testing of the AI Miniature Timelapse system.

---

## 1. Immutable Security Contract

> [!IMPORTANT]
> **STRICT SECURITY RULE**: NEVER hardcode, print, or commit real API keys or sensitive credentials.
> All configuration samples and documentation MUST use placeholder tokens exclusively.

### Allowed Secret Placeholders
- `<NVIDIA_API_KEY>`
- `<SESSION_TOKEN>` or `session-token-placeholder`
- `<ALLOWED_ORIGIN>` (e.g. `http://127.0.0.1:4173`)

---

## 2. System Architecture & Port Allocation

| Component | Tech Stack | Port / Binding | Entrypoint |
|-----------|------------|----------------|------------|
| **NIM Proxy Server** | Python / ASGI / Uvicorn | `127.0.0.1:4174` | `src/nim_proxy_server.py` |
| **Relay Runner UI** | Standard ES Modules / HTML5 | `127.0.0.1:4173` | `ui/index.html` |
| **Upstream NIM Service** | NVIDIA NIM API | `https://integrate.api.nvidia.com` | Upstream endpoint |

---

## 3. Strict Local Execution Order

To run the complete system locally, follow this exact numbered sequence.

### Step 1: Environment Setup
Ensure Python 3.11+ and `uv` package manager are available.

```bash
# 1. Clone & enter project directory
cd ai-miniature-timelapse

# 2. Sync virtual environment and dependencies
uv sync --all-extras

# 3. Install Playwright browser binaries (for browser QA)
uv run playwright install chromium
```

### Step 2: Environment Variables Configuration
Set required environment variables in your active shell (or create an uncommitted `.env` file):

```bash
# Required: Upstream NVIDIA NIM API Key (Placeholder syntax only)
export NIM_API_KEY="<NVIDIA_API_KEY>"

# Optional: Proxy CORS Allowed Origin (Default includes 127.0.0.1:4173 and localhost:4173)
export ALLOWED_ORIGIN="http://127.0.0.1:4173"

# Optional: Proxy Session Token Secret (Default: generated per session)
export NIM_PROXY_SESSION_TOKEN="session-token-placeholder"
```

### Step 3: Boot NIM Proxy Server (Terminal 1)
Start the proxy server bound to local loopback `127.0.0.1:4174`.

```bash
# Start proxy server
uv run python3 src/nim_proxy_server.py --host 127.0.0.1 --port 4174
```

### Step 4: Verify Proxy Server Health
Verify the proxy server is active and healthy. `GET /health` does not require an `Origin` header or `X-Session-Token`.

```bash
curl -s http://127.0.0.1:4174/health
```

**Expected Response**:
```json
{
  "status": "ok",
  "version": "1.0",
  "upstream": ["integrate.api.nvidia.com", "api.nvidia.com"],
  "default_model": "meta/llama-3.1-8b-instruct"
}
```

### Step 5: Boot Relay Runner UI Server (Terminal 2)
Start the local HTTP static file server to serve the ES module web app:

```bash
# Navigate to ui directory and start Python HTTP server
cd ui && python3 -m http.server 4173 --bind 127.0.0.1
```

### Step 6: Access Relay Runner UI
Open your browser and navigate to:
```text
http://127.0.0.1:4173/index.html
```

---

## 4. QA & Smoke Testing Execution Order

Execute tests in the following exact sequence to validate python domain logic, profile contracts, security redaction, and browser UI interaction.

### Execution Command Sequence

```bash
# Command 1: Run Python Unit & Integration Test Suite (325 tests)
uv run pytest tests/ --ignore=tests/browser -v

# Command 2: Ensure HTTP Server is running on port 4173 (Required for Playwright)
curl -I http://127.0.0.1:4173/index.html

# Command 3: Run Playwright E2E Browser & Responsive QA Test Suite (34 tests)
uv run pytest tests/browser/ -v

# Command 4: Run Full Combined Test Suite (359 tests)
uv run pytest tests/ -v
```

### API Endpoint Smoke Test Command

Validate the NIM Proxy endpoint directly with a standard Relay Prompt request payload. Browser clients must not send the NVIDIA API key directly; the proxy uses `NIM_API_KEY` from the environment. `POST /api/nim/rewrite` requires both an allowed `Origin` and a valid `X-Session-Token`.

```bash
curl -X POST http://127.0.0.1:4174/api/nim/rewrite \
  -H "Content-Type: application/json" \
  -H "Origin: http://127.0.0.1:4173" \
  -H "X-Session-Token: <SESSION_TOKEN>" \
  -d '{
    "schema_version": "2.0",
    "request_id": "11111111-1111-4111-8111-111111111111",
    "source_revision": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "profile": {
      "id": "architecture.korean",
      "version": "1.0",
      "workflow_mode": "REFERENCE_FRAME_RELAY"
    },
    "subject": {
      "topic_label": "Architecture-Hanok"
    },
    "style_bible": {
      "visual_style": "cinematic miniature timelapse"
    },
    "scenes": [
      {
        "id": 1,
        "name": "Foundation and Walls",
        "start_state": "Empty soil surface with no materials placed yet.",
        "ordered_actions": [
          "Measure the foundation footprint.",
          "Place the first stone course."
        ],
        "end_state": "Foundation footprint is laid and the first wall course is complete.",
        "local_first_frame_prompt": "Ultra realistic macro photography of an empty hanok build site with only giant human hands beginning the first placement.",
        "local_video_prompt": "Hands-only miniature construction timelapse that completes foundation setup and the first wall course, then stops before roofing begins."
      }
    ],
    "mutable_fields": [
      "scenes.*.first_frame_prompt",
      "scenes.*.video_prompt"
    ],
    "immutable_rules": [
      "Never expose miniature people.",
      "Preserve scene order and identity."
    ]
  }'
```

---

## 5. Reverse Rollback Execution Order

If a local run or smoke test fails due to proxy corruption, port collision, or bad environment state, follow this strict reverse sequence:

1. **Step 1 (Stop UI)**: Stop UI HTTP server (`Ctrl+C` in Terminal 2 or `kill -9 $(lsof -t -i:4173)`).
2. **Step 2 (Stop Proxy)**: Stop NIM Proxy server (`Ctrl+C` in Terminal 1 or `kill -9 $(lsof -t -i:4174)`).
3. **Step 3 (Clear Environment)**: Unset API key & local session tokens (`unset NIM_API_KEY NIM_PROXY_SESSION_TOKEN`).
4. **Step 4 (Clean Caches)**: Clear bytecode and pytest caches (`rm -rf .pytest_cache ui/.cache src/__pycache__ tests/__pycache__`).
5. **Step 5 (Verify Idle Ports)**: Verify ports `4173` and `4174` are completely released (`lsof -i :4173 -i :4174`).
