"""
Provenance Model for UI Request Adapter (WP-2)

Defines immutable provenance tracking structures for UI requests, responses,
and model metadata without secrets per Section 14.6.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ProvenanceSource(str, Enum):
    LOCAL = "local"
    NIM = "nim"
    NIM_PARTIAL_FALLBACK = "nim_partial_fallback"


@dataclass
class ProvenanceModel:
    """
    Canonical provenance object for UI requests and responses per Section 14.6.
    Contains no secrets or sensitive authentication data.
    """

    source: ProvenanceSource
    provider: str = "nvidia_nim"
    model_id: str | None = None
    base_url_label: str | None = None
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    request_id: int | None = None
    source_revision: str | None = None
    fallback_scene_ids: list[int] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert provenance object to dict without secrets."""
        return {
            "source": (
                self.source.value if isinstance(self.source, ProvenanceSource) else str(self.source)
            ),
            "provider": self.provider,
            "model_id": self.model_id,
            "base_url_label": self.base_url_label,
            "generated_at": self.generated_at,
            "request_id": self.request_id,
            "source_revision": self.source_revision,
            "fallback_scene_ids": list(self.fallback_scene_ids),
            "validation_warnings": list(self.validation_warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProvenanceModel:
        """Create ProvenanceModel from a dictionary."""
        source_val = data.get("source", ProvenanceSource.LOCAL)
        if isinstance(source_val, str):
            try:
                source_val = ProvenanceSource(source_val)
            except ValueError:
                source_val = ProvenanceSource.LOCAL

        return cls(
            source=source_val,
            provider=data.get("provider", "nvidia_nim"),
            model_id=data.get("model_id"),
            base_url_label=data.get("base_url_label"),
            generated_at=data.get("generated_at") or datetime.now(UTC).isoformat(),
            request_id=data.get("request_id"),
            source_revision=data.get("source_revision"),
            fallback_scene_ids=data.get("fallback_scene_ids", []),
            validation_warnings=data.get("validation_warnings", []),
        )

    @classmethod
    def create_local(
        cls, request_id: int | None = None, source_revision: str | None = None
    ) -> ProvenanceModel:
        """Create a default local deterministic provenance record."""
        return cls(
            source=ProvenanceSource.LOCAL,
            provider="local_deterministic",
            request_id=request_id,
            source_revision=source_revision,
        )
