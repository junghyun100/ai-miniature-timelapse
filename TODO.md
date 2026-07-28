# 안전 종료용 TODO

이 문서는 현재까지의 진행 상황을 안전하게 고정하고, 다음 세션에서 바로 이어서 작업할 수 있도록 정리한 인수 문서입니다.

## 1) 현재 완료된 구현

### 공통 profile selection
- 프로필 선택 흐름이 공통화되었습니다.
- 단일 입력에서 건축, 차량, 제품, 홈 데코, 쿠킹 등 주요 카테고리를 같은 방식으로 선택할 수 있도록 정리되었습니다.
- 선택된 프로필에 따라 이후 프롬프트 구성과 미리보기 생성 흐름이 분기되도록 연결되었습니다.

### architecture / vehicle / product / home decor / cooking scene boundary contract
- 각 도메인별로 scene boundary 계약이 정리되었습니다.
- architecture는 장면 전개가 단계적으로 이어져야 하며, scene 간에 임의 점프가 생기지 않도록 규칙이 정리되었습니다.
- vehicle은 조립 단계가 완성 상태로 바로 끝나는 것이 아니라, 단계별 조립 진행이 드러나도록 경계를 제어하는 방향으로 정리되었습니다.
- product는 완전 분해 상태에서 시작해 조립 순서가 보이도록 하는 계약이 적용되었습니다.
- home decor는 손만 등장하는 제작 흐름, 재료 등장, 공정 전개, 최종 완성의 순서를 유지하도록 계약이 정리되었습니다.
- cooking은 재료 준비, 조리 진행, 마무리의 흐름이 scene 단위로 유지되도록 계약이 정리되었습니다.
- 전체적으로 각 프로필이 서로 다른 영상 장르이지만, 공통적인 파이프라인 규칙은 동일하게 유지되도록 정리되었습니다.

### Scene1-only master image
- 정지 이미지 생성용 Master Image Prompt는 Scene 1 전용으로 고정되었습니다.
- 이후 scene들은 master image를 다시 덮어쓰지 않고, 동영상용 흐름만 따라가도록 분리되었습니다.
- 이 분리로 인해 "첫 이미지"와 "연속 scene"의 역할이 더 명확해졌습니다.

### serializer / copy / preview consistency
- Source Draft, Applied Prompt, Scene Preview, 복사 버튼의 역할이 서로 섞이지 않도록 정리되었습니다.
- 복사되는 텍스트가 어떤 상태의 프롬프트인지 구분할 수 있도록 일관성을 강화했습니다.
- preview는 단순 텍스트 노출이 아니라, 현재 적용된 결과를 보여주는 역할로 분리되었습니다.
- 실패 시 local draft로 돌아가는 흐름도 유지되도록 정리했습니다.

### architecture 13 subtype parity
- architecture 계열은 13개 subtype 기준으로 정합성을 맞추는 방향으로 정리되었습니다.
- subtype별 이름, scene 흐름, 첫 장면 조건, 후속 장면 전개가 서로 어긋나지 않도록 맞추는 작업이 반영되었습니다.
- 향후 subtype 추가나 문구 수정 시에도 같은 기준을 유지하는 것이 전제입니다.

## 2) 검증 결과

### 완료된 검증
- 최종 테스트 결과는 `94 passed` 기준으로 정리되었습니다.
- `node --check` 검증을 통과했습니다.
- `git diff --check` 검증도 통과했습니다.

### 검증 해석
- 문법 수준의 문제와 공백/패치 무결성 문제는 현재 기준으로 정리된 상태입니다.
- 다만 UI에서 보이는 일부 상태 문구는 실제 NIM 적용 결과를 증명하는 것이 아니라, 로컬 draft / 성공 / 실패 상태를 나타내는 표시일 수 있으므로 별도 확인이 필요합니다.

## 3) 남은 작업 우선순위

### P0. 실제 NVIDIA NIM 호출 미연결
- 현재 가장 중요한 미해결 항목입니다.
- UI 상에서 NIM이 성공처럼 보이더라도, 실제 호출이 연결되어 있지 않거나 실패를 local draft로 덮는 경우가 있을 수 있습니다.
- 다음 단계에서는 실제 request/response 흐름을 끝까지 검증해야 합니다.

### P0. 브라우저 API key / localStorage 제거와 키 회전
- 키를 브라우저에 직접 저장하거나 localStorage에 유지하는 방식은 제거하는 것이 우선입니다.
- 키 회전, 안전한 주입 방식, 세션 분리, 노출 방지 정책이 필요합니다.
- UI에서 보이는 입력칸은 편의용일 수 있지만, 실제 저장 방식과 분리되어야 합니다.

### P1. proxy model / session / CORS / schema / post-normalization
- NIM 호출을 직접 브라우저에서 처리하지 말고 proxy 계층으로 분리하는 작업이 필요합니다.
- model 선택, session 관리, CORS, schema validation, post-normalization 단계가 분리되어야 합니다.
- 응답이 씬 헤더를 지우거나 형식을 바꿔도 안정적으로 파싱되도록 보강해야 합니다.

