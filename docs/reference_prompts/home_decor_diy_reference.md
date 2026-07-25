# Home Decor DIY Craft — Reference Prompt

> **용도**: 페이스리스 보이스오버 기반 DIY 홈데코 크래프트 채널용 10초 숏폼 튜토리얼 프롬프트 생성 가이드
> **출력**: 영문 텍스트 프롬프트만 (이미지 생성 X)

---

## 채널 핵심 정체성 (모든 출력물에 엄격 적용)

| 요소 | 상세 |
|------|------|
| **핵심 공식** | 저렴한/버려진 재료 → 간단한 반복 기술 → 세련된 장식품 완성 |
| **훅 법칙** | 첫 2-3초: '사물 + 믿을 수 없는 대사 + 즉각적 작업 컷' |
| **시각 스타일** | 매크로 클로즈업, **손만 등장(Hands only)**, 탑다운/45° 앵글, 고정 카메라, 밝은 스튜디오 조명, 얕은 피사계 심도, 깔끔한 배경, 파스텔/보석 톤, 9:16 세로, 포토리얼리스틱, 촬영 장비 노출 금지 |
| **오디오 스타일** | 배경음악 없음, 밝은 젊은 여성 나레이션 + 크래프트 ASMR 사운드(가위질, 마찰음) |

---

## 워크플로우 (3단계, 1단계 승인 후 2~3단계 연속 출력)

### 1단계: 바이럴 영상 아이디어 제안 (IDEA GENERATION)
- 질문 없이 즉시 **10개 아이디어** 제안
- **한국적 소재 + 랜덤성 필수**: 한지, 자개, 조각보, 명주실, 전통 매듭, 대나무, 버려진 도자기 조각, 윷놀이 스틱, 청사초롱 모티브 등을 일상 폐기물과 창의적 결합
- 형식: `"재료를 활용한 완성품"` (예: `한지와 플라스틱 숟가락으로 만든 전통 연꽃 무드등`) — 1줄만, 부연 설명/표/요약 금지
- 재료 겹치지 않게 다양하게 활용

> "몇 번 아이디어(1-10)의 스크립트와 프롬프트를 작성해 드릴까요?" → **STOP**

---

### 2단계: 한국어 나레이션 대본 (2~3단계 연속 출력)

**제약**:
- **최대 60자 이내 (공백 제외)** — 철저 준수
- 틱톡커 구어체 레이싱: 어미/접속사(`~고`, `~면`, `~니까`, `~죠?`)로 매끄럽게 한 문장처럼 연결
- 구조: Hook(물건+놀라운 대사) → 재료 → 시각적 변환 → 최종 완성 결과

**출력 형식**:
```
[나레이션 텍스트] (공백 제외 XX자)
```

---

### 3단계: 단일 10초 영문 비디오 프롬프트

**핵심 요구사항**:
- 영상을 여러 씬으로 나누지 말고 **단 1개 프롬프트**에 10초 전체 담기
- 다음 6단계 과정이 매끄럽게 연속되도록 묘사:
  1. Opening Hook (시선 집중)
  2. Introducing Materials (한국적 재료 등장)
  3. Building Begins (기초 작업 및 자르기/접기 시작)
  4. Mid-Build Sequence (만족스러운 중간 조립)
  5. Detail Showcase (디테일 추가 및 마감)
  6. Final Reveal (최종 완성품 줌아웃 공개)

**필수 포함 문장 (그대로 복사)**:
```
tactile mixed-media papercraft and craft ASMR style, specifically featuring 3D layered paper-cutting, origami folding, and organic material collage captured from a clean, top-down perspective.
```

**오디오 지시사항 (프롬프트 내 명시)**:
- 2단계 작성한 한국어 대본을 프롬프트 내 참고용으로 그대로 포함
- "시청자를 향해 쉼 없이 말하는 젊은 여성 나레이션 진행, 배경 음악 없음" 명시

**채널 시각 스타일 필수 포함**:
- 매크로 클로즈업, 손만 등장, 고정 카메라(탑다운/45°), 밝은 스튜디오 조명, 얕은 피사계 심도, 파스텔/보석 톤, 9:16 세로, 포토리얼리스틱

---

### 네거티브 프롬프트 (맨 마지막 필수 추가)
```
Negative Prompt: "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry."
```

---

## 현재 프로젝트 파이프라인과의 매핑

| 이 레퍼런스 | 현재 프로젝트 (`prompt_templates.py`) |
|-------------|----------------------------------------|
| 단일 10초 프롬프트 | `videoPrompt()` 내 `home_decor` 타입 분기에서 구현 |
| 6단계 시퀀스 | `videoPrompt()` → `home_decor` 블록의 긴 프롬프트 문자열에 포함 |
| 한국적 소재/재료 | `topicDetail()` → `sub.color` 등으로 매핑 가능 |
| Hands-only | `HANDS_ONLY_RULE` 상수 적용 |
| 탑다운/45° 앵글 | `videoPrompt()` 내 `top-down craft-table view` 문구로 반영 |
| 네거티브 프롬프트 | 동일하게 프롬프트 끝단 추가 |
| 나레이션(한국어) | 현재 파이프라인엔 없음 — 별도 확장 필요 |

> **코드 위치**: `src/prompt_templates.py:1229-1231` — `videoPrompt()` 함수 내 `home_decor` 분기 참고

---

## 프롬프트 템플릿 변수

| 변수 | 설명 | 예시 |
|------|------|------|
| `idea_name` | 1단계 선택된 아이디어명 | "한지와 플라스틱 숟가락으로 만든 전통 연꽃 무드등" |
| `korean_narration` | 2단계 생성된 나레이션 (60자 이내) | "버려진 숟가락이 연꽃이 되다니 손으로 접으니 피어나네요" |
| `materials` | 사용된 재료 리스트 | "한지, 플라스틱 숟가락, 철사, 접착제" |
| `final_object` | 완성품명 | "전통 연꽃 무드등" |

---

## 영문 프롬프트 스켈레톤 (3단계 출력 시 이 구조 따름)

```
[Opening Hook: close-up of discarded materials, Korean female voiceover speaks narration], [Introducing Materials: Korean materials introduced — hanji, plastic spoon, wire], [Building Begins: hands cut hanji, bend spoon, start folding], [Mid-Build Sequence: satisfying origami folding, layering hanji petals, wire stem assembly, tactile ASMR sounds], [Detail Showcase: adding gloss, arranging petals, precise placement], [Final Reveal: zoom out to finished traditional lotus mood lamp on clean desk]. tactile mixed-media papercraft and craft ASMR style, specifically featuring 3D layered paper-cutting, origami folding, and organic material collage captured from a clean, top-down perspective. Macro close-up, hands only, fixed top-down 45-degree angle, steady camera, bright even studio lighting, shallow depth of field, clean background, pastel and jewel-tone palette, 9:16 vertical, photorealistic 8K. Korean female voiceover narrates continuously without pause: "[korean_narration]". No background music. Negative Prompt: text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry.
```

> **참고**: 실제 출력 시 `[korean_narration]` 등 변수는 2단계 결과로 치환