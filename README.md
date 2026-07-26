# ai-miniature-timelapse

Miniature construction timelapse pipeline with Reference-Frame Relay v2.0 implementation.

## Overview

AI-assisted miniature timelapse generator implementing the [Reference-Frame Relay v2.0 specification](docs/reference-frame-relay-spec.md). Supports four workflow profiles with deterministic relay state machines, NIM proxy integration, and a browser-based Relay Runner UI.

### Supported Profiles

| Profile | Workflow Mode | Duration | Scenes | Use Case |
|---------|---------------|----------|--------|----------|
| `architecture.korean` | REFERENCE_FRAME_RELAY | 30s / 60s | 3 / 6 | Korean Hanok construction (foundation → roof → walls/interior/garden/hero) |
| `vehicle.assembly` | REFERENCE_FRAME_RELAY | 30s / 60s | 3 / 6 | Vehicle assembly (10 categories, 6-stage assembly: Chassis → Engine → Drivetrain → Interior → Body → Final) |
| `home_decor.diy` | SINGLE_CLIP_FROM_MASTER | 10s | 1 | Home decor DIY (6-step craft: Hook → Materials → Build → Mid-build → Detail → Reveal) |
| `cooking.miniature` | REFERENCE_FRAME_RELAY | 30s | 3 | Miniature cooking (Prep → Cook → Plate, ASMR audio only) |

**Key**: All videos are 10s × N clips. No single-clip 10s videos except home_decor.diy.

## Quick Start

### 1. Start Relay Runner UI (Browser)

```bash
# Terminal 1: Start HTTP server for ES modules
cd ui && python3 -m http.server 8765

# Open http://localhost:8765/index.html in browser
```

### 2. Run Tests

```bash
# Python unit tests (208 tests)
python3 -m pytest tests/ --ignore=tests/browser -v

# Playwright E2E browser tests (18 tests)
python3 -m pytest tests/browser/ -v

# All tests
python3 -m pytest tests/ --ignore=tests/browser -v && python3 -m pytest tests/browser -v
```

### 3. CLI Pipeline (Legacy)

```bash
python3 src/watch_and_finalize.py "Korean hanok" --duration 60 --base-dir output
```

## Project Structure

```
ai-miniature-timelapse/
├── src/
│   ├── domain.py               # Canonical domain models (Project, Scene, AssetRef, RelayBranch)
│   ├── relay_state.py          # Relay state machine (Section 10)
│   ├── profile_types.py        # Profile registry & interface (Section 13)
│   ├── profiles/               # 4 profile implementations
│   │   ├── architecture.py     # Korean Hanok (Section 13.5)
│   │   ├── vehicle.py          # Vehicle assembly (Section 13.6)
│   │   ├── home_decor.py       # Home decor DIY (Section 13.8)
│   │   └── cooking.py          # Miniature cooking (Section 13.9)
│   ├── serializers.py          # Canonical serialization (Section 11.6)
│   ├── nim_proxy_server.py     # NIM proxy (FastAPI, Section 14)
│   ├── nim_client.py           # NIM async client with retry/fallback
│   ├── schema_validator.py     # JSON Schema validation
│   ├── persistence.py          # Project persistence (Section 16)
│   └── watch_and_finalize.py   # Legacy CLI pipeline
├── tests/
│   ├── domain/                 # Domain model & source revision tests
│   ├── profiles/               # Profile traceability tests (Section 21.2)
│   ├── nim/                    # NIM contract & proxy tests
│   ├── relay/                  # Relay state machine tests
│   ├── serializers/            # Serialization & copy action tests
│   ├── persistence/            # Persistence round-trip tests
│   └── browser/                # Playwright E2E tests for Relay Runner UI
├── ui/
│   ├── index.html              # Relay Runner UI (Section 15)
│   ├── app.js                  # ES module:1-440          # Core logic (state machine, serialization, persistence)
│   └── styles.css              # UI styling
├── schema/                     # JSON Schemas (10 files, Section 14)
└── docs/
    └── reference-frame-relay-spec.md  # Full v2.0 specification
```

