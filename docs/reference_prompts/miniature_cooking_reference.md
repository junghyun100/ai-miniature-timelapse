# Miniature Cooking (10s × 3 cuts = 30s) — Reference Prompt

> **용도**: 미니어처 요리 30초 숏폼(10초 × 3씬)용 영문 비디오 프롬프트 생성 가이드
> **출력**: 영문 텍스트 프롬프트만 (이미지 생성 X)

---

## 유일한 변수
```
영상으로 만들고 싶은 음식 이름: [요리 이름]
```
→ 그 외 모든 요소(도구, 열원, 조리 과정, 그릇 등)는 **선택된 요리에 맞춰 자동 적절히 조정**

---

## 중요 규칙 (엄격 적용)

| 규칙 | 상세 |
|------|------|
| **미니어처 사람 금지** | 미니어처 요리사/작은 사람 절대 포함 안 함 |
| **손만 등장** | 화면상 유일한 인간 형태 = **거대한 실제 사람의 손(1~2개)** — 미니어처 조리도구 자연스럽게 다룸 |
| **사물은 모두 미니어처** | 손을 제외한 도구, 재료, 그릇, 열원 모두 완벽한 미니어처 |
| **3씬 완벽 연속성** | 주방, 조명, 조리도구, 나무 도마, 스토브, 카메라 스타일 **30초 내내 동일** |
| **물리적 사실성** | 논리적 요리 단계 절대 건너뛰지 않음, 음식 반응(지글거림, 갈변, 김) 사실적 묘사 |

---

## 시각 스타일 & 카메라 (고정)
- **Ultra-realistic, 8K HDR, Macro cinematography**
- **100mm 매크로 렌즈**, 극단적 클로즈업, 부드러운 포커스 이동
- 초현실적 음식 질감 및 김(Steam) 묘사
- **화면 흔들림(Shaky camera) 절대 금지**

---

## 오디오 (필수)
- **만족스러운 ASMR 사운드만**: 도마 써는 소리, 지글지글 굽는 소리, 보글보글 끓는 소리 등
- **목소리(Voices) / 음악(Music) 절대 금지**

---

## 환경 & 열원 (고정, 요리에 맞춰 적절 조정)
- 부드럽게 흐려진 배경의 **깔끔한 모던 주방**
- **자연스러운 나무 도마 위** 수제 미니어처 요리 스테이션
- 요리에 맞는 **미니어처 조리 도구**(구리 냄비, 점토 냄비, 무쇠 팬 등)
- 요리에 맞는 **미니어처 열원**(티라이트 캔들, 미니 장작불 등)

---

## 출력 형식: 3개 씬 (각각 하나의 상세한 영문 문단)

### SCENE 1 — PREPARATION (0–10 Seconds)
> **[요리 이름]에 맞는 완벽한 재료 준비 과정**(씻기, 껍질 벗기기, 썰기, 반죽하기 등) 묘사.  
> → 모든 재료가 준비된 상태로 끝남.  
> → 다음 씬과 완벽 연결(도마 위 상태, 손 위치, 조명 유지).

### SCENE 2 — COOKING (10–20 Seconds)
> Scene 1에서 **매끄럽게 이어지며**, 조리도구·환경 **완벽하게 동일 유지**.  
> → 끓이기/튀기기/굽기 등 **실제 요리 과정**을 사실적 반응(지글거림, 갈변, 김 모락모락)과 함께 묘사.  
> → 요리 논리적 단계 순서대로 진행(절대 건너뛰기 금지).

### SCENE 3 — FINISHING & PLATING (20–30 Seconds)
> Scene 2에서 **매끄럽게 이어짐**.  
> → 미니어처 도구로 **서빙, 가니쉬 추가**(치즈, 허브, 후추, 참기름 등).  
> → 요리에 맞는 **미니 그릇에 담기**.  
> → **자연스럽게 피어오르는 김과 질감 강조되는 초근접 시네마틱 히어로 샷**으로 마무리.

---

## 네거티브 프롬프트 (각 씬 맨 마지막 필수 추가)
```
Negative Prompt: "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, tiny chef, small person, shaky camera, camera shake, music, voice, narration, dialogue, talking."
```

---

## 현재 프로젝트 파이프라인과의 매핑

