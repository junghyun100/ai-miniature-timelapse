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
    "selection", "subject", "category",
    "model_name", "dish_name", "dish_key", "craft_name",
    "idea_name", "materials", "final_object", "korean_narration",
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

export const PROFILE_SELECTION_CONFIG = {
    "architecture.korean": {
        genre_label: "Architecture",
        subtype_key: "subtype",
        subject_key: "topic",
        fields: [
            {
                key: "subtype",
                label: "Architecture subtype",
                type: "select",
                required: true,
                default: "Hanok",
                options: ["Hanok", "Palace", "Temple", "Seowon", "Modern Hanok", "Dolmen", "Villa", "Store", "School", "Hotel", "Apartment", "Factory", "Barn"]
            },
            {
                key: "topic",
                label: "Topic",
                type: "text",
                required: true,
                default: "Korean hanok",
                placeholder: "e.g. Joseon-era courtyard hanok"
            }
        ]
    },
    "vehicle.assembly": {
        genre_label: "Vehicle",
        subtype_key: "category",
        subject_key: "model",
        fields: [
            { key: "category", label: "Vehicle category", type: "vehicle-category", required: true, default: "car" },
            { key: "model", label: "Model", type: "vehicle-model", required: true, default: "" }
        ]
    },
    "product.assembly": {
        genre_label: "Product",
        subtype_key: "subtype",
        subject_key: "subject",
        fields: [
            {
                key: "subtype",
                label: "Product subtype",
                type: "select",
                required: true,
                default: "Watch",
                options: ["Watch", "Camera", "Sneaker", "Robot", "Dinosaur", "Wizard House", "Spaceship", "Hoverbike", "Mech", "Dragon"]
            },
            {
                key: "subject",
                label: "Subject",
                type: "text",
                required: true,
                default: "Mechanical watch",
                placeholder: "e.g. skeleton mechanical watch"
            }
        ]
    },
    "home_decor.diy": {
        genre_label: "HomeDecor",
        subtype_key: "subtype",
        subject_key: "final_object",
        fixed_subtype: "DIY",
        fields: [
            { key: "idea_name", label: "Idea name", type: "text", required: true, default: "Hanji lotus mood lamp" },
            { key: "materials", label: "Materials", type: "text", required: true, default: "hanji paper, discarded plastic spoons, silk thread" },
            { key: "final_object", label: "Final object", type: "text", required: true, default: "traditional lotus mood lamp" },
            {
                key: "korean_narration",
                label: "Korean narration (60 characters excluding spaces)",
                type: "textarea",
                required: true,
                default: "버려진 숟가락에 한지를 겹쳐 붙이면 전통 연꽃 무드등이 완성돼요"
            }
        ]
    },
    "cooking.miniature": {
        genre_label: "Cooking",
        subtype_key: "subtype",
        subject_key: "dish_key",
        fixed_subtype: "Miniature",
        fields: [
            {
                key: "dish_key",
                label: "Dish",
                type: "select",
                required: true,
                default: "kimchi_jjigae",
                options: [
                    { value: "kimchi_jjigae", label: "Kimchi Jjigae" },
                    { value: "bibimbap", label: "Bibimbap" },
                    { value: "bulgogi", label: "Bulgogi" },
                    { value: "jjajangmyeon", label: "Jjajangmyeon" },
                    { value: "samgyeopsal", label: "Samgyeopsal (Grilled Pork Belly)" },
                    { value: "dakgalbi", label: "Dakgalbi (Spicy Stir-fried Chicken)" }
                ]
            }
        ]
    }
};

function cleanTopicSegment(value) {
    return String(value ?? "").trim().replace(/\s+/g, " ");
}

function titleCaseSelection(value) {
    return cleanTopicSegment(value)
        .split(" ")
        .map(part => part ? `${part.charAt(0).toUpperCase()}${part.slice(1)}` : part)
        .join(" ");
}

function getConfiguredOptionLabel(profileId, key, value) {
    const field = PROFILE_SELECTION_CONFIG[profileId]?.fields.find(item => item.key === key);
    const option = field?.options?.find(item => (
        typeof item === "object" ? item.value === value : item === value
    ));
    return typeof option === "object" ? option.label : value;
}

export function getDefaultSelectionValues(profileId) {
    const config = PROFILE_SELECTION_CONFIG[profileId];
    if (!config) return {};
    const values = {};
    for (const field of config.fields) {
        values[field.key] = field.default ?? "";
    }
    if (config.fixed_subtype) values.subtype = config.fixed_subtype;
    return values;
}

export function deriveTopicLabel(profileId, selectionValues = {}) {
    const config = PROFILE_SELECTION_CONFIG[profileId];
    if (!config) return "";
    const subtype = config.fixed_subtype
        || selectionValues[config.subtype_key]
        || profileId.split(".")[1];
    const subjectValue = selectionValues[config.subject_key]
        || selectionValues.topic
        || selectionValues.subject
        || subtype;
    const subject = getConfiguredOptionLabel(profileId, config.subject_key, subjectValue);
    return [
        config.genre_label,
        titleCaseSelection(subtype),
        cleanTopicSegment(subject)
    ].filter(Boolean).join("-");
}

export function getLegacySelectionFields(profileId, selectionValues = {}) {
    const values = { ...selectionValues };
    switch (profileId) {
        case "architecture.korean":
            return {
                topic: cleanTopicSegment(values.topic),
                subtype: cleanTopicSegment(values.subtype)
            };
        case "vehicle.assembly":
            return {
                topic: cleanTopicSegment(values.model),
                subtype: cleanTopicSegment(values.category),
                category: cleanTopicSegment(values.category),
                model_name: cleanTopicSegment(values.model)
            };
        case "product.assembly":
            return {
                topic: cleanTopicSegment(values.subject),
                subtype: cleanTopicSegment(values.subtype),
                subject: cleanTopicSegment(values.subject)
            };
        case "home_decor.diy":
            return {
                topic: cleanTopicSegment(values.idea_name),
                subtype: "DIY",
                craft_name: cleanTopicSegment(values.idea_name),
                idea_name: cleanTopicSegment(values.idea_name),
                materials: cleanTopicSegment(values.materials),
                final_object: cleanTopicSegment(values.final_object),
                korean_narration: cleanTopicSegment(values.korean_narration),
                narration: cleanTopicSegment(values.korean_narration)
            };
        case "cooking.miniature":
            {
                const dishName = getConfiguredOptionLabel(profileId, "dish_key", values.dish_key);
            return {
                topic: cleanTopicSegment(dishName),
                subtype: "Miniature",
                dish_key: cleanTopicSegment(values.dish_key),
                dish_name: cleanTopicSegment(dishName)
            };
            }
        default:
            return { topic: cleanTopicSegment(values.topic) };
    }
}

export function getCanonicalSelection(profileId, selectionValues = {}) {
    const values = { ...selectionValues };
    switch (profileId) {
        case "architecture.korean":
            return {
                subtype: cleanTopicSegment(values.subtype).toLowerCase().replace(/\s+/g, "_"),
                topic: cleanTopicSegment(values.topic)
            };
        case "vehicle.assembly":
            return {
                vehicle_category: cleanTopicSegment(values.category).toLowerCase(),
                model_name: cleanTopicSegment(values.model)
            };
        case "product.assembly":
            return {
                subtype: cleanTopicSegment(values.subtype).toLowerCase().replace(/\s+/g, "_"),
                subject: cleanTopicSegment(values.subject)
            };
        case "home_decor.diy":
            return {
                idea_name: cleanTopicSegment(values.idea_name),
                materials: cleanTopicSegment(values.materials)
                    .split(",")
                    .map(material => material.trim())
                    .filter(Boolean),
                final_object: cleanTopicSegment(values.final_object),
                korean_narration: cleanTopicSegment(values.korean_narration)
            };
        case "cooking.miniature":
            return { dish_key: cleanTopicSegment(values.dish_key) };
        default:
            return { ...values };
    }
}

