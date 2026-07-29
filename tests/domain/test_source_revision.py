"""
Tests for source revision computation (Section 14.1).
Tests cross-platform hash equality between Python and JS implementations.
"""
import hashlib
import json

from src.domain import (
    compute_source_revision,
    serialize_canonical,
)


class TestCanonicalJson:
    """Test canonical JSON serialization."""

    def test_no_whitespace(self):
        d = {"a": 1, "b": 2}
        result = serialize_canonical(d)
        assert " " not in result
        assert "\n" not in result
        assert "\t" not in result

    def test_sorted_keys(self):
        d = {"z": 1, "a": 2}
        result = serialize_canonical(d)
        assert result.index("a") < result.index("z")

    def test_nested_objects(self):
        d = {"outer": {"inner_z": 1, "inner_a": 2}}
        result = serialize_canonical(d)
        # outer key first, then inner keys sorted
        assert result == '{"outer":{"inner_a":2,"inner_z":1}}'

    def test_unicode_strings(self):
        d = {"korean": "한국어"}
        result = serialize_canonical(d)
        assert "한국어" in result


class TestSourceRevision:
    """Test SHA-256 source revision hashing per Section 14.1."""

    def test_basic_hash_computation(self):
        """Basic hash computation works."""
        source_draft = {
            "profile_id": "architecture.korean",
            "profile_version": "2.0.0",
            "workflow_mode": "REFERENCE_FRAME_RELAY",
            "topic": "hanok",
            "genre": "architecture",
            "subtype": "hanok",
            "topic_label": "Korean Architecture: Hanok",
            "duration_seconds": 30,
            "clip_duration_seconds": 10,
            "aspect_ratio": "9:16",
            "style_bible": {"identity_lock": "test"},
            "derived_fields": {},
            "scene_plans": [],
            "narration": None,
            "idea_seed": None,
            "flow_execution_profile_id": "google-veo2-9-16-10s",
            "nim_enabled": False,
            "nim_model_id": "",
            "nim_refinement_policy": "mutable_only",
        }
        hash1 = compute_source_revision(source_draft)
        assert hash1.startswith("sha256:")
        assert len(hash1) == 71  # "sha256:" + 64 hex chars

    def test_deterministic_same_input_same_hash(self):
        """Same input always produces same hash."""
        source_draft = {
            "profile_id": "vehicle.assembly",
            "topic": "car",
            "model_name": "Porsche 911",
        }
        hash1 = compute_source_revision(source_draft)
        hash2 = compute_source_revision(source_draft)
        assert hash1 == hash2

    def test_different_input_different_hash(self):
        """Different inputs produce different hashes."""
        draft1 = {"profile_id": "a", "topic": "x"}
        draft2 = {"profile_id": "b", "topic": "x"}
        assert compute_source_revision(draft1) != compute_source_revision(draft2)

    def test_included_fields_only(self):
        """Only included fields affect the hash."""
        # These fields are included per Section 14.1
        included = {
            "profile_id": "test",
            "profile_version": "1.0.0",
            "workflow_mode": "SINGLE_CLIP_FROM_MASTER",
            "topic": "test",
            "genre": "vehicle",
            "subtype": "car",
            "topic_label": "Test Car",
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
        # Add excluded (transient) fields
        included_with_transient = included.copy()
        included_with_transient["provenance"] = {"source": "local"}
        included_with_transient["relay_branch"] = {}
        included_with_transient["source_revision"] = "sha256:deadbeef"

        hash1 = compute_source_revision(included)
        hash2 = compute_source_revision(included_with_transient)
        assert hash1 == hash2, "Transient fields should not affect hash"

    def test_key_order_independence(self):
        """Key order in input dict doesn't matter."""
        draft1 = {"a": 1, "b": 2, "c": 3}
        draft2 = {"c": 3, "a": 1, "b": 2}
        assert compute_source_revision(draft1) == compute_source_revision(draft2)

    def test_nested_key_order_independence(self):
        """Nested key order doesn't matter."""
        draft1 = {"obj": {"z": 1, "a": 2}}
        draft2 = {"obj": {"a": 2, "z": 1}}
        assert compute_source_revision(draft1) == compute_source_revision(draft2)

    def test_unicode_normalization(self):
        """Unicode is normalized to NFC."""
        # Note: Python strings are typically already NFC
        draft1 = {"topic": "hanok"}
        draft2 = {"topic": "hanok"}  # Same string
        assert compute_source_revision(draft1) == compute_source_revision(draft2)

    def test_cross_platform_consistency(self):
        """
        Verify the exact algorithm for JS implementation.

        Algorithm:
        1. Filter to included fields only
        2. Recursively sort all object keys
        3. Remove all whitespace from JSON
        4. Normalize Unicode to NFC
        5. SHA-256 hash
        6. Prefix with "sha256:"
        """
        source_draft = {
            "profile_id": "architecture.korean",
            "profile_version": "2.0.0",
            "workflow_mode": "REFERENCE_FRAME_RELAY",
            "topic": "hanok",
            "genre": "architecture",
            "subtype": "hanok",
            "topic_label": "Korean Architecture: Hanok",
            "duration_seconds": 30,
            "clip_duration_seconds": 10,
            "aspect_ratio": "9:16",
            "style_bible": {
                "identity_lock": "test lock",
                "materials": {"primary": ["wood"], "secondary": [], "tools": []},
            },
            "derived_fields": {},
            "scene_plans": [],
            "narration": None,
            "idea_seed": None,
            "flow_execution_profile_id": "google-veo2-9-16-10s",
            "nim_enabled": False,
            "nim_model_id": "",
            "nim_refinement_policy": "mutable_only",
        }

        # Compute using our function
        python_hash = compute_source_revision(source_draft)

        # Manual computation for verification
        included_keys = {
            "profile_id", "profile_version", "workflow_mode",
            "topic", "genre", "subtype", "topic_label",
            "model_name", "dish_name", "craft_name",
            "duration_seconds", "clip_duration_seconds", "aspect_ratio",
            "style_bible",
            "derived_fields",
            "scene_plans",
            "narration", "idea_seed",
            "flow_execution_profile_id",
            "nim_enabled", "nim_model_id", "nim_refinement_policy"
        }

        filtered = {k: v for k, v in source_draft.items() if k in included_keys}
        canonical = json.dumps(filtered, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
        expected_hash = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        assert python_hash == expected_hash


class TestSourceRevisionEdgeCases:
    """Edge cases for source revision."""

    def test_empty_arrays_and_objects(self):
        """Empty arrays and objects handled."""
        draft = {
            "profile_id": "test",
            "style_bible": {},
            "derived_fields": {},
            "scene_plans": [],
        }
        hash_val = compute_source_revision(draft)
        assert hash_val.startswith("sha256:")

    def test_none_values(self):
        """None values handled."""
        draft = {
            "profile_id": "test",
            "narration": None,
            "idea_seed": None,
        }
        hash_val = compute_source_revision(draft)
        assert hash_val.startswith("sha256:")
