/**
 * AI Miniature Timelapse - Browser Application Module
 *
 * Implements the Relay Runner UI per Section 10, 11.6 of the spec:
 * - Scene state machine visualization (LOCKED → AWAITING_MASTER_IMAGE → VIDEO_READY → CONFIRMED → COMPLETE)
 * - Canonical prompt serialization (Copy Master Image, Copy Scene Video, Copy Full Scene, Copy All)
 * - Source Revision computation (matching Python src/domain.py)
 * - LocalStorage persistence for project state
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

// Scene status constants matching Python domain.py SceneStatus enum
export const SceneStatus = {
    LOCKED: "LOCKED",
    AWAITING_MASTER_IMAGE: "AWAITING_MASTER_IMAGE",
    AWAITING_PREVIOUS_FRAME: "AWAITING_PREVIOUS_FRAME",
    VIDEO_READY: "VIDEO_READY",
    CONFIRMED: "CONFIRMED",
    COMPLETE: "COMPLETE",
    NEEDS_RETRY: "NEEDS_RETRY",
    STALE: "STALE"
};

// Workflow mode constants
export const WorkflowMode = {
    REFERENCE_FRAME_RELAY: "REFERENCE_FRAME_RELAY",
    SINGLE_CLIP_FROM_MASTER: "SINGLE_CLIP_FROM_MASTER"
};

// Input mode constants
export const InputMode = {
    MASTER_IMAGE: "MASTER_IMAGE",
    PREVIOUS_FINAL_FRAME: "PREVIOUS_FINAL_FRAME",
    NONE: "NONE"
};

// Immutable negative prompt per Section 11.6
export const IMMUTABLE_NEGATIVE = "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, small people, tiny workers, human figures";

// Storage keys
export const STORAGE_KEYS = {
    FLOW_PACK: 'miniature_timelapse_flow_pack',
    FLOW_PACK_MANUAL: 'miniature_timelapse_flow_pack_manual',
    FLOW_GENERATION_SOURCE: 'miniature_timelapse_flow_generation_source',
    NIM_BASE_URL: 'miniature_timelapse_nim_base_url',
    SOURCE_OVERRIDES: 'miniature_timelapse_source_overrides',
    RELAY_STATES: 'miniature_timelapse_relay_states',
    ACTIVE_PROJECT: 'miniature_timelapse_active_project'
};

// ============================================================================
// Source Revision Computation (Section 14.1)
// ============================================================================

export function normalizeUnicode(value) {
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

export function sortKeysRecursive(obj) {
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

export function filterIncludedFields(sourceDraft) {
    const filtered = {};
    for (const [key, value] of Object.entries(sourceDraft)) {
        if (INCLUDED_SOURCE_REVISION_KEYS.has(key)) {
            filtered[key] = value;
        }
    }
    return filtered;
}

export function canonicalJSON(sourceDraft) {
    const filtered = filterIncludedFields(sourceDraft);
    const normalized = sortKeysRecursive(normalizeUnicode(filtered));
    return JSON.stringify(normalized);
}

export async function computeSourceRevision(sourceDraft) {
    const canonical = canonicalJSON(sourceDraft);
    const encoder = new TextEncoder();
    const data = encoder.encode(canonical);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return `sha256:${hashHex}`;
}

// ============================================================================
// Serialization (Section 11.6)
// ============================================================================

export function serializeAssetRef(assetRef) {
    if (!assetRef) return "none";
    const parts = [assetRef.logical_id];
    if (assetRef.kind) parts.push(`kind=${assetRef.kind}`);
    if (assetRef.scope) parts.push(`scope=${assetRef.scope}`);
    if (assetRef.flow_asset_label) parts.push(`label=${assetRef.flow_asset_label}`);
    if (assetRef.local_path) parts.push(`local=${assetRef.local_path}`);
    if (assetRef.source_scene_id !== undefined) parts.push(`source_scene=${assetRef.source_scene_id}`);
    return parts.join(" | ");
}

export function serializeProjectHeader(project) {
    return [
        `Project: ${project.topic}`,
        `Topic Label: ${project.topic_label}`,
        `Profile: ${project.profile_id}@${project.profile_version}`,
        `Workflow: ${project.workflow_mode}`,
        `Duration: ${project.duration_seconds}s (${project.scene_count} scene${project.scene_count !== 1 ? 's' : ''} × ${project.clip_duration_seconds}s)`,
        `Aspect Ratio: ${project.aspect_ratio}`,
        `Source: ${project.provenance?.source || 'local'}`,
        `Source Revision: ${project.source_revision}`
    ];
}

export function serializeMasterImage(scene) {
    return [
        "MASTER IMAGE",
        `First Frame Prompt: ${scene.first_frame_prompt}`,
        `Template Exclusions: ${scene.template_exclusions}`,
        `Negative Prompt: ${IMMUTABLE_NEGATIVE}`
    ];
}

export function serializeSceneBlock(scene, sceneIndex) {
    return [
        `SCENE ${sceneIndex} — ${scene.name}`,
        `Input: ${serializeAssetRef(scene.asset_ref)}`,
        `Video Prompt: ${scene.video_prompt}`,
        `Template Exclusions: ${scene.template_exclusions}`,
        `Negative Prompt: ${IMMUTABLE_NEGATIVE}`
    ];
}

export function serializeFullPlan(project) {
    const lines = [];
    lines.push(...serializeProjectHeader(project));
    lines.push("");

    if (project.scenes.length > 0) {
        lines.push(...serializeMasterImage(project.scenes[0]));
        lines.push("");
    }

    for (let i = 0; i < project.scenes.length; i++) {
        lines.push(...serializeSceneBlock(project.scenes[i], i + 1));
        if (i < project.scenes.length - 1) lines.push("");
    }

    return lines.join("\n");
}

export function serializeMasterImagePrompt(project) {
    if (!project.scenes.length) return "";
    return serializeMasterImage(project.scenes[0]).join("\n");
}

export function serializeSceneVideoPrompt(project, sceneId) {
    const scene = project.scenes.find(s => s.id === sceneId);
    if (!scene) return "";
    return [
        `SCENE ${sceneId} — ${scene.name}`,
        `Video Prompt: ${scene.video_prompt}`,
        `Template Exclusions: ${scene.template_exclusions}`,
        `Negative Prompt: ${IMMUTABLE_NEGATIVE}`
    ].join("\n");
}

export function serializeFullScene(project, sceneId) {
    const scene = project.scenes.find(s => s.id === sceneId);
    if (!scene) return "";

    if (sceneId === 1) {
        return [
            ...serializeMasterImage(scene),
            "",
            ...serializeSceneBlock(scene, 1)
        ].join("\n");
    } else {
        return serializeSceneBlock(scene, sceneId).join("\n");
    }
}

// ============================================================================
// Copy Actions (Section 11.6)
// ============================================================================

export const CopyAction = {
    MASTER_IMAGE: "master_image",
    SCENE_VIDEO: "scene_video",
    FULL_SCENE: "full_scene",
    ALL: "all"
};

export function performCopyAction(project, action, sceneId = null) {
    const timestamp = new Date().toISOString();
    const sourceRevision = project.source_revision;

    let text = "";
    let resultSceneId = null;

    switch (action) {
        case CopyAction.MASTER_IMAGE:
            text = serializeMasterImagePrompt(project);
            resultSceneId = 1;
            break;
        case CopyAction.SCENE_VIDEO:
            if (!sceneId) throw new Error("scene_id required for SCENE_VIDEO");
            text = serializeSceneVideoPrompt(project, sceneId);
            resultSceneId = sceneId;
            break;
        case CopyAction.FULL_SCENE:
            if (!sceneId) throw new Error("scene_id required for FULL_SCENE");
            text = serializeFullScene(project, sceneId);
            resultSceneId = sceneId;
            break;
        case CopyAction.ALL:
            text = serializeFullPlan(project);
            break;
        default:
            throw new Error(`Unknown copy action: ${action}`);
    }

    return {
        action,
        scene_id: resultSceneId,
        text,
        source_revision: sourceRevision,
        timestamp
    };
}

// ============================================================================
// Relay State Machine (Section 10)
// ============================================================================

export function getInitialSceneStatus(sceneIndex, workflowMode, hasMasterImage = false, hasPreviousFrame = false) {
    if (sceneIndex === 0) { // Scene 1
        if (workflowMode === WorkflowMode.REFERENCE_FRAME_RELAY) {
            return hasMasterImage ? SceneStatus.VIDEO_READY : SceneStatus.AWAITING_MASTER_IMAGE;
        } else {
            return hasMasterImage ? SceneStatus.VIDEO_READY : SceneStatus.AWAITING_MASTER_IMAGE;
        }
    } else { // Scene 2+
        if (workflowMode === WorkflowMode.REFERENCE_FRAME_RELAY) {
            return hasPreviousFrame ? SceneStatus.VIDEO_READY : SceneStatus.AWAITING_PREVIOUS_FRAME;
        } else {
            return SceneStatus.LOCKED;
        }
    }
}

export function canTransition(fromState, toState) {
    const transitions = {
        [SceneStatus.LOCKED]: [SceneStatus.AWAITING_MASTER_IMAGE, SceneStatus.AWAITING_PREVIOUS_FRAME, SceneStatus.NEEDS_RETRY],
        [SceneStatus.AWAITING_MASTER_IMAGE]: [SceneStatus.VIDEO_READY, SceneStatus.NEEDS_RETRY, SceneStatus.LOCKED],
        [SceneStatus.AWAITING_PREVIOUS_FRAME]: [SceneStatus.VIDEO_READY, SceneStatus.NEEDS_RETRY, SceneStatus.LOCKED],
        [SceneStatus.VIDEO_READY]: [SceneStatus.CONFIRMED, SceneStatus.NEEDS_RETRY],
        [SceneStatus.CONFIRMED]: [SceneStatus.COMPLETE, SceneStatus.NEEDS_RETRY],
        [SceneStatus.COMPLETE]: [SceneStatus.NEEDS_RETRY, SceneStatus.STALE],
        [SceneStatus.NEEDS_RETRY]: [SceneStatus.AWAITING_MASTER_IMAGE, SceneStatus.AWAITING_PREVIOUS_FRAME, SceneStatus.LOCKED],
        [SceneStatus.STALE]: [SceneStatus.LOCKED]
    };
    return transitions[fromState]?.includes(toState) || false;
}

export function createInitialRelayBranch(project) {
    const sceneStatuses = {};
    for (let i = 0; i < project.scenes.length; i++) {
        const scene = project.scenes[i];
        const hasMaster = i === 0 && scene.asset_ref?.local_path;
        const hasPrev = i > 0 && scene.asset_ref?.local_path;
        sceneStatuses[String(i + 1)] = getInitialSceneStatus(i, project.workflow_mode, hasMaster, hasPrev);
    }
    return {
        branch_id: crypto.randomUUID(),
        parent_branch_id: null,
        scene_statuses: sceneStatuses,
        asset_refs: project.scenes.map(s => s.asset_ref),
        created_at: new Date().toISOString(),
        lineage_revision: project.source_revision,
        nonce: crypto.randomUUID().slice(0, 8)
    };
}

export function getNextActionableScene(relayBranch, project) {
    for (const scene of project.scenes) {
        const status = relayBranch.scene_statuses[String(scene.id)];
        if ([SceneStatus.AWAITING_MASTER_IMAGE, SceneStatus.AWAITING_PREVIOUS_FRAME, SceneStatus.VIDEO_READY].includes(status)) {
            return scene.id;
        }
    }
    return null;
}

export function isAllComplete(relayBranch, project) {
    return project.scenes.every(scene => relayBranch.scene_statuses[String(scene.id)] === SceneStatus.COMPLETE);
}

// ============================================================================
// Persistence (Section 16.2)
// ============================================================================

export function saveProjectState(project) {
    const state = {
        version: 1,
        project: project,
        saved_at: new Date().toISOString()
    };
    localStorage.setItem(STORAGE_KEYS.ACTIVE_PROJECT, JSON.stringify(state));
}

export function loadProjectState() {
    const stored = localStorage.getItem(STORAGE_KEYS.ACTIVE_PROJECT);
    if (!stored) return null;
    try {
        return JSON.parse(stored).project;
    } catch {
        return null;
    }
}

export function clearProjectState() {
    localStorage.removeItem(STORAGE_KEYS.ACTIVE_PROJECT);
}

export function listSavedProjects() {
    // For future: scan localStorage for multiple project keys
    const active = loadProjectState();
    return active ? [{ project_id: 'active', ...active }] : [];
}

// ============================================================================
// UI Helpers
// ============================================================================

export function getSceneStatusClass(status) {
    const classes = {
        [SceneStatus.LOCKED]: 'scene-card locked',
        [SceneStatus.AWAITING_MASTER_IMAGE]: 'scene-card ready',
        [SceneStatus.AWAITING_PREVIOUS_FRAME]: 'scene-card ready',
        [SceneStatus.VIDEO_READY]: 'scene-card active',
        [SceneStatus.CONFIRMED]: 'scene-card complete',
        [SceneStatus.COMPLETE]: 'scene-card complete',
        [SceneStatus.NEEDS_RETRY]: 'scene-card retry',
        [SceneStatus.STALE]: 'scene-card stale'
    };
    return classes[status] || 'scene-card';
}

export function getSceneStatusLabel(status) {
    const labels = {
        [SceneStatus.LOCKED]: '🔒 Locked',
        [SceneStatus.AWAITING_MASTER_IMAGE]: '🖼️ Awaiting Master Image',
        [SceneStatus.AWAITING_PREVIOUS_FRAME]: '⏭️ Awaiting Previous Frame',
        [SceneStatus.VIDEO_READY]: '▶️ Video Ready',
        [SceneStatus.CONFIRMED]: '✅ Confirmed',
        [SceneStatus.COMPLETE]: '🏁 Complete',
        [SceneStatus.NEEDS_RETRY]: '🔄 Needs Retry',
        [SceneStatus.STALE]: '⚠️ Stale'
    };
    return labels[status] || status;
}

export function getSceneStatusBadgeClass(status) {
    const classes = {
        [SceneStatus.LOCKED]: 'state-neutral',
        [SceneStatus.AWAITING_MASTER_IMAGE]: 'state-warning',
        [SceneStatus.AWAITING_PREVIOUS_FRAME]: 'state-warning',
        [SceneStatus.VIDEO_READY]: 'state-warning',
        [SceneStatus.CONFIRMED]: 'state-success',
        [SceneStatus.COMPLETE]: 'state-success',
        [SceneStatus.NEEDS_RETRY]: 'state-warning',
        [SceneStatus.STALE]: 'state-warning'
    };
    return classes[status] || 'state-neutral';
}

export async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        return true;
    }
}

export function showToast(message, type = 'info', duration = 3000) {
    // Simple toast implementation - could be enhanced
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), duration);
}

// ============================================================================
// Default Configuration
// ============================================================================

export const DEFAULT_FLOW_PROFILE = {
    id: "flow.frames_first.10s",
    display_name: "Frames to Video: First, 10s",
    provider: "google_flow",
    model_label: "Google Flow (10s)",
    supports_start_frame: true,
    supported_clip_durations_seconds: [10],
    supports_prompt_audio: "unknown",
    last_verified_at: new Date().toISOString(),
    verification_url: "https://support.google.com/flow/answer/16352836"
};

export const DEFAULT_PROFILES = {
    'architecture.korean': {
        id: 'architecture.korean',
        version: '2.0.0',
        display_name: 'Architecture (Korean Hanok)',
        workflow_mode: WorkflowMode.REFERENCE_FRAME_RELAY,
        allowed_total_durations: [30, 60],
        default_total_duration: 30,
        clip_duration_seconds: 10,
        scene_plans_30s: [
            { scene_id: 1, name: "Foundation and Walls", start_state: "compacted earth, stone footings, sill beams, columns, hanji frames", ordered_actions: ["place stone footings", "seat sill beams", "raise columns", "fit hanji frames"], end_state: "single-story timber wall frame complete", forbidden_changes: InputMode.MASTER_IMAGE, input_mode: InputMode.MASTER_IMAGE },
            { scene_id: 2, name: "Roofing and Exterior", start_state: "Scene 1 final frame", ordered_actions: ["crossbeams", "purlins", "rafters", "eave supports", "giwa tiles", "hanji doors/windows"], end_state: "roof and exterior complete", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
            { scene_id: 3, name: "Painting, Landscaping, and Reveal", start_state: "Scene 2 final frame", ordered_actions: ["wood finish", "dancheong on beam ends", "stone path", "low wall", "moss", "grass", "small pine", "remove tools"], end_state: "coherent hanok revealed", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME }
        ]
    }
};