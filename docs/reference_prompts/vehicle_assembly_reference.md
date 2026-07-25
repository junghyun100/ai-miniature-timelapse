# Vehicle Assembly Miniature Timelapse — Reference Prompt

> **용도**: 자동차/오토바이/비행기/보트/농기계/헬리콥터/건설중장비/우주선/군용탱크/자전거 등 차량 조립 미니어처 타임랩스용 프롬프트 생성 가이드
> **출력**: 영문 텍스트 프롬프트만 (이미지 생성 X)

---

## 워크플로우 (4단계, 각 단계 사용자 승인 후 진행)

### 1단계: 카테고리 선택 (Category Selection)
고정 10개 카테고리 제시 후 선택 대기:
1. 자동차 (Car)
2. 오토바이 (Motorcycle)
3. 비행기 (Airplane)
4. 보트/선박 (Boat)
5. 농기계 (Agricultural Machinery)
6. 헬리콥터 (Helicopter)
7. 건설 중장비 (Construction Vehicle)
8. 우주선 (Spaceship)
9. 군용 탱크 (Tank)
10. 자전거 (Bicycle)

> "이 중 어떤 카테고리로 영상을 기획할까요?" → **STOP**

---

### 2단계: 구체적 모델 아이디어 제안 (Idea Generation)
선택된 카테고리 내 상징적 클래식/인기 현대 모델 10개 제안 (예: 자동차 → '포르쉐 911', '포드 머스탱' 등 구체적 명시)

> "어떤 모델로 조립 영상을 만들까요?" → **STOP**

---

### 3~4단계: 마스터 이미지 + 단일 10초 동영상 프롬프트 동시 생성

#### 출력 형식 1: IMAGE PROMPT (마스터 이미지 프롬프트)
- 100% 분해된 미니어처 모델 부품들이 나무 작업대 위에 가지런히 놓인 **극사실적 매크로 사진** (Hyper-realistic macro photo)
- 섀시(chassis), 바퀴(wheels), 서스펜션, 엔진 블록, 스티어링, 외부 패널 등 **모든 부품이 조립되지 않은 채 개별적으로 명확히 분리** — 완성된 차량 모습 절대 금지
- 핀셋, 미니 드라이버, 부드러운 브러시 등 도구 배치, 85mm 렌즈, 얕은 피사계 심도, 8K 제품 사진 퀄리티, 밝은 작업실 조명

#### 출력 형식 2: VIDEO PROMPT (단일 10초 동영상 프롬프트 — 6단계 압축)
마스터 이미지 구도/조명 완벽 유지하며 미니어처 모델 완성되는 과정 **단 1개 영문 비디오 프롬프트**로 작성.

**6단계 조립 퀵컷 스톱모션 (실제 기계 조립 논리 순서)**:
1. **Engine**: 핀셋으로 엔진 들어 섀시에 정확히 안착
2. **Fasteners**: 미니 드라이버 회전하며 나사 단단히 조임
3. **Wheels & Suspension**: 바퀴와 서스펜션 장착
4. **Steering**: 조향 장치 제자리에 꾹 눌러 결합
5. **Body Panels**: 외부 바디 패널 덮고 매끄럽게 조립
6. **Final Polish**: 부드러운 브러시로 먼지 털어내며 완벽한 모델 조립 마무리

**부품 감소 및 클린업 규칙 (엄격 적용)**:
- 완전히 분해된 부품들로 시작 → 완성된 모델로 끝나야 함
- 부품 조립될수록 작업대 위 흩어져 있던 잉여 부품들 자연스럽게 화면에서 사라짐
- 마지막 6단계: 주변에 **어떠한 부품도 남아있지 않고 오직 '완성된 제품'만** 깔끔한 작업대 위에 남음
  - 영문 필수 포함: *"As parts are attached, they logically disappear from the workbench. By the final step, the workspace is completely clean, leaving only the fully assembled model."*

**필수 규칙**:
- 거대한 사람 손(Hands)이 도구 사용해 부품 조립 — 부품이 이유 없이 공중 부양/순간이동 금지 (No floating, teleporting parts)
- 처음부터 끝까지 카메라 각도와 조명 물리적으로 완벽 고정
- **Negative Prompt 필수 포함** (맨 마지막에 그대로 추가):
```
Negative Prompt: "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry."
```

---

## 현재 프로젝트 파이프라인과의 매핑

| 이 레퍼런스 | 현재 프로젝트 (`prompt_templates.py`) |
|-------------|----------------------------------------|
| IMAGE PROMPT | `firstFramePrompt()` → `car`, `motorcycle`, `airplane`, `boat`, `watch`, `camera`, `sneaker`, `robot`, `dinosaur`, `mecha`, `dragon`, `wizard_house`, `spaceship`, `hoverbike`, `mech` 타입 분기 |
| VIDEO PROMPT 6단계 | `videoPrompt()` → 동일 타입 분기 내 단일 프롬프트 문자열에 6단계 연속 묘사 |
| 부품 감소/클린업 | `videoPrompt()` 내 `"As parts are attached, they logically disappear from the workbench..."` 문구 포함 |
| Hands-only | `HANDS_ONLY_RULE` 상수 (`prompt_templates.py:6-9`) 적용 |
| Negative Prompt | `NEGATIVE_PROMPT` 상수 (`prompt_templates.py:4`) 동일 적용 |
| 카메라 고정 | `CONTINUITY_RULE` / `COMMON_CONTINUITY_LOCK` 상수 적용 |

> **코드 위치**: `src/prompt_templates.py:1200-1213` — `videoPrompt()` 함수 내 `['car','motorcycle','airplane',...]` 분기 블록

---

## 프롬프트 템플릿 변수

| 변수 | 설명 | 예시 |
|------|------|------|
| `model_name` | 2단계 선택된 모델명 | "Porsche 911" |
| `category` | 1단계 선택된 카테고리 | "Car" |
| `duration` | 영상 길이 (이 프롬프트는 10초 고정) | 10 |

---

## 영문 프롬프트 스켈레톤 (출력 시 이 구조 따름)

### IMAGE PROMPT
```
Hyper-realistic macro photo of 100% disassembled miniature [model_name] model parts neatly arranged on a wooden workbench, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, no completed model visible, chassis/body/frame components, wheels/engines/arms/wings/panels/components separated clearly, tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, [model_name], scene: Master Image.
```

### VIDEO PROMPT
```
hyper-realistic macro ASMR assembly timelapse, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, precise mechanical assembly logic, 100% disassembled parts to fully assembled model, no floating or teleporting parts, parts attach in a realistic order and disappear from the workbench as they are installed, final step leaves only the fully assembled model on a clean workbench, tweezers, mini screwdriver, soft brush, 85mm lens, shallow depth of field, 8K product quality, bright workshop lighting, [model_name.toLowerCase()], scene: Assembly. As parts are attached, they logically disappear from the workbench. By the final step, the workspace is completely clean, leaving only the fully assembled model. Negative Prompt: text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry.
```