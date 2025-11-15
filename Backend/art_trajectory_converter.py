import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from pydantic import BaseModel

try:
    import dotenv
    from openai import OpenAI
    from constants import OPENAI_MODEL_NAME
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    OPENAI_MODEL_NAME = "gpt-4o-mini"

try:
    import art
    from art import Trajectory, FinalAnswer
    ART_AVAILABLE = True
except ImportError:
    ART_AVAILABLE = False

    class FinalAnswer(BaseModel):
        answer: str
        metadata: Dict[str, Any] = {}
    
    @dataclass
    class Trajectory:
        reward: float = 0.0
        messages_and_choices: List[Any] = field(default_factory=list)
        metadata: Dict[str, Any] = field(default_factory=dict)
        metrics: Dict[str, Any] = field(default_factory=dict)
        final_answer: Optional[FinalAnswer] = None


if ART_AVAILABLE:
    class ProjectTrajectory(Trajectory):
        """Custom trajectory class for UML diagram generation project."""
        final_answer: Optional[FinalAnswer] = None
        
        def to_dict(self) -> Dict[str, Any]:
            """Convert trajectory to dictionary for JSON serialization."""
            return {
                "reward": self.reward,
                "messages_and_choices": self.messages_and_choices,
                "metadata": self.metadata,
                "metrics": self.metrics,
                "final_answer": self.final_answer.dict() if self.final_answer else None
            }
else:
    @dataclass
    class ProjectTrajectory(Trajectory):
        """Custom trajectory class for UML diagram generation project."""
        final_answer: Optional[FinalAnswer] = None
        
        def to_dict(self) -> Dict[str, Any]:
            """Convert trajectory to dictionary for JSON serialization."""
            return {
                "reward": self.reward,
                "messages_and_choices": self.messages_and_choices,
                "metadata": self.metadata,
                "metrics": self.metrics,
                "final_answer": self.final_answer.dict() if self.final_answer else None
            }


async def judge_correctness(
    prompt: str, 
    final_diagram: str, 
    client: Optional[OpenAI] = None
) -> Dict[str, Any]:
    """
    Judge if the final diagram correctly satisfies the user's prompt.
    Returns a dict with 'accept' (bool) and 'reasoning' (str).
    """
    if client is None:
        client = get_openai_client()
    
    if client is None:
        # Fallback: simple heuristic check
        return {
            "accept": bool(final_diagram and prompt),
            "reasoning": "Could not perform LLM-based correctness check"
        }
    
    system_prompt = """You are a correctness judge for UML diagram generation. 
Evaluate whether the generated diagram correctly satisfies the user's prompt requirements.
Be strict but fair - the diagram should meet the key requirements from the prompt."""
    
    user_prompt = f"""User Prompt:
{prompt}

Generated Diagram:
{final_diagram}

Evaluate if this diagram correctly satisfies the prompt requirements. 
Respond with JSON: {{"accept": true/false, "reasoning": "explanation"}}"""
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return {
            "accept": result.get("accept", False),
            "reasoning": result.get("reasoning", "No reasoning provided")
        }
    except Exception as e:
        return {
            "accept": False,
            "reasoning": f"Error in correctness judgment: {str(e)}"
        }


