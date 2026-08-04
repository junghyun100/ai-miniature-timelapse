from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "ui" / "index.html"


def test_ui_nim_proxy_contract_is_wired_into_index_html():
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="nimSessionToken"' in html
    assert 'id="nimApiKey"' in html
    assert html.index("nvidia/nemotron-3-super-120b-a12b") < html.index(
        "nvidia/nemotron-3-ultra-550b-a55b"
    )
    assert "Proxy Session Token" in html
    assert 'placeholder="Proxy session token (세션 전용, 브라우저 미저장)"' in html
    assert "const NIM_PROXY_REWRITE_URL = 'http://127.0.0.1:4174/api/nim/rewrite';" in html
    assert "const NIM_PROXY_TRANSLATE_URL = 'http://127.0.0.1:4174/api/nim/translate';" in html
    assert "const NIM_PROXY_SESSION_URL = 'http://127.0.0.1:4174/session';" in html
    assert "await refreshProxySessionToken({ silent: true });" in html
    assert "proxyApiKeyConfigured = body?.api_key_configured === true;" in html
    assert "한글 추가 지시를 번역하려면 NVIDIA NIM API 키를 입력하세요." in html
    assert "translateKoreanInstructionWithNim" in html
    assert "applyTranslatedInstruction" in html
    assert "source: 'nim_translation'" in html
    assert "if (response.status === 401)" in html
    assert "'X-Session-Token': token" in html
    assert "schema_version: '2.0'" in html
    assert "source_revision: projectData.source_revision" in html
    assert "mutable_fields: [" in html
    assert "'scenes.*.first_frame_prompt'" in html
    assert "'scenes.*.video_prompt'" in html
    assert "project.provenance = {" in html
    assert "source: 'nim'" in html
    assert "source: 'local'" in html
    assert "flowPackEl.value = serializeFullPlan(project);" in html


def test_ui_nim_proxy_contract_keeps_optional_api_key_session_only():
    html = INDEX_HTML.read_text(encoding="utf-8")

    forbidden = [
        "Authorization",
        "https://integrate.api.nvidia.com/v1",
        "miniature_timelapse_nim_base_url",
    ]
    for token in forbidden:
        assert token not in html
    assert "headers['X-NIM-API-Key'] = sessionApiKey" in html
    assert "nimApiKeyEl.value = '';" in html


def test_ui_nim_proxy_stale_guard_and_scene_update_rules_exist():
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "responseBody.source_revision !== requestPayload.source_revision" in html
    assert "project.source_revision !== requestPayload.source_revision" in html
    assert "responseBody.scenes.length !== projectData.scenes.length" in html
    assert (
        "responseBody.scenes.map((scene, index) => [projectData.scenes[index].id, scene])" in html
    )
    assert "const rewrittenFirstFrame = index === 0" in html
    assert "appendMasterOverride(rewrittenFirstFrame, nimAppliedOverrides)" in html
    assert "const rewrittenVideo = ensureIdentityLock(" in html
    assert "rewritten.video_prompt || scene.video_prompt" in html
    assert "projectData.identity_lock" in html
    assert "video_prompt: appendSceneControlBlock(rewrittenVideo" in html
    assert "NIM response missing scene(s):" in html
    assert "NVIDIA NIM 영문 적용본" in html
    assert "NIM 실패, 로컬 플랜으로 계속합니다" in html


def test_ui_restores_identity_and_scale_contracts_after_nim_rewrite():
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "function normalizeUserOverrides(instructions)" in html
    assert (
        "planned completed footprint or full assembly occupies approximately ${coverage}%" in html
    )
    assert (
        "the subject may grow only through the listed physical construction or assembly actions"
        in html
    )
    assert "function ensureIdentityLock(prompt, identityLock)" in html
    assert "MASTER COMPOSITION CONTRACT:" in html
    assert "USER OVERRIDE LOCK (HIGH PRIORITY):" in html
    assert "TEMPORAL DELTA LOCK:" in html
    assert "Never morph, redesign, replace, remove, reset, or rebuild" in html
    assert "`${control} PROMPT BODY: ${body}" in html
    assert (
        "User physical scale, planned footprint, component-count, and composition overrides" in html
    )
    assert "Translate user_overrides.additional_instructions into concise natural English" in html
    assert "function extractProxySessionToken(value)" in html
    assert "근정전 becomes Geunjeongjeon Hall" in html
    assert "Korean additional instructions require a successful NIM translation" in html
    assert "delete nimAppliedOverrides.additional_instructions" in html
    assert "appendMasterOverride(rewrittenFirstFrame, nimAppliedOverrides)" in html
    assert "appendSceneControlBlock(rewrittenVideo, scene, nimAppliedOverrides" in html