### P1. browser / mobile QA
- 데스크톱과 모바일에서 다음 항목을 다시 검증해야 합니다.
- Source Draft 카드 배치
- Applied Prompt의 읽기 전용 여부
- Scene Preview의 적용 결과 표시
- 복사 버튼과 상태 배지의 가독성
- 긴 프롬프트의 스크롤, 선택, 하이라이트

### P2. 문서 / 배포
- 명세서, README, 실행 가이드, 운영 가이드를 정리해야 합니다.
- 다음 세션에서 다른 모델이 바로 구현할 수 있도록 작업 범위와 역할 분리를 문서화해야 합니다.
- 실제 배포 전에는 연결 상태, 실패 시 fallback, 보안 정책을 다시 확인해야 합니다.

## 4) 메인 에이전트 역할

메인 에이전트는 직접 구현을 무리하게 늘리지 말고, 다음 역할에 집중합니다.

- 전체 범위 정의와 우선순위 결정
- 프로필별 명세 통합
- scene boundary와 first frame 규칙 검증
- 프롬프트 구조의 일관성 검증
- UI 상태와 실제 적용 결과의 불일치 점검
- 서브에이전트 산출물 병합 여부 판단
- 테스트 결과 최종 승인
- 커밋 대상 선별과 푸시 판단

메인 에이전트는 "무엇을 만들지"와 "어디까지를 완료로 볼지"를 책임지고, 코드 변경은 최소한의 조정만 수행하는 쪽이 적합합니다.

## 5) GPT-5.4-mini 서브에이전트 역할

서브에이전트는 파일 범위가 명확한 구현과 테스트에 집중해야 합니다.

### 권장 분할
- `src/profiles/architecture.py` : architecture subtype / scene boundary / first frame 규칙
- `src/profiles/vehicle.py` : vehicle assembly 단계 규칙과 model 분기
- `src/profiles/product.py` : disassembled assembly contract와 copy consistency
- `src/profiles/home_decor.py` : hands-only craft flow와 negative prompt 고정
- `src/profiles/cooking.py` : cooking flow scene boundary와 narrative consistency
- `src/profile_types.py` : 공통 타입/선택지/label 계약
- `ui/app.js` : preview, copy, status, Applied Prompt 분리
- `ui/styles.css` : 카드형 입력, 배지, 스크롤, 가독성
- `tests/*` : scene boundary, selection contract, UI contract, regression

### 서브에이전트 운영 원칙
- 한 번에 여러 도메인을 섞지 말고, 파일 범위를 좁게 유지합니다.
- 구현 후에는 반드시 테스트 또는 정적 검증 결과를 함께 보고합니다.
- 불명확한 부분은 수정하지 말고, 메인 에이전트에게 확인이 필요한 항목으로 분리합니다.

## 6) 다음 세션 시작 명령과 권장 작업 분할

### 권장 시작 명령
```text
현재 TODO.md를 기준으로 P0 항목부터 이어서 작업해 주세요.
1) 실제 NVIDIA NIM 호출 연결 여부를 확인하고,
2) 브라우저 API key / localStorage 저장 방식을 제거하거나 분리하고,
3) proxy model / session / CORS / schema / post-normalization 설계를 반영해 주세요.
구현은 GPT-5.4-mini 서브에이전트로 파일 범위별로 분할하고,
메인 에이전트는 검증과 통합만 맡겨 주세요.
```

### 권장 작업 분할
1. NIM 실제 호출 경로 검증
1. 키 저장 방식 정리
1. proxy / session / schema 보강
1. profile별 scene boundary 재검토
1. UI preview / Applied Prompt / copy 버튼 정합성 확인
1. 브라우저 QA 및 모바일 QA
1. 문서 갱신 및 배포 점검

## 7) 위험 / 주의사항

- 사용자 변경 사항은 보존해야 하며, 불필요한 되돌리기는 금지합니다.
- 비밀 키를 커밋하거나 로그에 남기면 안 됩니다.
- NIM UI에서 보이는 성공 메시지는 실제 적용 증거가 아닐 수 있습니다.
- local draft로 복귀하는 상태가 있더라도, 실제 원격 반영 여부를 별도로 확인해야 합니다.
- scene preview와 applied prompt가 시각적으로 비슷해 보여도, 실제 데이터 소스가 다를 수 있으므로 혼동하지 않아야 합니다.
- 프롬프트 구조를 바꿀 때는 architecture, vehicle, product, home decor, cooking 사이의 공통 계약이 깨지지 않도록 주의해야 합니다.

## 요약

현재까지는 공통 profile selection, 도메인별 scene boundary 계약, Scene1-only master image 분리, serializer/copy/preview 일관성, architecture subtype 정합성까지 정리된 상태입니다.
다음 우선순위는 실제 NVIDIA NIM 연결, 키/세션 보안, proxy 파이프라인, 그리고 브라우저/모바일 QA입니다.
