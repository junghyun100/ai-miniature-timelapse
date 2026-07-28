# 안전 종료용 TODO / 실행 명세

이 문서는 기준 커밋 `05f6a59` 시점의 상태를 고정하고, 다음 모델이 그대로 이어서 구현할 수 있도록 만든 상세 실행 명세다. 검증 기준은 `94 passed`이다.

이 문서는 **루트 `TODO.md`만** 수정하는 인수 문서이며, 다른 파일은 건드리지 않는다.

## 0) 문서 목적

- 현재까지 확정된 계약과 미해결 문제를 분리해 기록한다.
- 다음 모델이 구현 범위를 오해하지 않도록 사실/추정/미확인 사항을 구분한다.
- NIM relays, UI adapter, post-normalization, provenance, QA, 운영 문서를 한 번에 위임할 수 있도록 작업 지시를 표준화한다.
- 회귀 금지 규칙을 명시해 architecture, vehicle, product, home decor, cooking 전반의 기존 안정성을 보존한다.

## 1) 현재 상태

### 1.1 완료된 profile 계약

현재 기준으로 다음 계약은 **완료**로 본다.

- 공통 `profile selection` 흐름이 정리되어 있다.
- architecture / vehicle / product / home decor / cooking이 하나의 선택 흐름으로 연결된다.
- 각 profile은 서로 다른 장르이지만, 공통 파이프라인 계약을 따른다.
- `Scene 1`만 `MASTER_IMAGE`를 사용한다.
- `Scene 2+`는 `PREVIOUS_FINAL_FRAME`를 사용한다.
- `Scene Preview`, `Applied Prompt`, copy 동작의 기준이 하나의 canonical model로 수렴해야 한다는 방향이 잡혀 있다.
- architecture 13 subtype 정합성은 기준점이 마련되어 있다.

### 1.2 현재 구현의 실질적 상태

- 최종 테스트 기준은 `94 passed`다.
- `node --check`와 `git diff --check`는 통과 상태로 정리되어 있다.
- 그러나 NIM 관련 흐름은 아직 **표시상 성공**과 **실제 호출 성공**이 다를 수 있다.
- 따라서 UI가 성공처럼 보여도 실제 NIM call, proxy relay, session bootstrap, post-normalization 성공을 따로 검증해야 한다.

### 1.3 이번 명세의 핵심 목표

이 문서의 목표는 다음이다.

1. 비밀값을 브라우저에서 제거한다.
2. NIM을 브라우저 직접 호출이 아니라 loopback proxy 뒤로 둔다.
3. request / response / retry / timeout / abort / stale guard를 UI adapter에 넣는다.
4. post-normalization으로 scene contract를 다시 보정한다.
5. browser-Python source revision parity를 보장한다.
6. Applied Prompt / Scene Preview / Copy의 canonical source를 하나로 고정한다.
7. desktop / mobile QA와 운영 문서를 마무리한다.

## 2) 알려진 문제

### 2.1 사실로 확인된 문제

- `UI toggle`은 실제 NIM 호출 그 자체를 의미하지 않는다.
- browser에 저장된 API key, `base URL`, 또는 `localStorage` 기반 보관은 보안상 위험하다.
- `forward_to_nim()`이 현재 `profile.id`를 upstream `model`로 사용하는 것은 확인된 버그다.
- session bootstrap, `CORS`, post-normalization, source parity는 현재 코드 근거와 검증 필요를 구분해야 한다.
- NIM 응답이 늦게 오면 더 최신 draft를 덮어쓸 위험이 있다.

### 2.2 미확인 사항

다음은 아직 검증 필요다.

- proxy가 실제로 `model_id`를 올바르게 전달하는지
- session token이 URL fragment 기반 메모리 전용 방식으로만 처리되는지
- `/health`가 운영 전제에 맞는 readiness만 반환하는지
- response post-normalization이 scene header 손실과 fallback을 복구하는지
- browser-Python parity가 source revision 단위로 끝까지 맞는지
- desktop/mobile에서 copy와 preview가 동일 canonical model을 쓰는지

### 2.3 사실과 추정 분리

- **사실**: 현재 문서상 문제 목록에 적힌 항목들은 모두 해결해야 할 리스크다.
- **사실**: `94 passed`는 과거 검증 결과이며, 기능적 완성의 증거는 아니다.
- **추정**: 실제 UI 성공 표시가 NIM 성공을 뜻할 것이라는 기대는 아직 검증되지 않았다.
- **추정**: browser 직접 호출을 유지한 채 일부만 수정하면 보안·정합성 문제가 남을 가능성이 높다.

## 3) P0~P3 백로그

### P0

- WP-0 비밀 제거·키 회전
- WP-1 NIM loopback proxy

### P1

- WP-2 UI request adapter
- WP-3 response post-normalization
- WP-4 browser-Python source revision parity

### P2