export function countNarrationCharacters(value) {
    return Array.from(String(value ?? "").replace(/\s/g, "")).length;
}

export function resolveProjectWorkflowMode(profileId, duration, profileMode) {
    if (profileId === "product.assembly") {
        return Number(duration) === 10
            ? WorkflowMode.SINGLE_CLIP_FROM_MASTER
            : WorkflowMode.REFERENCE_FRAME_RELAY;
    }
    return profileMode;
}

export function validateSelectionValues(profileId, selectionValues = {}) {
    const config = PROFILE_SELECTION_CONFIG[profileId];
    if (!config) return { valid: false, errors: ["Unknown profile."] };
    const errors = [];
    for (const field of config.fields) {
        if (field.required && !cleanTopicSegment(selectionValues[field.key])) {
            errors.push(`${field.label} is required.`);
        }
    }
    if (
        profileId === "home_decor.diy"
        && countNarrationCharacters(selectionValues.korean_narration) > 60
    ) {
        errors.push("Korean narration must be 60 characters or fewer excluding spaces.");
    }
    return { valid: errors.length === 0, errors };
}

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

export function splitPromptNegative(prompt, fallbackNegative = IMMUTABLE_NEGATIVE) {
    const rawPrompt = String(prompt || "").trim();
    const match = rawPrompt.match(/\s*Negative Prompt:\s*["“]?([\s\S]*?)["”]?\s*$/i);
    const body = match ? rawPrompt.slice(0, match.index).trim() : rawPrompt;
    const extracted = match ? match[1].trim() : String(fallbackNegative || IMMUTABLE_NEGATIVE).trim();
    const negative = extracted.replace(/^["“]+|["”]+$/g, "").replace(/\.+$/, "").trim();
    return { body, negative };
}

function serializePromptBlock({
    heading,
    promptLabel,
    prompt,
    templateExclusions,
    fallbackNegative,
    prefixLines = []
}) {
    const { body, negative } = splitPromptNegative(prompt, fallbackNegative);
    return [
        heading,
        ...prefixLines,
        `${promptLabel}: ${body}`,
        `Template Exclusions: ${templateExclusions}`,
        `Negative Prompt: ${negative}.`
    ];
}

export function getSceneInputLabel(sceneIndex, inputMode) {
    const index = Number(sceneIndex);
    if (index <= 1 || inputMode === InputMode.MASTER_IMAGE) return "Master Image";
    return `Scene ${index - 1} Final Frame`;
}

export function serializeMasterImage(scene) {
    return serializePromptBlock({
        heading: "MASTER IMAGE",
        promptLabel: "First Frame Prompt",
        prompt: scene.first_frame_prompt,
        templateExclusions: scene.template_exclusions,
        fallbackNegative: scene.negative_prompt_base || IMMUTABLE_NEGATIVE
    });
}