def calculate_action_reward(
    action_type: str,
    action: Dict[str, Any],
    context: Dict[str, Any],
    previous_steps: List[Dict[str, Any]]
) -> int:
    """
    Calculate individual reward for a single action based on its type and context.
    Returns the immediate reward for this specific action.
    """
    reward = 0
    
    # Check if this is new_button after a diagram was generated
    new_button_after_diagram = False
    if action_type == "new_button":
        for prev_step in previous_steps:
            prev_state = prev_step.get("state", {})
            if prev_state.get("diagram"):
                new_button_after_diagram = True
                break
    
    # Base rewards for important actions
    if action_type == "diagram_generated":
        reward += 2  # System generated diagram (small positive)
        
    elif action_type == "variation_selection":
        reward += 5  # User made a selection (good sign)
        
    elif action_type == "feedback":
        rating = action.get("rating", 0)
        if rating > 0:
            if rating == 1:
                reward -= 5  # Very negative feedback
            elif rating == 2:
                reward -= 2  # Negative feedback
            elif rating == 3:
                reward += 1  # Neutral/acceptable
            elif rating == 4:
                reward += 3  # Good feedback
            elif rating == 5:
                reward += 5  # Excellent feedback
                
    elif action_type == "prompt_update":
        # Count previous prompt updates
        num_prev_updates = sum(1 for s in previous_steps if s.get("action", {}).get("type") == "prompt_update")
        if num_prev_updates < 2:
            reward += 1  # Reasonable refinement
        elif num_prev_updates < 4:
            reward += 0  # Neutral
        else:
            reward -= 1  # Too many updates
            
    elif action_type == "diagram_edited":
        reward += 2  # User actively improving the diagram
        
    elif action_type == "new_button":
        if new_button_after_diagram:
            reward -= 5  # User rejected the previous diagram
        else:
            reward -= 1  # Starting fresh (less negative if no previous diagram)
        
    elif action_type == "mermaid_copy" or action_type == "image_copy":
        reward += 3  # User found value in the diagram
        
    elif action_type == "tab_away":
        metadata = action.get("metadata", {})
        if metadata.get("had_diagram", False):
            # Check if user will come back and click new_button (negative signal)
            # We can't know future, so just use current state
            reward -= 3  # User left (could be positive or negative, but default negative)
        else:
            reward -= 2  # Left without diagram (likely gave up)
    
    return reward