- WP-5 Applied Prompt·Scene Preview·Copy canonical source
- WP-6 desktop/mobile QA

### P3

- WP-7 실행·운영 문서
- WP-8 최종 release gate

## 4) 회귀 금지

다음 항목은 절대 후퇴시키지 않는다.

- `Architecture 13 subtype 30/60`
- `Vehicle 10 category dependent model 30/60`
- `Product 10 subtype 10/30/60`
- `HomeDecor 10s narration`
- `Cooking 30s`
- `N+1 start==N stop`
- `non-final completion 금지`
- `final-only reveal`
- `Scene1-only master`
- `hands-only`
- `negative once-last`

회귀 금지의 의미:

- 기존 scene boundary를 다시 느슨하게 만들지 않는다.
- Scene 2+에 새 master image를 만들지 않는다.
- final frame relay를 text-only continuity로 되돌리지 않는다.
- hands-only 계약을 miniature people 허용 방향으로 바꾸지 않는다.
- negative prompt를 scene마다 변형하지 않는다.

## 5) 메인 에이전트 / GPT-5.4-mini 역할

### 5.1 메인 에이전트 역할

메인 에이전트는 다음을 책임진다.

- 작업 우선순위 결정
- 사실/추정/미확인 구분
- WP 간 충돌 조정
- 병렬 작업 가능 여부 판단
- 통합 체크포인트 승인
- rollback 판단
- release gate 최종 승인

### 5.2 GPT-5.4-mini 역할

GPT-5.4-mini는 다음을 맡는다.

- 파일 범위가 좁은 구현
- adapter / proxy / normalization 같은 국소 수정
- 테스트 추가 및 정적 검증
- 명세에 맞는 데이터 구조 변환

### 5.3 파일 충돌 경계

다음 원칙을 지킨다.

- 한 WP가 다른 WP의 canonical source를 임의로 덮어쓰지 않는다.
- proxy와 UI adapter는 같은 필드를 서로 다른 의미로 재정의하지 않는다.
- browser 쪽과 Python 쪽은 source revision 계약을 공유한다.
- preview/copy/Applied Prompt는 서로 다른 렌더러를 쓰지 않는다.

### 5.4 병렬 가능 매트릭스

병렬 가능:

- WP-0 + WP-1
- WP-2 + WP-4
- WP-5 + WP-6
- WP-7은 WP-3, WP-4가 안정된 뒤 병렬 가능

순차 권장:

- WP-0 → WP-1 → WP-2 → WP-3
- WP-4는 WP-3의 data contract를 따라야 함
- WP-8은 모든 이전 WP 완료 뒤 수행

### 5.5 통합 체크포인트

다음 지점에서 반드시 통합 점검한다.

1. secret 제거 후 browser에 남은 값이 없는지
2. proxy health, model_id, session token이 실제로 연결되는지
3. adapter request가 stale request를 버리는지
4. post-normalization이 scene fallback을 보전하는지
5. preview/copy가 canonical source를 그대로 읽는지
6. desktop/mobile에서 동일 결과가 보이는지

### 5.6 rollback 원칙

- 실패 시 해당 WP의 변경만 되돌린다.
- canonical data model을 깨뜨리는 변경은 즉시 중단한다.
- branch-level rollback 대신 scene-level or module-level rollback을 우선한다.
- 비밀값 회수 또는 재발급이 필요한 경우 먼저 키 회전을 수행한다.

## 6) WP 공통 형식

각 WP는 아래 항목을 반드시 포함한다.

- 목표
- 문제
- 수정 허용 파일
- 불변 계약
- 단계별 구현
- API / 데이터 예시
- 실패 규칙
- acceptance criteria
- 구체 테스트
- 선행 의존성
- 완료 보고 형식

---

## 7) WP-0 비밀 제거·키 회전

### 목표

브라우저 저장형 비밀을 제거하고, API key가 유출되었을 가능성을 전제로 안전한 재발급/회전 경로를 만든다.

### 문제

- 브라우저 직접 저장은 노출 표면이 크다.
- `localStorage`는 XSS, 디버깅, 사용자 공유 환경에서 취약하다.
- 키가 로그, clipboard, copied prompt, error message에 섞일 수 있다.

### 수정 허용 파일

- `ui/index.html`
- `ui/app.js`
- `tests/test_ui_nim_integration.py`

### 불변 계약

- raw API key는 브라우저 state, exported JSON, logs, clipboard, git history에 남지 않는다.
- placeholder는 실제 값과 시각적으로 구분된다.
- key rotation은 기존 사용자 흐름을 최대한 끊지 않는다.

### 단계별 구현

1. 비밀값 저장 위치를 inventory한다.
2. 브라우저 영속 저장을 제거한다.
3. session-scoped 전달 방식으로 바꾼다.
4. 회전 전/후 key 구분 규칙을 만든다.
5. error path에서 secret masking을 확인한다.

### API / 데이터 예시

