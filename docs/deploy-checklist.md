# Reference-Frame Relay v2.0 Deploy & Release Checklist

This document details the pre-release verification checklist, deployment steps, post-release smoke tests, and emergency rollback procedures.

---

## 1. Immutable Security & Compliance Rules

- [ ] **Secret Redaction**: Zero real API keys or sensitive credentials present in codebase, tests, or documentation.
- [ ] **Placeholder Syntax**: All configuration examples use placeholder tokens (`<NVIDIA_API_KEY>`, `<SESSION_TOKEN>`, `<ALLOWED_ORIGIN>`).
- [ ] **Execution Order**: Pre-release verification and deployment commands executed in exact specified sequence.
- [ ] **Rollback Plan**: Rollback criteria and reverse execution sequence explicitly reviewed prior to release.

---

## 2. Pre-Release Verification Checklist

Run each verification command in order before approving a release build.

### Phase A: Static Integrity & Syntax Checks
- [ ] **Python Syntax Check**:
  ```bash
  uv run python3 -m py_compile src/*.py
  ```
- [ ] **JavaScript ES Module Syntax Check**:
  ```bash
  node --check ui/app.js ui/error_handling.js
  ```
- [ ] **Git Patch & Whitespace Integrity**:
  ```bash
  git diff --check
  ```

### Phase B: Automated Test Suite Execution
- [ ] **Python Unit & Integration Test Suite (325 tests)**:
  ```bash
  uv run pytest tests/ --ignore=tests/browser -v
  ```
- [ ] **Playwright E2E & Responsive QA Browser Test Suite (34 tests)**:
  ```bash
  # Ensure HTTP server is active on port 4173 first
  uv run pytest tests/browser/ -v
  ```

### Phase C: Security & Secret Leak Audit
- [ ] **Search Codebase for Hardcoded Secrets**:
  ```bash
  grep -rnE "nvapi-[A-Za-z0-9]{20,}" src/ ui/ docs/ README.md
  ```
  *(Must return 0 results).*

---

## 3. Release Execution Order

Execute deployment steps in the following exact numbered order:

1. **Step 1 (Tag Release)**: Create git release tag for version tracking:
   ```bash
   git tag -a v2.0.0 -m "Release v2.0.0 - Reference-Frame Relay Implementation"
   ```
2. **Step 2 (Environment Prep)**: Inject production environment variables (using secret management system):
   ```bash
   export NIM_API_KEY="<PRODUCTION_NVIDIA_API_KEY>"
   export ALLOWED_ORIGIN="http://127.0.0.1:4173"
   export NIM_PROXY_SESSION_TOKEN="<SESSION_TOKEN>"
   ```
3. **Step 3 (Boot NIM Proxy Server)**: Start NIM Proxy in production mode:
   ```bash
   uv run python3 src/nim_proxy_server.py --host 127.0.0.1 --port 4174
   ```
4. **Step 4 (Verify Proxy Health)**:
   ```bash
   curl -s -f http://127.0.0.1:4174/health
   ```
5. **Step 5 (Boot UI Static Server)**:
   ```bash
   cd ui && python3 -m http.server 4173 --bind 127.0.0.1
   ```
6. **Step 6 (Execute Smoke Tests)**: Verify system responsiveness via curl and browser navigation.

---

## 4. Post-Release Smoke Testing

Immediately following deployment, run the post-release smoke test script:

```bash
# 1. Verify Proxy Health
curl -s http://127.0.0.1:4174/health | grep '"status":"ok"'

# 2. Verify UI HTTP Server Headers
curl -I http://127.0.0.1:4173/index.html | grep "HTTP/1.0 200 OK"

# 3. Verify Proxy Endpoint Response with Valid Payload
curl -s -X POST http://127.0.0.1:4174/api/nim/rewrite \
  -H "Content-Type: application/json" \
  -H "Origin: http://127.0.0.1:4173" \
  -H "X-Session-Token: <SESSION_TOKEN>" \
  -d '{
    "schema_version": "2.0",
    "request_id": "22222222-2222-4222-8222-222222222222",
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
  }' | grep '"provenance"'
```

The browser-facing app must never send the NVIDIA API key directly. The upstream key is injected into the proxy via `NIM_API_KEY`, while browser-originated rewrite calls authenticate with `Origin` and `X-Session-Token`.

---

## 5. Rollback Criteria & Reverse Execution Order

### Rollback Criteria (Triggers)
Initiate immediate rollback if ANY of the following conditions occur post-release:
- [ ] Post-release smoke test fails (HTTP status != 200 or missing `provenance`).
- [ ] Unredacted secret or API key exposed in response headers or log files.
- [ ] Proxy memory leak or crash rate > 0%.
- [ ] Playwright E2E browser tests fail against release deployment.

### Reverse Rollback Execution Sequence

Execute rollback steps in strict reverse order of release deployment:

```text
1. [STOP UI SERVER]
   Kill process running on port 4173:
   kill -9 $(lsof -t -i:4173)

2. [STOP PROXY SERVER]
   Kill proxy process running on port 4174:
   kill -9 $(lsof -t -i:4174)

3. [PURGE CREDENTIALS & SESSION TOKENS]
   Unset production environment secrets:
   unset NIM_API_KEY ALLOWED_ORIGIN NIM_PROXY_SESSION_TOKEN

4. [ROLLBACK GIT REPOSITORY]
   Revert git repository to previous release tag:
   git checkout <PREVIOUS_RELEASE_TAG>

5. [CLEAR RUNTIME CACHES]
   Remove runtime caches and generated artifacts:
   rm -rf .pytest_cache ui/.cache src/__pycache__ output/*

6. [RESTART PREVIOUS STABLE BUILD]
   Follow Release Execution Steps 2-5 using previous stable release tag.

7. [RUN VERIFICATION SUITE]
   Verify rollback stability:
   uv run pytest tests/--ignore=tests/browser -v
```