def calculate_reward(trajectory_steps: List[Dict[str, Any]], final_answer: Optional[FinalAnswer] = None) -> int:
    """
    Calculate integer reward for the trajectory based on actions and outcomes.
    Returns positive rewards for good actions and negative rewards for poor outcomes.
    Scaled appropriately (typically -10 to +20 range).
    """
    reward = 0
    
    if not trajectory_steps:
        return 0
    
    # Track important events and context
    has_diagram_generated = False
    has_variation_selected = False
    has_feedback = False
    feedback_rating = 0
    num_prompt_updates = 0
    num_edits = 0
    has_final_diagram = False
    new_button_after_diagram = False  # Track if new_button came after diagram generation
    tab_away_count = 0
    diagram_generated_before_new = False
    
    # First pass: track context
    for i, step in enumerate(trajectory_steps):
        action = step.get("action", {})
        action_type = action.get("type", "")
        
        if action_type == "diagram_generated":
            has_diagram_generated = True
            diagram_generated_before_new = True
        
        if action_type == "new_button" and diagram_generated_before_new:
            # Check if there was a diagram before this new_button
            for j in range(i):
                prev_step = trajectory_steps[j]
                prev_state = prev_step.get("state", {})
                if prev_state.get("diagram"):
                    new_button_after_diagram = True
                    break
    
    # Second pass: calculate rewards
    for step in trajectory_steps:
        action = step.get("action", {})
        action_type = action.get("type", "")
        state = step.get("state", {})
        next_state = step.get("next_state", {})
        
        # Base rewards for important actions
        if action_type == "diagram_generated":
            reward += 2  # System generated diagram (small positive)
            has_diagram_generated = True
            
        elif action_type == "variation_selection":
            reward += 5  # User made a selection (good sign)
            has_variation_selected = True
            
        elif action_type == "feedback":
            rating = action.get("rating", 0)
            if rating > 0:
                # Reward based on rating: scaled appropriately
                if rating == 1:
                    reward -= 5  # Very negative feedback
                elif rating == 2:
                    reward -= 2  # Negative feedback
                elif rating == 3:
                    reward += 1  # Neutral/acceptable
                elif rating == 4:
                    reward += 3  # Good feedback
                elif rating == 5:
                    reward += 5  # Excellent feedback
                feedback_rating = rating
                has_feedback = True
                
        elif action_type == "prompt_update":
            num_prompt_updates += 1
            # Small reward for refinement, but too many updates indicate confusion
            if num_prompt_updates <= 2:
                reward += 1  # Reasonable refinement
            elif num_prompt_updates <= 4:
                reward += 0  # Neutral
            else:
                reward -= 1  # Too many updates (negative signal)
                
        elif action_type == "diagram_edited":
            num_edits += 1
            reward += 2  # User actively improving the diagram
            
        elif action_type == "new_button":
            # Strong negative if it comes after a diagram was generated (user didn't like it)
            if new_button_after_diagram:
                reward -= 5  # User rejected the previous diagram
            else:
                reward -= 1  # Starting fresh (less negative if no previous diagram)
            
        elif action_type == "mermaid_copy" or action_type == "image_copy":
            # User found value in the diagram - positive signal
            reward += 3
            
        elif action_type == "tab_away":
            tab_away_count += 1
            metadata = action.get("metadata", {})
            if metadata.get("had_diagram", False):
                # If user tabs away with diagram, it's slightly positive (might be done)
                # But if they come back and click new_button, that's negative
                reward -= 3
            else:
                reward -= 2  # Left without diagram (likely gave up)
    
    # Completion bonus: trajectory with final diagram
    if final_answer and final_answer.answer:
        has_final_diagram = True
        reward += 5  # Base completion bonus
        
        # Bonus for successful trajectory flow
        if has_diagram_generated and has_variation_selected:
            reward += 3  # Complete workflow: generate -> select
            
        if has_feedback and feedback_rating >= 4:
            reward += 3  # High satisfaction bonus
        elif has_feedback and feedback_rating >= 3:
            reward += 1  # Moderate satisfaction
        elif has_feedback and feedback_rating <= 2:
            reward -= 2  # Low satisfaction penalty
            
    # Efficiency bonus: fewer iterations to completion
    total_actions = len(trajectory_steps)
    if total_actions <= 5 and has_final_diagram:
        reward += 3  # Very efficient completion
    elif total_actions <= 10 and has_final_diagram:
        reward += 2  # Efficient completion
    elif total_actions <= 15 and has_final_diagram:
        reward += 1  # Reasonable efficiency
    
    # Penalties for inefficiency or failure
    if total_actions > 20 and not has_final_diagram:
        reward -= 5  # Too many actions without result
    elif total_actions > 15 and not has_final_diagram:
        reward -= 3  # Many actions without completion
    
    # Penalty for many prompt updates (indicates confusion)
    if num_prompt_updates > 5:
        reward -= 2
    elif num_prompt_updates > 8:
        reward -= 4  # Severe confusion
    
    # Penalty if no diagram was ever generated
    if not has_diagram_generated and total_actions > 3:
        reward -= 5  # User tried but system didn't generate
    
    # Strong penalty: diagram generated but user clicked new_button (didn't like it)
    if has_diagram_generated and new_button_after_diagram and not has_variation_selected:
        reward -= 3  # Additional penalty for rejecting without even selecting
    
    # Penalty if diagram generated but never selected (and no new_button)
    if has_diagram_generated and not has_variation_selected and not new_button_after_diagram and total_actions > 5:
        reward -= 2  # Generated but user didn't engage
    
    # Multiple tab_aways might indicate confusion
    if tab_away_count > 3:
        reward -= 1
    
    return reward