```json
{
  "api_key_source": "env|session|ephemeral",
  "secret_state": "redacted",
  "rotation_required": true
}
```

### 실패 규칙

- key가 브라우저 storage에 남으면 실패다.
- placeholder가 실제 키처럼 복사되면 실패다.
- secret masking이 누락되면 실패다.

### acceptance criteria

- 브라우저 reload 후에도 secret이 복원되지 않는다.
- secret이 UI 텍스트, export, console에 노출되지 않는다.
- key rotation 안내가 사용자에게 명확하다.

### 구체 테스트

- browser storage inspection
- copy output redaction check
- error message snapshot check
- reload persistence check

### 선행 의존성

- 없음. P0 독립 착수 가능.

### 완료 보고 형식

```text
WP-0 complete
- secret sources removed: ...
- rotation path: ...
- redaction verified: yes/no
- residual risk: ...
```

### 복사 가능한 위임 프롬프트

```text
WP-0를 맡아 주세요. 목표는 브라우저 저장형 비밀 제거와 키 회전입니다.
사실: localStorage와 UI 입력이 secret 노출 위험을 만들 수 있습니다.
불변 계약: raw API key는 browser storage, logs, export, clipboard, git history에 남지 않아야 합니다.
허용 파일: secret handling 관련 실제 코드만, TODO.md는 변경하지 마세요.
해야 할 일: 저장 위치 inventory, session-scoped 전달, masking, reload 검증, copy/export redaction 테스트.
실패 규칙: 브라우저 reload 후 secret 복원, placeholder가 실제 키처럼 보임, error path 노출.
완료 보고: 제거된 source, rotation path, redaction 결과, residual risk를 적어 주세요.
```

---

## 8) WP-1 NIM loopback proxy(model_id, env key, health, CORS, session token)

### 목표

NIM 호출을 브라우저에서 분리하고, loopback proxy가 `model_id`, env key, health, CORS, session token을 책임지게 한다.

### 문제

- 브라우저에서 직접 호출하면 secret과 CORS 문제가 생긴다.
- `profile.id`를 `model`로 잘못 보낼 위험이 있다.
- session bootstrap이 없으면 요청 분리와 재시도가 불안정하다.

### 수정 허용 파일

- `src/nim_proxy_server.py`
- `tests/nim/test_nim_proxy.py`

### 불변 계약

- `model_id`는 `profile.id`와 혼동되지 않는다.
- proxy는 session token을 검증한다.
- session token 권장안은 URL fragment `#nim-session=<per-launch-token>`를 메모리에만 읽고 즉시 URL에서 제거하는 방식이다.
- `/health`는 token을 반환하지 않는다.
- health endpoint는 실제 readiness만 반영한다.
- CORS는 필요한 origin만 허용한다.

### 단계별 구현

1. `model_id`와 `profile.id`를 분리한다.
2. env key를 browser가 아니라 proxy가 읽는다.
3. session token은 URL fragment에서 읽은 뒤 즉시 URL에서 제거하고 메모리에만 둔다.
4. `/health`를 추가한다.
5. CORS policy를 제한한다.
6. request path에 session token을 전달하고 proxy가 검증한다.

### API / 데이터 예시

```json
{
  "model_id": "nim-model-name",
  "profile_id": "architecture-hanok",
  "session_token": "st_***",
  "origin": "http://localhost:3000"
}
```

예시 endpoint:

```text
GET  /health
POST /api/nim/rewrite
```

신규 설계 제안으로만 남기는 항목:

```text
/api/nim/bootstrap
/api/nim/relay
```

### 실패 규칙

- `profile.id`가 그대로 model name으로 나가면 실패다.
- `model_id`가 잘못 매핑되면 실패다.
- health가 green인데 rewrite가 실패하면 실패다.
- session token 없이 rewrite가 통과하면 실패다.
- 허용되지 않은 origin이 응답을 받으면 실패다.

### acceptance criteria

- proxy가 브라우저 secret 없이 동작한다.
- relay 요청마다 session token 검증이 있다.
- health endpoint가 실제 readiness를 보여 준다.
- CORS가 필요한 UI만 통과시킨다.

### 구체 테스트

- rewrite / health integration test
- model_id mapping test
- CORS origin test
- health endpoint test
- missing token failure test

### 선행 의존성

- WP-0 선행 또는 동시 진행 가능
- browser adapter는 proxy contract를 알아야 함

### 완료 보고 형식

```text
WP-1 complete
- proxy endpoints: ...
- model_id mapping: ...
- session token flow: ...
- CORS policy: ...
- health check: ...
```

### 복사 가능한 위임 프롬프트

