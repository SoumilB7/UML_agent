/**
 * RL Action Tracking Utility
 * Tracks user actions for reinforcement learning purposes
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const RL_ACTION_ENDPOINT = `${API_URL}/rl/action`;

export type ActionType =
  | 'image_copy'
  | 'variation_selection'
  | 'variation_hover'
  | 'tab_away'
  | 'new_button'
  | 'mermaid_copy'
  | 'prompt_update'
  | 'feedback'
  | 'diagram_generated'
  | 'diagram_edited'
  | 'zoom'
  | 'pan';

export interface RLActionMetadata {
  [key: string]: any;
}

export interface RLActionPayload {
  action_type: ActionType;
  timestamp?: string;
  metadata?: RLActionMetadata;
  rating?: number;
  feedback_text?: string;
  prompt?: string;
  previous_prompt?: string;
  variation_index?: number;
  mermaid_code?: string;
  diagram_id?: string;
  all_variations?: string[]; // All variation codes
  user_id?: string;
  session_id?: string;
}

// --- User & Session Management ---

const USER_ID_KEY = 'uml_agent_user_id';

function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

function getOrCreateUserId(): string {
  if (typeof window === 'undefined') return 'server-side';

  let userId = localStorage.getItem(USER_ID_KEY);
  if (!userId) {
    userId = generateUUID();
    localStorage.setItem(USER_ID_KEY, userId);
  }
  return userId;
}

// Session ID is created once per page load
let currentSessionId: string | null = null;

function getSessionId(): string {
  if (!currentSessionId) {
    currentSessionId = generateUUID();
  }
  return currentSessionId;
}

// --------------------------------

/**
 * Record a user action to the backend
 */
export async function recordAction(payload: RLActionPayload): Promise<void> {
  try {
    // Add timestamp if not provided
    if (!payload.timestamp) {
      payload.timestamp = new Date().toISOString();
    }

    // Add user and session IDs
    payload.user_id = getOrCreateUserId();
    payload.session_id = getSessionId();

    console.log(`[RL Tracking] Recording action: ${payload.action_type}`, {
      endpoint: RL_ACTION_ENDPOINT,
      payload
    });

    const response = await fetch(RL_ACTION_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('[RL Tracking] Failed to record RL action:', {
        status: response.status,
        statusText: response.statusText,
        error: errorData
      });
    } else {
      console.log(`[RL Tracking] Successfully recorded action: ${payload.action_type}`);
    }
  } catch (error) {
    console.error('[RL Tracking] Error recording RL action:', error);
  }
}

/**
 * Helper functions for specific action types
 */
export const trackImageCopy = (diagramId?: string, mermaidCode?: string) => {
  recordAction({
    action_type: 'image_copy',
    diagram_id: diagramId,
    mermaid_code: mermaidCode,
  });
};

export const trackVariationHover = (
  variationIndex: number,
  diagramId?: string,
  hoveredMermaidCode?: string,
  allVariations?: string[]
) => {
  recordAction({
    action_type: 'variation_hover',
    variation_index: variationIndex,
    diagram_id: diagramId,
    mermaid_code: hoveredMermaidCode, // The hovered variation
    all_variations: allVariations, // All 3 variations
  });
};

export const trackVariationSelection = (
  variationIndex: number,
  diagramId?: string,
  selectedMermaidCode?: string,
  allVariations?: string[]
) => {
  recordAction({
    action_type: 'variation_selection',
    variation_index: variationIndex,
    diagram_id: diagramId,
    mermaid_code: selectedMermaidCode, // The selected variation
    all_variations: allVariations, // All 3 variations
  });
};

export const trackTabAway = (diagramId?: string, mermaidCode?: string) => {
  recordAction({
    action_type: 'tab_away',
    diagram_id: diagramId,
    mermaid_code: mermaidCode,
    metadata: {
      had_diagram: !!mermaidCode,
    },
  });
};

export const trackNewButton = (diagramId?: string, previousMermaidCode?: string) => {
  recordAction({
    action_type: 'new_button',
    diagram_id: diagramId,
    mermaid_code: previousMermaidCode,
    metadata: {
      had_diagram: !!previousMermaidCode,
    },
  });
};

export const trackMermaidCopy = (diagramId?: string, mermaidCode?: string) => {
  recordAction({
    action_type: 'mermaid_copy',
    diagram_id: diagramId,
    mermaid_code: mermaidCode,
  });
};

export const trackPromptUpdate = (
  prompt: string,
  previousPrompt?: string,
  diagramId?: string
) => {
  recordAction({
    action_type: 'prompt_update',
    prompt,
    previous_prompt: previousPrompt,
    diagram_id: diagramId,
  });
};

export const trackFeedback = (
  rating: number,
  feedbackText: string,
  diagramId?: string,
  mermaidCode?: string
) => {
  recordAction({
    action_type: 'feedback',
    rating,
    feedback_text: feedbackText,
    diagram_id: diagramId,
    mermaid_code: mermaidCode,
  });
};

export const trackDiagramGenerated = (
  prompt: string,
  mermaidCode: string,
  diagramId: string,
  numVariations?: number
) => {
  recordAction({
    action_type: 'diagram_generated',
    prompt,
    mermaid_code: mermaidCode,
    diagram_id: diagramId,
    metadata: {
      num_variations: numVariations || 1,
    },
  });
};

export const trackDiagramEdited = (
  prompt: string,
  mermaidCode: string,
  diagramId: string,
  previousMermaidCode?: string
) => {
  recordAction({
    action_type: 'diagram_edited',
    prompt,
    mermaid_code: mermaidCode,
    diagram_id: diagramId,
    metadata: {
      had_previous_diagram: !!previousMermaidCode,
    },
  });
};

export const trackZoomToggle = (
  enabled: boolean,
  diagramId?: string,
  mermaidCode?: string
) => {
  recordAction({
    action_type: 'zoom',
    diagram_id: diagramId,
    mermaid_code: mermaidCode,
    metadata: {
      enabled: enabled,
    },
  });
};

export const trackPanToggle = (
  enabled: boolean,
  diagramId?: string,
  mermaidCode?: string
) => {
  recordAction({
    action_type: 'pan',
    diagram_id: diagramId,
    mermaid_code: mermaidCode,
    metadata: {
      enabled: enabled,
    },
  });
};