def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client if API key is available."""
    if not LLM_AVAILABLE:
        return None
    
    try:
        # Look for .env in the Backend folder (where this script is located)
        script_dir = Path(__file__).parent
        env_path = script_dir / '.env'
        
        # Try to get API key from .env file in Backend folder
        api_key = None
        if env_path.exists():
            api_key = dotenv.get_key(str(env_path), 'OPENAI_API_KEY')
        
        # Fallback to environment variable
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key:
            return OpenAI(api_key=api_key)
    except Exception:
        pass
    return None


# Actions that should get LLM-generated reasoning
IMPORTANT_ACTIONS = {
    "prompt_update",
    "diagram_generated", 
    "variation_selection",
    "new_button",
    "diagram_edited",
    "feedback"
}

# Actions that are context-only (use fallback, but include in context)
CONTEXT_ACTIONS = {
    "tab_away",
    "pan",
    "zoom",
    "mermaid_copy",
    "image_copy",
    "variation_hover"
}


def generate_reasoning_llm(action: Dict[str, Any], context: Dict[str, Any], recent_actions: List[Dict[str, Any]] = None, client: Optional[OpenAI] = None) -> str:
    """Generate reasoning using LLM with deep user intent analysis."""
    if client is None:
        client = get_openai_client()
    
    if client is None:
        return generate_reasoning_fallback(action, context)
    
    action_type = action.get("action_type", "")
    prompt = action.get("prompt") or context.get("current_prompt", "")
    previous_prompt = action.get("previous_prompt") or context.get("previous_prompt", "")
    mermaid_code = action.get("mermaid_code", "")
    variation_index = action.get("variation_index")
    all_variations = action.get("all_variations", [])
    rating = action.get("rating")
    feedback_text = action.get("feedback_text", "")
    previous_diagram = context.get("current_diagram", "")
    
    # Build detailed context description
    context_desc = ""
    
    if action_type == "variation_selection":
        # For variation selection: compare all variations to understand why this one was chosen
        context_desc = f"User prompt: {prompt}\n\n"
        context_desc += f"User selected variation {variation_index + 1} out of {len(all_variations)} options.\n\n"
        context_desc += "=== ALL AVAILABLE VARIATIONS FOR COMPARISON ===\n\n"
        for i, var in enumerate(all_variations):
            marker = "← SELECTED BY USER" if i == variation_index else "(not selected)"
            context_desc += f"--- Variation {i + 1} {marker} ---\n{var}\n\n"
        context_desc += f"=== SELECTED VARIATION ({variation_index + 1}) ===\n{mermaid_code}\n"
        
    elif action_type == "prompt_update":
        # For prompt update: compare old vs new to determine if refinement or perspective change
        context_desc = "=== PROMPT COMPARISON ===\n\n"
        context_desc += f"PREVIOUS PROMPT:\n{previous_prompt if previous_prompt else 'None'}\n\n"
        context_desc += f"NEW PROMPT:\n{prompt if prompt else 'None'}\n\n"
        if previous_diagram:
            context_desc += f"Current diagram before prompt change:\n{previous_diagram}\n"
        
    elif action_type == "new_button":
        # For new button: understand why current diagram wasn't sufficient
        context_desc = f"User prompt: {prompt if prompt else 'None'}\n\n"
        if previous_diagram:
            context_desc += f"=== EXISTING DIAGRAM BEING REPLACED ===\n{previous_diagram}\n\n"
        context_desc += "User clicked 'New' button to generate a completely new diagram instead of editing.\n"
        
    elif action_type == "diagram_generated":
        context_desc = f"User prompt: {prompt[:300] if prompt else 'None'}\n\n"
        context_desc += f"Generated diagram:\n{mermaid_code[:400]}...\n"
        if action.get("metadata", {}).get("num_variations"):
            context_desc += f"\nGenerated {action['metadata']['num_variations']} variations for user to choose from.\n"
            
    elif action_type == "diagram_edited":
        context_desc = f"User prompt: {prompt if prompt else 'None'}\n\n"
        context_desc += "=== DIAGRAM COMPARISON ===\n\n"
        if previous_diagram:
            context_desc += f"PREVIOUS DIAGRAM:\n{previous_diagram}\n\n"
        context_desc += f"EDITED DIAGRAM:\n{mermaid_code}\n"
        
    elif action_type == "feedback":
        context_desc = f"User prompt: {prompt[:300] if prompt else 'None'}\n\n"
        if mermaid_code:
            context_desc += f"Diagram being rated:\n{mermaid_code[:400]}...\n\n"
        context_desc += f"Rating: {rating}/5\n"
        if feedback_text:
            context_desc += f"Feedback text: {feedback_text}\n"
    else:
        # Generic context
        context_desc = f"Current prompt: {prompt[:200] if prompt else 'None'}\n"
        if mermaid_code:
            context_desc += f"Current diagram: {mermaid_code[:300]}...\n"
    
    # Include recent context actions
    if recent_actions:
        context_actions_list = []
        for ctx_action in recent_actions[-5:]:
            ctx_type = ctx_action.get("action_type", "")
            if ctx_type in CONTEXT_ACTIONS:
                context_actions_list.append(ctx_type)
        if context_actions_list:
            context_desc += f"\nRecent user interactions: {', '.join(context_actions_list)}\n"
    
    # Build action-specific analysis prompts
    if action_type == "variation_selection":
        analysis_prompt = """CRITICAL: You must provide SPECIFIC, CONCRETE reasoning by comparing the actual code differences.

