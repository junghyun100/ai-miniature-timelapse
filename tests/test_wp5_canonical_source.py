"""
WP-5 Tests: Single Canonical Source, Read-Only Projections, Stale Plan Copy Block, Export Parity
"""

import json
import subprocess
from pathlib import Path

import pytest

from src.domain import (
    AspectRatio,
    AssetKind,
    AssetRef,
    AssetScope,
    InputMode,
    Project,
    Scene,
    ScenePlan,
    StyleBible,
    WorkflowMode,
)
from src.export_prompts import export_project_json, export_text_bundle
from src.scene_md_export import build_scene_md
from src.serializers import (
    IMMUTABLE_NEGATIVE,
    is_plan_stale,
    perform_copy_action,
    serialize_full_plan,
)

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def canonical_project() -> Project:
    style_bible = StyleBible(
        identity_lock="Identity lock for hanok house",
        materials={"primary": ["wood", "stone"], "secondary": [], "tools": []},
        camera={"lens": "85mm", "angle": "45", "movement": "locked", "distance": "fixed"},
        lighting={"key": "soft daylight", "fill": "ambient", "mood": "warm", "consistency": "locked"},
        color_palette=["warm wood"],
        workspace="compacted earth tray",
        hands_rule="giant human hands only",
        motion_rule="rapid procedural timelapse",
    )

    scene1_asset = AssetRef(
        logical_id="scene_01_master",
        kind=AssetKind.IMAGE,
        scope=AssetScope.SCENE,
        flow_asset_label="Scene 1 master image",
        local_path="scenes/scene_01_master.png",
        source_scene_id=1,
        confirmed_by_user=True,
    )

    scene2_asset = AssetRef(
        logical_id="scene_01_last_frame",
        kind=AssetKind.IMAGE,
        scope=AssetScope.SCENE,
        flow_asset_label="Scene 1 final frame",
        local_path="scenes/scene_01_last_frame.png",
        source_scene_id=1,
        confirmed_by_user=True,
    )

    scenes = [
        Scene(
            id=1,
            name="Foundation and Base",
            input_mode=InputMode.MASTER_IMAGE,
            asset_ref=scene1_asset,
            first_frame_prompt="Master image prompt for hanok foundation",
            video_prompt="Video prompt for hanok foundation building",
            template_exclusions="exclusions s1",
            negative_prompt=IMMUTABLE_NEGATIVE,
            clip_duration_seconds=10,
            lineage_revision="sha256:" + "0" * 64,
        ),
        Scene(
            id=2,
            name="Roofing",
            input_mode=InputMode.PREVIOUS_FINAL_FRAME,
            asset_ref=scene2_asset,
            first_frame_prompt="",
            video_prompt="Video prompt for hanok roofing",
            template_exclusions="exclusions s2",
            negative_prompt=IMMUTABLE_NEGATIVE,
            clip_duration_seconds=10,
            lineage_revision="sha256:" + "0" * 64,
        ),
    ]

    proj = Project(
        schema_version="2.0",
        topic="hanok",
        topic_label="Architecture-Hanok",
        genre="architecture",
        subtype="hanok",
        profile_id="architecture.korean",
        profile_version="2.0.0",
        workflow_mode=WorkflowMode.REFERENCE_FRAME_RELAY,
        duration_seconds=20,
        clip_duration_seconds=10,
        aspect_ratio=AspectRatio.RATIO_9_16,
        style_bible=style_bible,
        derived_fields={},
        scene_plans=[
            ScenePlan(1, "Foundation and Base", "start", ["a"], "end", InputMode.MASTER_IMAGE),
            ScenePlan(2, "Roofing", "start", ["b"], "end", InputMode.PREVIOUS_FINAL_FRAME),
        ],
        scene_count=2,
        source_revision="",
        flow_execution_profile_id="flow.frames_first.10s",
        scenes=scenes,
    )
    proj.source_revision = proj.compute_source_revision()
    return proj


