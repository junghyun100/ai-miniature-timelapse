"""Vehicle scene boundary tests for the browser UI generator."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "ui" / "app.js"
INDEX_HTML = ROOT / "ui" / "index.html"
VEHICLE_JSON = ROOT / "ui" / "data" / "vehicle.json"


def _load_vehicle_data() -> dict:
    return json.loads(VEHICLE_JSON.read_text(encoding="utf-8"))


def _load_vehicle_profile(category: str = "airplane", model_name: str = "Spitfire Mk IX") -> dict:
    script = r"""
(async () => {
  const fs = require('fs');
  const source = fs.readFileSync(process.argv[1], 'utf8').replace(/^export\s+/gm, '');
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => JSON.parse(process.env.VEHICLE_DATA),
  });
  const api = new Function(`${source}\nreturn { DEFAULT_PROFILES };`)();
  const profileFactory = api.DEFAULT_PROFILES['vehicle.assembly'];
  const profile = await profileFactory(process.env.VEHICLE_CATEGORY, process.env.VEHICLE_MODEL);
  const scenes30 = profile.scene_plans[30];
  const scenes60 = profile.scene_plans[60];
  const prompts = {
    scene_30_1: profile.scene_prompt_factory('airplane', '', scenes30[0], 1),
    scene_30_2: profile.scene_prompt_factory('airplane', '', scenes30[1], 2),
    scene_30_3: profile.scene_prompt_factory('airplane', '', scenes30[2], 3),
    scene_60_1: profile.scene_prompt_factory('airplane', '', scenes60[0], 1),
    scene_60_6: profile.scene_prompt_factory('airplane', '', scenes60[5], 6),
  };
  process.stdout.write(JSON.stringify({
    scene_plans: profile.scene_plans,
    prompts,
  }));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""
    env = os.environ.copy()
    env["VEHICLE_DATA"] = VEHICLE_JSON.read_text(encoding="utf-8")
    env["VEHICLE_CATEGORY"] = category
    env["VEHICLE_MODEL"] = model_name
    result = subprocess.run(
        ["node", "-e", script, str(APP_JS)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_vehicle_json_airplane_steps_are_logical():
    """Airplane assembly order should move from structure to finish."""
    data = _load_vehicle_data()
    airplane_steps = data["assemblySteps"]["airplane"]

    assert airplane_steps == [
        "Airframe and fuselage skeleton assembled",
        "Engine and cockpit mount secured",
        "Wings and tail attached",
        "Landing gear and control linkages installed",
        "Exterior panels, canopy, and propeller fitted",
        "Final polish revealing complete aircraft on clean workbench",
    ]


def test_vehicle_scene_contract_fields_are_present_in_source():
    """The browser generator should declare the new scene boundary fields."""
    source = APP_JS.read_text(encoding="utf-8")
    helper_block = source.split("function buildVehicleSceneTemplate(", 1)[1].split("export const DEFAULT_PROFILES", 1)[0]
    factory_block = source.split("scene_prompt_factory:", 1)[1].split("},", 1)[0]
    source_draft = INDEX_HTML.read_text(encoding="utf-8")
    source_draft_block = source_draft.split("scene_plans: scenePlans.map(sp => ({", 1)[1].split("narration:", 1)[0]

    for token in [
        "completion_range",
        "is_final_scene",
        "exact_stop_state",
        "reserved_future_actions",
        "forbidden_future_actions",
    ]:
        assert token in helper_block

    for legacy_phrase in [
        "100% disassembled parts to fully assembled model",
        "workspace is completely clean, leaving only the fully assembled model",
        "By the final step, the workspace is completely clean, leaving only the fully assembled model",
    ]:
        assert legacy_phrase not in factory_block

    for token in [
        "completion_range",
        "is_final_scene",
        "exact_stop_state",
        "reserved_future_actions",
        "forbidden_future_actions",
    ]:
        assert token in source_draft_block


def test_vehicle_scene_prompts_are_scene_bounded():
    """Non-final scenes should stop early and keep future work untouched."""
    profile = _load_vehicle_profile()

    scenes_30 = profile["scene_plans"]["30"]
    scenes_60 = profile["scene_plans"]["60"]

    assert [scene["completion_range"] for scene in scenes_30] == ["0-30%", "30-75%", "75-100%"]
    assert [scene["completion_range"] for scene in scenes_60] == [
        "0-15%",
        "15-35%",
        "35-55%",
        "55-75%",
        "75-90%",
        "90-100%",
    ]

    assert scenes_30[0]["is_final_scene"] is False
    assert scenes_30[1]["is_final_scene"] is False
    assert scenes_30[2]["is_final_scene"] is True
    assert scenes_30[0]["reserved_future_actions"]
    assert scenes_30[2]["reserved_future_actions"] == []
    assert scenes_30[1]["start_state"] == scenes_30[0]["exact_stop_state"]
    assert scenes_30[2]["start_state"] == scenes_30[1]["exact_stop_state"]
    assert scenes_60[1]["start_state"] == scenes_60[0]["exact_stop_state"]
    assert scenes_60[5]["start_state"] == scenes_60[4]["exact_stop_state"]

    non_final_banned = [
        "fully assembled model",
        "workspace is completely clean",
        "final polish",
        "final reveal",
    ]

    prompt_1 = profile["prompts"]["scene_30_1"]
    prompt_2 = profile["prompts"]["scene_30_2"]
    prompt_3 = profile["prompts"]["scene_30_3"]

    for prompt in (prompt_1, prompt_2):
        lowered = prompt.lower()
        for banned in non_final_banned:
            assert banned not in lowered
        for required in [
            "Exact input/start state:",
            "This clip covers only",
            "Exact stop state:",
            "Reserved future actions and parts, kept for a later finishing stage:",
            "The model must remain visibly incomplete",
            "Do not proceed beyond this stop state",
            "Maintain the same camera angle, scale, lighting direction, and workbench layout throughout",
            "hands only",
            "No floating or teleporting parts",
        ]:
            assert required.lower() in lowered
        assert prompt.count("Negative Prompt:") == 1
        assert prompt.rstrip().endswith("blurry.")

    assert prompt_1.count("Stop immediately when") == 1
    assert prompt_2.count("Stop immediately when") == 1
    assert "Stop immediately when Stop immediately when" not in prompt_1
    assert "Stop immediately when Stop immediately when" not in prompt_2

    final_lower = prompt_3.lower()
    assert "fully assembled model" in final_lower
    assert "clean workbench" in final_lower
    assert "final reveal" in final_lower
    assert "exact stop state:" in final_lower
    assert prompt_3.count("Negative Prompt:") == 1
    assert prompt_3.rstrip().endswith("blurry.")

    prompt_60_1 = profile["prompts"]["scene_60_1"]
    prompt_60_6 = profile["prompts"]["scene_60_6"]

    for banned in non_final_banned:
        assert banned not in prompt_60_1.lower()
    assert "Exact stop state:" in prompt_60_1
    assert "Reserved future actions and parts, kept for a later finishing stage:" in prompt_60_1
    assert "The model must remain visibly incomplete" in prompt_60_1
    assert "fully assembled model" in prompt_60_6.lower()
    assert "clean workbench" in prompt_60_6.lower()
    assert prompt_60_1.count("Negative Prompt:") == 1
    assert prompt_60_6.count("Negative Prompt:") == 1
