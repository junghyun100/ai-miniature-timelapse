# TODO: Reference-Frame Relay v2 Handoff

이 문서는 현재 작업 상태를 다음 구현 모델이 바로 이어받을 수 있도록 정리한 로컬 전용 인수 문서입니다.

중요: 이 TODO는 사용자의 지시에 따라 커밋/푸시 대상이 아닙니다. 릴리즈 가능한 변경은 코드/테스트/정식 문서에 반영하고, 이 파일은 작업 지휘와 검증 체크리스트로만 사용합니다.

## 0. 현재 판단

현재 워크트리는 Reference-Frame Relay v2 방향으로 상당수 구현 변경이 들어와 있습니다. 다만 릴리즈 완료로 보려면 아직 "구현됨"과 "검증됨"을 분리해야 합니다.

현재 완료로 보이는 큰 축:

- Reference-Frame Relay를 기준으로 한 프롬프트 구조 재정의
- Scene 1 전용 Master Image Prompt와 Scene 2+ Previous Final Frame 모드 분리
- Source Draft, Applied Prompt, Scene Preview, Copy/Export의 canonical source 통합 시도
- NIM proxy, request adapter, retry/fallback, provenance, source revision 관련 구현 추가
- deployment/run/ops 문서 추가
- profile별 scene boundary 계약 강화

현재 반드시 재검증해야 하는 큰 축:

- 실제 UI에서 NIM toggle enabled 상태일 때 proxy를 통해 진짜 upstream 호출이 되는지
- NIM 응답 성공 시 Applied Prompt, Scene Outputs, Scene Preview, copy/export가 모두 같은 canonical applied plan을 보는지
- NIM 실패 시 local deterministic fallback이 적용되며 성공처럼 표시되지 않는지
- negative prompt가 모든 scene의 video prompt 끝에 정확히 1회 유지되는지
- non-final scene이 완성품까지 진행하지 않고 exact_stop_state에서 멈추는지
- 브라우저 localStorage/sessionStorage/로그/문서에 실 API key가 남지 않는지

이번 세션 WP-8 검증 증적:

- `4173` 포트에 남아있는 테스트용 UI 서버 없음 확인
- static gate 통과:
  - `UV_CACHE_DIR=/private/tmp/uv-cache rtk uv run python3 -m py_compile src/*.py`
  - `rtk node --check ui/app.js ui/error_handling.js ui/fetch_wrapper.js ui/provenance_model.js ui/request_adapter.js ui/source_revision.js ui/state_store.js`
  - `rtk git diff --check`
- targeted WP tests 통과: `197 passed, 73 warnings`
- non-browser tests 통과: `UV_CACHE_DIR=/private/tmp/uv-cache rtk uv run pytest tests/ --ignore=tests/browser -q` -> `333 passed, 258 warnings`
- browser tests 통과: `UV_CACHE_DIR=/private/tmp/uv-cache rtk uv run pytest tests/browser -q` -> `34 passed`
- secret/document scan 통과:
  - `rtk rg -n "nvapi-[A-Za-z0-9_-]{20,}" . --glob '!TODO.md'` -> no matches
  - `rtk rg -n "localStorage.*api|api.*localStorage|sessionStorage.*api|api.*sessionStorage|Authorization: Bearer nvapi|Authorization: Bearer <NVIDIA_API_KEY>|X-NIM-API-Key" ui src docs README.md` -> no matches
  - `rtk rg -n "8000|8765|/v1/nim/relay-prompts|localhost:8765" README.md docs/run-guide.md docs/deploy-checklist.md docs/ops-guide.md TODO.md` -> no matches

이번 세션에서 정리된 구현/문서 계약:

- UI는 NVIDIA API key를 직접 받지 않고 `Proxy Session Token`만 입력받는다.
- UI NIM 호출은 `POST http://127.0.0.1:4174/api/nim/rewrite`와 `X-Session-Token`을 사용한다.
- proxy health check는 `GET /health`로 unauthenticated, rewrite endpoint는 `Origin`과 `X-Session-Token`을 요구한다.
- NIM 성공 시 response `source_revision`이 현재 Source Draft revision과 같을 때만 Applied Prompt를 갱신한다.
- NIM 실패/불일치/stale 응답은 local fallback provenance로 표시하고 성공처럼 표시하지 않는다.
- Scene 2+ first frame은 비어 있어야 하며 previous final frame/start frame handoff 안내로 처리한다.
- negative prompt는 canonical applied plan에서 유지되어 Scene Preview/copy/export가 같은 값을 보아야 한다.

아직 실제 외부 도구에서 확인해야 하는 항목:

- Google Flow 화면에서 Scene 1 master image 생성 후 승인하는 실제 수동 handoff
- Scene 2+에서 이전 scene final frame을 start frame으로 넣었을 때 visual drift가 어느 정도 줄어드는지 확인
- profile별 prompt quality sample이 실제 Flow 출력에서도 non-final scene completion을 억제하는지 확인
- NVIDIA NIM upstream은 로컬 테스트/모킹이 아니라 실제 회전된 key로 별도 smoke 필요

## 1. 작업 원칙

메인 에이전트 역할:

- 전체 명세와 완료 기준을 유지한다.
- 서브에이전트에게 작은 작업 패키지를 나눠 지시한다.
- 서브에이전트 결과를 병합하기 전 테스트와 diff를 검토한다.
- 사용자 변경사항을 되돌리지 않는다.
- 커밋/푸시 대상에서 이 TODO를 제외한다.

GPT-5.4 계열 서브에이전트 역할:

- 파일 범위가 명확한 구현 또는 테스트만 맡는다.
- 수정한 파일 목록과 실행한 검증 명령을 최종 보고한다.
- 불명확한 요구사항은 임의 확장하지 않고 "확인 필요"로 남긴다.
- 서로 다른 서브에이전트가 같은 파일을 동시에 수정하지 않도록 한다.

권장 운영 방식:

- 하나의 WP를 여러 파일에 걸쳐 크게 맡기기보다, canonical model, UI adapter, proxy, QA처럼 충돌이 적은 단위로 나눈다.
- 구현 subagent와 review subagent를 분리한다.
- 메인은 마지막에 `git diff`, 테스트 결과, 브라우저 QA 결과, secret scan을 보고 릴리즈 여부를 결정한다.

## 2. 공통 불변 조건

아래 조건은 모든 WP에서 깨지면 안 됩니다.

- Scene 1만 Master Image Prompt를 가진다.
- Scene 2 이상은 first frame을 새로 생성하지 않고 previous final frame/start frame을 전제로 한다.
- Scene N의 exact_stop_state는 Scene N+1의 start_state와 의미상 동일해야 한다.
- non-final scene은 전체 완성, final reveal, cleanup을 수행하면 안 된다.
- final scene만 full reveal, final polish, clean workspace, zoom out을 사용할 수 있다.
- miniature people, tiny workers, human characters는 모든 profile에서 금지한다.
- giant human hands / hands only 규칙은 모든 profile에서 유지한다.
- negative prompt는 video prompt 마지막에 정확히 1회 붙는다.
- NIM은 문장 표현만 다듬을 수 있고 scene count, scene id, start_state, exact_stop_state, forbidden actions, negative prompt를 바꾸면 안 된다.
- Source Draft가 바뀌면 기존 Applied Prompt는 stale 상태가 되어야 한다.
- Applied Prompt, Scene Outputs, Scene Preview, Copy, Export는 같은 canonical applied plan에서 파생되어야 한다.

## 3. 현재 변경 파일군

현재 워크트리에는 구현 변경과 신규 파일이 존재합니다. 다음 모델은 작업 전 반드시 `git status --short`와 `git diff --stat`를 먼저 확인해야 합니다.

주요 변경 파일군:

- UI: `ui/app.js`, `ui/index.html`, `ui/styles.css`, `ui/error_handling.js`, `ui/fetch_wrapper.js`, `ui/provenance_model.js`, `ui/request_adapter.js`, `ui/source_revision.js`, `ui/state_store.js`
- Python pipeline: `src/domain.py`, `src/export_prompts.py`, `src/nim_client.py`, `src/nim_proxy_server.py`, `src/scene_md_export.py`, `src/serializers.py`
- Python support modules: `src/error_handling.py`, `src/fallback_builder.py`, `src/fetch_wrapper.py`, `src/lineage_resolver.py`, `src/provenance_model.py`, `src/response_normalizer.py`, `src/scene_canonicalizer.py`, `src/state_store.py`, `src/ui_adapter.py`
- Tests: `tests/nim/test_nim_proxy.py`, `tests/nim/test_wp0_secrets.py`, `tests/test_wp2_ui_request_adapter.py`, `tests/test_wp3_post_normalization.py`, `tests/test_wp4_source_revision_parity.py`, `tests/test_wp5_canonical_source.py`, `tests/serializers/test_serializers.py`
- Docs: `README.md`, `docs/run-guide.md`, `docs/deploy-checklist.md`, `docs/ops-guide.md`

## WP-0: Secret Removal And Key Safety

목표:

- 브라우저 UI에서 NVIDIA NIM API key를 직접 저장하거나 장기 보관하지 않는다.
- localStorage/sessionStorage/indexedDB에 실 키가 남지 않는다.
- 로그, 에러 배지, 테스트 fixture, README, docs에 실 키가 남지 않는다.

검증 항목:

- `ui/*`에서 `NIM_API_KEY`, `nvapi-` 실 값 저장 로직 제거 여부 확인
- `src/nim_proxy_server.py`가 env 기반 key만 사용하거나 안전한 1회성 session token만 쓰는지 확인
- 에러 메시지는 secret redaction 후 표시되는지 확인
- 문서 예시는 placeholder만 쓰는지 확인

필수 테스트:

```bash
rtk uv run pytest tests/nim/test_wp0_secrets.py -q
rtk rg -n "nvapi-[A-Za-z0-9_-]{20,}" . --glob '!TODO.md'
```

완료 조건:

- secret scan 결과 실 키 0건
- UI 저장소에 API key가 남지 않는다는 테스트 존재
- proxy/server 로그에 Authorization 값이 출력되지 않음

## WP-1: NIM Loopback Proxy

목표:

- browser -> loopback proxy -> NVIDIA NIM 구조를 완성한다.
- 브라우저는 upstream API key를 몰라야 한다.
- proxy는 request schema를 검증하고 upstream 응답을 canonical response로 변환한다.

검증 항목:

- proxy endpoint와 UI request path가 실제로 일치하는지 확인
- health endpoint가 현재 실행 가이드와 일치하는지 확인
- CORS는 허용 origin에만 응답하는지 확인
- 모델명은 `profile.id`가 아니라 명시적인 NIM model id를 사용해야 한다.
- upstream 401/403/404는 retry하지 않고 즉시 실패해야 한다.
- upstream 429/5xx/network timeout은 제한된 retry 후 실패해야 한다.

필수 테스트:

```bash
rtk uv run pytest tests/nim/test_nim_proxy.py -q
```

완료 조건:

- 실제 NIM 호출 성공/실패가 proxy 레벨에서 재현 가능
- 실패 원인이 UI 상태 메시지에 구체적으로 전달됨
- local draft fallback과 NIM success가 명확히 구분됨

## WP-2: UI Request Adapter And Runtime State

목표:

- Source Draft를 canonical request payload로 변환한다.
- Review & Generate가 실행되면 현재 editable Source Draft revision을 계산한다.
- NIM enabled면 proxy 호출을 수행하고, disabled면 local deterministic plan을 적용한다.
- 로딩 중에는 stale response가 적용되지 않도록 request_id/source_revision을 고정한다.

검증 항목:

- Generate 버튼 클릭 전/후 상태 전이가 명확한지 확인
- loading progress 또는 spinner가 응답 완료까지 유지되는지 확인
- 응답 도착 전에 Source Draft가 수정되면 이전 응답이 폐기되는지 확인
- NIM enabled/disabled 체크 상태가 시각적으로 확실한지 확인
- "local draft is currently applied"가 NIM 성공 후 잘못 표시되지 않는지 확인