export function serializeSceneBlock(scene, sceneIndex) {
    return serializePromptBlock({
        heading: `SCENE ${sceneIndex} — ${scene.name}`,
        promptLabel: "Video Prompt",
        prompt: scene.video_prompt,
        templateExclusions: scene.template_exclusions,
        fallbackNegative: scene.negative_prompt_base || IMMUTABLE_NEGATIVE,
        prefixLines: [
            `Input: ${getSceneInputLabel(sceneIndex, scene.input_mode)}`,
            `Output: ${serializeAssetRef(scene.asset_ref)}`
        ]
    });
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
    return serializeSceneBlock(scene, sceneId).join("\n");
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
        // For REFERENCE_FRAME_RELAY: Scene 2+ starts LOCKED, unlocks to AWAITING_PREVIOUS_FRAME when previous scene is CONFIRMED
        // For SINGLE_CLIP_FROM_MASTER: always LOCKED (only 1 scene)
        return SceneStatus.LOCKED;
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
        // Check if asset has been confirmed by user (master image uploaded/approved)
        const hasMaster = i === 0 && scene.asset_ref?.confirmed_by_user;
        const hasPrev = i > 0 && scene.asset_ref?.confirmed_by_user;
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
// Vehicle Data Loader (loads from ui/data/vehicle.json - single source of truth)
// ============================================================================

let _vehicleDataPromise = null;

export async function loadVehicleData() {
    if (!_vehicleDataPromise) {
        _vehicleDataPromise = fetch('./data/vehicle.json')
            .then(res => {
                if (!res.ok) throw new Error(`Failed to load vehicle.json: ${res.status}`);
                return res.json();
            })
            .catch(err => {
                console.error('Vehicle data load failed:', err);
                _vehicleDataPromise = null; // Allow retry
                throw err;
            });
    }
    return _vehicleDataPromise;
}

export function getVehicleDataSync() {
    // For synchronous access after initial load
    if (_vehicleDataPromise && _vehicleDataPromise._cached) {
        return _vehicleDataPromise._cached;
    }
    return null;
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

const VEHICLE_PROGRESS_RANGES = {
    30: ["0-30%", "30-75%", "75-100%"],
    60: ["0-15%", "15-35%", "35-55%", "55-75%", "75-90%", "90-100%"]
};

const VEHICLE_AIRPLANE_30_SCENE_NAMES = [
    "Airframe Skeleton & Engine Mount",
    "Wings, Tail, Landing Gear & Controls",
    "Exterior Panels, Canopy, Propeller & Final Reveal"
];

const VEHICLE_AIRPLANE_60_SCENE_NAMES = [
    "Airframe Skeleton",
    "Engine & Cockpit Mount",
    "Wings & Tail",
    "Landing Gear & Controls",
    "Exterior Panels & Canopy",
    "Propeller, Final Polish & Reveal"
];

const VEHICLE_DEFAULT_30_SCENE_NAMES = [
    "Core Structure & Mounts",
    "Secondary Assemblies & Linkages",
    "Exterior Finish & Reveal"
];

const VEHICLE_DEFAULT_60_SCENE_NAMES = [
    "Core Structure",
    "Power Unit Mount",
    "Major Assemblies",
    "Systems & Linkages",
    "Exterior Details",
    "Final Finish & Reveal"
];

function summarizeVehicleActions(actions) {
    return actions.filter(Boolean).join("; ");
}

function joinVisibleParts(parts) {
    return parts.filter(Boolean).join(", ");
}

function sanitizeVehicleFutureAction(action) {
    const lowered = String(action || "").toLowerCase();
    if ([
        "final polish",
        "final reveal",
        "clean workbench",
        "hero reveal",
        "final finish",
        "fully assembled",
        "completed model",
        "reveal"
    ].some(token => lowered.includes(token))) {
        return "later finishing stage";
    }
    return action;
}

function sanitizeVehicleFutureActions(actions) {
    return Array.from(new Set(actions.map(sanitizeVehicleFutureAction).filter(Boolean)));
}

function buildVehicleSceneTemplate({
    scene_id,
    name,
    start_state,
    ordered_actions,
    end_state,
    completion_range,
    is_final_scene,
    exact_stop_state,
    reserved_future_actions,
    forbidden_future_actions,
    input_mode,
    forbidden_changes
}) {
    return {
        scene_id,
        name,
        start_state,
        ordered_actions,
        end_state,
        completion_range,
        is_final_scene,
        exact_stop_state,
        reserved_future_actions,
        forbidden_future_actions,
        forbidden_changes,
        input_mode
    };
}

function getVehicleSceneNames(category, duration) {
    if (category === "airplane") {
        return duration === 60 ? VEHICLE_AIRPLANE_60_SCENE_NAMES : VEHICLE_AIRPLANE_30_SCENE_NAMES;
    }
    return duration === 60 ? VEHICLE_DEFAULT_60_SCENE_NAMES : VEHICLE_DEFAULT_30_SCENE_NAMES;
}

function buildVehicleSceneStateText({
    sceneName,
    currentActions,
    reservedFutureActions,
    isFinalScene
}) {
    const currentActionList = summarizeVehicleActions(currentActions);
    if (isFinalScene) {
        return `${sceneName} is complete; all remaining parts are installed and the model is ready for the final reveal on a clean workbench.`;
    }
    const futureActionList = sanitizeVehicleFutureActions(reservedFutureActions || []);
    const futureSummary = futureActionList.length ? futureActionList.join(", ") : "no remaining actions";
    return `Completed actions in this scene: ${currentActionList || sceneName}. The model must remain visibly incomplete, with future parts still separate, visible, and unused: ${futureSummary}.`;
}

function buildVehicleSceneContract({
    sceneIndex,
    sceneCount,
    sceneName,
    currentActions,
    futureActions,
    startState,
    inputMode,
    baseForbiddenChanges,
    completionRange
}) {
    const isFinalScene = sceneIndex === sceneCount - 1;
    const reservedFutureActions = isFinalScene ? [] : sanitizeVehicleFutureActions([...futureActions]);
    const exactStopState = buildVehicleSceneStateText({
        sceneName,
        currentActions,
        reservedFutureActions,
        isFinalScene
    });
    const forbiddenFutureActions = isFinalScene
        ? []
        : reservedFutureActions.map(action => `Do not proceed beyond this stop state into: ${sanitizeVehicleFutureAction(action)}`);

    return buildVehicleSceneTemplate({
        scene_id: sceneIndex + 1,
        name: sceneName,
        start_state: startState,
        ordered_actions: currentActions,
        end_state: exactStopState,
        completion_range: completionRange,
        is_final_scene: isFinalScene,
        exact_stop_state: exactStopState,
        reserved_future_actions: reservedFutureActions,
        forbidden_future_actions: forbiddenFutureActions,
        input_mode: inputMode,
        forbidden_changes: baseForbiddenChanges
    });
}

function buildVehicleScenePlans(data, category, duration) {
    const steps = data.assemblySteps[category] || data.assemblySteps.car;
    const sceneNames = getVehicleSceneNames(category, duration);
    const sceneCount = duration === 60 ? 6 : 3;
    const completionRanges = VEHICLE_PROGRESS_RANGES[duration] || VEHICLE_PROGRESS_RANGES[30];
    const stepGroups = duration === 60
        ? steps.map(step => [step])
        : [
            steps.slice(0, 2),
            steps.slice(2, 4),
            steps.slice(4, 6)
        ];
    const baseForbiddenChanges = [
        "Camera angle",
        "Lighting direction",
        "Workbench surface",
        "Parts must not float or teleport",
        "Hands only"
    ];

    const scenes = [];
    let previousExactStopState = "all parts disassembled on workbench";

    stepGroups.forEach((group, sceneIndex) => {
        const futureActions = stepGroups
            .slice(sceneIndex + 1)
            .flat()
            .filter(Boolean);
        const sceneName = sceneNames[sceneIndex] || `Scene ${sceneIndex + 1}`;
        const scene = buildVehicleSceneContract({
            sceneIndex,
            sceneCount,
            sceneName,
            currentActions: group.filter(Boolean),
            futureActions,
            startState: previousExactStopState,
            inputMode: sceneIndex === 0 ? InputMode.MASTER_IMAGE : InputMode.PREVIOUS_FINAL_FRAME,
            baseForbiddenChanges,
            completionRange: completionRanges[sceneIndex] || completionRanges[completionRanges.length - 1]
        });
        scenes.push(scene);
        previousExactStopState = scene.exact_stop_state;
    });

    return scenes;
}

const PRODUCT_SUBTYPE_DETAILS = {
    watch: { label: "Mechanical Watch", materials: ["stainless steel", "sapphire crystal", "leather strap", "movement parts"], key_parts: ["case", "bezel", "dial", "hands", "crown", "movement", "strap", "buckle"], stages: ["Place the main plate and movement bridge into the open case base", "Seat the gear train and mainspring barrel, then lock the movement screws", "Align the dial and press the hour and minute hands into place", "Close the case with bezel, crystal, and crown fitted", "Thread the leather strap through the lugs and fasten the buckle", "Sweep away dust and reveal the finished mechanical watch"] },
    camera: { label: "Vintage Camera", materials: ["metal body", "leatherette", "glass lens elements", "shutter mechanism"], key_parts: ["body", "lens barrel", "shutter", "viewfinder", "film compartment", "winder"], stages: ["Lock the shutter box and body shell to the base frame", "Install the lens barrel and glass elements into the front mount", "Fit the film chamber, winding spool, and viewfinder assembly", "Close the top plate and back door, then add control dials", "Attach leatherette panels, strap lugs, and small branding details", "Brush away debris and reveal the finished vintage camera"] },
    sneaker: { label: "Sneaker", materials: ["mesh upper", "foam midsole", "rubber outsole", "laces", "overlays"], key_parts: ["upper", "midsole", "outsole", "lacing system", "tongue", "heel counter", "insole"], stages: ["Stretch the upper over the last and align the toe box", "Glue the foam midsole to the rubber outsole", "Pull the laces through the eyelets and settle the tongue", "Attach the heel counter and side overlays for structure", "Add stitching lines, logo marks, and texture touches", "Sweep away fibers and reveal the finished sneaker"] },
    robot: { label: "Robot", materials: ["metal", "plastic", "wire", "LED", "servo", "circuit board"], key_parts: ["head", "torso", "arms", "legs", "joints", "power core", "sensor array"], stages: ["Assemble the torso frame and power core housing", "Mount the arms, shoulder joints, and elbow actuators", "Attach the legs, hips, and knee joints", "Install the head, sensor array, and chest armor", "Add armor plates, wiring, and light details", "Brush away dust and reveal the finished robot"] },
    dinosaur: { label: "Dinosaur Skeleton", materials: ["fossil bone replica", "metal armature", "display base"], key_parts: ["skull", "spine", "ribs", "pelvis", "femurs", "tail vertebrae", "claws"], stages: ["Pin the skull and spine into the metal armature", "Attach ribs, pelvis, and tail vertebrae in sequence", "Add the front legs, hind legs, and claw joints", "Shape the neck, tail, and posture on the display base", "Add surface texture, color wash, and fossil detail", "Brush away crumbs and reveal the finished dinosaur skeleton"] },
    wizard_house: { label: "Wizard House", materials: ["wood", "stone", "thatch", "crystal", "potion bottles", "magic effects"], key_parts: ["base", "walls", "roof", "chimney", "door", "windows", "tower", "magical details"], stages: ["Set the stone base and lower walls on the foundation", "Raise upper walls, door frame, and window openings", "Build the roof structure and chimney", "Attach tower pieces, balconies, and trims", "Add crystals, potion bottles, lanterns, and magical details", "Sweep away dust and reveal the finished wizard house"] },
    spaceship: { label: "Spaceship", materials: ["metal hull", "engine parts", "thrusters", "cockpit glass", "solar panels"], key_parts: ["hull", "engines", "cockpit", "wings/fins", "landing gear", "antenna", "thrusters"], stages: ["Assemble the fuselage shell and central hull frame", "Mount the engines, thrusters, and power conduits", "Fit the cockpit, canopy, and antenna array", "Attach wings, fins, landing gear, and exterior panels", "Add decals, panel lines, and energy details", "Brush away debris and reveal the finished spaceship"] },
    hoverbike: { label: "Hoverbike", materials: ["metal frame", "anti-grav engines", "seat", "handlebars", "thrusters"], key_parts: ["frame", "engines", "seat", "handlebars", "thrusters", "stabilizers", "dashboard"], stages: ["Build the frame and anti-gravity engine core", "Mount the seat, handlebars, and dashboard housing", "Attach thrusters and stabilizers under the frame", "Fit the fairings, control lines, and body covers", "Add light strips, decals, and mechanical detailing", "Sweep away dust and reveal the finished hoverbike"] },
    mech: { label: "Mech", materials: ["armor plates", "hydraulics", "actuators", "cockpit", "weapons", "joints"], key_parts: ["torso", "legs", "arms", "cockpit", "shoulders", "hips", "feet", "hands", "weapons"], stages: ["Assemble the torso core and hip frame", "Mount the legs, feet, and hydraulic pistons", "Attach the arms, shoulders, and hand assemblies", "Install the head unit, cockpit, and joint covers", "Add armor plates, weapons, and wiring details", "Brush away debris and reveal the finished mech"] },
    dragon: { label: "Dragon", materials: ["scales", "wings", "claws", "horns", "eyes", "tail", "spikes"], key_parts: ["head", "neck", "body", "wings", "front legs", "hind legs", "tail", "horns", "spikes"], stages: ["Shape the head and neck over the internal armature", "Attach body segments, wings, and shoulder joints", "Mount the front legs, hind legs, and claws", "Extend the tail, horns, and back spikes", "Add scale texture, paint wash, and eye details", "Brush away dust and reveal the finished dragon figure"] }
};

const PRODUCT_RANGES = {
    10: ["0-100%"],
    30: ["0-30%", "30-75%", "75-100%"],
    60: ["0-15%", "15-35%", "35-55%", "55-75%", "75-90%", "90-100%"]
};

function productSubtypeKey(value) {
    return cleanTopicSegment(value).toLowerCase().replace(/\s+/g, "_");
}

function buildProductScenePlans(subtypeKey, duration) {
    const product = PRODUCT_SUBTYPE_DETAILS[subtypeKey] || PRODUCT_SUBTYPE_DETAILS.watch;
    const stages = product.stages;
    const groups = duration === 60
        ? stages.map(stage => [stage])
        : duration === 30
            ? [
                stages.slice(0, 2),
                stages.slice(2, 4),
                stages.slice(4, 6)
            ]
            : [stages];
    const names = duration === 60
        ? ["Core Structure", "Major Sub-Assemblies", "Sub-assembly Integration", "External Components", "Fine Details", "Final Reveal"]
        : duration === 30
            ? ["Core Assembly", "Integration", "Detail Reveal"]
            : ["Full Assembly"];
    let previousState = `All ${product.label} parts disassembled on the workbench`;

    return groups.map((actions, index) => {
        const isFinal = index === groups.length - 1;
        const currentActions = actions.filter(Boolean).join("; ");
        const futureActions = groups
            .slice(index + 1)
            .flat()
            .filter(Boolean)
            .map(sanitizeVehicleFutureAction);
        const endState = isFinal
            ? `${product.label} fully assembled alone on a clean workbench`
            : `Completed actions in this scene: ${currentActions}. The ${product.label.toLowerCase()} remains visibly incomplete, with future parts still separate, visible, and untouched on the workbench: ${futureActions.slice(0, 3).join(", ") || "no remaining actions"}.`;
        const scene = {
            scene_id: index + 1,
            name: names[index],
            start_state: previousState,
            ordered_actions: actions,
            end_state: endState,
            completion_range: PRODUCT_RANGES[duration][index],
            is_final_scene: isFinal,
            exact_stop_state: endState,
            reserved_future_actions: isFinal ? [] : futureActions,
            forbidden_future_actions: isFinal ? [] : futureActions.map(action => `Do not install later-stage parts in this scene: ${action}`),
            forbidden_changes: ["Camera angle", "Lighting direction", "Workbench surface", "No floating or teleporting parts", "Hands only"],
            input_mode: index === 0 ? InputMode.MASTER_IMAGE : InputMode.PREVIOUS_FINAL_FRAME
        };
        previousState = endState;
        return scene;
    });
}

const PRODUCT_NEGATIVE = "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, tiny workers, floating parts, teleporting parts, completed model at start, messy final workbench";

function buildProductProfile(selection = {}) {
    const subtypeKey = productSubtypeKey(selection.subtype || "Watch");
    const product = PRODUCT_SUBTYPE_DETAILS[subtypeKey] || PRODUCT_SUBTYPE_DETAILS.watch;
    const subject = cleanTopicSegment(selection.subject || product.label);
    const materials = product.materials.join(", ");
    const keyParts = product.key_parts.join(", ");
    const identityLock = `One coherent miniature ${subject}, product subtype ${product.label}, with unchanged proportions, materials (${materials}), component inventory (${keyParts}), color, camera, workbench, and lighting throughout.`;
    return {
        id: "product.assembly",
        version: "2.0.0",
        display_name: `Product Assembly (${product.label})`,
        workflow_mode: WorkflowMode.SINGLE_CLIP_FROM_MASTER,
        allowed_total_durations: [10, 30, 60],
        default_total_duration: 10,
        clip_duration_seconds: 10,
        scene_plans: {
            10: buildProductScenePlans(subtypeKey, 10),
            30: buildProductScenePlans(subtypeKey, 30),
            60: buildProductScenePlans(subtypeKey, 60)
        },
        identity_lock: identityLock,
        style_bible: {
            materials: { primary: product.materials, secondary: ["paint", "decals", "adhesive"], tools: ["tweezers", "mini screwdriver", "soft brush", "nippers"] },
            camera: { lens: "85mm macro", angle: "fixed product close-up", movement: "locked", distance: "fixed" },
            lighting: { key: "bright workshop overhead", fill: "soft bounce", mood: "clean", consistency: "locked" },
            color_palette: ["subject-specific", "material-accurate"],
            workspace: "clean wooden workbench",
            hands_rule: "giant human hands only",
            motion_rule: "precise subtype-specific assembly"
        },
        negative_prompt_base: PRODUCT_NEGATIVE,
        first_frame_prompt_factory: () => `Hyper-realistic macro photo of 100% disassembled miniature ${subject} (${product.label}) parts neatly arranged on a wooden workbench, materials: ${materials}, all key parts separated clearly: ${keyParts}, giant human hands only, no miniature people, no completed model visible, tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, scene: Master Image.`,
        scene_prompt_factory: (topic, detail, scenePlan) => {
            const currentActions = scenePlan.ordered_actions.join("; ");
            const reservedFutureActions = (scenePlan.reserved_future_actions || []).map(sanitizeVehicleFutureAction);
            const futureClause = scenePlan.is_final_scene
                ? "Final-only permissions: final brush sweep, cleanup, and final reveal are allowed only here."
                : `Prohibited future work: ${reservedFutureActions.slice(0, 3).join(", ") || "none remain"}.`;
            return `Hyper-realistic macro ASMR assembly timelapse of ${subject}, product subtype ${product.label}, giant human hands only, precise subtype-specific assembly logic, materials: ${materials}, key parts: ${keyParts}. Completion range: ${scenePlan.completion_range}. Exact input/start state: ${scenePlan.start_state}. Ordered current actions: ${currentActions}. Exact stop state: ${scenePlan.exact_stop_state}. ${futureClause} Identity Lock: ${identityLock}. No floating or teleporting parts. ${detail} Negative Prompt: ${PRODUCT_NEGATIVE}.`;
        }
    };
}

const ARCHITECTURE_SUBTYPE_DETAILS = {
    hanok: {
        label: "Hanok",
        materials: ["warm post-and-beam wood", "natural stone footings", "white hanji screens", "black giwa clay tiles"],
        features: ["rectangular timber bay plan", "deep curved eaves", "restrained dancheong on beam ends"]
    },
    temple: {
        label: "Temple",
        materials: ["natural timber", "gray clay roof tiles", "stone lanterns", "paper screens", "bronze bell details"],
        features: ["Buddhist main hall", "bracketed eaves", "meditative courtyard"]
    },
    palace: {
        label: "Palace",
        materials: ["painted dancheong timber", "glazed yonggiwa tiles", "raised stone platforms", "metal roof ornaments"],
        features: ["multi-tiered roof", "ornate gongpo brackets", "formal palace courtyard"]
    },
    seowon: {
        label: "Seowon",
        materials: ["unpainted timber", "clay tiles", "white plaster walls", "stone foundations"],
        features: ["Confucian lecture hall", "shrine and dormitory wings", "serene garden court"]
    },
    modern_hanok: {
        label: "Modern Hanok",
        materials: ["engineered timber", "modern glazing", "concrete foundation", "traditional giwa tiles", "hanji-inspired screens"],
        features: ["open floor plan", "floor-to-ceiling windows", "traditional curved roof integrated with modern volumes"]
    },
    dolmen: {
        label: "Dolmen",
        materials: ["massive weathered capstone", "supporting stones", "earth mound", "burial chamber stones"],
        features: ["prehistoric megalithic table form", "burial chamber", "weathered archaeological setting"]
    },
    villa: {
        label: "Villa",
        materials: ["light oak", "architectural concrete", "clear glazing", "stone cladding"],
        features: ["open-plan pavilion", "terraced garden", "broad modern roof planes"]
    },
    store: {
        label: "Store",
        materials: ["timber storefront", "glass display panels", "plaster walls", "metal signage frame"],
        features: ["street-facing entrance", "display windows", "compact retail interior"]
    },
    school: {
        label: "School",
        materials: ["brick", "painted concrete", "clear glazing", "steel railings"],
        features: ["classroom wing", "central entrance", "covered circulation"]
    },
    hotel: {
        label: "Hotel",
        materials: ["stone facade panels", "glass curtain wall", "warm timber accents", "metal balcony rails"],
        features: ["lobby entrance", "repeated guest-room bays", "porte-cochere"]
    },
    apartment: {
        label: "Apartment",
        materials: ["architectural concrete", "brick accents", "glass windows", "metal balcony rails"],
        features: ["repeated residential bays", "balconies", "shared entrance core"]
    },
    factory: {
        label: "Factory",
        materials: ["steel frame", "corrugated metal panels", "concrete slab", "industrial glazing"],
        features: ["wide production hall", "sawtooth or long-span roof", "loading doors"]
    },
    barn: {
        label: "Barn",
        materials: ["rough timber frame", "weathered board siding", "stone base", "metal or shingle roof"],
        features: ["large central doors", "loft opening", "simple agricultural roof"]
    }
};

function architectureSubtypeKey(value) {
    return cleanTopicSegment(value).toLowerCase().replace(/\s+/g, "_");
}

function architectureSceneDefinitions(duration) {
    if (duration === 60) {
        return [
            ["Foundation", ["mark and measure the bare footprint", "level the ground", "place foundation stones or slab elements"], "0-15%"],
            ["Walls and Openings", ["raise the primary structural frame", "build walls", "fit door and window openings"], "15-35%"],
            ["Roof Structure", ["assemble roof beams and rafters", "install subtype-appropriate roof covering"], "35-55%"],
            ["Exterior", ["close exterior surfaces", "install doors and windows", "add architectural trim"], "55-75%"],
            ["Painting and Weathering", ["apply subtype-appropriate primer or wood finish", "paint restrained accents", "add realistic weathering"], "75-90%"],
            ["Landscaping and Reveal", ["complete paths and ground cover", "add subtype-appropriate site details", "remove hands and reveal at normal cinematic speed"], "90-100%"]
        ];
    }
    return [
        ["Foundation and Walls", ["mark and measure the bare footprint", "build the foundation", "raise the structural frame", "fit wall and opening frames"], "0-35%"],
        ["Roofing and Exterior", ["assemble the roof structure", "install roof covering", "close exterior surfaces", "fit doors, windows, and trim"], "35-75%"],
        ["Painting, Landscaping, and Reveal", ["apply subtype-appropriate finishes", "add realistic weathering", "complete paths and landscaping", "remove hands and reveal at normal cinematic speed"], "75-100%"]
    ];
}

function buildArchitectureScenePlans(duration) {
    const definitions = architectureSceneDefinitions(duration);
    let previousStop = "Completely unstarted bare ground with every structural, wall, roof, finish, and landscape material separated and unused.";
    const exactStopStates = duration === 60
        ? [
            "Foundation laid and level, with wall, roof, and finish materials still separate and unused.",
            "Walls and door and window frames installed, with roofing and finish materials still separate and unused.",
            "Roof frame and roof covering installed, with exterior fixtures, paint, and landscaping materials still separate and unused.",
            "Exterior surfaces, doors, windows, and decorative details installed, with painting and landscaping materials still separate and unused.",
            "Primer, paint, and weathering applied, with all landscaping materials still separate and unused.",
            "Completed Korean architecture scene with landscaping integrated and final reveal complete.",
        ]
        : [
            "Foundation, walls, and door and window frames installed, with roof and finish materials still separate and unused.",
            "Roofing and exterior details installed, with primer, paint, weathering, and landscaping materials still separate and unused.",
            "Completed Korean architecture scene with painting, weathering, landscaping, and final reveal complete.",
        ];
    return definitions.map(([name, actions, completionRange], index) => {
        const isFinal = index === definitions.length - 1;
        const exactStop = exactStopStates[index];
        const futureActions = Array.from(new Set(
            definitions
                .slice(index + 1)
                .flatMap(([, future]) => future)
                .map(action => action.includes("reveal") ? "later site finishing stage" : action)
        ));
        const scene = {
            scene_id: index + 1,
            name,
            start_state: previousStop,
            ordered_actions: actions,
            end_state: exactStop,
            completion_range: completionRange,
            is_final_scene: isFinal,
            exact_stop_state: exactStop,
            reserved_future_actions: futureActions,
            forbidden_future_actions: futureActions.map(action => `Do not perform later-stage action: ${action}`),
            forbidden_changes: ["Do not change architecture identity, camera, lighting, scale, or site layout", "Do not advance into later construction stages early"],
            input_mode: index === 0 ? InputMode.MASTER_IMAGE : InputMode.PREVIOUS_FINAL_FRAME
        };
        previousStop = exactStop;
        return scene;
    });
}

function buildArchitectureProfile(selection = {}) {
    const subtypeKey = architectureSubtypeKey(selection.subtype || "Hanok");
    const subtype = ARCHITECTURE_SUBTYPE_DETAILS[subtypeKey] || ARCHITECTURE_SUBTYPE_DETAILS.hanok;
    const materials = subtype.materials.join(", ");
    const features = subtype.features.join(", ");
    const identityLock = `One coherent miniature ${subtype.label} with unchanged footprint, proportions, ${features}, and subtype-accurate materials (${materials}) throughout. Never transform into another building type.`;
    const negativePrompt = IMMUTABLE_NEGATIVE.replace(/\.+$/, "");

    return {
        id: "architecture.korean",
        version: "2.0.0",
        display_name: `Architecture (${subtype.label})`,
        workflow_mode: WorkflowMode.REFERENCE_FRAME_RELAY,
        allowed_total_durations: [30, 60],
        default_total_duration: 30,
        clip_duration_seconds: 10,
        scene_plans: {
            30: buildArchitectureScenePlans(30),
            60: buildArchitectureScenePlans(60)
        },
        identity_lock: identityLock,
        style_bible: {
            materials: { primary: subtype.materials, secondary: ["site ground", "landscape materials"], tools: ["miniature trowel", "chisel", "level", "brush"] },
            camera: { lens: "85mm macro", angle: "fixed 45-degree", movement: "locked", distance: "fixed" },
            lighting: { key: "cinematic studio key", fill: "soft ambient", mood: "material-accurate", consistency: "locked" },
            color_palette: subtype.materials,
            workspace: "sand or soil construction tray",
            hands_rule: "giant human hands only",
            motion_rule: "ultra fast procedural construction timelapse"
        },
        negative_prompt_base: negativePrompt,
        first_frame_prompt_factory: (topic) => `Ultra realistic macro photography, completely unstarted miniature ${subtype.label} construction site on an empty sand or soil surface, no foundation or structure built yet, every ${materials} component separated and staged outside the untouched footprint, subtype features reserved for later construction: ${features}, giant human fingers beginning only the first placement, tiny realistic construction tools, no completed building visible, 8K detail, cinematic studio lighting, shallow depth of field. Identity Lock: ${identityLock}. Topic: ${topic}.`,
        scene_prompt_factory: (topic, detail, scenePlan) => {
            const finalRules = scenePlan.is_final_scene
                ? "Only in this final scene, remove the hands, return to normal cinematic speed, and perform a cinematic zoom-out reveal."
                : `Prohibited future work: ${scenePlan.reserved_future_actions.join(", ") || "none remain"}. Stop immediately at the exact stop state. Later-stage components and materials remain separate, visible, and untouched.`;
            return `Ultra fast timelapse speed, human hands continuously constructing and moving rapidly, giant human hands only, no miniature people, multiple rapid scene cuts, cinematic macro photography. Architecture subtype: ${subtype.label}. Topic: ${topic}. Subtype materials: ${materials}. Subtype features: ${features}. Completion range: ${scenePlan.completion_range}. Exact input/start state: ${scenePlan.start_state}. Ordered current actions: ${scenePlan.ordered_actions.join("; ")}. Exact stop state: ${scenePlan.exact_stop_state}. ${finalRules} Maintain the exact same building identity, camera angle, scale, lighting direction, ground tray, and object placement. ${detail} Negative Prompt: ${negativePrompt}.`;
        }
    };
}

const COOKING_DISHES = {
    kimchi_jjigae: { name: "Kimchi Jjigae", ingredients: "kimchi, pork belly, tofu, green onion, gochujang, garlic", cookware: "miniature earthenware pot (ttukbaegi)", heat: "tea light candle under the pot", garnish: "sesame oil and sliced green onion", serveware: "miniature black stone bowl" },
    bibimbap: { name: "Bibimbap", ingredients: "rice, spinach, bean sprouts, carrot, zucchini, mushrooms, beef, egg, gochujang", cookware: "miniature stone bowl", heat: "tea light candle under the bowl", garnish: "sesame oil, sesame seeds, and fried egg", serveware: "the same miniature stone bowl" },
    bulgogi: { name: "Bulgogi", ingredients: "thin beef, soy sauce, pear, onion, garlic, green onion, sesame oil", cookware: "miniature cast-iron grill pan", heat: "tea light candle under the pan", garnish: "sesame seeds and green onion", serveware: "miniature white porcelain plate" },
    jjajangmyeon: { name: "Jjajangmyeon", ingredients: "noodles, chunjang, pork, onion, zucchini, potato, cabbage", cookware: "miniature wok", heat: "tea light candle under the wok", garnish: "cucumber julienne", serveware: "miniature black noodle bowl" },
    samgyeopsal: { name: "Samgyeopsal (Grilled Pork Belly)", ingredients: "pork belly, garlic, chili, ssamjang, lettuce, perilla leaves, kimchi", cookware: "miniature tabletop grill", heat: "tea light candle under the grill", garnish: "grilled garlic and chili", serveware: "miniature grill plate with lettuce wraps" },
    dakgalbi: { name: "Dakgalbi (Spicy Stir-fried Chicken)", ingredients: "chicken thigh, gochujang, gochugaru, sweet potato, cabbage, perilla, rice cakes", cookware: "miniature wide iron pan", heat: "tea light candle under the pan", garnish: "melted cheese and perilla leaves", serveware: "the same miniature iron pan" }
};

const COOKING_NEGATIVE = "text, subtitle, caption, watermark, logo, burnt-in text, overlay text, bad anatomy, deformed hands, blurry, miniature people, tiny chef, small person, shaky camera, camera shake, music, voice, narration, dialogue, talking";
const COOKING_PREP_STOP = "All ingredients are washed, cut, measured, and arranged in miniature prep bowls, ready for cooking; no heat has been applied.";
const COOKING_COOK_STOP = "The dish is fully cooked in its cookware with realistic steam visible, while every later serving component remains completely untouched.";
const COOKING_FINAL_STOP = "The finished dish is plated in its serveware, garnished, steaming naturally, and held in the final cinematic hero reveal.";

function buildCookingScenePlans(dish) {
    const definitions = [
        ["Preparation", `raw ${dish.ingredients} on the wooden cutting board; no cutting or heat yet`, ["wash and sort ingredients", "peel and cut ingredients precisely", "measure sauces and seasonings", "arrange everything in miniature prep bowls"], COOKING_PREP_STOP],
        ["Cooking", COOKING_PREP_STOP, [`transfer prepared ingredients into ${dish.cookware}`, `cook over ${dish.heat}`, "show realistic sizzling, browning, bubbling, reduction, and steam", "finish cooking while all serving components remain untouched"], COOKING_COOK_STOP],
        ["Finishing and Plating", COOKING_COOK_STOP, [`serve into ${dish.serveware}`, `add ${dish.garnish}`, "show natural steam and detailed food texture", "finish with a cinematic hero reveal"], COOKING_FINAL_STOP]
    ];
    return definitions.map(([name, start, actions, stop], index) => ({
        scene_id: index + 1,
        name,
        start_state: start,
        ordered_actions: actions,
        end_state: stop,
        completion_range: ["0-33%", "33-67%", "67-100%"][index],
        is_final_scene: index === 2,
        exact_stop_state: stop,
        reserved_future_actions: index === 0
            ? ["later heat-application stage", "later serving stage"]
            : index === 1
                ? ["later serving stage"]
                : [],
        forbidden_future_actions: index === 2 ? [] : ["Do not plate, garnish, show a hero reveal, or display a final plated result in this scene"],
        forbidden_changes: ["same kitchen", "same cutting board", "same cookware", "same lighting", "same fixed camera", "hands only"],
        input_mode: index === 0 ? InputMode.MASTER_IMAGE : InputMode.PREVIOUS_FINAL_FRAME
    }));
}

function buildCookingProfile(selection = {}) {
    const dish = COOKING_DISHES[selection.dish_key] || COOKING_DISHES.kimchi_jjigae;
    return {
        id: "cooking.miniature",
        version: "2.0.0",
        display_name: `Miniature Cooking (${dish.name})`,
        workflow_mode: WorkflowMode.REFERENCE_FRAME_RELAY,
        allowed_total_durations: [30],
        default_total_duration: 30,
        clip_duration_seconds: 10,
        scene_plans: { 30: buildCookingScenePlans(dish) },
        identity_lock: `One continuous miniature ${dish.name} cooking station with the same wooden cutting board, ${dish.cookware}, ${dish.heat}, kitchen, tools, lighting, and fixed 100mm macro camera throughout.`,
        style_bible: {
            materials: { primary: dish.ingredients.split(", "), secondary: [dish.cookware, dish.serveware], tools: ["miniature knife", "ladle", "spatula", "chopsticks"] },
            camera: { lens: "100mm macro", angle: "extreme close-up", movement: "soft focus pulls only", distance: "fixed" },
            lighting: { key: "soft kitchen light", fill: "warm heat-source glow", mood: "appetizing", consistency: "locked" },
            color_palette: ["natural ingredient colors", "steam white", "oil sheen"],
            workspace: "natural wooden cutting board in a softly blurred modern kitchen",
            hands_rule: "giant human hands only",
            motion_rule: "realistic cooking physics with ASMR only"
        },
        negative_prompt_base: COOKING_NEGATIVE,
        first_frame_prompt_factory: () => `Ultra-realistic 8K HDR macro photography, 100mm macro lens, extreme close-up. Giant human hands only, no miniature people or tiny chef, raw ingredients for ${dish.name}: ${dish.ingredients}, neatly separated on a natural wooden cutting board, ${dish.cookware}, ${dish.heat}, miniature utensils visible but unused, no cutting and no heat yet, identical kitchen, lighting, board, tools, and camera carried into every scene. No voices, no music, only satisfying ASMR sounds. Negative Prompt: ${COOKING_NEGATIVE}.`,
        scene_prompt_factory: (topic, detail, scenePlan) => {
            const finalRule = scenePlan.is_final_scene
                ? `Ladle ${dish.name} into ${dish.serveware}, add ${dish.garnish}, then allow the plated steam-filled cinematic hero reveal.`
                : "Do not advance into any later stage. Stop at the exact stop state. Later-stage components and materials remain separate, visible, and untouched.";
            return `Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, seamless continuation from the exact previous state. Giant human hands only, no miniature people, same kitchen, same natural wooden cutting board, same ${dish.cookware}, same lighting, same fixed camera. Dish: ${dish.name}. Exact input/start state: ${scenePlan.start_state}. This clip covers only ${scenePlan.name}: ${scenePlan.ordered_actions.join("; ")}. Use realistic cooking physics and logical order without skipped steps. Exact stop state: ${scenePlan.exact_stop_state}. ${finalRule} No voices, no music, only dish-appropriate ASMR sounds. ${detail} Negative Prompt: ${COOKING_NEGATIVE}.`;
        }
    };
}

function buildHomeDecorProfile(selection = {}) {
    const materials = cleanTopicSegment(selection.materials || "hanji paper, recycled materials");
    const finalObject = cleanTopicSegment(selection.final_object || "Korean decorative object");
    const narration = cleanTopicSegment(selection.korean_narration);
    const ideaName = cleanTopicSegment(selection.idea_name || finalObject);
    const negativePrompt = IMMUTABLE_NEGATIVE.replace(/\.+$/, "");
    return {
        id: "home_decor.diy",
        version: "2.0.0",
        display_name: "Home Decor DIY (Korean Craft)",
        workflow_mode: WorkflowMode.SINGLE_CLIP_FROM_MASTER,
        allowed_total_durations: [10],
        default_total_duration: 10,
        clip_duration_seconds: 10,
        scene_plans: {
            10: [{
                scene_id: 1,
                name: "DIY Craft Tutorial",
                start_state: "Raw low-cost craft materials and tools only on a clean table; no finished object visible.",
                ordered_actions: ["Opening Hook", "Introducing Materials", "Building Begins", "Mid-Build Sequence", "Detail Showcase", "Final Reveal"],
                end_state: `Finished ${finalObject} revealed on the clean desk.`,
                completion_range: "0-100%",
                is_final_scene: true,
                exact_stop_state: `Finished ${finalObject} revealed on the clean desk.`,
                reserved_future_actions: [],
                forbidden_future_actions: [],
                forbidden_changes: ["hands only", "fixed top-down camera", "bright studio lighting", "no music"],
                input_mode: InputMode.MASTER_IMAGE
            }]
        },
        identity_lock: `One coherent ${ideaName} transforming ${materials} into ${finalObject} in one continuous 10-second craft workflow.`,
        style_bible: {
            materials: { primary: materials.split(",").map(item => item.trim()).filter(Boolean), secondary: ["Korean craft accents"], tools: ["scissors", "craft knife", "tweezers", "glue"] },
            camera: { lens: "macro", angle: "fixed clean top-down 45-degree", movement: "locked", distance: "fixed" },
            lighting: { key: "bright even studio", fill: "soft", mood: "pastel and jewel-tone", consistency: "locked" },
            color_palette: ["pastel", "jewel tone"],
            workspace: "clean craft table",
            hands_rule: "hands only",
            motion_rule: "continuous satisfying craft ASMR"
        },
        negative_prompt_base: negativePrompt,
        first_frame_prompt_factory: () => `Ultra-realistic 8K macro photo of raw ${materials} neatly arranged on a clean craft table, giant human hands only, no miniature people, no completed ${finalObject} visible, scissors, craft knife, cutting mat, ruler, tweezers, and glue laid out clearly, bright even studio lighting, pastel and jewel-tone palette, fixed clean top-down perspective, scene: Master Image.`,
        scene_prompt_factory: () => `Single 10-second continuous clip, not split into multiple scenes. [Opening Hook: close-up of discarded materials and the Korean narration begins immediately], [Introducing Materials: hands present ${materials}], [Building Begins: hands cut, fold, bend, and attach the base pieces], [Mid-Build Sequence: a satisfying repeated assembly technique transforms the materials], [Detail Showcase: hands add precise Korean-inspired decorative finishing details], [Final Reveal: zoom out to the finished ${finalObject} on a clean desk]. tactile mixed-media papercraft and craft ASMR style, specifically featuring 3D layered paper-cutting, origami folding, and organic material collage captured from a clean, top-down perspective. Macro close-up, hands only, no face or body, fixed top-down 45-degree angle, steady camera, bright even studio lighting, shallow depth of field, clean background, pastel and jewel-tone palette, 9:16 vertical, photorealistic 8K. Korean female voiceover narrates continuously without pause: "${narration}". No background music, only light craft ASMR sounds. Negative Prompt: ${negativePrompt}.`
    };
}

export const DEFAULT_PROFILES = {
    'architecture.korean': {
        id: 'architecture.korean',
        version: '2.0.0',
        display_name: 'Architecture (Korean Hanok)',
        workflow_mode: WorkflowMode.REFERENCE_FRAME_RELAY,
        allowed_total_durations: [30, 60],
        default_total_duration: 30,
        clip_duration_seconds: 10,
        scene_plans: {
            30: buildArchitectureScenePlans(30),
            60: buildArchitectureScenePlans(60)
        },
        identity_lock: "One coherent single-story Korean hanok with a rectangular timber bay plan, natural stone footings, warm post-and-beam woodwork, white hanji doors and windows, deep curved black giwa eaves, and restrained dancheong only on appropriate beam ends and eaves. Never a stone castle, Gothic church, European cottage, pagoda tower, palace tower, or fantasy fortress.",
        style_bible: {
            materials: { primary: ["wood", "stone"], secondary: ["moss"], tools: ["chisel", "trowel"] },
            camera: { lens: "85mm", angle: "45", movement: "locked", distance: "fixed" },
            lighting: { key: "soft daylight", fill: "ambient", mood: "warm", consistency: "locked" },
            color_palette: ["warm wood", "terracotta", "stone gray"],
            workspace: "compacted earth tray",
            hands_rule: "giant human hands only",
            motion_rule: "rapid procedural timelapse"
        },
        first_frame_prompt_factory: buildArchitectureProfile({ subtype: "Hanok" }).first_frame_prompt_factory,
        scene_prompt_factory: buildArchitectureProfile({ subtype: "Hanok" }).scene_prompt_factory,
        resolve_selection: buildArchitectureProfile
    },
    // Vehicle Assembly - 10 Categories (car, motorcycle, airplane, boat, agricultural, helicopter, construction, spaceship, tank, bicycle)
// Generated from reference prompts - each category has specific identity_lock, style_bible, scene_plans, prompts
    'vehicle.assembly': (() => {
        // This IIFE runs at module load time, but vehicle data is loaded async.
        // We return a function that builds the profile once data is available.
        let _cachedProfile = null;

    async function buildVehicleProfile(data, category, modelName) {
        const cat = category;
        const name = modelName || (data.models[cat]?.[0] || cat);
        const scenePlans30 = buildVehicleScenePlans(data, cat, 30);
        const scenePlans60 = buildVehicleScenePlans(data, cat, 60);

        return {
            id: 'vehicle.assembly',
            version: '2.0.0',
            display_name: `Vehicle Assembly: ${name}`,
            workflow_mode: WorkflowMode.REFERENCE_FRAME_RELAY,
            allowed_total_durations: [30, 60],
            default_total_duration: 30,
            clip_duration_seconds: 10,
            _subtype: cat,
            _model_name: name,
            scene_plans: {
                30: scenePlans30,
                60: scenePlans60,
            },
            identity_lock: data.identityLocks[cat] || data.identityLocks.car,
            style_bible: data.styleBibles[cat] || data.styleBibles.car,
            negative_prompt_base: data.negativeBase,
            template_exclusions: ["completed model at start", "floating parts", "teleporting parts"],
            first_frame_prompt_factory: (topic, detail) => `Hyper-realistic macro photo of 100% disassembled miniature ${name} model parts neatly arranged on a wooden workbench, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, no completed model visible, chassis/body/frame components, ${data.keyParts[cat] || data.keyParts.car} separated clearly, tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, ${name}, scene: Master Image.`,
            scene_prompt_factory: (topic, detail, scenePlan) => {
                const sceneName = scenePlan.name;
                const identityLock = data.identityLocks[cat] || data.identityLocks.car;
                const negativePrompt = (data.negativeBase || IMMUTABLE_NEGATIVE).replace(/\.+$/, "");
                const openLine = `hyper-realistic macro ASMR assembly timelapse, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, precise mechanical assembly logic, tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, 8K product quality, bright workshop lighting, ${name.toLowerCase()}, scene: ${sceneName}.`;
                const inputLine = `Exact input/start state: ${scenePlan.start_state}.`;
                const currentActions = scenePlan.ordered_actions.filter(Boolean);
                const actionLine = currentActions.length ? `This clip covers only ${scenePlan.name}. ${summarizeVehicleActions(currentActions)}.` : `This clip covers only ${scenePlan.name}.`;
                const lockLine = `Identity Lock: ${identityLock}.`;
                const exactStopLine = `Exact stop state: ${scenePlan.exact_stop_state}.`;
                const reservedFutureActions = sanitizeVehicleFutureActions(scenePlan.reserved_future_actions || []);
                const reservedFutureLine = reservedFutureActions.length
                    ? `Reserved future actions and parts, kept for a later finishing stage: ${joinVisibleParts(reservedFutureActions)}.`
                    : "Reserved future actions and parts: none remain.";
                const continuityLine = `Maintain the same camera angle, scale, lighting direction, and workbench layout throughout, with hands only and no floating or teleporting parts.`;
                const stopBoundaryLine = scenePlan.is_final_scene
                    ? "Allow the final polish, cleanup, and hero reveal only in this last scene."
                    : `Stop immediately when ${currentActions[currentActions.length - 1]} is finished. Do not proceed beyond this stop state.`;
                const sceneRules = scenePlan.is_final_scene
                    ? "Allow the final polish, cleanup, and hero reveal only in this last scene."
                    : "Keep later finishing work out of this scene.";
                const endingLine = scenePlan.is_final_scene
                    ? "By the end, the fully assembled model sits alone on a clean workbench, ready for the final reveal."
                    : `End on the exact stop state with future parts still separate on the workbench.`;
                const incompleteLine = scenePlan.is_final_scene
                    ? "The model may reach the fully assembled state in this scene."
                    : "The model must remain visibly incomplete.";
                return `${openLine} ${inputLine} ${actionLine} ${lockLine} ${exactStopLine} ${reservedFutureLine} ${stopBoundaryLine} ${incompleteLine} ${sceneRules} ${continuityLine} ${endingLine} Negative Prompt: ${negativePrompt}.`;
            },
        };
    }

    // Return an async function that lazy-loads vehicle data and builds the profile
    return async function getVehicleProfile(category = 'car', modelName = null) {
        if (!_cachedProfile) {
            const data = await loadVehicleData();
            _cachedProfile = await buildVehicleProfile(data, category, modelName);
        }
        // If different category/model requested, rebuild
        if (_cachedProfile._subtype !== category || _cachedProfile._model_name !== (modelName || (await loadVehicleData()).models[category]?.[0] || category)) {
            const data = await loadVehicleData();
            _cachedProfile = await buildVehicleProfile(data, category, modelName);
        }
        return _cachedProfile;
    };
})(),
    "product.assembly": {
        ...buildProductProfile(getDefaultSelectionValues("product.assembly")),
        resolve_selection: buildProductProfile
    },
    'home_decor.diy': {
        id: 'home_decor.diy',
        version: '2.0.0',
        display_name: 'Home Decor DIY (Korean Craft)',
        workflow_mode: WorkflowMode.SINGLE_CLIP_FROM_MASTER,
        allowed_total_durations: [10],
        default_total_duration: 10,
        clip_duration_seconds: 10,
        scene_plans: {
            10: [
                { scene_id: 1, name: "Hook, Build, Detail, and Reveal", start_state: "raw low-cost and Korean craft materials on a clean desk", ordered_actions: ["opening hook and immediate first cut", "introduce Korean materials", "cut and fold the base", "repeat the satisfying assembly technique", "add decorative details", "reveal the finished decor object"], end_state: "finished Korean decor object revealed", forbidden_changes: ["camera", "lighting", "hands only"], input_mode: InputMode.MASTER_IMAGE }
            ]
        },
        identity_lock: "One coherent Korean traditional craft piece using hanji paper, jogakbo patchwork, jadeok mother-of-pearl, myeongju silk, and maedeup knots. Pastel/jewel-tone palette, tactile mixed-media papercraft aesthetic. Never plastic factory goods, modern synthetic materials, or non-Korean craft styles.",
        style_bible: {
            materials: { primary: ["hanji paper", "jogakbo fabric"], secondary: ["jadeok (mother-of-pearl)", "myeongju silk", "wire"], tools: ["craft knife", "tweezers", "fine brush", "needle"] },
            camera: { lens: "100mm macro", angle: "top-down 45°", movement: "locked", distance: "fixed" },
            lighting: { key: "bright even studio", fill: "soft", mood: "warm pastel", consistency: "locked" },
            color_palette: ["pastel pink", "sage green", "cream", "pearl white", "soft gold"],
            workspace: "clean craft desk",
            hands_rule: "giant human hands only",
            motion_rule: "satisfying ASMR craft sequence"
        },
        first_frame_prompt_factory: buildHomeDecorProfile(getDefaultSelectionValues("home_decor.diy")).first_frame_prompt_factory,
        scene_prompt_factory: buildHomeDecorProfile(getDefaultSelectionValues("home_decor.diy")).scene_prompt_factory,
        resolve_selection: buildHomeDecorProfile
    },
    'cooking.miniature': {
        id: 'cooking.miniature',
        version: '2.0.0',
        display_name: 'Miniature Cooking',
        workflow_mode: WorkflowMode.REFERENCE_FRAME_RELAY,
        allowed_total_durations: [30],
        default_total_duration: 30,
        clip_duration_seconds: 10,
        scene_plans: {
            30: buildCookingScenePlans(COOKING_DISHES.kimchi_jjigae)
        },
        identity_lock: "Ultra-realistic 8K HDR miniature cooking on natural wooden cutting board, clean modern kitchen blurred background. Giant human hands only, no miniature people, no tiny chef. 100mm macro lens, extreme close-up, soft focus pulls, identical kitchen/lighting/tools across all scenes. Satisfying ASMR sounds only (chop, sizzle, boil, pour), no voices, no music, no shaky camera.",
        style_bible: {
            materials: { primary: ["food ingredients"], secondary: ["garnishes"], tools: ["miniature knife", "miniature pot/ttukbaegi", "miniature ladle", "chopsticks"] },
            camera: { lens: "100mm macro", angle: "extreme close-up", movement: "locked", distance: "fixed" },
            lighting: { key: "soft natural", fill: "warm", mood: "appetizing", consistency: "locked" },
            color_palette: ["ingredient-natural", "steam-white", "oil-glisten"],
            workspace: "natural wooden cutting board, miniature cookware",
            hands_rule: "giant human hands only",
            motion_rule: "ASMR cooking sequence, realistic physics"
        },
        first_frame_prompt_factory: buildCookingProfile({ dish_key: "kimchi_jjigae" }).first_frame_prompt_factory,
        scene_prompt_factory: buildCookingProfile({ dish_key: "kimchi_jjigae" }).scene_prompt_factory,
        resolve_selection: buildCookingProfile
    }
};
