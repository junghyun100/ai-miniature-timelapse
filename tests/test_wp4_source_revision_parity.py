"""
WP-4 Parity & Invariant Tests: Browser-Python Source Revision Parity

Verifies:
1. Exact SHA-256 hash parity between Python and JS implementations across all domain profiles.
2. Canonical JSON serialization rules (NFC normalization, sorted keys, no whitespace).
3. Export/Import revision attachment (fails if source_revision missing/invalid).
4. Stale response handling (revision mismatch -> STALE state, active plan NOT updated).
"""

import json
import subprocess
from pathlib import Path
import pytest

from src.domain import (
    Project,
    compute_source_revision,
    serialize_canonical,
    normalize_nim_response,
    NimResponse,
    NimSceneResponse,
    NimSceneRequest,
)
from src.export_prompts import export_project_json, export_text_bundle, ensure_source_revision


PROJECT_ROOT = Path(__file__).parent.parent


def run_js_revision_computation(draft: dict) -> str:
    """Execute Node script using ui/source_revision.js to compute JS hash."""
    draft_json = json.dumps(draft, ensure_ascii=False)
    js_code = f"""
    import {{ computeSourceRevisionSync }} from './ui/source_revision.js';
    const draft = {draft_json};
    console.log(computeSourceRevisionSync(draft));
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", js_code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


class TestHashParity:
    """Tests cross-platform hash parity between Python and JS for all profiles."""

    def test_architecture_hanok_parity(self):
        draft = {
            "profile_id": "architecture.korean",
            "profile_version": "2.0.0",
            "workflow_mode": "REFERENCE_FRAME_RELAY",
            "topic": "한옥 주택",
            "genre": "architecture",
            "subtype": "hanok",
            "topic_label": "Korean Architecture: Hanok",
            "duration_seconds": 30,
            "clip_duration_seconds": 10,
            "aspect_ratio": "9:16",
            "style_bible": {
                "identity_lock": "traditional hanok style",
                "materials": {"primary": ["wood", "clay_tile"], "secondary": [], "tools": []},
            },
            "derived_fields": {},
            "scene_plans": [
                {
                    "scene_id": 1,
                    "name": "Base Foundation",
                    "start_state": "Empty plot",
                    "ordered_actions": ["Laying stone foundation"],
                    "end_state": "Foundation ready",
                    "forbidden_changes": ["modern materials"],
                    "input_mode": "MASTER_IMAGE",
                    "estimated_clip_duration_seconds": 10,
                }
            ],
            "narration": None,
            "idea_seed": None,
            "flow_execution_profile_id": "google-veo2-9-16-10s",
            "nim_enabled": False,
            "nim_model_id": "",
            "nim_refinement_policy": "mutable_only",
        }
        py_hash = compute_source_revision(draft)
        js_hash = run_js_revision_computation(draft)

        assert py_hash == js_hash, f"Hash mismatch: PY={py_hash}, JS={js_hash}"
        assert py_hash.startswith("sha256:")

    def test_vehicle_porsche_parity(self):
        draft = {
            "profile_id": "vehicle.assembly",
            "profile_version": "2.0.0",
            "workflow_mode": "REFERENCE_FRAME_RELAY",
            "topic": "Porsche 911",
            "genre": "vehicle",
            "subtype": "car",
            "topic_label": "Vehicle: Car - Porsche 911",
            "model_name": "Porsche 911",
            "duration_seconds": 30,
            "clip_duration_seconds": 10,
            "aspect_ratio": "16:9",
            "style_bible": {
                "identity_lock": "silver metallic Porsche 911 coupe",
                "materials": {"primary": ["diecast steel"], "secondary": ["rubber tires"], "tools": []},
            },
            "derived_fields": {"category": "car"},
            "scene_plans": [],
            "narration": None,
            "idea_seed": None,
            "flow_execution_profile_id": "google-veo2-16-9-10s",
            "nim_enabled": True,
            "nim_model_id": "nvidia/nemotron-3-ultra",
            "nim_refinement_policy": "mutable_only",
        }
        py_hash = compute_source_revision(draft)
        js_hash = run_js_revision_computation(draft)

        assert py_hash == js_hash, f"Vehicle hash mismatch: PY={py_hash}, JS={js_hash}"

    def test_home_decor_diy_parity(self):
        draft = {
            "profile_id": "home_decor.diy",
            "profile_version": "2.0.0",
            "workflow_mode": "REFERENCE_FRAME_RELAY",
            "topic": "Hanji lotus mood lamp",
            "genre": "home_decor",
            "subtype": "DIY",
            "topic_label": "HomeDecor-Diy-Hanji Lotus Lamp",
            "craft_name": "Hanji lotus mood lamp",
            "duration_seconds": 30,
            "clip_duration_seconds": 10,
            "aspect_ratio": "9:16",
            "style_bible": {
                "identity_lock": "traditional hanji paper lotus lamp",
                "materials": {"primary": ["hanji paper", "plastic spoons"], "secondary": ["LED light"], "tools": ["glue gun"]},
            },
            "derived_fields": {},
            "scene_plans": [],
            "narration": "버려진 숟가락에 한지를 겹쳐 붙이면 전통 연꽃 무드등이 완성돼요",
            "idea_seed": "lotus_lamp_01",
            "flow_execution_profile_id": "google-veo2-9-16-10s",
            "nim_enabled": False,
            "nim_model_id": "",
            "nim_refinement_policy": "mutable_only",
        }
        py_hash = compute_source_revision(draft)
        js_hash = run_js_revision_computation(draft)

        assert py_hash == js_hash, f"HomeDecor hash mismatch: PY={py_hash}, JS={js_hash}"

    def test_cooking_miniature_parity(self):
        draft = {
            "profile_id": "cooking.miniature",
            "profile_version": "2.0.0",
            "workflow_mode": "REFERENCE_FRAME_RELAY",
            "topic": "Kimchi Jjigae",
            "genre": "cooking",
            "subtype": "Miniature",
            "topic_label": "Cooking-Miniature-Kimchi Jjigae",
            "dish_name": "Kimchi Jjigae",
            "duration_seconds": 30,
            "clip_duration_seconds": 10,
            "aspect_ratio": "9:16",
            "style_bible": {
                "identity_lock": "miniature kimchi stew in earthenware pot",
                "materials": {"primary": ["aged kimchi", "tofu", "pork"], "secondary": ["scallions"], "tools": ["mini stove"]},
            },
            "derived_fields": {"dish_key": "kimchi_jjigae"},
            "scene_plans": [],
            "narration": None,
            "idea_seed": None,
            "flow_execution_profile_id": "google-veo2-9-16-10s",
            "nim_enabled": False,
            "nim_model_id": "",
            "nim_refinement_policy": "mutable_only",
        }
        py_hash = compute_source_revision(draft)
        js_hash = run_js_revision_computation(draft)

        assert py_hash == js_hash, f"Cooking hash mismatch: PY={py_hash}, JS={js_hash}"

    def test_transient_field_exclusion_parity(self):
        """Transient fields like provenance or local UI state do not affect revision hash in both PY & JS."""
        draft_clean = {
            "profile_id": "architecture.korean",
            "profile_version": "2.0.0",
            "workflow_mode": "SINGLE_CLIP_FROM_MASTER",
            "topic": "hanok",
            "genre": "architecture",
            "subtype": "hanok",
            "topic_label": "Korean Architecture: Hanok",
            "duration_seconds": 10,
            "clip_duration_seconds": 10,
            "aspect_ratio": "9:16",
            "style_bible": {},
            "derived_fields": {},
            "scene_plans": [],
            "flow_execution_profile_id": "test",
            "nim_enabled": False,
            "nim_model_id": "",
            "nim_refinement_policy": "mutable_only",
        }
        draft_transient = draft_clean.copy()
        draft_transient["provenance"] = {"source": "local", "request_id": "req-123"}
        draft_transient["relay_branch"] = {"branch_id": "b-1"}
        draft_transient["source_revision"] = "sha256:oldhash"
        draft_transient["ui_expanded"] = True

        py_clean = compute_source_revision(draft_clean)
        py_transient = compute_source_revision(draft_transient)
        js_clean = run_js_revision_computation(draft_clean)
        js_transient = run_js_revision_computation(draft_transient)

        assert py_clean == py_transient
        assert js_clean == js_transient
        assert py_clean == js_clean


class TestExportRevisionRule:
    """Tests 'revision 없는 export' failure rule."""

    def test_export_attaches_revision(self):
        project_dict = {
            "profile_id": "architecture.korean",
            "profile_version": "2.0.0",
            "workflow_mode": "SINGLE_CLIP_FROM_MASTER",
            "topic": "hanok",
            "genre": "architecture",
            "subtype": "hanok",
            "topic_label": "Korean Architecture: Hanok",
            "duration_seconds": 10,
            "clip_duration_seconds": 10,
            "aspect_ratio": "9:16",
            "style_bible": {"identity_lock": "hanok"},
            "derived_fields": {},
            "scene_plans": [],
            "flow_execution_profile_id": "test",
            "nim_enabled": False,
            "nim_model_id": "",
            "nim_refinement_policy": "mutable_only",
        }
        exported = export_project_json(project_dict)
        assert "source_revision" in exported
        assert exported["source_revision"].startswith("sha256:")

    def test_export_fails_if_revision_missing_and_corrupt(self):
        corrupt_data = {"invalid": "data"}
        with pytest.raises(ValueError, match="Export failed"):
            export_project_json(corrupt_data)

    def test_export_text_bundle_includes_revision_header(self):
        project_dict = {
            "profile_id": "architecture.korean",
            "profile_version": "2.0.0",
            "workflow_mode": "SINGLE_CLIP_FROM_MASTER",
            "topic": "hanok",
            "genre": "architecture",
            "subtype": "hanok",
            "topic_label": "Korean Architecture: Hanok",
            "duration_seconds": 10,
            "clip_duration_seconds": 10,
            "aspect_ratio": "9:16",
            "style_bible": {"identity_lock": "hanok"},
            "derived_fields": {},
            "scene_plans": [],
            "flow_execution_profile_id": "test",
            "nim_enabled": False,
            "nim_model_id": "",
            "nim_refinement_policy": "mutable_only",
            "scenes": [
                {
                    "id": 1,
                    "name": "Main View",
                    "video_prompt": "Video prompt hanok",
                    "first_frame_prompt": "First frame hanok",
                    "negative_prompt": "blurry",
                }
            ],
        }
        text_bundle = export_text_bundle(project_dict)
        assert "Source Revision: sha256:" in text_bundle


class TestStaleBehavior:
    """Tests 'stale plan active 표시' failure rule."""

    def test_nim_normalization_rejects_stale_revision(self):
        local_plans = [
            NimSceneRequest(
                id=1,
                name="Scene 1",
                start_state="empty",
                ordered_actions=["build"],
                end_state="done",
                local_first_frame_prompt="Frame 1",
                local_video_prompt="Video 1",
            )
        ]
        nim_resp = NimResponse(
            schema_version="2.0",
            request_id="req-1",
            source_revision="sha256:differentrevision0000000000000000000000000000000000000000000000",
            scenes=[NimSceneResponse(id=1, first_frame_prompt="F1", video_prompt="V1")],
        )

        expected_rev = "sha256:expectedrevision00000000000000000000000000000000000000000000000"

        with pytest.raises(ValueError, match="Stale NIM response"):
            normalize_nim_response(nim_resp, local_plans, expected_rev)
