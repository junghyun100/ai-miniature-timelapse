/**
 * AI Miniature Timelapse - Browser Source Revision Computation
 *
 * Per Section 14.1 of the Reference-Frame Relay Specification v2.0
 *
 * This implementation MUST produce identical SHA-256 hashes to the Python
 * implementation in src/domain.py:compute_source_revision().
 *
 * Algorithm:
 * 1. Filter to included fields only
 * 2. Recursively sort all object keys
 * 3. Remove all whitespace from JSON
 * 4. Normalize Unicode to NFC
 * 5. SHA-256 hash
 * 6. Prefix with "sha256:"
 */

const INCLUDED_SOURCE_REVISION_KEYS = new Set([
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
]);

/**
 * Normalize Unicode string to NFC form.
 * JavaScript strings are UTF-16; String.prototype.normalize('NFC') handles this.
 */
function normalizeUnicode(value) {
    if (typeof value === 'string') {
        return value.normalize('NFC');
    }
    if (Array.isArray(value)) {
        return value.map(normalizeUnicode);
    }
    if (value !== null && typeof value === 'object') {
        const result = {};
        for (const [k, v] of Object.entries(value)) {
            result[k] = normalizeUnicode(v);
        }
        return result;
    }
    return value;
}

/**
 * Recursively sort object keys for canonical serialization.
 * Arrays maintain order; only object keys are sorted.
 */
function sortKeysRecursive(obj) {
    if (Array.isArray(obj)) {
        return obj.map(sortKeysRecursive);
    }
    if (obj !== null && typeof obj === 'object') {
        const sorted = {};
        for (const key of Object.keys(obj).sort()) {
            sorted[key] = sortKeysRecursive(obj[key]);
        }
        return sorted;
    }
    return obj;
}

/**
 * Filter source draft to only included fields per Section 14.1.
 */
function filterIncludedFields(sourceDraft) {
    const filtered = {};
    for (const [key, value] of Object.entries(sourceDraft)) {
        if (INCLUDED_SOURCE_REVISION_KEYS.has(key)) {
            filtered[key] = value;
        }
    }
    return filtered;
}

/**
 * Compute the canonical JSON string for hashing.
 * No whitespace, sorted keys, NFC normalized.
 */
function canonicalJSON(sourceDraft) {
    const filtered = filterIncludedFields(sourceDraft);
    const normalized = sortKeysRecursive(normalizeUnicode(filtered));
    return JSON.stringify(normalized);
}

/**
 * Compute SHA-256 hash of canonical JSON.
 * Returns "sha256:<hex>" format matching Python implementation.
 */
async function computeSourceRevision(sourceDraft) {
    const canonical = canonicalJSON(sourceDraft);
    const encoder = new TextEncoder();
    const data = encoder.encode(canonical);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return `sha256:${hashHex}`;
}

/**
 * Synchronous version using Web Crypto API (not available in all contexts).
 * For environments without crypto.subtle, use the async version above.
 */
function computeSourceRevisionSync(sourceDraft) {
    // Note: This is a placeholder for environments without crypto.subtle.
    // In browser, use computeSourceRevision() async version.
    // For testing, you can use a pure JS SHA-256 implementation.
    throw new Error('Synchronous version not available. Use computeSourceRevision() async version.');
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        computeSourceRevision,
        canonicalJSON,
        filterIncludedFields,
        sortKeysRecursive,
        normalizeUnicode,
        INCLUDED_SOURCE_REVISION_KEYS
    };
}