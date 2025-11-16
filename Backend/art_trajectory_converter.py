import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field

from openai import OpenAI
import dotenv
from pydantic import BaseModel


class FinalAnswer(BaseModel):
    """Final answer from a trajectory."""
    answer: str
    metadata: Dict[str, Any] = {}


@dataclass
class Trajectory:
    """ART Trajectory structure."""
    reward: float = 0.0
    messages_and_choices: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    final_answer: Optional[FinalAnswer] = None



def calculate_rewards(steps: List[Dict], final_diagram: Optional[str]) -> tuple[int, List[int]]:
    """Calculate total trajectory reward and individual step rewards."""
    
    # MAIN REWARD SCHEME
    ACTION_REWARDS = {
        "diagram_generated": 2,
        "variation_selection": 5,
        "diagram_edited": 2,
        "mermaid_copy": 3,
        "image_copy": 3,
    }
    
    FEEDBACK_REWARDS = {1: -5, 2: -2, 3: 1, 4: 3, 5: 5}
    
    # PREV CONTEXT
    context = {
        "has_diagram": False,
        "has_selection": False,
        "feedback_rating": 0,
        "prompt_updates": 0,
    }
    
    step_rewards = []
    total = 0

    for i, step in enumerate(steps):
        action = step.get("action", {})
        action_type = action.get("type", "")
        reward = 0
        
        reward += ACTION_REWARDS.get(action_type, 0)
        
        if action_type == "feedback":
            rating = action.get("rating", 0)
            reward += FEEDBACK_REWARDS.get(rating, 0)
            context["feedback_rating"] = rating
            
        elif action_type == "prompt_update":
            context["prompt_updates"] += 1
            reward += 1 if context["prompt_updates"] <= 2 else (0 if context["prompt_updates"] <= 4 else -1)
            
        elif action_type == "new_button":
            has_prev_diagram = any(s.get("state", {}).get("diagram") for s in steps[:i])
            reward += -5 if has_prev_diagram else -1
            
        elif action_type == "tab_away":
            had_diagram = action.get("metadata", {}).get("had_diagram", False)
            reward += -3 if had_diagram else -2
        
        if action_type == "diagram_generated":
            context["has_diagram"] = True
        if action_type == "variation_selection":
            context["has_selection"] = True
        
        step_rewards.append(reward)
        total += reward
    
    if final_diagram:
        total += 5
        if context["has_diagram"] and context["has_selection"]:
            total += 3
        if context["feedback_rating"] >= 4:
            total += 3
        elif context["feedback_rating"] == 3:
            total += 1
        elif context["feedback_rating"] <= 2:
            total -= 2
    
    # Efficiency bonuses
    num_steps = len(steps)
    if final_diagram:
        if num_steps <= 5:
            total += 3
        elif num_steps <= 10:
            total += 2
        elif num_steps <= 15:
            total += 1
    
    if not final_diagram:
        if num_steps > 20:
            total -= 5
        elif num_steps > 15:
            total -= 3
    
    if context["prompt_updates"] > 5:
        total -= 2
    if context["prompt_updates"] > 8:
        total -= 4
    
    if not context["has_diagram"] and num_steps > 3:
        total -= 5
    
    if context["has_diagram"] and not context["has_selection"] and num_steps > 5:
        total -= 2
    
    return total, step_rewards


