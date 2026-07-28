/**
 * Provenance Model for UI Request Adapter (WP-2)
 *
 * Tracks immutable request, revision, provider, and fallback metadata
 * without exposing secrets per Section 14.6.
 */

export const ProvenanceSource = {
  LOCAL: 'local',
  NIM: 'nim',
  NIM_PARTIAL_FALLBACK: 'nim_partial_fallback'
};

export class ProvenanceModel {
  constructor({
    source = ProvenanceSource.LOCAL,
    provider = 'nvidia_nim',
    model_id = null,
    base_url_label = null,
    generated_at = new Date().toISOString(),
    request_id = null,
    source_revision = null,
    fallback_scene_ids = [],
    validation_warnings = []
  } = {}) {
    this.source = source;
    this.provider = provider;
    this.model_id = model_id;
    this.base_url_label = base_url_label;
    this.generated_at = generated_at;
    this.request_id = request_id;
    this.source_revision = source_revision;
    this.fallback_scene_ids = Array.isArray(fallback_scene_ids) ? [...fallback_scene_ids] : [];
    this.validation_warnings = Array.isArray(validation_warnings) ? [...validation_warnings] : [];
  }

  toDict() {
    return {
      source: this.source,
      provider: this.provider,
      model_id: this.model_id,
      base_url_label: this.base_url_label,
      generated_at: this.generated_at,
      request_id: this.request_id,
      source_revision: this.source_revision,
      fallback_scene_ids: [...this.fallback_scene_ids],
      validation_warnings: [...this.validation_warnings]
    };
  }

  static createLocal(requestId = null, sourceRevision = null) {
    return new ProvenanceModel({
      source: ProvenanceSource.LOCAL,
      provider: 'local_deterministic',
      request_id: requestId,
      source_revision: sourceRevision
    });
  }

  static fromNimResponse(responseData = {}, requestId = null, sourceRevision = null) {
    const rawSource = responseData?.provenance?.source || responseData?.source;
    let source = ProvenanceSource.NIM;
    if (rawSource === ProvenanceSource.LOCAL || rawSource === ProvenanceSource.NIM_PARTIAL_FALLBACK) {
      source = rawSource;
    }

    return new ProvenanceModel({
      source,
      provider: responseData.provider || 'nvidia_nim',
      model_id: responseData.model_id || null,
      base_url_label: responseData.base_url_label || null,
      generated_at: responseData.generated_at || new Date().toISOString(),
      request_id: responseData.request_id || requestId,
      source_revision: responseData.source_revision || sourceRevision,
      fallback_scene_ids: responseData.fallback_scene_ids || [],
      validation_warnings: responseData.validation_warnings || []
    });
  }
}