```text
WP-1을 맡아 주세요. 목표는 NIM loopback proxy 구축입니다.
사실: browser direct call은 secret/CORS/session 문제를 만든다.
불변 계약: model_id, env key, health, CORS, session token이 proxy에서 관리되어야 합니다.
허용 파일: src/nim_proxy_server.py, tests/nim/test_nim_proxy.py.
해야 할 일: model_id/profile_id 분리, /health, /api/nim/rewrite, origin 제한, token 검증.
실패 규칙: profile.id가 model로 나감, token 없이 통과, 허용되지 않은 origin 허용.
완료 보고: endpoints, mapping, token flow, CORS, health를 적어 주세요.
```

---

## 9) WP-2 UI request adapter/fetch/retry/timeout/abort/stale/loading/provenance

### 목표

UI가 proxy를 호출할 때 request adapter를 통해 fetch, retry, timeout, abort, stale detection, loading state, provenance를 일관되게 처리한다.

### 문제

- 늦게 도착한 응답이 최신 draft를 덮을 수 있다.
- retry 정책이 없으면 일시적 실패가 user-visible error로만 남는다.
- loading / stale / aborted / retrying 상태가 섞이면 UX가 불분명해진다.

### 수정 허용 파일

- `ui/app.js`
- `ui/index.html`
- `tests/test_ui_nim_integration.py`

### 불변 계약

- 모든 request는 monotonic request id를 가진다.
- 모든 request는 source revision hash를 가진다.
- abort signal 없이 장시간 요청이 살아남지 않는다.
- stale response는 current draft를 덮지 않는다.
- stale 판정은 `request_id`, `source_revision`, `current revision`을 모두 비교한다.
- retry는 network, `429`, `5xx`에 대해서만 최대 2회 허용한다.
- retry 금지는 `400`, `401`, `403`, `404`다.
- deadline은 60초다.

### 단계별 구현

1. request metadata를 표준화한다.
2. fetch wrapper에 timeout과 abort를 넣는다.
3. retry policy를 `network/429/5xx` 최대 2회, `400/401/403/404` no retry, 60초 deadline으로 고정한다.
4. stale guard를 request id와 source revision으로 판정한다.
5. loading/provenance state를 UI에 노출한다.
6. 실패 원인을 분리해 보여 준다.

### API / 데이터 예시

```json
{
  "schema_version": "1.0",
  "request_id": "uuid",
  "source_revision": "sha256:...",
  "model_id": "nim-model-name",
  "profile": {
    "id": "architecture-hanok",
    "version": "13",
    "workflow_mode": "REFERENCE_FRAME_RELAY"
  },
  "subject": "Korean hanok",
  "style_bible": {
    "hands_rule": "giant human hands only"
  },
  "scenes": [],
  "mutable_fields": ["subject", "style_bible"],
  "immutable_rules": ["Scene 1 first-frame only", "negative once-last"],
  "state": "loading|retrying|stale|aborted|done",
  "attempt": 2,
  "timeout_ms": 30000
}
```

응답 예시:

```json
{
  "request_id": "uuid",
  "source_revision": "sha256:...",
  "scenes": []
}
```

### 실패 규칙

- request id가 뒤섞이면 실패다.
- timeout 후에도 응답을 적용하면 실패다.
- abort된 request를 success로 바꾸면 실패다.
- stale response가 current draft를 덮으면 실패다.
- request / response schema가 위 예시와 다르면 실패다.

### acceptance criteria

- 최신 draft만 렌더링된다.
- loading / retrying / aborted 상태가 분명히 구분된다.
- provenance가 어떤 source에서 왔는지 드러난다.
- timeout과 abort가 실제로 동작한다.

### 구체 테스트

- stale response race test
- timeout test
- abort test
- retry backoff test
- provenance display test

### 선행 의존성

- WP-1의 relay contract
- source revision 계약

### 완료 보고 형식

```text
WP-2 complete
- adapter states: ...
- timeout/abort: ...
- stale guard: ...
- provenance: ...
```

### 복사 가능한 위임 프롬프트

```text
WP-2를 맡아 주세요. 목표는 UI request adapter의 안정화입니다.
사실: 늦은 응답이 최신 draft를 덮을 위험이 있습니다.
불변 계약: request id, source revision, abort, timeout, retry, stale guard, provenance가 있어야 합니다.
허용 파일: UI adapter, fetch wrapper, state store, error handling, provenance model.
해야 할 일: monotonic request id, timeout/abort, retry policy, stale response discard, loading state 구분.
실패 규칙: timeout 후 응답 적용, abort를 success로 처리, stale response overwrite.
완료 보고: states, timeout/abort, stale guard, provenance를 적어 주세요.
```

---

## 10) WP-3 response post-normalization/scene fallback/negative once-last/Scene1 first-frame/identity/asset lineage

### 목표

NIM 또는 proxy 응답이 문구를 바꾸거나 일부 scene를 누락해도, post-normalization으로 canonical scene contract를 복구한다.

### 문제

- response가 scene header를 날릴 수 있다.
- NIM이 negative prompt를 바꾸거나 반복 구조를 흔들 수 있다.
- fallback이 없으면 한 scene 실패가 전체 plan 실패로 번질 수 있다.
- lineage가 끊기면 final frame relay가 무너진다.