REQUIRED ANALYSIS:
1. Compare the SELECTED variation with EACH of the other variations - what are the EXACT structural differences?
2. Identify SPECIFIC features in the selected variation that are DIFFERENT or BETTER than the alternatives:
   - Different state names or structures?
   - Different transition patterns or flows?
   - Different handling of parallel states, composite states, or final states?
   - Better alignment with specific requirements from the prompt?
3. Explain WHY these differences make the selected variation the better choice for the user's needs.

DO NOT give generic statements like "best matches requirements" or "better suited to needs". 
You MUST reference specific code elements, state names, transitions, or structural patterns that differ between variations."""
        
    elif action_type == "prompt_update":
        analysis_prompt = """CRITICAL: Compare the EXACT text differences between old and new prompts.

REQUIRED ANALYSIS:
1. Word-by-word comparison: What SPECIFIC words, phrases, or requirements were ADDED, REMOVED, or CHANGED?
2. Determine if this is:
   - A REFINEMENT (adding details, clarifying existing requirements)
   - A PERSPECTIVE CHANGE (completely different approach or focus)
   - A CORRECTION (fixing misunderstandings or errors)
3. Identify what was MISSING or UNSATISFACTORY in the previous prompt that led to this change.
4. Reference SPECIFIC prompt text differences, not vague descriptions.

DO NOT say generic things like "user wanted to improve" - cite exact text changes."""
        
    elif action_type == "new_button":
        analysis_prompt = """CRITICAL: Analyze the EXISTING diagram against the user's prompt to find what's wrong.

REQUIRED ANALYSIS:
1. Compare the existing diagram code with the user's prompt requirements - what SPECIFIC requirements are MISSING or INCORRECT?
2. Identify concrete problems:
   - Missing states, transitions, or relationships?
   - Incorrect state names, structures, or flows?
   - Wrong diagram type or syntax issues?
   - Misalignment with specific prompt requirements?
3. Explain WHY starting fresh was chosen over editing - what would be too difficult to fix?

DO NOT say vague things like "didn't meet needs" - cite SPECIFIC missing or incorrect elements."""
        
    elif action_type == "diagram_generated":
        analysis_prompt = """Analyze the generated diagram from the user's perspective:
- How well does it align with the prompt requirements?
- What aspects might the user be looking for when they review the variations?"""
        
    elif action_type == "diagram_edited":
        analysis_prompt = """CRITICAL: Compare the EXACT code differences between previous and edited diagrams.

REQUIRED ANALYSIS:
1. Line-by-line comparison: What SPECIFIC code was ADDED, REMOVED, or MODIFIED?
2. Identify the EXACT changes:
   - New states, transitions, or relationships added?
   - States, transitions, or relationships removed?
   - State names, labels, or structures modified?
