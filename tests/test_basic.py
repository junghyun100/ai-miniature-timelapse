"""Tests for ai-miniature-timelapse pipeline."""

import json
from pathlib import Path


def test_vehicle_json_exists():
    """vehicle.json 파일이 존재하는지 확인."""
    vehicle_json = Path("ui/data/vehicle.json")
    assert vehicle_json.exists(), "vehicle.json should exist"


def test_vehicle_json_structure():
    """vehicle.json이 올바른 구조를 가지는지 확인."""
    vehicle_json = Path("ui/data/vehicle.json")
    data = json.loads(vehicle_json.read_text(encoding="utf-8"))

    # 필수 키 확인
    required_keys = [
        "categories", "models", "identityLocks", "keyParts",
        "assemblySteps", "styleBibles", "negativeBase"
    ]
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"

    # 10개 카테고리 확인
    assert len(data["categories"]) == 10
    expected_categories = ["car", "motorcycle", "airplane", "boat", "agricultural",
                           "helicopter", "construction", "spaceship", "tank", "bicycle"]
    for cat in expected_categories:
        assert cat in data["categories"], f"Missing category: {cat}"

    # 각 카테고리별 모델 10개 확인
    for cat in expected_categories:
        assert cat in data["models"], f"Missing models for {cat}"
        assert len(data["models"][cat]) == 10, f"Category {cat} should have 10 models"


def test_export_script_syntax():
    """export_vehicle_data.py 구문 검사."""
    export_script = Path("scripts/export_vehicle_data.py")
    assert export_script.exists()
    # Just verify it can be imported (syntax check)
    compile(export_script.read_text(encoding="utf-8"), export_script, "exec")


def test_pipeline_scripts_syntax():
    """파이프라인 스크립트 구문 검사."""
    for script_name in ["run_full_pipeline.py", "stitch_finalize.py"]:
        script_path = Path(f"src/{script_name}")
        assert script_path.exists(), f"{script_name} should exist"
        compile(script_path.read_text(encoding="utf-8"), script_path, "exec")


def test_orchestrator_import():
    """오케스트레이터 모듈 임포트 테스트."""
    from profile_types import Profile, ScenePlan, WorkflowMode
    assert Profile
    assert WorkflowMode
    assert ScenePlan


def test_vehicle_module_import():
    """vehicle 모듈 임포트 테스트."""
    from src.profiles.vehicle import (
        VehicleCategory,
        build_scene_plans_30s,
        get_categories,
    )
    categories = get_categories()
    assert len(categories) == 10
    assert callable(build_scene_plans_30s)
    assert VehicleCategory.CAR in VehicleCategory


def test_src_python_files_syntax():
    """src/ 내 모든 Python 파일 구문 검사."""
    src_dir = Path("src")
    for py_file in src_dir.rglob("*.py"):
        compile(py_file.read_text(encoding="utf-8"), py_file, "exec")


def test_ui_app_js_syntax():
    """ui/app.js 구문 검사 (기본적인 JS 문법만)."""
    app_js = Path("ui/app.js")
    assert app_js.exists()
    # 기본적인 JS 문법 문제는 없을 것으로 가정 (ES modules 사용)
    content = app_js.read_text(encoding="utf-8")
    assert "export" in content  # ES modules 사용 확인
    assert "async function loadVehicleData" in content