필수 테스트:

```bash
rtk uv run pytest tests/test_wp2_ui_request_adapter.py -q
rtk node --check ui/app.js ui/request_adapter.js ui/fetch_wrapper.js ui/error_handling.js
```

완료 조건:

- Applied Prompt 상단 provenance가 실제 적용 소스와 일치
- Generate 직후 Source Draft, Applied Prompt, Scene Preview의 stale/current 상태가 구분됨
- 실패 시 fallback 문구가 "NIM 성공"으로 보이지 않음

## WP-3: Post-NIM Normalization And Scene Boundary Guard

목표:

- NIM 응답이 헤더를 바꾸거나 일부 필드를 누락해도 canonical scene plan으로 복원한다.
- 복원 불가능한 응답은 실패로 처리하고 deterministic fallback을 적용한다.
- 특히 Scene 1부터 완성품까지 가는 오류를 막는다.

검증 항목:

- NIM이 scene header를 삭제해도 scene id/count가 보존되는지 확인
- NIM이 first frame을 Scene 2+에 추가하면 제거되는지 확인
- NIM이 negative prompt를 제거/수정하면 고정값으로 복구되는지 확인
- non-final scene video prompt에 final reveal/full completed/clean workspace가 들어가지 않는지 확인
- exact_stop_state와 reserved_future_actions가 prompt에 반영되는지 확인

필수 테스트:

```bash
rtk uv run pytest tests/test_wp3_post_normalization.py tests/serializers/test_serializers.py -q
```

완료 조건:

- Vehicle scene 1은 powertrain/chassis 등 지정 단계까지만 진행하고 완성 차량/비행기로 끝나지 않음
- Architecture scene 1은 foundation/walls까지만 진행하고 roof/landscaping/final reveal로 넘어가지 않음
- Product/Home Decor/Cooking도 각 profile에 맞는 stop boundary가 존재함

## WP-4: Source Revision Parity

목표:

- Python과 browser가 같은 Source Draft에 대해 같은 source_revision을 계산한다.
- Source Draft 변경은 Applied Prompt stale 상태를 유발한다.

검증 항목:

- canonical JSON serialization 키 순서, whitespace, null 처리 방식 통일
- UI와 Python fixtures가 같은 hash를 생성하는지 확인
- export/import 후 revision이 유지되는지 확인

필수 테스트:

```bash
rtk uv run pytest tests/test_wp4_source_revision_parity.py -q
```

완료 조건:

- Python/browser parity fixture 통과
- stale NIM response가 적용되지 않음

## WP-5: Canonical Applied Source For Preview, Copy, Export

목표:

- Applied Prompt, Scene Outputs, Scene Preview, copy buttons, export markdown/json이 모두 같은 canonical applied plan을 사용한다.

검증 항목:

- Applied Prompt에 있는 negative prompt가 Scene Preview에도 동일하게 존재
- copy 버튼이 local template을 다시 생성하지 않고 applied plan에서 복사
- Scene Outputs와 Scene Preview가 서로 다른 parser를 쓰더라도 결과가 불일치하지 않음
- 초기 화면에서는 Applied Prompt, Scene Outputs, Scene Preview가 비어 있음
- Generate 실패 시에만 deterministic fallback이 채워짐

필수 테스트:

```bash
rtk uv run pytest tests/test_wp5_canonical_source.py tests/serializers/test_serializers.py -q
```

완료 조건:

- UI에서 보이는 내용과 복사되는 내용이 동일
- "Applied from NIM response"일 때 복사 결과도 NIM 적용본
- "Local Draft"일 때 복사 결과도 local deterministic applied plan

## WP-6: Profile-Specific Prompt Fidelity

목표:

- 사용자가 제공한 reference prompt 4종과 추가 profile들이 최대한 원형 의도를 유지한다.
- 모든 profile은 동일한 pipeline 구조를 따르되, domain vocabulary와 scene boundary는 profile별로 달라야 한다.

검증 항목:

- Korean architecture: hanok/temple/villa/store/school/hotel/apartment/factory/barn 등 subtype별 재질, 색감, 공정 언어가 구체적인지 확인
- Vehicle assembly: category/model 고정 선택지가 있고, 각 scene이 단계별 조립 stop boundary를 갖는지 확인
- Product/object assembly: 100% disassembled parts, tool logic, clean final workspace가 final scene 전용인지 확인
- Home decor DIY: 10초 단일 튜토리얼, hands only, Korean material + narration, no music 조건 유지
- Miniature cooking: 재료 준비 -> 조리 -> 플레이팅 흐름이 scene별로 과도하게 완성되지 않는지 확인

필수 테스트:

```bash
rtk uv run pytest tests/profiles tests/test_basic.py -q
```

완료 조건:

- profile별 Topic label은 기본적으로 `Genre-Subtype` 형식
- 각 profile의 first frame prompt가 공통 템플릿 반복에 머물지 않고 subtype/model/material을 충분히 반영
- camera/lighting/material/color recommendation이 profile별로 반영

## WP-7: Browser And Mobile QA

목표:

- 실제 사용 화면에서 Source Draft -> Review & Generate -> Applied Prompt -> Scene Preview -> Copy -> Flow handoff 흐름이 혼동 없이 작동한다.

검증 항목:

- Source Draft는 editable card inputs로 보이고 Applied Prompt는 read-only scroll panel로 보임
- Master Image Prompt가 Video Prompt보다 위에 표시됨
- copy 버튼 텍스트가 모바일/데스크톱에서 잘리지 않음
- Scene Preview가 Applied Prompt 전용 결과임이 명확함
- loading bar/spinner가 NIM 응답 전까지 유지됨
- status badge 색상과 문구가 success/fallback/error/stale을 직관적으로 구분함
- Google Flow link가 Applied Prompt/Flow handoff 영역에서 접근 가능

필수 테스트:

```bash
rtk uv run pytest tests/browser/ -q
```

수동 QA:

- Desktop viewport에서 architecture 30초 generate
- Mobile viewport에서 vehicle 30초 generate
- NIM disabled local draft generate
- NIM enabled success generate
- NIM enabled forced failure fallback
- Source Draft 수정 후 stale 표시 확인
- Scene 2+에 first frame prompt가 표시되지 않는지 확인

완료 조건:

- 사용자가 "지금 복사하는 프롬프트가 실제 적용본인지" 화면에서 즉시 판단 가능
- 화면에 성공처럼 보이는 실패 상태가 없음
- 긴 prompt 스크롤과 복사가 안정적

## WP-8: Final Release Gate

목표:

- WP-0부터 WP-7까지의 구현이 "작성됨"이 아니라 "릴리즈 가능하게 검증됨"을 증명한다.
- 이 gate를 통과하기 전에는 커밋/푸시/릴리즈 태그를 만들지 않는다.
- TODO.md는 커밋 대상에서 제외한다.

### WP-8.1 Release Candidate Inventory

릴리즈 후보를 만들기 전 다음을 기록한다.

- current branch
- current commit
- `git status --short`
- staged files
- unstaged files
- untracked files
- TODO.md가 staged에 포함되어 있지 않은지
- 실 API key가 포함된 파일이 없는지

필수 명령:

```bash
rtk git status --short
rtk git diff --stat
rtk git diff --cached --stat
```

통과 기준:

- TODO.md는 modified일 수 있으나 staged/commit 대상이 아님
- 의도하지 않은 파일 변경이 없음
- untracked 파일이 모두 필요한 구현/테스트/문서 파일로 설명 가능

### WP-8.2 Static Release Gate

필수 명령:

```bash
rtk uv run python3 -m py_compile src/*.py
rtk node --check ui/app.js ui/error_handling.js ui/fetch_wrapper.js ui/provenance_model.js ui/request_adapter.js ui/source_revision.js ui/state_store.js
rtk git diff --check
```

통과 기준:

- Python syntax error 0건
- JS syntax error 0건
- whitespace error 0건

실패 시:

- 실패 파일만 수정한다.
- unrelated formatting은 하지 않는다.
- 수정 후 같은 gate를 다시 실행한다.