### 수정 허용 파일

- `src/domain.py`
- `ui/app.js`
- `tests/nim/test_nim_contract.py`

### 불변 계약

- `Scene 1` first frame은 한 번만 존재한다.
- `negative once-last`는 유지된다.
- scene별 identity lock은 유지된다.
- asset lineage는 ancestor confirmation을 포함한다.
- 실패한 scene만 재시도 가능해야 한다.

### 단계별 구현

1. response를 파싱한다.
2. scene header와 field order를 정규화한다.
3. scene별 fallback을 적용한다.
4. `Scene 1`과 `Scene 2+`의 input mode를 강제한다.
5. identity lock과 negative line을 재삽입한다.
6. lineage hash를 재계산한다.

### API / 데이터 예시

```json
{
  "scene_id": 2,
  "input_mode": "PREVIOUS_FINAL_FRAME",
  "input_asset_ref": "scene_01_last_frame",
  "identity_lock": "single coherent Korean hanok",
  "negative_prompt": "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, small people, tiny workers, human figures"
}
```

### 실패 규칙

- Scene 2+에 first frame이 재생성되면 실패다.
- negative prompt가 한 번 더 중복되거나 바뀌면 실패다.
- scene fallback이 canonical identity를 깨면 실패다.
- lineage hash가 ancestors를 반영하지 않으면 실패다.

### acceptance criteria

- response가 일부 망가져도 canonical scene model이 유지된다.
- `Scene 1` first-frame 규칙이 강제된다.
- last-frame handoff와 identity lock이 복구된다.
- fallback scene이 적어도 deterministic하게 생성된다.

### 구체 테스트

- mangled response parse test
- missing header fallback test
- negative prompt stability test
- Scene 1 vs Scene 2 input mode test
- lineage hash regression test

### 선행 의존성

- WP-2 request metadata
- canonical scene schema

### 완료 보고 형식

```text
WP-3 complete
- normalization rules: ...
- fallback coverage: ...
- identity lock: ...
- lineage parity: ...
```

### 복사 가능한 위임 프롬프트

```text
WP-3을 맡아 주세요. 목표는 response post-normalization과 scene fallback입니다.
사실: NIM 응답은 header 삭제, negative prompt 변경, scene 누락을 일으킬 수 있습니다.
불변 계약: Scene 1 first-frame 단일화, negative once-last, identity lock, asset lineage 보존이 필요합니다.
허용 파일: response normalizer, scene canonicalizer, fallback builder, lineage resolver.
해야 할 일: response parse, field order 정규화, fallback scene 생성, negative line 재삽입, lineage hash 재계산.
실패 규칙: Scene 2+ first frame 재생성, negative line 변형, lineage hash ancestor 누락.
완료 보고: normalization rules, fallback coverage, identity lock, lineage parity를 적어 주세요.
```

---

## 11) WP-4 browser-Python source revision parity

### 목표

브라우저와 Python 소스가 동일한 `source revision`을 기준으로 움직이게 해, copy/export/preview/CLI 결과가 서로 어긋나지 않도록 한다.

### 문제

- 브라우저에서 본 Draft와 Python이 계산한 Draft가 다를 수 있다.
- source revision이 다르면 stale plan을 잘못 적용할 수 있다.
- copy/export가 다른 serialization을 사용하면 사용자가 다른 결과를 얻게 된다.

### 수정 허용 파일

- `src/domain.py`
- `ui/app.js`
- `tests/nim/test_nim_parity.py`

### 불변 계약

- 동일 입력은 동일 revision을 낸다.
- browser와 Python은 같은 canonical serialization을 쓴다.
- revision mismatch 시 stale로 판정한다.

### 단계별 구현

1. canonical serialization order를 확정한다.
2. browser hash와 Python hash를 동일 규칙으로 맞춘다.
3. export/import 시 revision을 붙인다.
4. mismatch 시 stale state를 표시한다.
5. parity test를 추가한다.

### API / 데이터 예시

```json
{
  "source_revision": "sha256:abcd...",
  "serialization_version": 2,
  "canonical_fields": ["topic", "profile", "workflow_mode", "scene_count"]
}
```

### 실패 규칙

- browser hash와 Python hash가 다르면 실패다.
- export된 plan이 revision 없이 나가면 실패다.
- stale plan이 active처럼 보이면 실패다.

### acceptance criteria

- 동일 input에 대해 browser와 Python source revision이 일치한다.
- export/import/preview/copy가 같은 revision을 보여 준다.
- mismatch는 명시적 stale로 표시된다.

### 구체 테스트

- browser vs Python hash parity test
- serialization order test
- stale export test
- CLI round-trip test

### 선행 의존성

- WP-2 and WP-3

### 완료 보고 형식

```text
WP-4 complete
- revision algorithm: ...
- parity result: ...
- stale behavior: ...
```

