# Korean Architecture Miniature Timelapse — Reference Prompt

> **용도**: 한국 전통/현대 건축물 미니어처 건설 타임랩스용 프롬프트 생성 가이드
> **출력**: 영문 텍스트 프롬프트만 (이미지 생성 X)

---

## 워크플로우 (4단계, 각 단계 사용자 승인 후 진행)

### 1단계: 바이럴 영상 주제 제안 (Topic Generation)
시청자 호기심 극대화 미니어처 건설 주제 5가지 제안  
형식: `[제목 / 호기심 유발 요인 / 1줄 요약]` — 키워드: Miniature, DIY, Construction, Timelapse, Building 필수 포함

> "이 중 어떤 주제로 영상을 기획할까요?" → **STOP**

---

### 2단계: 영상 길이 선택 (Select Video Duration)

| 옵션 | 길이 | 씬 수 | 구성 |
|------|------|-------|------|
| 1 | 30초 | 3 Scene | 2개 공정을 1개 씬으로 압축 |
| 2 | 60초 | 6 Scene | 상세한 전체 공정 |

> "원하시는 영상 길이를 선택해 주세요: 1. 30초 / 2. 60초" → **STOP**

---

### 3단계: 마스터 이미지 프롬프트 (First Frame Image Prompt)
**필수 포함 묘사**:
```
Ultra realistic macro photography, miniature construction site, sand or soil surface, giant human fingers interacting with miniature materials, tiny realistic construction tools, partially prepared foundation area, 8K detail, cinematic studio lighting, shallow depth of field.
```

> 작성 완료 후 다음 단계 진행 여부 확인 → **STOP**

---

### 4단계: 연속 동영상 프롬프트 (Continuous Motion Prompts)
**글로벌 규칙 (모든 비디오 프롬프트 필수 포함)**:
- `ultra fast timelapse speed`
- `human hands continuously constructing and moving rapidly`
- `multiple rapid scene cuts`
- `cinematic macro photography`
- **미니어처 사람 금지, 오직 '거대한 손'만 등장**

**네거티브 프롬프트 (맨 마지막 필수 추가)**:
```
Negative Prompt: "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry."
```

---

#### 조건 A: 60초 선택 시 (6개 Scene × 10초)

| Scene | 단계 | 핵심 묘사 |
|-------|------|-----------|
| 1 | Foundation | 땅 측량, 미니어처 시멘트 바르기, 기초 벽돌 놓기 |
| 2 | Wall & Windows | 벽체 및 창문/문 틀 공사 |
| 3 | Roofing | 지붕 뼈대 조립 및 기와/패널 설치 |
| 4 | Exterior | 외벽 마감, 문/창문 설치, 디테일 장식 |
| 5 | Painting | 프라이머, 페인트칠, 웨더링(풍화) 효과 |
| 6 | Landscaping & Reveal | 잔디, 흙, 울타리 등 조경 완성 → 손 빠지고 **normal cinematic speed**로 완성된 건축물 시네마틱 줌 아웃 |

**연속성 규칙**: 각 Scene의 마지막 프레임 = 다음 Scene의 시작 프레임

---

#### 조건 B: 30초 선택 시 (3개 Scene × 10초, 2단계씩 압축)

| Scene | 압축 내용 |
|-------|-----------|
| 1 | Foundation & Walls: 기초부터 벽체/창문 틀까지 한 번에 |
| 2 | Roofing & Exterior: 지붕 뼈대/패널 → 외벽 마감/디테일까지 |
| 3 | Painting & Landscaping Reveal: 페인트 → 조경 → 손 빠짐 → 완성품 줌 아웃 |

---

## 현재 프로젝트 파이프라인과의 매핑

| 이 레퍼런스 | 현재 프로젝트 (`prompt_templates.py`) |
|-------------|----------------------------------------|
| 6단계/3단계 고정 | `sceneNamesFor('hanok', 60)` → 6개 씬 정의됨 |
| 첫 프레임 별도 | `build_first_frame_prompt('hanok', 'Scene 1')` 구현됨 |
| 연속성 규칙 | `continuityRule()`, `carryOverText()` 함수로 구현 |
| Hands-only | `HANDS_ONLY_RULE` 상수로 강제 적용 |
| 네거티브 프롬프트 | `NEGATIVE_PROMPT` 상수 + 각 씬마다 포함 |
| Building type 템플릿 | `build_first_frame_prompt()` 내 `hanok`, `modern_house`, `cafe` 등 10종 정의 |

> **코드 위치**: `src/prompt_templates.py` — `sceneNamesFor()`, `firstFramePrompt()`, `videoPrompt()`, `continuityRule()` 함수들

---

## 프롬프트 변수
| 변수 | 값 예시 |
|------|---------|
| `topic` | "Korean hanok" |
| `topic_label` | "Architecture-Hanok-warm wood, hanji paper, clay tiles" |
| `building_type` | "hanok" |
| `duration` | 30 / 60 |
| `format` | "9:16" / "16:9" |