### WP-8.3 Automated Test Gate

필수 명령:

```bash
rtk uv run pytest tests/nim/test_wp0_secrets.py -q
rtk uv run pytest tests/nim/test_nim_proxy.py -q
rtk uv run pytest tests/test_wp2_ui_request_adapter.py -q
rtk uv run pytest tests/test_wp3_post_normalization.py -q
rtk uv run pytest tests/test_wp4_source_revision_parity.py -q
rtk uv run pytest tests/test_wp5_canonical_source.py -q
rtk uv run pytest tests/serializers/test_serializers.py -q
rtk uv run pytest tests/profiles tests/test_basic.py -q
```

가능하면 최종 전체 테스트:

```bash
rtk uv run pytest tests/ -q
```

통과 기준:

- WP별 테스트 모두 pass
- 전체 테스트 pass
- skip이 있다면 사유가 문서화되어야 함

### WP-8.4 Security Gate

필수 명령:

```bash
rtk rg -n "nvapi-[A-Za-z0-9_-]{20,}" . --glob '!TODO.md'
rtk rg -n "localStorage.*api|api.*localStorage|sessionStorage.*api|api.*sessionStorage" ui src docs README.md
```

통과 기준:

- 실 API key 패턴 0건
- 브라우저 저장소에 API key를 저장하는 코드 0건
- 문서에는 placeholder만 존재
- error/log sanitizer 테스트 통과

중요:

- 과거 대화에 노출된 키는 이미 노출된 것으로 간주하고 회전해야 한다.
- 코드가 안전해도 기존 키를 계속 쓰면 release gate fail로 본다.

### WP-8.5 NIM Integration Gate

준비:

- 새로 회전한 NVIDIA NIM key를 env로만 주입한다.
- UI에는 실 키를 입력하지 않는다.
- proxy는 loopback에만 bind한다.

권장 실행:

```bash
export NIM_API_KEY="<NVIDIA_API_KEY>"
export ALLOWED_ORIGIN="http://127.0.0.1:4173"
export NIM_PROXY_SESSION_TOKEN="<SESSION_TOKEN>"
rtk uv run python3 src/nim_proxy_server.py --host 127.0.0.1 --port 4174
```

별도 터미널:

```bash
cd ui
python3 -m http.server 4173 --bind 127.0.0.1
```

검증 시나리오:

- NIM disabled: local deterministic draft applied
- NIM enabled + valid key: Applied Prompt provenance is NIM
- NIM enabled + invalid key: fallback applied with explicit failure message
- NIM enabled + stale response: response discarded and current Source Draft preserved
- NIM response missing scene headers: normalized or rejected safely
- NIM response modifying negative prompt: fixed negative restored

통과 기준:

- NIM 성공 상태에서 Applied Prompt label/provenance/copy/export가 모두 NIM 적용본
- NIM 실패 상태에서 fallback이 적용되고 성공 배지로 표시되지 않음
- NIM 응답이 structural invariant를 깨면 release fail 또는 safe fallback

### WP-8.6 Canonical UI Gate

수동 QA 체크:

- 초기 진입 시 Applied Prompt, Scene Outputs, Scene Preview는 비어 있음
- Review & Generate 전에는 copy 버튼이 disabled이거나 명확한 empty 상태
- Generate 후 Applied Prompt와 Scene Preview 내용이 동일한 canonical plan에서 파생됨
- Applied Prompt에 있는 negative prompt가 Scene Preview와 copy 결과에도 존재
- Scene 2+에는 Master Image Prompt/First Frame Prompt가 표시되지 않음
- Master Image Prompt block이 Video Prompt block보다 위에 표시됨
- copy 버튼 label이 잘리지 않음
- Topic label 변경 시 prompt 내용이 자동 갱신되거나 stale 상태로 표시됨

통과 기준:

- 사용자가 Flow에 붙여 넣을 프롬프트가 어느 소스에서 왔는지 혼동하지 않음
- Scene Preview는 local template preview가 아니라 Applied Prompt preview임
- 실패 시 기본 템플릿/fallback이 들어가되 실패 원인이 보존됨