### 복사 가능한 위임 프롬프트

```text
WP-4를 맡아 주세요. 목표는 browser-Python source revision parity입니다.
사실: browser와 Python이 다른 serialization을 쓰면 stale 판정이 깨집니다.
불변 계약: 동일 input은 동일 source revision, mismatch는 stale.
허용 파일: browser revision logic, Python hashing logic, shared schema, CLI export.
해야 할 일: canonical serialization 확정, hash parity, export/import revision attach, parity tests.
실패 규칙: browser/Python hash 불일치, revision 없는 export, stale plan active 표시.
완료 보고: algorithm, parity result, stale behavior를 적어 주세요.
```

---

## 12) WP-5 Applied Prompt·Scene Preview·Copy 단일 canonical source

### 목표

Applied Prompt, Scene Preview, Copy, JSON download, CLI export가 모두 같은 canonical source를 읽도록 한다.

### 문제

- preview와 applied prompt가 서로 다른 모델을 읽을 수 있다.
- copy가 local template를 재생성하면 화면과 복사본이 달라진다.
- 어떤 텍스트가 최종본인지 사용자가 알기 어렵다.

### 수정 허용 파일

- `ui/app.js`
- `ui/index.html`
- `tests/test_ui_nim_integration.py`

### 불변 계약

- canonical plan은 단 하나다.
- render는 read-only projection이다.
- copy는 visible canonical text를 그대로 복사한다.
- local draft와 applied plan이 혼동되지 않는다.

### 단계별 구현

1. canonical plan store를 단일화한다.
2. Applied Prompt와 Scene Preview를 같은 source에서 렌더링한다.
3. copy action을 projection 기반으로 바꾼다.
4. export를 같은 source로 연결한다.
5. mismatch 가능성을 제거한다.

### API / 데이터 예시

```json
{
  "canonical_source": "applied_plan",
  "projections": ["applied_prompt", "scene_preview", "copy_current_stage", "copy_all"]
}
```

### 실패 규칙

- preview가 applied prompt와 다른 내용을 보여 주면 실패다.
- copy가 화면에 보이지 않는 텍스트를 내면 실패다.
- export가 local template를 따로 재구성하면 실패다.

### acceptance criteria

- 화면과 copy와 export가 같은 문장을 사용한다.
- canonical source를 바꾸면 모든 projection이 함께 바뀐다.
- stale plan은 copy 불가로 처리된다.

### 구체 테스트

- projection equality test
- copy vs preview diff test
- stale copy block test
- export consistency test

### 선행 의존성

- WP-3 and WP-4

### 완료 보고 형식

```text
WP-5 complete
- canonical source: ...
- projections: ...
- copy/export parity: ...
```

### 복사 가능한 위임 프롬프트

```text
WP-5를 맡아 주세요. 목표는 Applied Prompt, Scene Preview, Copy의 단일 canonical source화입니다.
사실: preview와 copy가 서로 다른 텍스트를 만들면 사용자가 혼란을 겪습니다.
불변 계약: one canonical plan, read-only projections, copy equals visible canonical text.
허용 파일: prompt renderer, preview renderer, copy handler, export handler.
해야 할 일: source 단일화, projection 정렬, stale plan copy block, export parity.
실패 규칙: preview/copy mismatch, invisible text copy, local template regeneration.
완료 보고: canonical source, projections, copy/export parity를 적어 주세요.
```

---

## 13) WP-6 desktop/mobile QA

### 목표

desktop과 mobile에서 layout, readability, copy UX, preview visibility, loading/error state를 검증한다.

### 문제

- 좁은 화면에서 카드, 배지, copy action이 겹칠 수 있다.
- 긴 prompt에서 스크롤, select, highlight가 무너질 수 있다.
- mobile에서 상태가 축약되며 의미를 잃을 수 있다.

### 수정 허용 파일

- `ui/styles.css`
- `ui/index.html`
- `tests/test_ui_profile_selection.py`
- `tests/test_ui_vehicle_scene_boundaries.py`

### 불변 계약

- desktop과 mobile에서 canonical meaning은 같다.
- read-only surface는 read-only로 보여야 한다.
- copy action은 손쉬워야 하지만 canonical source를 바꾸지 않는다.

### 단계별 구현

1. 주요 breakpoint를 정의한다.
2. mobile에서 card stacking을 점검한다.
3. long prompt scrolling을 확인한다.
4. copy affordance와 status badge를 점검한다.
5. loading / stale / error visual state를 점검한다.

### API / 데이터 예시

```text
breakpoints: 375px, 768px, 1280px
states: loading, ready, stale, error, copied
```

### 실패 규칙

- mobile에서 copy 버튼이 숨으면 실패다.
- long prompt가 잘려서 읽히지 않으면 실패다.
- status badge가 의미를 잃으면 실패다.

### acceptance criteria