def generate_reasoning(action: Dict, context: Dict, use_llm: bool = True) -> str:
    """Generate reasoning for an action using LLM or fallback."""
    
    action_type = action.get("action_type", "")
    
    # FALLBACK REASONING TEMPLATES
    TEMPLATES = {
        "prompt_update": lambda a, c: f"User updated prompt to: '{c.get('current_prompt', '')[:80]}...'",
        "diagram_generated": lambda a, c: f"System generated {a.get('metadata', {}).get('num_variations', 3)} diagram variations.",
        "variation_selection": lambda a, c: f"User selected variation {a.get('variation_index', 0) + 1} as best match.",
        "new_button": lambda a, c: "User clicked 'New' to generate fresh diagram.",
        "diagram_edited": lambda a, c: "User manually edited the diagram code.",
        "feedback": lambda a, c: f"User rated diagram {a.get('rating', 0)}/5 stars.",
        "mermaid_copy": lambda a, c: "User copied Mermaid code for external use.",
        "image_copy": lambda a, c: "User copied diagram image.",
        "tab_away": lambda a, c: "User navigated away.",
        "zoom": lambda a, c: "User zoomed diagram for better view.",
        "pan": lambda a, c: "User panned diagram.",
        "variation_hover": lambda a, c: "User exploring variations.",
    }
    
    if not use_llm:
        template = TEMPLATES.get(action_type, lambda a, c: f"User performed {action_type}.")
        return template(action, context)
    
    IMPORTANT = {"prompt_update", "diagram_generated", "variation_selection", "new_button", "diagram_edited", "feedback"}
    
    if action_type not in IMPORTANT:
        template = TEMPLATES.get(action_type, lambda a, c: f"User performed {action_type}.")
        return template(action, context)
    
    try:
        client = _get_llm_client()
        if not client:
            template = TEMPLATES.get(action_type, lambda a, c: f"User performed {action_type}.")
            return template(action, context)
        
        prompt = f"""Analyze this user action in 2-3 sentences with SPECIFIC details:

Action: {action_type}
Prompt: {context.get('current_prompt', 'N/A')[:200]}
Current Diagram: {context.get('current_diagram', 'N/A')[:200]}

Be specific - reference exact code elements, states, or text differences. No vague phrases."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        reasoning = response.choices[0].message.content.strip()
        return reasoning if reasoning else TEMPLATES.get(action_type, lambda a, c: f"User performed {action_type}.")(action, context)
    
    except Exception:
        template = TEMPLATES.get(action_type, lambda a, c: f"User performed {action_type}.")
        return template(action, context)


def _get_llm_client() -> Optional[OpenAI]:
    """Get OpenAI client if available."""
    try:
        script_dir = Path(__file__).parent
        env_path = script_dir / '.env'
        api_key = None
        if env_path.exists():
            api_key = dotenv.get_key(str(env_path), 'OPENAI_API_KEY')
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')
        return OpenAI(api_key=api_key) if api_key else None
    except Exception:
        return None



def convert_to_art_trajectories(
    input_file: str,
    output_file: str,
    use_llm: bool = True
):
    """
    Convert RL actions JSON to ART trajectories.
    
    Args:
        input_file: Path to rl_actions.json
        output_file: Path to save art_trajectories.json
        use_llm: Whether to use LLM for reasoning generation
    """
    

    rl_actions = None
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(input_file, "r", encoding=encoding) as f:
                rl_actions = json.load(f)
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    
    if rl_actions is None:
        raise ValueError(f"Could not decode {input_file} with any supported encoding")
    
    
    sessions = defaultdict(list)
    for action in rl_actions:
        diagram_id = action.get("diagram_id", "unknown")
        sessions[diagram_id].append(action)
    
    # Sort by timestamp
    for actions in sessions.values():
        actions.sort(key=lambda x: x.get("timestamp", ""))
    
    print(f"Found {len(sessions)} sessions with {len(rl_actions)} total actions")
    
    trajectories = []
    
    for diagram_id, actions in sessions.items():
        context = {"current_prompt": "", "current_diagram": ""}
        steps = []
        
        for action in actions:
            action_type = action.get("action_type", "")
            
            state = {
                "prompt": context["current_prompt"],
                "diagram": context["current_diagram"],
                "timestamp": action.get("timestamp", "")
            }
            
            reasoning = generate_reasoning(action, context, use_llm)
            
            if action.get("prompt"):
                context["current_prompt"] = action["prompt"]
            if action.get("mermaid_code"):
                context["current_diagram"] = action["mermaid_code"]
            
            next_state = {
                "prompt": context["current_prompt"],
                "diagram": context["current_diagram"],
                "timestamp": action.get("timestamp", "")
            }
            
            step = {
                "state": state,
                "action": {
                    "type": action_type,
                    "metadata": action.get("metadata", {}),
                    **{k: action[k] for k in ["variation_index", "rating", "feedback_text", "all_variations"] if k in action}
                },
                "reasoning": reasoning,
                "next_state": next_state
            }
            
            steps.append(step)
        

        final_diagram = steps[-1]["next_state"]["diagram"] if steps else None
        final_prompt = steps[-1]["next_state"]["prompt"] if steps else None
        
        total_reward, step_rewards = calculate_rewards(steps, final_diagram)
        
        for step, reward in zip(steps, step_rewards):
            step["reward"] = reward
        
        final_answer = FinalAnswer(
            answer=final_diagram,
            metadata={
                "prompt": final_prompt,
                "diagram_id": diagram_id,
                "num_steps": len(steps)
            }
        ) if final_diagram else None
        
        trajectory = Trajectory(
            reward=float(total_reward),
            messages_and_choices=steps,
            metadata={
                "diagram_id": diagram_id,
                "num_actions": len(actions),
                "start_timestamp": actions[0].get("timestamp", "") if actions else "",
                "end_timestamp": actions[-1].get("timestamp", "") if actions else ""
            },
            metrics={},
            final_answer=final_answer
        )
        
        trajectories.append(trajectory)

    # final output    
    output_data = []
    for traj in trajectories:
        output_data.append({
            "diagram_id": traj.metadata.get("diagram_id", "unknown"),
            "reward": traj.reward,
            "trajectory": traj.messages_and_choices,
            "final_answer": traj.final_answer.dict() if traj.final_answer else None,
            "metadata": traj.metadata,
            "metrics": traj.metrics
        })
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Converted {len(rl_actions)} actions into {len(trajectories)} trajectories")
    print(f"Output saved to {output_file}")
    



script_dir = Path(__file__).parent
project_root = script_dir.parent

convert_to_art_trajectories(
    input_file=str(project_root / "rl_actions.json"),
    output_file=str(project_root / "art_trajectories.json"),
    use_llm=True
)