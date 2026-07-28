# Reference-Frame Relay v2.0 Operations & Failure Recovery Guide

This guide details system operations, error sanitization policies, health checking, failure recovery runbooks, and rollback procedures for the AI Miniature Timelapse pipeline.

---

## 1. Operational Architecture & Process Dependencies

```
[ Browser Client / Relay Runner UI ] (Port 4173)
        │
        ▼ OPTIONS / POST /api/nim/rewrite with Origin + X-Session-Token
[ Local NIM Proxy Server ] (Port 4174)
        │
        ▼ HTTPS with env-injected NIM_API_KEY
[ Upstream NVIDIA NIM Service ] (integrate.api.nvidia.com)
```

### Critical Process Dependencies
1. **Upstream NIM Service**: External dependency. Requires valid API key, active network route, and HTTPS access.
2. **NIM Proxy Server**: Intermediate security & validation layer. Sanitizes logs, validates JSON schemas against canonical spec, enforces session tokens and CORS boundaries.
3. **Relay Runner UI**: Client interface. Computes SHA-256 source revisions, maintains state machine transitions, falls back gracefully to canonical local drafts upon network/NIM failure.

---

## 2. Security & Redaction Standards

### Immutable Secret Policy
> [!CAUTION]
> **NO REAL KEYS**: Real credentials (e.g. `nvapi-...`) MUST NEVER be written to disk, committed to source control, or output in server logs.

### Server Sanitization Mechanisms
- **Log Masking**: `nim_proxy_server.py` and `nim_client.py` employ regex redaction filters (`nvapi-[A-Za-z0-9_-]+` -> `[REDACTED_API_KEY]`) on all log statements and exception stack traces.
- **Header Redaction**: Session and upstream credential headers are stripped or redacted before printing debug logs.
- **Client-Side Sanitization**: `ui/error_handling.js` sanitizes error messages before displaying badges in the browser UI.
- **Browser Boundary**: Browser clients never send the NVIDIA API key directly; the proxy receives the upstream key only from server-side environment variables.

---

## 3. Monitoring & Health Checks

### Primary Health Endpoint
- **URL**: `http://127.0.0.1:4174/health`
- **Method**: `GET`
- **Frequency**: Every 30 seconds (automated or ops script)
- **Auth Boundary**: No `Origin` header or `X-Session-Token` is required for `GET /health`.

#### Health Check Verification Command
```bash
curl -s -f http://127.0.0.1:4174/health || echo "HEALTH_CHECK_FAILED"
```

---

## 4. Failure Recovery Runbooks (5 Scenarios)

### Scenario A: NIM Proxy Connection Refused / Port Conflict (Port 4174)
- **Symptom**: Browser or curl returns `ECONNREFUSED 127.0.0.1:4174` or `Errno 48 Address already in use`.
- **Root Cause**: Proxy server process crashed or another process is occupying port `4174`.
- **Recovery Procedure**:
  ```bash
  # 1. Identify process occupying port 4174
  lsof -i :4174

  # 2. Terminate the conflicting process
  kill -9 $(lsof -t -i:4174)

  # 3. Restart NIM Proxy Server
  uv run python3 src/nim_proxy_server.py --host 127.0.0.1 --port 4174
  ```

---

### Scenario B: Downstream NIM HTTP Errors (401 / 403 / 429 / 500)
- **Symptom**: Proxy logs show `401 Unauthorized`, `403 Forbidden`, `429 Rate Limit`, or `500 Upstream Error`.
- **Root Cause & Resolution**:
  1. **`401 / 403`**: API Key invalid or expired. Update `NIM_API_KEY` with placeholder replacement:
     ```bash
     export NIM_API_KEY="<NVIDIA_API_KEY>"
     ```
     *(Note: Proxy fast-fails 401/403 without upstream retry).*
  2. **`429 Rate Limit`**: Upstream rate limit reached. Proxy automatically executes exponential backoff retry up to 3 attempts. If retries exhaust, proxy returns sanitised `429` error response.
  3. **`500 Internal Error`**: Upstream NIM server temporary outage. Proxy attempts retries before failing gracefully to local draft.

---

### Scenario C: Schema Validation / JSON Parsing Failure
- **Symptom**: Proxy returns `HTTP 422 Unprocessable Entity` or `VALIDATION_ERROR`.
- **Root Cause**: Client request missing required fields (`source_revision`, `workflow_mode`, `first_frame_prompt`) or using incompatible `schema_version`.
- **Recovery Procedure**:
  1. Check client schema version against `schema/nim_prompt_request.json`.
  2. Verify source revision SHA-256 was computed over canonicalized Source Draft.
  3. Re-run local schema validation tests:
     ```bash
     uv run pytest tests/nim/test_nim_contract.py -k test_schema -v
     ```

---

### Scenario D: Stale Revision Guard Triggered / UI Draft Fallback
- **Symptom**: Proxy or UI rejects response with `STALE_SOURCE_REVISION`.
- **Root Cause**: User modified the Source Draft while a background NIM request was in flight. The returned prompts belong to an outdated source revision.
- **Recovery Procedure**:
  1. Relay Runner UI automatically discards stale response to prevent state corruption.
  2. UI retains canonical local draft prompts.
  3. User or client re-triggers prompt generation with updated `source_revision`.

---

### Scenario E: CORS / Invalid Origin Rejection
- **Symptom**: Browser console logs `CORS policy: No 'Access-Control-Allow-Origin' header is present`.
- **Root Cause**: UI origin (`http://127.0.0.1:4173`) does not match Proxy `ALLOWED_ORIGIN`.
- **Recovery Procedure**:
  ```bash
  # 1. Restart proxy with explicit allowed origin
  export ALLOWED_ORIGIN="http://127.0.0.1:4173"
  uv run python3 src/nim_proxy_server.py --host 127.0.0.1 --port 4174
  ```

---

## 5. Rollback Triggers & Reverse Rollback Order

### Explicit Rollback Triggers
Rollback MUST be initiated immediately if any of the following criteria are met:
1. **Critical Failure**: Unit or integration test pass rate falls below 100% (any test failure).
2. **Security Vulnerability**: Unredacted API key detected in logs or UI text elements.
3. **Data Corruption**: Stale revision guard failing to reject mismatched source revisions.
4. **Proxy Instability**: Proxy crash rate exceeding 0% during smoke tests.

### Rollback Execution Order (Reverse Sequence)

Execute rollback in exact reverse order of service startup:

```text
[Step 1: Shutdown UI Server] 
  └── Kill Python HTTP server on port 4173

[Step 2: Shutdown NIM Proxy Server]
  └── Kill proxy process on port 4174

[Step 3: Revoke Local Session Credentials]
  └── Clear NIM_API_KEY and active session tokens from environment

[Step 4: Restore Codebase & State to Previous Known-Good Commit]
  └── git checkout <LAST_STABLE_COMMIT_TAG>

[Step 5: Purge Caches & Temp State]
  └── rm -rf .pytest_cache ui/.cache src/__pycache__ output/*

[Step 6: Execute Health & Verification Suite]
  └── uv run pytest tests/ --ignore=tests/browser -v
```