3. Explain WHY each change was made - what problem did it solve or what requirement did it address?

DO NOT say generic things like "user made improvements" - cite SPECIFIC code changes."""
        
    elif action_type == "feedback":
        analysis_prompt = """Analyze the user's feedback:
- What does the rating indicate about their satisfaction?
- What specific aspects did they like or dislike?
- What insights can be drawn from their feedback text?"""
    else:
        analysis_prompt = "Analyze this action from the user's perspective and intent."
    
    system_prompt = """You are analyzing user interactions with a UML diagram generation system. 

CRITICAL REQUIREMENTS:
- You MUST provide SPECIFIC, CONCRETE reasoning based on ACTUAL code/prompt comparisons
- You MUST reference exact differences: state names, transitions, structures, text changes
- You MUST explain WHY the user made this choice by comparing what exists vs what was selected/changed
- DO NOT use vague phrases like "best matches", "better suited", "meets requirements" without specifics
- DO NOT just describe what happened - explain the REASONING behind the choice

Your output should be 2-3 sentences that cite SPECIFIC elements and explain the user's reasoning."""
    
    user_prompt = f"""Context:
{context_desc}

Action: {action_type}

Analysis needed:
{analysis_prompt}

Generate reasoning (2-3 sentences) that:
1. References SPECIFIC code elements, states, transitions, or text differences
2. Explains WHY the user made this choice based on concrete comparisons
3. Avoids vague statements - be precise and cite exact differences"""
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        reasoning = response.choices[0].message.content.strip()
        return reasoning if reasoning else generate_reasoning_fallback(action, context)
    except Exception:
        return generate_reasoning_fallback(action, context)