- desktop과 mobile 모두에서 주요 action이 가능하다.
- read-only / preview / copy 구분이 유지된다.
- long prompt가 스크롤 가능하다.

### 구체 테스트

- viewport screenshot comparison
- mobile interaction test
- keyboard navigation test
- text selection test

### 선행 의존성

- WP-5

### 완료 보고 형식

```text
WP-6 complete
- breakpoints: ...
- responsive checks: ...
- residual issues: ...
```

### 복사 가능한 위임 프롬프트

```text
WP-6을 맡아 주세요. 목표는 desktop/mobile QA입니다.
사실: 좁은 화면에서 copy, badge, preview가 깨질 수 있습니다.
불변 계약: desktop/mobile에서 canonical meaning은 같아야 합니다.
허용 파일: UI layout, responsive styles, QA helpers, screenshot harness.
해야 할 일: breakpoint 정의, stacking, scrolling, copy affordance, visual state checks.
실패 규칙: copy 버튼 숨김, long prompt 잘림, status 의미 손실.
완료 보고: breakpoints, responsive checks, residual issues를 적어 주세요.
```

---

## 14) WP-7 실행·운영 문서

### 목표

다른 모델과 운영자가 바로 작업할 수 있도록 실행 문서, 운영 문서, 로컬 명령어, failure handling을 정리한다.

### 문제

- 구현이 문서에 남지 않으면 다음 세션에서 같은 문제를 반복한다.
- 운영 명령과 secret placeholder가 섞이면 안전하지 않다.
- 실패 시 rollback과 rerun 기준이 없으면 release가 불안정하다.

### 수정 허용 파일

- `README.md`
- `docs/pipeline.md`
- `docs/google-flow-checklist.md`
- `docs/render-checklist.md`

### 불변 계약

- secret placeholder만 문서에 적는다.
- 실제 key, token, header는 문서에 적지 않는다.
- 실행 순서와 rollback 순서가 분리되어야 한다.

### 단계별 구현

1. local run 절차를 정리한다.
2. proxy boot sequence를 정리한다.
3. QA / smoke test 절차를 정리한다.
4. failure recovery를 정리한다.
5. release checklist를 정리한다.

### API / 데이터 예시

```text
NIM_API_KEY=***REDACTED***
NIM_BASE_URL=http://localhost:xxxx
SESSION_TOKEN=***REDACTED***
```

### 실패 규칙

- secret 실값이 문서에 들어가면 실패다.
- 실행 순서가 불명확하면 실패다.
- rollback 기준이 없으면 실패다.

### acceptance criteria

- 새 모델이 문서만 읽고도 로컬 실행 경로를 이해한다.
- 운영자가 secret 없이 절차를 실행할 수 있다.
- rollback과 retry 기준이 있다.

### 구체 테스트

- doc walkthrough test
- placeholder audit
- command copy check
- rollback scenario review

### 선행 의존성

- WP-0 through WP-6의 결정 사항

### 완료 보고 형식

```text
WP-7 complete
- docs updated: ...
- commands: ...
- rollback notes: ...
```

### 복사 가능한 위임 프롬프트

```text
WP-7을 맡아 주세요. 목표는 실행·운영 문서 정리입니다.
사실: 다음 모델이 바로 따라올 수 있어야 합니다.
불변 계약: secret placeholder only, execution order, rollback order, no real keys.
허용 파일: README, run guide, ops guide, deploy checklist.
해야 할 일: local run, proxy boot, QA/smoke, failure recovery, release checklist 작성.
실패 규칙: real secret 노출, 실행 순서 불명확, rollback 기준 부재.
완료 보고: docs updated, commands, rollback notes를 적어 주세요.
```

---

## 15) WP-8 최종 release gate

### 목표

모든 WP를 검증하고, 회귀 금지 항목이 지켜졌음을 확인한 뒤 release 여부를 판단한다.

### 문제

- 개별 WP가 성공해도 통합 시 깨질 수 있다.
- release gate가 없으면 stale plan이 배포될 수 있다.
- final check가 없으면 secret, proxy, normalization, QA가 느슨하게 남을 수 있다.

### 수정 허용 파일

- `tests/`
- `docs/`
- defect가 확인된 경우에만 product code

### 불변 계약

- final gate는 한 번의 체크리스트로 끝나지 않고 증거를 요구한다.
- release는 regression matrix를 통과해야 한다.
- `Scene 1` / `Scene 2+` / `negative once-last` / `hands-only`는 최종에도 유지된다.

### 단계별 구현

1. WP-0~WP-7 완료 여부를 확인한다.
2. regression matrix를 실행한다.
3. secret exposure audit를 실행한다.
4. preview/copy/export parity를 확인한다.
5. desktop/mobile QA를 확인한다.
6. rollback point를 명시한 뒤 release 판단을 내린다.

### API / 데이터 예시