### WP-8.6A Flow Handoff Boundary Gate

목표:

- 이 앱이 자동으로 검증할 수 있는 것과 Google Flow 화면에서 사용자가 직접 확인해야 하는 것을 분리한다.

확인 항목:

- 앱은 Google Flow 프로젝트 내부 상태를 자동 검증한다고 표시하지 않는다.
- "previous final frame attached" 같은 상태는 사용자가 Flow 화면에서 완료했다고 표시한 confirmation일 뿐, 시스템 자동 검증으로 표현하지 않는다.
- Scene 2+ instructions는 "upload/use the saved final frame from Scene N as the start frame"을 명확히 안내한다.
- Flow handoff copy에는 prompt뿐 아니라 어떤 image/start frame을 넣어야 하는지도 scene별로 포함된다.
- Scene 1은 approved master image를 사용하고, Scene 2+는 previous saved final frame을 사용한다는 작업 순서가 화면과 문서에서 일치한다.

통과 기준:

- 사용자가 앱 화면만 보고 "Flow에 어떤 프레임을 넣어야 하는지" 판단 가능
- 앱이 외부 Flow 결과를 자동 검증한 것처럼 오해시키는 문구 0건
- 수동 confirmation과 automated validation이 UI/문서에서 구분됨

### WP-8.7 Prompt Quality Gate

각 profile에서 최소 1개씩 sample generate를 수행한다.

필수 sample:

- Architecture-Hanok, 30s
- Vehicle-Airplane-P-51 Mustang, 30s
- Product-Watch or Product-Camera, 30s
- HomeDecor-Korean material craft, 10s
- Cooking-Korean miniature dish, 30s

각 sample에서 확인:

- Scene 1 first frame은 실제 시작 상태이며 이미 완성된 대상이 없음
- Scene 1 video는 전체 완성까지 가지 않고 exact_stop_state에서 종료
- Scene 2는 previous final frame/start frame을 전제로 시작
- final scene만 reveal/cleanup/zoom-out 허용
- subject identity가 generic construction/object로 드리프트하지 않음
- forbidden_future_actions가 prompt에 명확히 포함됨

통과 기준:

- "첫 영상부터 완성되어버림" 재현 0건
- "Scene Preview와 Applied Prompt 불일치" 재현 0건
- "작은 사람 등장"을 유발할 수 있는 누락 negative 0건

### WP-8.8 Docs And Operations Gate

검증 문서:

- `README.md`
- `docs/reference-frame-relay-spec.md`
- `docs/run-guide.md`
- `docs/deploy-checklist.md`
- `docs/ops-guide.md`

확인 항목:

- 포트 번호가 코드와 문서에서 일치
- endpoint path가 코드와 문서에서 일치
- `GET /health`는 token 없이 가능하고 `POST /api/nim/rewrite`는 `Origin`과 `X-Session-Token`이 필요하다는 경계가 문서에 명시
- 실행 순서가 실제로 동작
- rollback 명령에 오타가 없음
- secret placeholder만 존재
- Flow workflow terminology가 Master image, Start frame, Saved frame, Scenebuilder로 통일

통과 기준:

- 새 모델이 문서만 보고 local run과 QA를 재현 가능
- deploy checklist가 WP-8 gate와 충돌하지 않음

### WP-8.9 Commit And Push Gate

커밋 전 확인:

```bash
rtk git status --short
rtk git diff -- TODO.md
rtk git diff --cached --name-only
```

커밋 대상:

- 구현 파일
- 테스트 파일
- 정식 문서 파일

커밋 제외:

- `TODO.md`
- 실 키나 로컬 환경 파일
- generated output
- cache

권장 staging 방식:

```bash
rtk git add README.md pyproject.toml src tests ui docs schema
rtk git restore --staged TODO.md
rtk git status --short
```

최종 확인:

- TODO.md가 staged에 없어야 함
- secret scan pass
- test gate pass
- 사용자가 푸시를 요청했을 때만 push

커밋 메시지 예시:

```text
Finalize reference-frame relay NIM pipeline gates
```

### WP-8.10 Release Approval Criteria

