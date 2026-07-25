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
        scene_plans: {
            30: [
                { scene_id: 1, name: "Foundation and Walls", start_state: "compacted earth, stone footings, sill beams, columns, hanji frames", ordered_actions: ["place stone footings", "seat sill beams", "raise columns", "fit hanji frames"], end_state: "single-story timber wall frame complete", forbidden_changes: InputMode.MASTER_IMAGE, input_mode: InputMode.MASTER_IMAGE },
                { scene_id: 2, name: "Roofing and Exterior", start_state: "Scene 1 final frame", ordered_actions: ["crossbeams", "purlins", "rafters", "eave supports", "giwa tiles", "hanji doors/windows"], end_state: "roof and exterior complete", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 3, name: "Painting, Landscaping, and Reveal", start_state: "Scene 2 final frame", ordered_actions: ["wood finish", "dancheong on beam ends", "stone path", "low wall", "moss", "grass", "small pine", "remove tools"], end_state: "coherent hanok revealed", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME }
            ],
            60: [
                { scene_id: 1, name: "Foundation", start_state: "compacted earth", ordered_actions: ["tension guide strings", "place natural stone footings", "level footings", "seat sill beams"], end_state: "stone foundation and sill beams complete", forbidden_changes: InputMode.MASTER_IMAGE, input_mode: InputMode.MASTER_IMAGE },
                { scene_id: 2, name: "Wall and Windows", start_state: "Scene 1 final frame", ordered_actions: ["raise columns", "mortise-and-tenon joints", "connect beams", "fit hanji door/window frames"], end_state: "single-story timber wall frame complete", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 3, name: "Roofing", start_state: "Scene 2 final frame", ordered_actions: ["crossbeams", "purlins", "rafters", "eave supports", "giwa tiles row by row"], end_state: "traditional roof complete", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 4, name: "Exterior Finishing", start_state: "Scene 3 final frame", ordered_actions: ["install hanji doors/windows", "finish exposed timber", "add wooden trim", "remove debris"], end_state: "roof and exterior complete", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 5, name: "Painting and Weathering", start_state: "Scene 4 final frame", ordered_actions: ["protective wood finish", "restrained dancheong on beam ends", "preserve hanji and giwa colors"], end_state: "painted hanok shell complete", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 6, name: "Landscaping and Reveal", start_state: "Scene 5 final frame", ordered_actions: ["stone path", "low wall", "moss", "grass", "small pine", "remove tools"], end_state: "coherent hanok revealed", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME }
            ]
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
        first_frame_prompt_factory: (topic, detail) => `Ultra realistic macro photography of a completely unstarted miniature Korean hanok construction site, an untouched compacted-earth tray with an empty rectangular footprint and taut guide strings, every natural stone footing, timber sill beam, timber column, white hanji frame, rafter, and black giwa roof tile still separate and neatly staged outside the footprint, no foundation or wall already built, no completed hanok visible, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, giant human fingers beginning the very first action by lifting one natural stone footing toward its marked position, tiny traditional measuring and woodworking tools, locked 85mm-equivalent macro camera, fixed 45-degree angle, unchanged subject scale and framing, 8K detail, soft daylight from camera-left, warm rim light, natural shadows, unchanged through every scene, shallow depth of field, Identity Lock: One coherent single-story Korean hanok with a rectangular timber bay plan, natural stone footings, warm post-and-beam woodwork, white hanji doors and windows, deep curved black giwa eaves, and restrained dancheong only on appropriate beam ends and eaves. Never a stone castle, Gothic church, European cottage, pagoda tower, palace tower, or fantasy fortress., ${topic} | ${detail}, scene: Foundation and Walls.`
    },
    // Vehicle Assembly - 10 Categories (car, motorcycle, airplane, boat, agricultural, helicopter, construction, spaceship, tank, bicycle)