## Key Features

### Relay Runner UI (Section 15)
- **Profile selection** with dynamic config grid
- **Scene grid** with visual state badges (LOCKED → AWAITING_MASTER_IMAGE → VIDEO_READY → CONFIRMED → COMPLETE)
- **Stepper navigation** between scenes
- **Canonical prompt copy** (Master Image / Scene Video / Full Scene / All)
- **State transitions** via Confirm Step button
- **Persistence**: Save/Resume via localStorage
- **JSON export** for handoff

### Source Revision Hashing (Section 14.1)
- SHA-256 of canonicalized Source Draft
- Identical algorithm in Python (`src/domain.py`) and browser (`ui/app.js`)
- Cross-platform consistency verified in tests

### NIM Proxy (Section 14)
- FastAPI server with schema validation
- Origin/session token auth
- Error sanitization (no secrets in logs)
- Upstream retry with exponential backoff
- Response normalization per Section 14.5

### Profile Registry (Section 13)
- Four profiles with distinct workflow modes
- Scene plans with start_state, ordered_actions, end_state, forbidden_changes
- Style bible factories (materials, camera, lighting, palette, workspace, hands_rule, motion_rule)
- First frame & scene prompt factories

## Test Coverage

| Suite | Tests | Coverage |
|-------|-------|----------|
| Domain / Source Revision | 26 | Canonical JSON, hash determinism, NFC normalization |
| Profiles | 24 | Section 21.2 traceability, all 4 profiles |
| NIM Contract | 32 | Request/response schema, normalization, fallback, provenance |
| NIM Proxy | 24 | Auth, CORS, schema validation, forwarding, security |
| Relay State Machine | 30 | Transitions, cascading, branching, validation |
| Serializers | 20 | Full plan, copy actions, asset refs |
| Persistence | 10 | Save/load round-trip, schema version |
| **Python Total** | **208** | |
| **Playwright E2E** | **18** | UI load, profiles, state transitions, copy, persistence |

## Configuration

### NIM Proxy (Optional)
```bash
# Terminal 2: Start NIM proxy
cd src && python3 -m uvicorn nim_proxy_server:app --host 127.0.0.1 --port 8000
```

Enable in UI: Check "NIM Enabled" → enter model, base URL, API key, refinement policy.

## Specification Compliance

This implementation follows **Reference-Frame Relay v2.0** (see `docs/reference-frame-relay-spec.md`):

- ✅ Section 7: Domain invariants & validation
- ✅ Section 10: Relay state machine with transitions
- ✅ Section 11.6: Canonical prompt serialization
- ✅ Section 13: Profile registry (4 profiles)
- ✅ Section 14: NIM contract, source revision, normalization
- ✅ Section 15: Relay Runner UI
- ✅ Section 16: Persistence
- ✅ Section 21: Test fixtures & traceability

## Implementation Highlights

### Reference Prompt Alignment (All 4 Profiles)
All profile prompt factories now match the reference prompts in `docs/reference_prompts/` exactly:

- **Negative prompts hardened** — Each profile uses its reference-spec negative prompt verbatim (no template fallbacks)
- **Scene plans extended** — 30s = 3 scenes, 60s = 6 scenes (all 10s clips) per profile
- **Subject-specific prompts** — Each subtype/category/dish generates specialized prompts using reference skeleton wording
- **Identity locks enforced** — Style bibles carry the exact identity_lock strings from reference specs

### NIM Integration
- **Models**: `nvidia/nemotron-3-super-120b-a12b` (default) / `nvidia/nemotron-3-ultra-550b-a55b` (premium)
- **Strict contract** — Request/response validated against JSON schemas; no fallback/template prompts when NIM unavailable (fails fast with validation error per user requirement)
- **Source revision** — SHA-256 of canonical Source Draft computed identically in Python and browser

### Removed Legacy Code
- All template/fallback prompt generators removed from `nim_client.py`, `prompt_templates.py`, `pipeline.py`
- Legacy `prompt_templates.py` marked for deletion (replaced by profile factories)

## License

Internal project — not for distribution.