릴리즈 승인 조건:

- WP-0 through WP-7 completion evidence exists
- WP-8.1 through WP-8.9 all pass
- NIM success/failure/fallback states are reproducible
- UI canonical consistency is manually verified
- profile prompt quality sample is manually verified
- docs run commands match actual server behavior
- rollback path is tested or at least command-reviewed
- TODO.md remains local-only

릴리즈 차단 조건:

- 실 API key 노출
- NIM success 표시와 실제 Applied Prompt provenance 불일치
- Scene Preview와 copy/export 불일치
- Scene 1이 final object까지 완성되는 prompt 생성
- Scene 2+에 first frame prompt 생성
- negative prompt 누락 또는 중복
- stale NIM response가 최신 Source Draft를 덮어씀
- docs의 port/endpoint와 코드 불일치
- 테스트 실패

### WP-8.11 Main/Subagent Release Responsibility Gate

목표:

- 최종 승인 책임과 구현 증적 제출 책임을 분리한다.

역할:

- 메인 에이전트는 release gate owner다.
- 메인 에이전트는 각 WP의 증적을 검토하고, merge/commit/push 가능 여부를 최종 판단한다.
- 서브에이전트는 지정된 WP 또는 파일 범위의 implementation owner다.
- 서브에이전트는 수정 파일, 테스트 명령, pass/fail 결과, 남은 위험을 보고한다.
- browser/mobile QA 담당 서브에이전트는 screenshot 또는 Playwright 결과를 증적으로 남긴다.
- NIM integration 담당 서브에이전트는 실제 proxy/upstream smoke 결과와 redacted error 결과를 증적으로 남긴다.

최종 승인 전 메인 에이전트 확인:

- 모든 subagent 결과가 현재 워크트리에 반영되어 있는지
- subagent가 보고한 테스트를 메인에서도 필요한 범위만 재실행했는지
- 실패/skip/수동 확인 항목이 release blocker인지 문서화했는지
- TODO.md가 staged 대상이 아닌지
- 사용자에게 push 여부를 확인했거나 사용자가 이미 명시적으로 요청했는지

통과 기준:

- 구현자와 승인자의 역할이 섞이지 않음
- release gate를 통과하지 않은 상태에서 push하지 않음
- 남은 위험이 "추정"이 아니라 "검증 결과 또는 차단 조건"으로 정리됨

## 4. 다음 모델에게 줄 권장 프롬프트

```text
현재 저장소의 TODO.md를 기준으로 Reference-Frame Relay v2 release gate를 마무리해 주세요.

운영 원칙:
- 메인 에이전트는 지시/검증/통합만 수행합니다.
- 구현은 GPT-5.4 계열 서브에이전트로 WP 단위로 나눕니다.
- TODO.md는 로컬 인수 문서이므로 커밋/푸시하지 않습니다.
- 사용자 변경사항은 되돌리지 않습니다.

먼저 다음을 수행하세요:
1. git status --short와 git diff --stat으로 현재 변경 범위를 확인합니다.
2. WP-0부터 WP-7까지 실제 구현/테스트/문서가 완료되었는지 증거를 확인합니다.
3. WP-8 Final Release Gate의 각 하위 게이트를 순서대로 실행합니다.
4. 실패한 gate는 원인별로 작은 서브에이전트 작업으로 분리합니다.
5. 모든 gate가 통과하면 TODO.md를 제외하고 필요한 파일만 커밋 대상으로 선별합니다.
6. 사용자가 명시적으로 요청한 경우에만 push합니다.
```

## 5. 현재 가장 먼저 할 일

1. 현재 워크트리 변경이 실제로 WP-0~WP-7 구현 완료 상태인지 검증한다.
2. `docs/run-guide.md`, `docs/deploy-checklist.md`, `src/nim_proxy_server.py`, UI request path의 port/endpoint 일치 여부를 확인한다.
3. WP-8.2 static gate부터 실행한다.
4. 실패 시 해당 gate만 작은 구현 작업으로 분리한다.
5. 모든 gate 통과 전에는 release commit/push를 하지 않는다.