```json
{
  "release_candidate": true,
  "wp_status": {
    "WP-0": "done",
    "WP-1": "done",
    "WP-2": "done",
    "WP-3": "done",
    "WP-4": "done",
    "WP-5": "done",
    "WP-6": "done",
    "WP-7": "done"
  }
}
```

### 실패 규칙

- 하나라도 미완료 WP가 있으면 gate 실패다.
- regression 금지 항목이 흔들리면 실패다.
- secret exposure가 남으면 실패다.

### acceptance criteria

- 모든 WP가 완료 보고를 남겼다.
- regression matrix가 통과했다.
- release gate가 명시적으로 승인되었다.

### 구체 테스트

- end-to-end smoke check
- regression matrix check
- secret audit
- parity audit
- mobile QA signoff

### 선행 의존성

- WP-0 through WP-7 전부

### 완료 보고 형식

```text
WP-8 complete
- gate result: pass/fail
- evidence: ...
- rollback point: ...
```

### 복사 가능한 위임 프롬프트

```text
WP-8을 맡아 주세요. 목표는 최종 release gate입니다.
사실: 모든 WP가 끝나도 통합 검증이 남습니다.
불변 계약: regression matrix, secret audit, preview/copy/export parity, desktop/mobile QA가 필요합니다.
허용 파일: release checklist, verification notes, release metadata.
해야 할 일: WP 완료 확인, matrix 실행, secret audit, parity audit, QA signoff, rollback point 명시.
실패 규칙: 미완료 WP 존재, regression 위반, secret exposure.
완료 보고: gate result, evidence, rollback point를 적어 주세요.
```

---

## 16) repo 명령어

아래 명령어는 실제 구현 전에 확인용으로 사용한다. 비밀값은 반드시 placeholder만 쓴다.

```text
pytest:        python3 -m pytest tests/profiles tests/test_basic.py tests/test_ui_profile_selection.py tests/test_ui_vehicle_scene_boundaries.py -q
node check:    node --check ui/app.js
diff check:    git diff --check
local server:   python3 -m http.server 4173 --bind 127.0.0.1
proxy server:   NIM_API_KEY=<REDACTED> python3 src/nim_proxy_server.py --host 127.0.0.1 --port 4174
health:        /health
rewrite:       /api/nim/rewrite
```

예시 secret placeholder:

```text
NIM_API_KEY=***REDACTED***
NIM_BASE_URL=http://localhost:XXXX
SESSION_TOKEN=***REDACTED***
```

실제 pipeline 예시:

```text
python3 src/run_full_pipeline.py "car:Porsche 911" --duration 60 --format 9:16 --base-dir output
```

신규 설계 제안으로만 남기는 항목:

```text
/api/nim/bootstrap
/api/nim/relay
```

## 17) 통합 체크리스트

다음이 모두 `yes`여야 한다.

- `TODO.md`만 수정했는가
- root 목적 / 현재 상태 / 완료된 profile 계약이 있는가
- 사실/추정/미확인 분리가 있는가
- P0~P3 backlog가 있는가
- WP-0~WP-8이 모두 있는가
- 각 WP에 목표/문제/허용 파일/불변 계약/단계/예시/실패 규칙/acceptance/tests/dependencies/report가 있는가
- 회귀 금지 목록이 있는가
- 메인 에이전트 / GPT-5.4-mini 역할이 있는가
- 병렬 가능 매트릭스가 있는가
- 통합 체크포인트와 rollback 원칙이 있는가
- copy 가능한 위임 프롬프트가 각 WP에 있는가
- repo 명령어와 secret placeholder가 있는가
- Definition of Done이 있는가

## 18) Definition of Done

다음 조건을 모두 만족하면 이 TODO는 다음 모델에게 넘겨도 된다.

1. 보안상 브라우저 secret 저장을 더 이상 전제로 하지 않는다.
2. NIM relay가 proxy를 통해 분리된다.
3. UI adapter가 stale / retry / abort / timeout을 다룬다.
4. post-normalization이 scene contract를 복구한다.
5. browser-Python source revision parity가 맞는다.
6. Applied Prompt / Scene Preview / Copy가 같은 canonical source를 읽는다.
7. desktop/mobile QA가 끝난다.
8. 실행·운영 문서가 준비된다.
9. release gate가 명시적이고 재현 가능하다.

## 19) 최종 요약

현재 기준으로 완료된 것은 profile contract, scene boundary 방향성, Scene 1 master 분리, copy/preview 정합성의 기반, architecture subtype 정합성이다.

다음 우선순위는 `WP-0` 비밀 제거와 키 회전, `WP-1` NIM loopback proxy, `WP-2` request adapter, `WP-3` post-normalization, `WP-4` parity, `WP-5` canonical source, `WP-6` QA, `WP-7` 문서, `WP-8` release gate다.

이 문서는 다른 모델에게 그대로 넘겨 구현을 위임하는 용도이므로, 다음 세션에서는 이 문서의 WP 순서대로 진행하면 된다.
