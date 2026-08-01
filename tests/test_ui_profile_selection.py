"""Common browser profile-selection contract tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "ui" / "app.js"
INDEX_HTML = ROOT / "ui" / "index.html"
VEHICLE_JSON = ROOT / "ui" / "data" / "vehicle.json"


def _load_ui_contract() -> dict:
    script = r"""
(async () => {
  const fs = require('fs');
  const source = fs.readFileSync(process.argv[1], 'utf8').replace(/^export\s+/gm, '');
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => JSON.parse(process.env.VEHICLE_DATA),
  });
  const api = new Function(`${source}
    return {
      DEFAULT_PROFILES,
      PROFILE_SELECTION_CONFIG,
      getDefaultSelectionValues,
      deriveTopicLabel,
      getLegacySelectionFields,
      getCanonicalSelection,
      validateSelectionValues,
      countNarrationCharacters,
      resolveProjectWorkflowMode,
      serializeMasterImage,
      serializeSceneBlock,
      serializeSceneVideoPrompt,
      serializeFullPlan,
      getSceneInputLabel
    };
  `)();
  const profiles = { ...api.DEFAULT_PROFILES };
  profiles['vehicle.assembly'] = await profiles['vehicle.assembly']('airplane', 'P-51 Mustang');
  profiles['architecture.korean'] = profiles['architecture.korean'].resolve_selection({
    subtype: 'Temple',
    topic: 'Mountain Buddhist sanctuary',
  });
  profiles['home_decor.diy'] = profiles['home_decor.diy'].resolve_selection({
    idea_name: 'Hanji bottle lantern',
    materials: 'hanji paper, discarded glass bottle, silk thread',
    final_object: 'Korean lotus bottle lantern',
    korean_narration: '버린 병에 한지를 겹쳐 붙이면 연꽃 등불로 다시 피어나요',
  });
  profiles['cooking.miniature'] = profiles['cooking.miniature'].resolve_selection({
    dish_key: 'jjajangmyeon',
  });
  profiles['product.assembly'] = profiles['product.assembly'].resolve_selection({
    subtype: 'Camera',
    subject: 'Leica M3 rangefinder',
  });
  const summary = {};
  for (const [id, profile] of Object.entries(profiles)) {
    const prompts = {};
    for (const duration of profile.allowed_total_durations) {
      prompts[duration] = profile.scene_plans[duration].map(
        scene => profile.scene_prompt_factory
          ? profile.scene_prompt_factory(profile.display_name, '', scene)
          : ''
      );
    }
    summary[id] = {
      durations: profile.allowed_total_durations,
      default_duration: profile.default_total_duration,
      scene_plans: profile.scene_plans,
      workflow_mode: profile.workflow_mode,
      first_frame_prompt: profile.first_frame_prompt_factory
        ? profile.first_frame_prompt_factory(profile.display_name, '')
        : '',
      prompts,
    };
  }
  const sampleScene = {
    id: 1,
    name: 'Sample',
    input_mode: 'MASTER_IMAGE',
    first_frame_prompt: 'Still body. Negative Prompt: still-negative, no-logo.',
    video_prompt: 'Motion body. Negative Prompt: scene-negative, no-text.',
    negative_prompt_base: 'fallback-negative',
    template_exclusions: 'template exclusions',
    asset_ref: {
      logical_id: 'scene_1_final',
      flow_asset_label: 'Scene 1 Final Frame',
    },
  };
  const sampleProject = {
    topic: 'Sample',
    topic_label: 'Product-Camera-Sample',
    profile_id: 'product.assembly',
    profile_version: '2.0.0',
    workflow_mode: 'SINGLE_CLIP_FROM_MASTER',
    duration_seconds: 10,
    scene_count: 1,
    clip_duration_seconds: 10,
    aspect_ratio: '9:16',
    source_revision: 'sha256:sample',
    provenance: { source: 'local' },
    scenes: [sampleScene],
  };
  process.stdout.write(JSON.stringify({
    profiles: summary,
    selection_config: api.PROFILE_SELECTION_CONFIG,
    p51_label: api.deriveTopicLabel('vehicle.assembly', {
      category: 'airplane',
      model: 'P-51 Mustang',
    }),
    architecture_label: api.deriveTopicLabel('architecture.korean', {
      subtype: 'Hanok',
      topic: 'Joseon courtyard house',
    }),
    product_legacy: api.getLegacySelectionFields('product.assembly', {
      subtype: 'Watch',
      subject: 'Skeleton watch',
    }),
    cooking_legacy: api.getLegacySelectionFields('cooking.miniature', {
      dish_key: 'kimchi_jjigae',
    }),
    product_workflows: {
      10: api.resolveProjectWorkflowMode(
        'product.assembly',
        10,
        profiles['product.assembly'].workflow_mode
      ),
      30: api.resolveProjectWorkflowMode(
        'product.assembly',
        30,
        profiles['product.assembly'].workflow_mode
      ),
      60: api.resolveProjectWorkflowMode(
        'product.assembly',
        60,
        profiles['product.assembly'].workflow_mode
      ),
    },
    serialized: {
      master: api.serializeMasterImage(sampleScene).join('\n'),
      scene_block: api.serializeSceneBlock(sampleScene, 1).join('\n'),
      scene_video: api.serializeSceneVideoPrompt(sampleProject, 1),
      full_plan: api.serializeFullPlan(sampleProject),
    },
    timeline_inputs: [
      api.getSceneInputLabel(1, 'MASTER_IMAGE'),
      api.getSceneInputLabel(2, 'PREVIOUS_FINAL_FRAME'),
      api.getSceneInputLabel(6, 'PREVIOUS_FINAL_FRAME'),
    ],
    canonical: {
      architecture: api.getCanonicalSelection('architecture.korean', {
        subtype: 'Modern Hanok',
        topic: 'Glass courtyard house',
      }),
      vehicle: api.getCanonicalSelection('vehicle.assembly', {
        category: 'Airplane',
        model: 'P-51 Mustang',
      }),
      product: api.getCanonicalSelection('product.assembly', {
        subtype: 'Wizard House',
        subject: 'Moonlit apothecary',
      }),
      home: api.getCanonicalSelection('home_decor.diy', {
        idea_name: 'Bottle lamp',
        materials: 'hanji, glass bottle, silk thread',
        final_object: 'lotus lamp',
        korean_narration: '병이 등불로 다시 피어나요',
      }),
      cooking: api.getCanonicalSelection('cooking.miniature', {
        dish_key: 'dakgalbi',
      }),
    },
    home_valid: api.validateSelectionValues('home_decor.diy', {
      idea_name: 'Hanji lamp',
      materials: 'hanji, thread',
      final_object: 'lotus lamp',
      korean_narration: '한지를 접고 붙이면 연꽃 무드등이 완성돼요',
    }),
    home_invalid: api.validateSelectionValues('home_decor.diy', {
      idea_name: 'Hanji lamp',
      materials: 'hanji, thread',
      final_object: 'lotus lamp',
      korean_narration: '가'.repeat(61),
    }),
  }));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""
    env = os.environ.copy()
    env["VEHICLE_DATA"] = VEHICLE_JSON.read_text(encoding="utf-8")
    result = subprocess.run(
        ["node", "-e", script, str(APP_JS)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_all_common_profiles_and_duration_matrix_are_available():
    contract = _load_ui_contract()
    profiles = contract["profiles"]

    assert set(profiles) == {
        "architecture.korean",
        "vehicle.assembly",
        "product.assembly",
        "home_decor.diy",
        "cooking.miniature",
    }
    assert profiles["architecture.korean"]["durations"] == [30, 60]
    assert profiles["architecture.korean"]["default_duration"] == 30
    assert profiles["vehicle.assembly"]["durations"] == [30, 60]
    assert profiles["vehicle.assembly"]["default_duration"] == 30
    assert profiles["product.assembly"]["durations"] == [10, 30, 60]
    assert profiles["home_decor.diy"]["durations"] == [10]
    assert profiles["cooking.miniature"]["durations"] == [30]
    for profile in profiles.values():
        assert {int(duration) for duration in profile["scene_plans"]} == set(profile["durations"])


def test_profile_selection_schema_covers_each_required_input():
    config = _load_ui_contract()["selection_config"]

    field_keys = {
        profile_id: {field["key"] for field in profile["fields"]}
        for profile_id, profile in config.items()
    }
    assert field_keys["architecture.korean"] == {"subtype", "topic"}
    assert field_keys["vehicle.assembly"] == {"category", "model"}
    assert field_keys["product.assembly"] == {"subtype", "subject"}
    assert field_keys["home_decor.diy"] == {
        "idea_name",
        "materials",
        "final_object",
        "korean_narration",
    }
    assert field_keys["cooking.miniature"] == {"dish_key"}
    architecture_options = next(
        field["options"]
        for field in config["architecture.korean"]["fields"]
        if field["key"] == "subtype"
    )
    assert set(architecture_options) == {
        "Hanok",
        "Palace",
        "Temple",
        "Seowon",
        "Modern Hanok",
        "Dolmen",
        "Villa",
        "Store",
        "School",
        "Hotel",
        "Apartment",
        "Factory",
        "Barn",
    }
    cooking_options = next(
        field["options"]
        for field in config["cooking.miniature"]["fields"]
        if field["key"] == "dish_key"
    )
    assert {option["value"] for option in cooking_options} == {
        "kimchi_jjigae",
        "bibimbap",
        "bulgogi",
        "jjajangmyeon",
        "samgyeopsal",
        "dakgalbi",
    }


def test_topic_labels_and_home_decor_validation_follow_contract():
    contract = _load_ui_contract()

    assert contract["p51_label"] == "Vehicle-Airplane-P-51 Mustang"
    assert contract["architecture_label"] == "Architecture-Hanok-Joseon courtyard house"
    assert contract["product_legacy"] == {
        "topic": "Skeleton watch",
        "subtype": "Watch",
        "subject": "Skeleton watch",
    }
    assert contract["cooking_legacy"] == {
        "topic": "Kimchi Jjigae",
        "subtype": "Miniature",
        "dish_key": "kimchi_jjigae",
        "dish_name": "Kimchi Jjigae",
    }
    assert contract["home_valid"]["valid"] is True
    assert contract["home_invalid"]["valid"] is False
    assert "60 characters" in contract["home_invalid"]["errors"][0]


def test_scene_one_alone_uses_master_image_input():
    profiles = _load_ui_contract()["profiles"]

    for profile in profiles.values():
        for duration in profile["durations"]:
            scenes = profile["scene_plans"][str(duration)]
            assert scenes[0]["input_mode"] == "MASTER_IMAGE"
            assert all(scene["input_mode"] == "PREVIOUS_FINAL_FRAME" for scene in scenes[1:])

    source = INDEX_HTML.read_text(encoding="utf-8")
    assert "const firstFramePrompt = isFirst" in source
    assert "? profile.first_frame_prompt_factory(topic, promptDetail)" in source
    assert ": '';" in source
    assert (
        "input_mode: index === 0 ? InputMode.MASTER_IMAGE : InputMode.PREVIOUS_FINAL_FRAME"
        in source
    )


def test_architecture_factory_is_subtype_specific_and_scene_bounded():
    architecture = _load_ui_contract()["profiles"]["architecture.korean"]

    assert architecture["workflow_mode"] == "REFERENCE_FRAME_RELAY"
    assert "Temple" in architecture["first_frame_prompt"]
    assert "gray clay roof tiles" in architecture["first_frame_prompt"]
    assert "Buddhist main hall" in architecture["first_frame_prompt"]

    for duration in architecture["durations"]:
        scenes = architecture["scene_plans"][str(duration)]
        prompts = architecture["prompts"][str(duration)]
        for index, scene in enumerate(scenes):
            if index:
                assert scene["start_state"] == scenes[index - 1]["exact_stop_state"]
            for field in [
                "completion_range",
                "is_final_scene",
                "exact_stop_state",
                "reserved_future_actions",
                "forbidden_future_actions",
            ]:
                assert field in scene
            assert "Architecture subtype: Temple" in prompts[index]
            assert "gray clay roof tiles" in prompts[index]
            assert prompts[index].count("Negative Prompt:") == 1
            assert prompts[index].rstrip().endswith("human figures.")


def test_cooking_factory_enforces_three_exact_stages_and_negative_prompt():
    cooking = _load_ui_contract()["profiles"]["cooking.miniature"]
    scenes = cooking["scene_plans"]["30"]
    prompts = cooking["prompts"]["30"]

    assert [scene["name"] for scene in scenes] == [
        "Preparation",
        "Cooking",
        "Finishing and Plating",
    ]
    assert scenes[1]["start_state"] == scenes[0]["exact_stop_state"]
    assert scenes[2]["start_state"] == scenes[1]["exact_stop_state"]
    assert "raw" in scenes[0]["start_state"].lower()
    assert "ready for cooking" in scenes[0]["exact_stop_state"].lower()
    assert "fully cooked" in scenes[1]["exact_stop_state"].lower()
    assert "serving component" in scenes[1]["exact_stop_state"].lower()
    assert "plated" in scenes[2]["exact_stop_state"].lower()
    assert "Jjajangmyeon" in cooking["first_frame_prompt"]

    for prompt in prompts[:2]:
        lowered = prompt.lower()
        assert "hero" not in lowered
        assert "final" not in lowered
        assert "plated result" not in lowered
    assert "cinematic hero reveal" in prompts[2]

    for prompt in prompts:
        lowered = prompt.lower()
        for required in [
            "jjajangmyeon",
            "giant human hands only",
            "no voices, no music",
            "tiny chef",
            "shaky camera",
            "camera shake",
            "music",
            "voice",
        ]:
            assert required in lowered
        assert prompt.count("Negative Prompt:") == 1
        assert prompt.rstrip().endswith("talking.")


def test_home_decor_factory_preserves_reference_sequence_and_audio():
    home = _load_ui_contract()["profiles"]["home_decor.diy"]
    prompt = home["prompts"]["10"][0]

    for required in [
        "Opening Hook",
        "Introducing Materials",
        "Building Begins",
        "Mid-Build Sequence",
        "Detail Showcase",
        "Final Reveal",
        "hanji paper, discarded glass bottle, silk thread",
        "Korean lotus bottle lantern",
        "버린 병에 한지를 겹쳐 붙이면 연꽃 등불로 다시 피어나요",
        "tactile mixed-media papercraft and craft ASMR style, specifically featuring 3D layered paper-cutting, origami folding, and organic material collage captured from a clean, top-down perspective.",
        "hands only",
        "No background music",
    ]:
        assert required in prompt
    assert prompt.count("Negative Prompt:") == 1
    assert prompt.rstrip().endswith("human figures.")


def test_product_workflow_mode_depends_on_selected_duration():
    contract = _load_ui_contract()

    assert contract["profiles"]["product.assembly"]["workflow_mode"] == "SINGLE_CLIP_FROM_MASTER"
    assert contract["product_workflows"] == {
        "10": "SINGLE_CLIP_FROM_MASTER",
        "30": "REFERENCE_FRAME_RELAY",
        "60": "REFERENCE_FRAME_RELAY",
    }
    source = INDEX_HTML.read_text(encoding="utf-8")
    build_block = source.split("async function buildRelayPlan()", 1)[1].split(
        "// Get scene plans for duration", 1
    )[0]
    assert "typeof profile.resolve_selection === 'function'" in build_block
    assert "profile = profile.resolve_selection(selectionValues)" in build_block
    assert "resolveProjectWorkflowMode(currentProfileId, duration, profile.workflow_mode)" in source


def test_product_profile_uses_subtype_materials_parts_stages_and_ranges():
    product = _load_ui_contract()["profiles"]["product.assembly"]

    assert "Leica M3 rangefinder" in product["first_frame_prompt"]
    assert "Vintage Camera" in product["first_frame_prompt"]
    assert "metal body" in product["first_frame_prompt"]
    assert "lens barrel" in product["first_frame_prompt"]
    assert [scene["completion_range"] for scene in product["scene_plans"]["10"]] == ["0-100%"]
    assert [scene["completion_range"] for scene in product["scene_plans"]["30"]] == [
        "0-30%",
        "30-75%",
        "75-100%",
    ]
    assert [scene["completion_range"] for scene in product["scene_plans"]["60"]] == [
        "0-15%",
        "15-35%",
        "35-55%",
        "55-75%",
        "75-90%",
        "90-100%",
    ]
    assert "Lock the shutter box and body shell" in product["prompts"]["30"][0]
    assert "Install the lens barrel and glass elements" in product["prompts"]["30"][0]
    assert "Fit the film chamber" in product["prompts"]["30"][1]
    assert "Leica M3 rangefinder" in product["prompts"]["30"][1]


def test_serializers_dedupe_negative_and_keep_it_as_last_line():
    serialized = _load_ui_contract()["serialized"]

    for key in ["master", "scene_block", "scene_video"]:
        block = serialized[key]
        assert block.count("Negative Prompt:") == 1
        lines = block.splitlines()
        assert lines[-1].startswith("Negative Prompt:")
        assert lines[-2] == "Template Exclusions: template exclusions"

    assert serialized["master"].endswith("Negative Prompt: still-negative, no-logo.")
    assert serialized["scene_block"].endswith("Negative Prompt: scene-negative, no-text.")
    assert serialized["scene_video"].endswith("Negative Prompt: scene-negative, no-text.")
    assert "Negative Prompt:" not in serialized["scene_block"].split("Template Exclusions:", 1)[0]
    assert "Input: Master Image" in serialized["scene_block"]
    assert "Output: scene_1_final" in serialized["scene_block"]
    master_block, scene_block = serialized["full_plan"].split("SCENE 1", 1)
    assert master_block.count("Negative Prompt:") == 1
    assert scene_block.count("Negative Prompt:") == 1
    assert scene_block.rstrip().endswith("Negative Prompt: scene-negative, no-text.")


def test_timeline_input_label_uses_previous_scene_not_output_asset():
    contract = _load_ui_contract()

    assert contract["timeline_inputs"] == [
        "Master Image",
        "Scene 1 Final Frame",
        "Scene 5 Final Frame",
    ]
    source = INDEX_HTML.read_text(encoding="utf-8")
    timeline_block = source.split("// Scene Timeline", 1)[1].split("// Full plan output", 1)[0]
    assert "입력: ${getSceneInputLabel(i + 1, scene.input_mode)}" in timeline_block
    assert "출력: ${scene.asset_ref?.flow_asset_label || 'pending'}" in timeline_block
    assert "입력: ${scene.asset_ref?.flow_asset_label" not in timeline_block


def test_canonical_selection_is_backend_compatible_and_revisioned():
    contract = _load_ui_contract()

    assert contract["canonical"] == {
        "architecture": {
            "subtype": "modern_hanok",
            "topic": "Glass courtyard house",
        },
        "vehicle": {
            "vehicle_category": "airplane",
            "model_name": "P-51 Mustang",
        },
        "product": {
            "subtype": "wizard_house",
            "subject": "Moonlit apothecary",
        },
        "home": {
            "idea_name": "Bottle lamp",
            "materials": ["hanji", "glass bottle", "silk thread"],
            "final_object": "lotus lamp",
            "korean_narration": "병이 등불로 다시 피어나요",
        },
        "cooking": {"dish_key": "dakgalbi"},
    }
    source = INDEX_HTML.read_text(encoding="utf-8")
    assert "const canonicalSelection = getCanonicalSelection" in source
    assert "derived_fields: { selection: canonicalSelection }" in source
    assert "derived_fields: project.derived_fields" in source
    revision_keys = (
        APP_JS.read_text(encoding="utf-8")
        .split("const INCLUDED_SOURCE_REVISION_KEYS", 1)[1]
        .split("]);", 1)[0]
    )
    assert '"derived_fields"' in revision_keys


def test_non_final_prompts_never_expose_completion_language():
    profiles = _load_ui_contract()["profiles"]
    banned = [
        "final reveal",
        "hero",
        "fully assembled",
        "clean workbench",
        "plated result",
        "normal cinematic speed",
        "remove hands",
    ]

    for profile_id in [
        "architecture.korean",
        "cooking.miniature",
        "product.assembly",
    ]:
        profile = profiles[profile_id]
        for duration in profile["durations"]:
            scenes = profile["scene_plans"][str(duration)]
            prompts = profile["prompts"][str(duration)]
            assert len(scenes) == len(prompts)
            for scene, prompt in zip(scenes, prompts, strict=False):
                if scene["is_final_scene"]:
                    continue
                lowered = prompt.lower()
                for phrase in banned:
                    assert phrase not in lowered, (
                        f"{profile_id} {duration}s scene {scene['scene_id']} "
                        f"contains completion phrase: {phrase}"
                    )
                if profile_id == "architecture.korean":
                    assert (
                        "later-stage components and materials remain separate, visible, and untouched"
                        in lowered
                    )
                elif profile_id == "product.assembly":
                    assert "prohibited future work:" in lowered
                else:
                    assert "stop at the exact stop state" in lowered
                    assert (
                        "later-stage components and materials remain separate, visible, and untouched"
                        in lowered
                    )

    architecture_final = profiles["architecture.korean"]["prompts"]["30"][-1].lower()
    cooking_final = profiles["cooking.miniature"]["prompts"]["30"][-1].lower()
    product_final = profiles["product.assembly"]["prompts"]["30"][-1].lower()
    assert "normal cinematic speed" in architecture_final
    assert "hero reveal" in cooking_final
    assert "final reveal" in product_final


def test_selection_and_legacy_fields_are_saved_in_project_and_source_draft():
    source = INDEX_HTML.read_text(encoding="utf-8")
    build_block = source.split("async function buildRelayPlan()", 1)[1].split(
        "// Create initial relay branch", 1
    )[0]

    for token in [
        "selection: { ...selectionValues }",
        "...legacyFields",
        "selection: project.selection",
        "subject: project.subject",
        "category: project.category",
        "model_name: project.model_name",
        "dish_key: project.dish_key",
        "idea_name: project.idea_name",
        "materials: project.materials",
        "final_object: project.final_object",
        "korean_narration: project.korean_narration",
        "project.source_draft = sourceDraft",
    ]:
        assert token in build_block

    app_source = APP_JS.read_text(encoding="utf-8")
    revision_keys = app_source.split("const INCLUDED_SOURCE_REVISION_KEYS", 1)[1].split("]);", 1)[0]
    for key in [
        '"selection"',
        '"subject"',
        '"category"',
        '"model_name"',
        '"dish_key"',
        '"idea_name"',
        '"materials"',
        '"final_object"',
        '"korean_narration"',
    ]:
        assert key in revision_keys


def test_selection_renderer_uses_dom_text_apis_for_user_values():
    source = INDEX_HTML.read_text(encoding="utf-8")

    assert "selectionFields.replaceChildren()" in source
    assert "label.textContent = field.label" in source
    assert "option.textContent = optionLabel" in source
    assert "topicLabelPreview.textContent = deriveTopicLabel" in source
    assert "content.textContent = value" in source


def test_master_image_panel_precedes_video_and_copy_labels_can_wrap():
    html = INDEX_HTML.read_text(encoding="utf-8")
    styles = (ROOT / "ui" / "styles.css").read_text(encoding="utf-8")

    assert html.index('id="masterPromptPanel"') < html.index('id="videoPrompt"')
    assert 'id="copyMasterPanelBtn" data-copy-action="master_image"' in html
    assert 'id="copyVideoPanelBtn" data-copy-action="scene_video"' in html
    assert "copyVideoPanelBtn.disabled = !canCopyVideo" in html
    assert "copyMasterPanelBtn.disabled = !canCopyMaster" in html
    assert "data-copy-action" in html
    assert "copyToClipboard(target.textContent)" not in html
    assert "Master Image Prompt 복사 (정지 이미지용)" in html
    assert "Video Prompt 복사 (Flow 10초 비디오용)" in html
    assert ".copy-btn-label" in styles
    assert "overflow-wrap: anywhere" in styles