// Generated from reference prompts - each category has specific identity_lock, style_bible, scene_plans, prompts
'vehicle.assembly': (() => {
    const categories = ['car', 'motorcycle', 'airplane', 'boat', 'agricultural', 'helicopter', 'construction', 'spaceship', 'tank', 'bicycle'];
    const models = VEHICLE_MODELS;
    const identityLocks = VEHICLE_IDENTITY_LOCKS;
    const styleBibles = VEHICLE_STYLE_BIBLES;
    const keyParts = VEHICLE_KEY_PARTS;
    const assemblySteps = VEHICLE_ASSEMBLY_STEPS;
    const scenePlans30 = VEHICLE_SCENE_PLANS_30;
    const scenePlans60 = VEHICLE_SCENE_PLANS_60;
    const steps60 = VEHICLE_ASSEMBLY_STEPS_60;

    function buildVehicleProfile(category, modelName) {
        const cat = category;
        const name = modelName || (models[cat]?.[0] || cat);
        const plan30 = scenePlans30[cat] || [];
        const plan60 = scenePlans60[cat] || [];

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
                30: plan30,
                60: plan60,
            },
            identity_lock: identityLocks[cat] || VEHICLE_IDENTITY_LOCKS.car,
            style_bible: styleBibles[cat] || VEHICLE_STYLE_BIBLES.car,
            negative_prompt_base: VEHICLE_NEGATIVE_BASE,
            template_exclusions: ["completed model at start", "floating parts", "teleporting parts"],
            first_frame_prompt_factory: (topic, detail) => `Hyper-realistic macro photo of 100% disassembled miniature ${name} model parts neatly arranged on a wooden workbench, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, no completed model visible, chassis/body/frame components, ${keyParts[cat] || keyParts.car} separated clearly, tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, 8K product photo quality, bright workshop lighting, ${name}, scene: Master Image.`,
            scene_prompt_factory: (topic, detail, scenePlan, sceneIdx) => {
                const sceneName = scenePlan.name;
                const step = assemblySteps[cat]?.[sceneIdx - 1] || `assembly step ${sceneIdx}`;
                return `hyper-realistic macro ASMR assembly timelapse, giant human hands only, no miniature people, no small people, no tiny workers, no human figures, no characters, precise mechanical assembly logic, 100% disassembled parts to fully assembled model, no floating or teleporting parts, parts attach in realistic order and disappear from workbench as installed, final step leaves only the fully assembled model on a clean workbench, tweezers, mini screwdriver, soft brush, nippers, 85mm lens, shallow depth of field, 8K product quality, bright workshop lighting, ${name.toLowerCase()}, scene: ${sceneName}. ${step}. As parts are attached, they logically disappear from the workbench. By the final step, the workspace is completely clean, leaving only the fully assembled model. Negative Prompt: ${VEHICLE_NEGATIVE_BASE}.`;
            },
        };
    }

    // Default to car
    return buildVehicleProfile('car', models.car?.[0] || 'Porsche 911');
})(),
    'home_decor.diy': {
        id: 'home_decor.diy',
        version: '2.0.0',
        display_name: 'Home Decor DIY (Korean Craft)',
        workflow_mode: WorkflowMode.REFERENCE_FRAME_RELAY,
        allowed_total_durations: [30, 60],
        default_total_duration: 30,
        clip_duration_seconds: 10,
        scene_plans: {
            30: [
                { scene_id: 1, name: "Material Prep and Base Structure", start_state: "raw Korean materials on clean desk", ordered_actions: ["cut hanji paper to size", "fold jogakbo pieces", "prepare jadeok (mother-of-pearl) inlays", "build wire/base frame", "arrange all elements"], end_state: "prepared materials and base frame ready", forbidden_changes: InputMode.MASTER_IMAGE, input_mode: InputMode.MASTER_IMAGE },
                { scene_id: 2, name: "Assembly and Layering", start_state: "Scene 1 final frame", ordered_actions: ["glue hanji layers onto frame", "attach jogakbo patches", "inlay jadeok pieces", "wrap with myeongju silk thread", "secure all joints"], end_state: "assembled craft structure complete", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 3, name: "Finishing Details and Reveal", start_state: "Scene 2 final frame", ordered_actions: ["apply protective coating", "add decorative knots", "trim excess material", "attach hanging hardware", "remove tools, soft lighting hero shot"], end_state: "finished Korean decor piece revealed", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME }
            ],
            60: [
                { scene_id: 1, name: "Material Selection and Cutting", start_state: "raw Korean materials on clean desk", ordered_actions: ["select hanji paper sheets", "measure and mark dimensions", "precision cut with craft knife", "prepare jogakbo fabric scraps", "sort jadeok pieces by size"], end_state: "all materials precisely cut and sorted", forbidden_changes: InputMode.MASTER_IMAGE, input_mode: InputMode.MASTER_IMAGE },
                { scene_id: 2, name: "Base Frame Construction", start_state: "Scene 1 final frame", ordered_actions: ["bend wire into base shape", "reinforce joints with solder", "wrap frame with myeongju thread", "create mounting points", "verify structural integrity"], end_state: "sturdy wire base frame complete", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 3, name: "Hanji Layering", start_state: "Scene 2 final frame", ordered_actions: ["brush adhesive onto frame", "apply first hanji layer", "smooth out air bubbles", "add second colored hanji layer", "create translucent window panels"], end_state: "hanji skin fully applied to frame", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 4, name: "Jogakbo and Jadeok Inlay", start_state: "Scene 3 final frame", ordered_actions: ["arrange jogakbo pattern", "stitch patchwork onto surface", "glue jadeok inlay pieces", "press and set each piece", "trim excess fabric edges"], end_state: "decorative inlay complete", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 5, name: "Traditional Knotting and Details", start_state: "Scene 4 final frame", ordered_actions: ["tie maedeup decorative knots", "attach norigae tassel", "add metal ornament accents", "seal with natural lacquer", "polish jadeok surfaces"], end_state: "all traditional details applied", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 6, name: "Final Finish and Reveal", start_state: "Scene 5 final frame", ordered_actions: ["apply UV protective spray", "attach hanging loop or stand", "final dust removal with soft brush", "hero lighting setup", "remove all tools, cinematic reveal"], end_state: "finished Korean decor piece revealed", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME }
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
        first_frame_prompt_factory: (topic, detail) => `Ultra-realistic macro photography, clean top-down craft desk, giant human hands only, no miniature people, assorted Korean traditional materials neatly arranged: hanji paper sheets in pastel tones, jogakbo silk scraps, jadeok mother-of-pearl pieces, myeongju silk thread spools, copper wire, precision craft tools (knife, tweezers, brush, needle), untouched workspace, 100mm macro lens, shallow depth of field, 8K detail, bright even studio lighting, Identity Lock: One coherent Korean traditional craft piece using hanji paper, jogakbo patchwork, jadeok mother-of-pearl, myeongju silk, and maedeup knots. Pastel/jewel-tone palette, tactile mixed-media papercraft aesthetic., ${topic} | ${detail}, scene: Material Selection and Cutting.`
    },
    'cooking.miniature': {
        id: 'cooking.miniature',
        version: '2.0.0',
        display_name: 'Miniature Cooking',
        workflow_mode: WorkflowMode.REFERENCE_FRAME_RELAY,
        allowed_total_durations: [30, 60],
        default_total_duration: 30,
        clip_duration_seconds: 10,
        scene_plans: {
            30: [
                { scene_id: 1, name: "Preparation (Ingredients)", start_state: "raw ingredients on wooden cutting board", ordered_actions: ["wash and peel vegetables", "dice aromatics (onion, garlic, ginger)", "slice protein into bite pieces", "measure sauces and seasonings", "arrange in mini prep bowls"], end_state: "all ingredients prepped and organized", forbidden_changes: InputMode.MASTER_IMAGE, input_mode: InputMode.MASTER_IMAGE },
                { scene_id: 2, name: "Cooking (Heat Application)", start_state: "Scene 1 final frame", ordered_actions: ["heat oil in miniature pot", "sauté aromatics until fragrant", "add protein and sear", "pour in liquid base", "simmer with lid"], end_state: "dish cooking, steam rising", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 3, name: "Finishing and Plating", start_state: "Scene 2 final frame", ordered_actions: ["taste and adjust seasoning", "add finishing oil or garnish", "ladle into miniature bowl", "arrange toppings artistically", "hero shot with rising steam"], end_state: "finished dish plated and revealed", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME }
            ],
            60: [
                { scene_id: 1, name: "Ingredient Prep - Vegetables", start_state: "raw ingredients on wooden cutting board", ordered_actions: ["wash all produce thoroughly", "peel onion, garlic, ginger", "dice onion into fine mince", "slice garlic paper-thin", "julienne ginger and scallions"], end_state: "all vegetables prepped in mini bowls", forbidden_changes: InputMode.MASTER_IMAGE, input_mode: InputMode.MASTER_IMAGE },
                { scene_id: 2, name: "Ingredient Prep - Protein & Sauces", start_state: "Scene 1 final frame", ordered_actions: ["slice protein against grain", "marinate with light seasoning", "measure soy sauce, oil, spices", "prepare broth or water base", "arrange all mise en place"], end_state: "complete mise en place ready", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 3, name: "Cooking - Aromatics and Sear", start_state: "Scene 2 final frame", ordered_actions: ["heat miniature pot with oil", "sauté onion until translucent", "add garlic and ginger", "stir-fry until fragrant", "add protein and sear all sides"], end_state: "aromatics cooked, protein seared", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 4, name: "Cooking - Simmer and Develop", start_state: "Scene 3 final frame", ordered_actions: ["deglaze with liquid base", "add measured seasonings", "bring to gentle boil", "reduce heat and simmer", "skim impurities, cover partially"], end_state: "flavors melded, sauce reduced", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 5, name: "Finishing - Texture and Balance", start_state: "Scene 4 final frame", ordered_actions: ["add quick-cook vegetables", "adjust salt, acid, sweet", "thicken sauce if needed", "finish with sesame oil", "rest briefly off heat"], end_state: "perfectly balanced finished dish", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME },
                { scene_id: 6, name: "Plating and Hero Reveal", start_state: "Scene 5 final frame", ordered_actions: ["ladle into miniature stone bowl", "arrange protein visibly on top", "sprinkle scallions and seeds", "drizzle finishing oil", "macro hero shot with rising steam"], end_state: "finished dish plated and revealed", forbidden_changes: InputMode.PREVIOUS_FINAL_FRAME, input_mode: InputMode.PREVIOUS_FINAL_FRAME }
            ]
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
        first_frame_prompt_factory: (topic, detail) => `Ultra-realistic 8K HDR macro cinematography, 100mm macro lens, extreme close-up, soft focus pulls. Giant human hands only, no miniature people, no tiny chef, fresh raw ingredients for ${topic} on a natural wooden cutting board in a clean modern kitchen with softly blurred background. Whole vegetables, protein, aromatics neatly separated, miniature prep bowls ready, miniature knife poised to begin, identical kitchen lighting and camera for all scenes, satisfying ASMR sounds only (knife chopping, water drips), no voices no music. Identity Lock: Ultra-realistic miniature cooking on natural wooden cutting board, clean modern kitchen blurred background. Giant human hands only. 100mm macro lens, identical kitchen/lighting/tools across all scenes., ${topic} | ${detail}, scene: Preparation.`
    }
};