class TestCanonicalSingleSource:
    def test_copy_all_equals_export_text_bundle(self, canonical_project):
        """Export text bundle MUST match Copy All output (Export Parity)."""
        copy_all_res = perform_copy_action(canonical_project, "all")
        export_text = export_text_bundle(canonical_project)

        assert copy_all_res.text.strip() == export_text.strip()

    def test_copy_master_image_matches_full_plan_master_section(self, canonical_project):
        """Copy master image matches the MASTER IMAGE section in full plan."""
        copy_master = perform_copy_action(canonical_project, "master_image")
        full_plan = serialize_full_plan(canonical_project)

        assert copy_master.text in full_plan

    def test_copy_scene_video_matches_scene_block(self, canonical_project):
        """Copy scene video matches the SCENE block in full plan."""
        copy_s2 = perform_copy_action(canonical_project, "scene_video", scene_id=2)
        full_plan = serialize_full_plan(canonical_project)

        assert copy_s2.text in full_plan

    def test_scene_md_export_uses_canonical_scene_prompts(self, canonical_project):
        """scene_md_export uses canonical prompts on scene without regenerating templates."""
        proj_dict = canonical_project.to_dict()
        md_text = build_scene_md(proj_dict, proj_dict["scenes"][0])

        assert canonical_project.scenes[0].first_frame_prompt in md_text
        assert canonical_project.scenes[0].video_prompt in md_text


class TestStalePlanCopyBlock:
    def test_is_plan_stale_detection(self, canonical_project):
        """Detect stale plan when draft mismatch or is_stale set."""
        assert not is_plan_stale(canonical_project)

        canonical_project.is_stale = True
        assert is_plan_stale(canonical_project)

    def test_perform_copy_action_blocks_stale_plan(self, canonical_project):
        """perform_copy_action raises ValueError if plan is stale."""
        canonical_project.is_stale = True

        with pytest.raises(ValueError, match="Copy blocked: Plan is stale"):
            perform_copy_action(canonical_project, "all")

        with pytest.raises(ValueError, match="Copy blocked: Plan is stale"):
            perform_copy_action(canonical_project, "master_image")

    def test_perform_copy_action_blocks_draft_mismatch(self, canonical_project):
        """perform_copy_action raises ValueError if current draft hash mismatches plan."""
        draft_modified = canonical_project.to_dict()
        draft_modified["topic"] = "modified topic"

        with pytest.raises(ValueError, match="Copy blocked: Plan is stale"):
            perform_copy_action(canonical_project, "all", current_draft=draft_modified)

    def test_export_handlers_block_stale_plan(self, canonical_project):
        """export_text_bundle and export_project_json block stale plans."""
        canonical_project.is_stale = True

        with pytest.raises(ValueError, match="Export failed: plan is stale"):
            export_text_bundle(canonical_project)

        with pytest.raises(ValueError, match="Export failed: plan is stale"):
            export_project_json(canonical_project)

        proj_dict = canonical_project.to_dict()
        proj_dict["is_stale"] = True
        with pytest.raises(ValueError, match="Export failed: plan is stale"):
            build_scene_md(proj_dict, proj_dict["scenes"][0])


class TestJsPythonParity:
    def test_js_perform_copy_action_parity(self, canonical_project):
        """Execute Node script to verify JS performCopyAction matches Python."""
        project_dict = canonical_project.to_dict()
        project_json = json.dumps(project_dict, ensure_ascii=False)

        js_script = f"""
        import {{ performCopyAction, serializeFullPlan }} from './ui/app.js';
        const project = {project_json};
        console.log(JSON.stringify({{
            all: performCopyAction(project, 'all').text,
            master: performCopyAction(project, 'master_image').text,
            scene2: performCopyAction(project, 'scene_video', 2).text
        }}));
        """

        result = subprocess.run(
            ["node", "--input-type=module", "-e", js_script],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )

        js_output = json.loads(result.stdout.strip())
        py_all = perform_copy_action(canonical_project, "all").text
        py_master = perform_copy_action(canonical_project, "master_image").text
        py_scene2 = perform_copy_action(canonical_project, "scene_video", scene_id=2).text

        assert js_output["all"] == py_all
        assert js_output["master"] == py_master
        assert js_output["scene2"] == py_scene2