def generate_reasoning_fallback(action: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Generate reasoning for an action based on context."""
    action_type = action.get("action_type", "")
    prompt = action.get("prompt") or context.get("current_prompt", "")
    previous_prompt = action.get("previous_prompt") or context.get("previous_prompt", "")
    mermaid_code = action.get("mermaid_code", "")
    variation_index = action.get("variation_index")
    rating = action.get("rating")
    feedback_text = action.get("feedback_text", "")
    
    reasoning_parts = []
    
    if action_type == "prompt_update":
        if previous_prompt and prompt:
            reasoning_parts.append(f"User updated prompt from '{previous_prompt[:50]}...' to '{prompt[:50]}...'")
        else:
            reasoning_parts.append(f"User provided new prompt: '{prompt[:50]}...'")
        reasoning_parts.append("Expecting diagram generation based on new requirements.")
    
    elif action_type == "diagram_generated":
        reasoning_parts.append("System generated diagram variations based on user prompt.")
        if action.get("metadata", {}).get("num_variations"):
            reasoning_parts.append(f"Generated {action['metadata']['num_variations']} variations for user selection.")
    
    elif action_type == "variation_selection":
        if variation_index is not None:
            reasoning_parts.append(f"User selected variation {variation_index + 1} from available options.")
            if action.get("all_variations"):
                reasoning_parts.append("Selected variation best matches user requirements.")
    
    elif action_type == "variation_hover":
        reasoning_parts.append("User is exploring different diagram variations before selection.")
    
    elif action_type == "new_button":
        reasoning_parts.append("User clicked 'New' button to generate a new diagram.")
        if mermaid_code:
            reasoning_parts.append("This will trigger diagram generation with current prompt.")
    
    elif action_type == "mermaid_copy":
        reasoning_parts.append("User copied the Mermaid code, likely for use in external tools.")
    
    elif action_type == "image_copy":
        reasoning_parts.append("User copied the diagram image, likely for documentation or sharing.")
    
    elif action_type == "diagram_edited":
        reasoning_parts.append("User manually edited the diagram code.")
        if mermaid_code:
            reasoning_parts.append("Diagram state updated with user modifications.")
    
    elif action_type == "feedback":
        if rating:
            reasoning_parts.append(f"User provided {rating}-star rating.")
        if feedback_text:
            reasoning_parts.append(f"User feedback: '{feedback_text[:100]}...'")
        reasoning_parts.append("This indicates user satisfaction with the generated diagram.")
    
    elif action_type == "tab_away":
        had_diagram = action.get("metadata", {}).get("had_diagram", False)
        if had_diagram:
            reasoning_parts.append("User navigated away from diagram, indicating task completion or pause.")
        else:
            reasoning_parts.append("User navigated away without generating diagram.")
    
    elif action_type == "zoom" or action_type == "pan":
        reasoning_parts.append(f"User adjusted diagram view ({action_type}) for better visibility.")
    
    else:
        reasoning_parts.append(f"User performed {action_type} action.")
    
    return " ".join(reasoning_parts) if reasoning_parts else f"Action: {action_type}"


def convert_to_art_trajectory(
    rl_actions: List[Dict[str, Any]], 
    use_llm: bool = True,
    score_trajectories: bool = False
) -> List[ProjectTrajectory]:
    """Convert RL actions to ART trajectory format."""
    # Group actions by diagram_id (sessions)
    sessions = defaultdict(list)
    for action in rl_actions:
        diagram_id = action.get("diagram_id", "unknown")
        sessions[diagram_id].append(action)
    
    # Sort actions within each session by timestamp
    for diagram_id in sessions:
        sessions[diagram_id].sort(key=lambda x: x.get("timestamp", ""))
    
    trajectories = []
    
    # Get LLM client once if using LLM
    llm_client = get_openai_client() if use_llm else None
    
    for diagram_id, actions in sessions.items():
        context = {
            "current_prompt": "",
            "previous_prompt": "",
            "current_diagram": "",
        }
        
        trajectory_steps = []
        recent_actions = []  # Track recent actions for context
        
        for action in actions:
            action_type = action.get("action_type", "")
            
            # Build state representation (before action)
            state = {
                "prompt": context["current_prompt"],
                "diagram": context["current_diagram"],
                "timestamp": action.get("timestamp", ""),
            }
            
            # Generate reasoning - only use LLM for important actions
            if action_type in IMPORTANT_ACTIONS and use_llm and llm_client:
                # Use LLM with recent context actions
                reasoning = generate_reasoning_llm(action, context, recent_actions=recent_actions, client=llm_client)
            else:
                # Use fallback for context actions and non-important actions
                reasoning = generate_reasoning_fallback(action, context)
            
            # Track recent context actions for future LLM reasoning (only context actions)
            if action_type in CONTEXT_ACTIONS:
                recent_actions.append(action)
                if len(recent_actions) > 10:
                    recent_actions.pop(0)
            
            # Build action representation
            action_repr = {
                "type": action.get("action_type", ""),
                "metadata": action.get("metadata", {}),
            }
            
            # Add action-specific fields
            if action.get("variation_index") is not None:
                action_repr["variation_index"] = action["variation_index"]
            if action.get("rating") is not None:
                action_repr["rating"] = action["rating"]
            if action.get("feedback_text"):
                action_repr["feedback_text"] = action["feedback_text"]
            
            # Update context (after action)
            if action.get("prompt"):
                context["previous_prompt"] = context["current_prompt"]
                context["current_prompt"] = action["prompt"]
            
            if action.get("mermaid_code"):
                context["current_diagram"] = action["mermaid_code"]
            
            # Build next state (state after action)
            next_state = {
                "prompt": context["current_prompt"],
                "diagram": context["current_diagram"],
                "timestamp": action.get("timestamp", ""),
            }
            
            # Calculate individual action reward
            action_reward = calculate_action_reward(
                action_type,
                action,
                context,
                trajectory_steps  # Previous steps for context
            )
            
            trajectory_step = {
                "state": state,
                "action": action_repr,
                "reasoning": reasoning,
                "reward": action_reward,  # Individual action reward
                "next_state": next_state,
            }
            
            trajectory_steps.append(trajectory_step)
        
        # Get final answer (last diagram and prompt)
        final_answer = None
        if trajectory_steps:
            last_step = trajectory_steps[-1]
            final_state = last_step.get("next_state", {})
            final_diagram = final_state.get("diagram", "")
            final_prompt = final_state.get("prompt", "")
            
            if final_diagram:
                final_answer = FinalAnswer(
                    answer=final_diagram,
                    metadata={
                        "prompt": final_prompt,
                        "diagram_id": diagram_id,
                        "num_steps": len(trajectory_steps)
                    }
                )
        
        # Always calculate reward (not just when scoring)
        reward = calculate_reward(trajectory_steps, final_answer)
        
        # Create ART trajectory (reward is now int)
        traj = ProjectTrajectory(
            reward=float(reward),  # Convert to float for compatibility
            messages_and_choices=trajectory_steps,
            metadata={
                "diagram_id": diagram_id,
                "num_actions": len(actions),
                "start_timestamp": actions[0].get("timestamp", "") if actions else "",
                "end_timestamp": actions[-1].get("timestamp", "") if actions else "",
            },
            final_answer=final_answer
        )
        
        # Score the trajectory if requested
        if score_trajectories and final_answer and use_llm and llm_client:
            import asyncio
            try:
                correctness_result = asyncio.run(
                    judge_correctness(final_prompt, final_diagram, llm_client)
                )
                traj.metrics["correct"] = correctness_result["accept"]
                traj.metrics["correctness_reasoning"] = correctness_result["reasoning"]
            except Exception as e:
                traj.metrics["correct"] = False
                traj.metrics["scoring_error"] = str(e)
        
        trajectories.append(traj)
    
    return trajectories


def convert_rl_actions_file(
    input_file: str, 
    output_file: str, 
    use_llm: bool = True,
    score_trajectories: bool = False
):
    """Convert RL actions JSON file to ART trajectory format."""
    # Try multiple encodings to handle encoding issues
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    rl_actions = None
    
    for encoding in encodings:
        try:
            with open(input_file, "r", encoding=encoding, errors="replace") as f:
                rl_actions = json.load(f)
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    
    if rl_actions is None:
        raise ValueError(f"Could not decode {input_file} with any supported encoding")
    
    trajectories = convert_to_art_trajectory(
        rl_actions, 
        use_llm=use_llm,
        score_trajectories=score_trajectories
    )
    
    # Convert trajectories to serializable format
    output_data = []
    for traj in trajectories:
        traj_dict = {
            "diagram_id": traj.metadata.get("diagram_id", "unknown"),
            "reward": traj.reward,
            "metadata": traj.metadata,
            "metrics": traj.metrics,
            "final_answer": traj.final_answer.dict() if traj.final_answer else None,
            "trajectory": traj.messages_and_choices
        }
        output_data.append(traj_dict)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Converted {len(rl_actions)} actions into {len(trajectories)} trajectories")
    if score_trajectories:
        correct_count = sum(1 for t in trajectories if t.metrics.get("correct", False))
        print(f"Scored trajectories: {correct_count}/{len(trajectories)} marked as correct")
    print(f"Output saved to {output_file}")
    if use_llm and not get_openai_client():
        print("Warning: LLM not available, using fallback reasoning")


if __name__ == "__main__":
    # Paths relative to project root (parent of Backend folder)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    input_file = project_root / "rl_actions.json"
    output_file = project_root / "art_trajectories.json"
    
    # Set score_trajectories=True to enable correctness judging
    convert_rl_actions_file(
        str(input_file), 
        str(output_file),
        use_llm=True,
        score_trajectories=False  # Set to True to enable scoring
    )