| 이 레퍼런스 | 현재 프로젝트 (`prompt_templates.py`) |
|-------------|----------------------------------------|
| 3씬 고정(준비/조리/마무리) | 현재 파이프라인에는 없음 — **새 타입 `cooking` 추가 필요** |
| 10초 × 3 = 30초 | `duration=30` + `sceneNamesFor('cooking', 30)` → 3씬 정의 필요 |
| 연속성(주방/도구/조명 고정) | `CONTINUITY_RULE` / `COMMON_CONTINUITY_LOCK` 상수로 구현 가능 |
| Hands-only + 미니어처 도구 | `HANDS_ONLY_RULE` 적용 + `videoPrompt()` 내 요리 전용 묘사 추가 |
| ASMR 오디오 only | 현재 파이프라인에 오디오 지시 없음 — 프롬프트 내 명시 필요 |
| 100mm 매크로 / 8K HDR | `videoPrompt()` 내 렌즈/화질 명시 추가 필요 |
| 네거티브 프롬프트 확장 | `NEGATIVE_PROMPT`에 `miniature people, tiny chef, shaky camera, music, voice` 추가 권장 |

> **구현 가이드**: `prompt_templates.py`에 `cooking` 타입 추가 시:
> - `sceneNamesFor('cooking', 30)` → `["Preparation", "Cooking", "Finishing & Plating"]`
> - `firstFramePrompt()` → 나무 도마 위 생재료 배치, 손 시작 모습
> - `videoPrompt()` → 위 3씬 프롬프트 템플릿화, `topic` 변수로 요리명 주입

---

## 프롬프트 템플릿 변수

| 변수 | 설명 | 예시 (김치찌개) |
|------|------|----------------|
| `dish_name` | 요리명 (사용자 입력) | "Kimchi Jjigae" |
| `ingredients` | 주요 재료 | "kimchi, pork, tofu, green onion, gochujang" |
| `cookware` | 조리 도구 | "miniature earthenware pot (ttukbaegi)" |
| `heat_source` | 열원 | "tea light candle under pot" |
| `garnish` | 가니쉬 | "sesame oil drizzle, sliced green onion" |
| `serveware` | 담을 그릇 | "miniature black stone bowl" |

---

## 영문 프롬프트 스켈레톤 (각 씬 출력 시 이 구조 따름)

### SCENE 1 — PREPARATION
```
Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, soft focus pulls. Giant human hands only, no miniature people, preparing ingredients for [dish_name] on a natural wooden cutting board in a clean modern kitchen with softly blurred background. Washing [ingredients], peeling, precise knife cuts, dicing, mincing — every motion fluid and ASMR-rich (knife chopping sounds, water drips). All ingredients neatly arranged in miniature prep bowls, ready for cooking. Identical kitchen, lighting, cutting board, and hand position carry into next scene. No voices, no music, only satisfying ASMR sounds. Negative Prompt: text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, tiny chef, small person, shaky camera, camera shake, music, voice, narration, dialogue, talking.
```

### SCENE 2 — COOKING
```
Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, seamless continuation from previous scene. Giant human hands only, same kitchen, same wooden cutting board, same lighting, same camera. Hands transfer prepped ingredients into [cookware] over [heat_source]. Realistic cooking physics: oil shimmer, vigorous bubbling steam, browning Maillard reaction, reduction of broth, ingredients melding — all captured in hypnotic extreme close-up with authentic ASMR (sizzle, boil, simmer). Logical cooking sequence without skipped steps. Identical environment carries into next scene. No voices, no music, only satisfying ASMR sounds. Negative Prompt: text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, tiny chef, small person, shaky camera, camera shake, music, voice, narration, dialogue, talking.
```

### SCENE 3 — FINISHING & PLATING
```
Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, seamless continuation. Giant human hands only, same kitchen, same cookware, same lighting. Hands ladle finished [dish_name] into [serveware] using miniature utensils. Delicate garnish: [garnish]. Final cinematic hero shot: steam rising naturally, textures hyper-detailed (tofu pores, kimchi fibers, oil sheen), focus pull to hero angle. Hands gently exit frame. Satisfying ASMR (pour, drizzle, gentle clink). No voices, no music, only ASMR. Negative Prompt: text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, tiny chef, small person, shaky camera, camera shake, music, voice, narration, dialogue, talking.
```

---

## 사용 예시 (사용자 입력: "김치찌개")

| 씬 | 핵심 묘사 |
|------|-----------|
| **Preparation** | 김치 썰기, 돼지고기 깍둑썰기, 두부 자르기, 대파 송송 — 나무 도마 위 정렬 |
| **Cooking** | 뚝배기에 참기름 두르고 김치 볶기 → 고기 넣고 볶기 → 물 붓고 끓이기 → 두부/대파 넣고 보글보글 |
| **Finishing** | 검은 돌그릇에 국물 떠담기 → 참기름 한 바퀴, 대파 올리기 → 김 모락모락 히어로 샷 |