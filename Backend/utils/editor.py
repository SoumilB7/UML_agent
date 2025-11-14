import json
import logging
import re

from constants import OPENAI_MODEL_NAME, MERMAID_EDIT_SYSTEM_PROMPT
from utils.diagram import get_openai_client
from utils.logger import log_llm_call, log_mermaid_code

logger = logging.getLogger(__name__)


def apply_mermaid_edit(existing_mermaid_code: str, edit_instructions: dict) -> str:
    """
    Reliably applies edit instructions to existing Mermaid code without using LLM.
    
    Args:
        existing_mermaid_code (str): The existing Mermaid diagram code
        edit_instructions (dict): JSON object with "edits" array containing edit operations
        
    Returns:
        str: The updated Mermaid code with edits applied
    """
    if not edit_instructions or "edits" not in edit_instructions:
        logger.warning("No edits found in edit instructions")
        return existing_mermaid_code
    
    lines = existing_mermaid_code.split('\n')
    diagram_type = _detect_diagram_type(lines)
    
    # Apply each edit in sequence
    for edit in edit_instructions["edits"]:
        edit_type = edit.get("type")
        if not edit_type:
            continue
            
        try:
            if edit_type == "add_class":
                lines = _apply_add_class(lines, edit.get("details", {}))
            elif edit_type == "remove_class":
                lines = _apply_remove_class(lines, edit.get("target"))
            elif edit_type == "modify_class":
                lines = _apply_modify_class(lines, edit.get("target"), edit.get("details", {}))
            elif edit_type == "add_relationship":
                lines = _apply_add_relationship(lines, edit.get("details", {}))
            elif edit_type == "remove_relationship":
                lines = _apply_remove_relationship(lines, edit.get("details", {}))
            elif edit_type == "modify_relationship":
                lines = _apply_modify_relationship(lines, edit.get("details", {}))
            elif edit_type == "add_attribute":
                lines = _apply_add_attribute(lines, edit.get("target"), edit.get("details", {}))
            elif edit_type == "remove_attribute":
                lines = _apply_remove_attribute(lines, edit.get("target"), edit.get("details", {}))
            elif edit_type == "modify_attribute":
                lines = _apply_modify_attribute(lines, edit.get("target"), edit.get("details", {}))
            elif edit_type == "add_method":
                lines = _apply_add_method(lines, edit.get("target"), edit.get("details", {}))
            elif edit_type == "remove_method":
                lines = _apply_remove_method(lines, edit.get("target"), edit.get("details", {}))
            elif edit_type == "modify_method":
                lines = _apply_modify_method(lines, edit.get("target"), edit.get("details", {}))
            elif edit_type == "add_participant":
                lines = _apply_add_participant(lines, edit.get("details", {}))
            elif edit_type == "remove_participant":
                lines = _apply_remove_participant(lines, edit.get("target"))
            elif edit_type == "add_message":
                lines = _apply_add_message(lines, edit.get("details", {}))
            elif edit_type == "remove_message":
                lines = _apply_remove_message(lines, edit.get("details", {}))
            elif edit_type == "add_state":
                lines = _apply_add_state(lines, edit.get("details", {}))
            elif edit_type == "remove_state":
                lines = _apply_remove_state(lines, edit.get("target"))
            elif edit_type == "add_transition":
                lines = _apply_add_transition(lines, edit.get("details", {}))
            elif edit_type == "remove_transition":
                lines = _apply_remove_transition(lines, edit.get("details", {}))
            elif edit_type == "add_note":
                lines = _apply_add_note(lines, edit.get("details", {}))
            elif edit_type == "remove_note":
                lines = _apply_remove_note(lines, edit.get("details", {}))
            elif edit_type == "modify_note":
                lines = _apply_modify_note(lines, edit.get("details", {}))
            else:
                logger.warning(f"Unknown edit type: {edit_type}")
        except Exception as e:
            logger.error(f"Error applying edit {edit_type}: {e}", exc_info=True)
            # Continue with other edits even if one fails
    
    return '\n'.join(lines)


def _detect_diagram_type(lines: list) -> str:
    """Detect the type of Mermaid diagram from its lines."""
    for line in lines:
        line_lower = line.strip().lower()
        if line_lower.startswith('classdiagram'):
            return 'class'
        elif line_lower.startswith('sequencediagram'):
            return 'sequence'
        elif line_lower.startswith('statediagram'):
            return 'state'
        elif line_lower.startswith('flowchart'):
            return 'flowchart'
        elif line_lower.startswith('gantt'):
            return 'gantt'
    return 'unknown'


def _find_class_definition(lines: list, class_name: str) -> int:
    """Find the line index where a class is defined. Returns -1 if not found."""
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Match: class ClassName or class "ClassName"
        if re.match(rf'^class\s+{re.escape(class_name)}\s*$', stripped, re.IGNORECASE) or \
           re.match(rf'^class\s+"{re.escape(class_name)}"\s*$', stripped):
            return i
    return -1


def _find_class_attributes_start(lines: list, class_name: str, class_line_idx: int) -> int:
    """Find where attributes for a class start (colon syntax)."""
    for i in range(class_line_idx + 1, len(lines)):
        line = lines[i].strip()
        # Check if it's an attribute line: ClassName : +attr Type
        if re.match(rf'^{re.escape(class_name)}\s*:\s*[+\-#~]', line):
            return i
        # Check if we've hit another class definition or relationship
        if line.startswith('class ') or re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*(<|--|\.\.|o--|\*--)', line):
            break
    return -1


def _find_class_attributes_end(lines: list, class_name: str, start_idx: int) -> int:
    """Find where attributes for a class end."""
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        # Stop if we hit a non-attribute line for this class
        if not re.match(rf'^{re.escape(class_name)}\s*:\s*', line):
            return i
    return len(lines)


def _apply_add_class(lines: list, details: dict) -> list:
    """Add a new class to the diagram."""
    class_name = details.get("name")
    if not class_name:
        return lines
    
    attributes = details.get("attributes", [])
    methods = details.get("methods", [])
    position = details.get("position", "end")
    
    new_lines = [f"class {class_name}"]
    for attr in attributes:
        new_lines.append(f"{class_name} : {attr}")
    for method in methods:
        new_lines.append(f"{class_name} : {method}")
    
    # Find insertion point
    if position == "end":
        # Find last class definition
        insert_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('class '):
                # Find end of this class (next class or relationship)
                existing_class_name = lines[i].strip().split()[1] if len(lines[i].strip().split()) > 1 else ""
                insert_idx = i + 1
                while insert_idx < len(lines) and \
                      (lines[insert_idx].strip().startswith(existing_class_name + ' :') or 
                       lines[insert_idx].strip() == ''):
                    insert_idx += 1
                break
    elif position.startswith("after:"):
        after_class = position.split(":", 1)[1]
        idx = _find_class_definition(lines, after_class)
        if idx >= 0:
            # Find end of this class
            insert_idx = idx + 1
            while insert_idx < len(lines) and \
                  (lines[insert_idx].strip().startswith(after_class + ' :') or 
                   lines[insert_idx].strip() == ''):
                insert_idx += 1
        else:
            insert_idx = len(lines)
    elif position.startswith("before:"):
        before_class = position.split(":", 1)[1]
        insert_idx = _find_class_definition(lines, before_class)
        if insert_idx < 0:
            insert_idx = len(lines)
    else:
        insert_idx = len(lines)
    
    # Insert the new class
    lines[insert_idx:insert_idx] = new_lines
    return lines


def _apply_remove_class(lines: list, class_name: str) -> list:
    """Remove a class and all its attributes/methods and relationships."""
    class_idx = _find_class_definition(lines, class_name)
    if class_idx < 0:
        return lines
    
    # Find all lines related to this class
    indices_to_remove = [class_idx]
    
    # Remove attribute/method lines
    for i in range(class_idx + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith(f"{class_name} :"):
            indices_to_remove.append(i)
        elif line.startswith('class ') or re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*(<|--|\.\.|o--|\*--)', line):
            break
    
    # Remove relationships involving this class
    for i in range(len(lines) - 1, -1, -1):
        if i in indices_to_remove:
            continue
        line = lines[i].strip()
        # Check if this line contains a relationship with the class
        if re.search(rf'\b{re.escape(class_name)}\b', line) and \
           re.search(r'(<|--|\.\.|o--|\*--)', line):
            indices_to_remove.append(i)
    
    # Remove note lines
    for i in range(len(lines) - 1, -1, -1):
        if i in indices_to_remove:
            continue
        line = lines[i].strip()
        if line.startswith('note ') and class_name in line:
            indices_to_remove.append(i)
    
    # Remove in reverse order to maintain indices
    for idx in sorted(indices_to_remove, reverse=True):
        lines.pop(idx)
    
    return lines


def _apply_modify_class(lines: list, class_name: str, details: dict) -> list:
    """Modify an existing class."""
    class_idx = _find_class_definition(lines, class_name)
    if class_idx < 0:
        return lines
    
    # Rename class if needed
    new_name = details.get("new_name")
    if new_name and new_name != class_name:
        # Rename class definition
        lines[class_idx] = lines[class_idx].replace(f"class {class_name}", f"class {new_name}")
        # Rename all attribute/method lines
        for i in range(class_idx + 1, len(lines)):
            if lines[i].strip().startswith(f"{class_name} :"):
                lines[i] = lines[i].replace(f"{class_name} :", f"{new_name} :")
            elif lines[i].strip().startswith('class ') or \
                 re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*(<|--|\.\.|o--|\*--)', lines[i].strip()):
                break
        # Rename in relationships
        for i in range(len(lines)):
            lines[i] = re.sub(rf'\b{re.escape(class_name)}\b', new_name, lines[i])
        class_name = new_name
    
    # Find attribute/method section
    attr_start = _find_class_attributes_start(lines, class_name, class_idx)
    if attr_start < 0:
        attr_start = class_idx + 1
    
    attr_end = _find_class_attributes_end(lines, class_name, attr_start)
    
    # Handle attribute modifications
    remove_attrs = details.get("remove_attributes", [])
    add_attrs = details.get("add_attributes", [])
    modify_attrs = details.get("modify_attributes", [])
    
    # Remove attributes
    for attr_name in remove_attrs:
        for i in range(attr_end - 1, attr_start - 1, -1):
            if attr_name in lines[i] and lines[i].strip().startswith(f"{class_name} :"):
                lines.pop(i)
                attr_end -= 1
                break
    
    # Modify attributes
    for mod in modify_attrs:
        old_attr = mod.get("old", "")
        new_attr = mod.get("new", "")
        for i in range(attr_start, attr_end):
            if old_attr in lines[i]:
                lines[i] = lines[i].replace(old_attr, new_attr)
                break
    
    # Add attributes
    position = details.get("position", "end")
    for attr in add_attrs:
        if position == "end":
            lines.insert(attr_end, f"{class_name} : {attr}")
            attr_end += 1
        # Could add more position logic here
    
    # Handle method modifications (similar to attributes)
    remove_methods = details.get("remove_methods", [])
    add_methods = details.get("add_methods", [])
    modify_methods = details.get("modify_methods", [])
    
    # Re-find attribute/method section after modifications
    attr_start = _find_class_attributes_start(lines, class_name, class_idx)
    if attr_start < 0:
        attr_start = class_idx + 1
    attr_end = _find_class_attributes_end(lines, class_name, attr_start)
    
    # Remove methods
    for method_name in remove_methods:
        for i in range(attr_end - 1, attr_start - 1, -1):
            if method_name in lines[i] and lines[i].strip().startswith(f"{class_name} :"):
                lines.pop(i)
                attr_end -= 1
                break
    
    # Modify methods
    for mod in modify_methods:
        old_method = mod.get("old", "")
        new_method = mod.get("new", "")
        for i in range(attr_start, attr_end):
            if old_method in lines[i]:
                lines[i] = lines[i].replace(old_method, new_method)
                break
    
    # Add methods
    for method in add_methods:
        lines.insert(attr_end, f"{class_name} : {method}")
        attr_end += 1
    
    return lines


def _apply_add_relationship(lines: list, details: dict) -> list:
    """Add a relationship between classes."""
    from_class = details.get("from")
    to_class = details.get("to")
    rel_type = details.get("type", "-->")
    label = details.get("label", "")
    mult_from = details.get("multiplicity_from")
    mult_to = details.get("multiplicity_to")
    
    if not from_class or not to_class:
        return lines
    
    # Build relationship line
    if mult_from and mult_to:
        rel_line = f'{from_class} "{mult_from}" {rel_type} "{mult_to}" {to_class}'
    elif mult_from:
        rel_line = f'{from_class} "{mult_from}" {rel_type} {to_class}'
    elif mult_to:
        rel_line = f'{from_class} {rel_type} "{mult_to}" {to_class}'
    else:
        rel_line = f'{from_class} {rel_type} {to_class}'
    
    if label:
        rel_line += f' : {label}'
    
    # Find insertion point (after class definitions, before notes)
    insert_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith('note '):
            insert_idx = i
        elif re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*(<|--|\.\.|o--|\*--)', line):
            insert_idx = i + 1
            break
    
    lines.insert(insert_idx, rel_line)
    return lines


def _apply_remove_relationship(lines: list, details: dict) -> list:
    """Remove a relationship between classes."""
    from_class = details.get("from")
    to_class = details.get("to")
    rel_type = details.get("type")
    
    if not from_class or not to_class:
        return lines
    
    # Find and remove matching relationship
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if from_class in line and to_class in line and \
           (rel_type is None or rel_type in line) and \
           re.search(r'(<|--|\.\.|o--|\*--)', line):
            lines.pop(i)
            break
    
    return lines


def _apply_modify_relationship(lines: list, details: dict) -> list:
    """Modify an existing relationship."""
    from_class = details.get("from")
    to_class = details.get("to")
    old_type = details.get("old_type")
    new_type = details.get("new_type")
    new_label = details.get("new_label")
    new_mult_from = details.get("new_multiplicity_from")
    new_mult_to = details.get("new_multiplicity_to")
    
    if not from_class or not to_class:
        return lines
    
    # Find the relationship line
    for i, line in enumerate(lines):
        if from_class in line and to_class in line and \
           (old_type is None or old_type in line) and \
           re.search(r'(<|--|\.\.|o--|\*--)', line):
            # Rebuild the relationship line
            if new_mult_from and new_mult_to:
                new_line = f'{from_class} "{new_mult_from}" {new_type} "{new_mult_to}" {to_class}'
            elif new_mult_from:
                new_line = f'{from_class} "{new_mult_from}" {new_type} {to_class}'
            elif new_mult_to:
                new_line = f'{from_class} {new_type} "{new_mult_to}" {to_class}'
            else:
                # Replace old_type with new_type in the line
                if old_type:
                    new_line = re.sub(rf'{re.escape(old_type)}', new_type, line)
                else:
                    # Replace any relationship type with new_type
                    new_line = re.sub(r'(<\|--|--|\.\.>|o--|\*--)', new_type, line)
                # Ensure from_class and to_class are at the start and end
                # Extract existing multiplicities and label if any
                existing_label = None
                if ' : ' in line:
                    parts = line.split(' : ', 1)
                    existing_label = parts[1] if len(parts) > 1 else None
                    line_without_label = parts[0]
                else:
                    line_without_label = line
                
                # Check for multiplicities in the original line
                mult_match = re.search(rf'{re.escape(from_class)}\s*"([^"]+)"\s*{re.escape(old_type)}\s*"([^"]+)"\s*{re.escape(to_class)}', line_without_label)
                if mult_match:
                    new_line = f'{from_class} "{mult_match.group(1)}" {new_type} "{mult_match.group(2)}" {to_class}'
                else:
                    mult_match = re.search(rf'{re.escape(from_class)}\s*"([^"]+)"\s*{re.escape(old_type)}\s*{re.escape(to_class)}', line_without_label)
                    if mult_match:
                        new_line = f'{from_class} "{mult_match.group(1)}" {new_type} {to_class}'
                    else:
                        mult_match = re.search(rf'{re.escape(from_class)}\s*{re.escape(old_type)}\s*"([^"]+)"\s*{re.escape(to_class)}', line_without_label)
                        if mult_match:
                            new_line = f'{from_class} {new_type} "{mult_match.group(1)}" {to_class}'
                        else:
                            new_line = f'{from_class} {new_type} {to_class}'
            
            if new_label:
                new_line += f' : {new_label}'
            elif existing_label:
                new_line += f' : {existing_label}'
            
            lines[i] = new_line
            break
    
    return lines


def _apply_add_attribute(lines: list, class_name: str, details: dict) -> list:
    """Add an attribute to a class."""
    attribute = details.get("attribute")
    if not attribute:
        return lines
    
    class_idx = _find_class_definition(lines, class_name)
    if class_idx < 0:
        return lines
    
    attr_start = _find_class_attributes_start(lines, class_name, class_idx)
    if attr_start < 0:
        attr_start = class_idx + 1
    
    attr_end = _find_class_attributes_end(lines, class_name, attr_start)
    
    new_line = f"{class_name} : {attribute}"
    lines.insert(attr_end, new_line)
    return lines


def _apply_remove_attribute(lines: list, class_name: str, details: dict) -> list:
    """Remove an attribute from a class."""
    attribute = details.get("attribute")
    if not attribute:
        return lines
    
    class_idx = _find_class_definition(lines, class_name)
    if class_idx < 0:
        return lines
    
    attr_start = _find_class_attributes_start(lines, class_name, class_idx)
    if attr_start < 0:
        return lines
    
    attr_end = _find_class_attributes_end(lines, class_name, attr_start)
    
    # Find and remove exact match
    for i in range(attr_end - 1, attr_start - 1, -1):
        if attribute in lines[i] and lines[i].strip().startswith(f"{class_name} :"):
            lines.pop(i)
            break
    
    return lines


def _apply_modify_attribute(lines: list, class_name: str, details: dict) -> list:
    """Modify an attribute in a class."""
    old_attr = details.get("old")
    new_attr = details.get("new")
    if not old_attr or not new_attr:
        return lines
    
    class_idx = _find_class_definition(lines, class_name)
    if class_idx < 0:
        return lines
    
    attr_start = _find_class_attributes_start(lines, class_name, class_idx)
    if attr_start < 0:
        return lines
    
    attr_end = _find_class_attributes_end(lines, class_name, attr_start)
    
    for i in range(attr_start, attr_end):
        if old_attr in lines[i]:
            lines[i] = lines[i].replace(old_attr, new_attr)
            break
    
    return lines


def _apply_add_method(lines: list, class_name: str, details: dict) -> list:
    """Add a method to a class."""
    method = details.get("method")
    if not method:
        return lines
    
    class_idx = _find_class_definition(lines, class_name)
    if class_idx < 0:
        return lines
    
    attr_start = _find_class_attributes_start(lines, class_name, class_idx)
    if attr_start < 0:
        attr_start = class_idx + 1
    
    attr_end = _find_class_attributes_end(lines, class_name, attr_start)
    
    new_line = f"{class_name} : {method}"
    lines.insert(attr_end, new_line)
    return lines


def _apply_remove_method(lines: list, class_name: str, details: dict) -> list:
    """Remove a method from a class."""
    method = details.get("method")
    if not method:
        return lines
    
    class_idx = _find_class_definition(lines, class_name)
    if class_idx < 0:
        return lines
    
    attr_start = _find_class_attributes_start(lines, class_name, class_idx)
    if attr_start < 0:
        return lines
    
    attr_end = _find_class_attributes_end(lines, class_name, attr_start)
    
    for i in range(attr_end - 1, attr_start - 1, -1):
        if method in lines[i] and lines[i].strip().startswith(f"{class_name} :"):
            lines.pop(i)
            break
    
    return lines


def _apply_modify_method(lines: list, class_name: str, details: dict) -> list:
    """Modify a method in a class."""
    old_method = details.get("old")
    new_method = details.get("new")
    if not old_method or not new_method:
        return lines
    
    class_idx = _find_class_definition(lines, class_name)
    if class_idx < 0:
        return lines
    
    attr_start = _find_class_attributes_start(lines, class_name, class_idx)
    if attr_start < 0:
        return lines
    
    attr_end = _find_class_attributes_end(lines, class_name, attr_start)
    
    for i in range(attr_start, attr_end):
        if old_method in lines[i]:
            lines[i] = lines[i].replace(old_method, new_method)
            break
    
    return lines


def _apply_add_participant(lines: list, details: dict) -> list:
    """Add a participant to a sequence diagram."""
    name = details.get("name")
    if not name:
        return lines
    
    # Find where participants are defined
    insert_idx = 1  # After sequenceDiagram line
    for i, line in enumerate(lines):
        if line.strip().startswith('sequenceDiagram'):
            insert_idx = i + 1
            # Find end of participant definitions
            for j in range(i + 1, len(lines)):
                if not lines[j].strip().startswith('participant '):
                    insert_idx = j
                    break
            break
    
    lines.insert(insert_idx, f"participant {name}")
    return lines


def _apply_remove_participant(lines: list, participant_name: str) -> list:
    """Remove a participant and all its messages."""
    # Remove participant definition - handle both quoted and unquoted names
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        # Match: participant "NLP Extractor" or participant NLP_Extractor
        if line.startswith('participant '):
            # Extract the participant name from the line (handle quotes)
            parts = line.split('participant ', 1)
            if len(parts) > 1:
                name_in_line = parts[1].strip().strip('"').strip("'")
                if name_in_line == participant_name or participant_name in line:
                    lines.pop(i)
                    break
    
    # Remove messages involving this participant
    # Match participant name in message lines (handle quotes)
    quoted_name = f'"{participant_name}"'
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if re.search(r'(->>|-->>|->|-->)', line):
            # Check if participant name (quoted or unquoted) appears in the message line
            # Split by : to get the participant part (before the message text)
            if ':' in line:
                participant_part = line.split(':', 1)[0]
            else:
                participant_part = line
            
            # Check if quoted or unquoted name appears in participant part
            if quoted_name in participant_part or participant_name in participant_part:
                lines.pop(i)
    
    # Remove activate/deactivate lines for this participant
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith('activate ') or line.startswith('deactivate '):
            # Extract the participant name from activate/deactivate line
            parts = line.split(' ', 1)
            if len(parts) > 1:
                name_in_line = parts[1].strip().strip('"').strip("'")
                if name_in_line == participant_name:
                    lines.pop(i)
    
    return lines


def _apply_add_message(lines: list, details: dict) -> list:
    """Add a message to a sequence diagram."""
    from_participant = details.get("from")
    to_participant = details.get("to")
    message = details.get("message", "")
    msg_type = details.get("type", "->>")
    position = details.get("position", "end")
    
    if not from_participant or not to_participant:
        return lines
    
    # Handle newlines in message - Mermaid doesn't support \n in message labels
    # Replace \n with space or keep as single line
    # For multi-line messages, we'll keep them as a single line with the \n as literal text
    # (Mermaid will render it, though it's not ideal)
    message_clean = message.replace('\\n', ' ')  # Replace \n with space for cleaner output
    
    # Quote participant names if they contain spaces and aren't already quoted
    def quote_if_needed(name):
        if ' ' in name and not (name.startswith('"') and name.endswith('"')):
            return f'"{name}"'
        return name
    
    from_quoted = quote_if_needed(from_participant)
    to_quoted = quote_if_needed(to_participant)
    
    new_line = f"{from_quoted}{msg_type}{to_quoted}: {message_clean}"
    
    # Find insertion point based on position parameter
    insert_idx = len(lines)
    
    if position.startswith("after:"):
        # Find message containing the specified text
        search_text = position.split(":", 1)[1].strip()
        for i, line in enumerate(lines):
            if search_text in line and re.search(r'(->>|-->>|->|-->)', line):
                insert_idx = i + 1
                break
    elif position.startswith("before:"):
        # Find message containing the specified text
        search_text = position.split(":", 1)[1].strip()
        for i, line in enumerate(lines):
            if search_text in line and re.search(r'(->>|-->>|->|-->)', line):
                insert_idx = i
                break
    else:
        # Default: find last message and insert after it
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if re.search(r'(->>|-->>|->|-->)', line):
                insert_idx = i + 1
                break
    
    lines.insert(insert_idx, new_line)
    return lines


def _apply_remove_message(lines: list, details: dict) -> list:
    """Remove a message from a sequence diagram."""
    from_participant = details.get("from")
    to_participant = details.get("to")
    message = details.get("message")
    
    if not from_participant or not to_participant:
        return lines
    
    # Normalize message for matching (handle newlines)
    if message:
        # Replace \n with actual newline for matching
        message_normalized = message.replace('\\n', '\n')
        # Also try matching parts of the message
        message_parts = message_normalized.split('\n')
    else:
        message_parts = []
    
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if from_participant in line and to_participant in line and \
           re.search(r'(->>|-->>|->|-->)', line):
            if message is None:
                # Remove any message between these participants
                lines.pop(i)
                break
            else:
                # Check if message matches (handle newlines and partial matches)
                line_normalized = line.replace('\\n', '\n')
                if message_normalized in line_normalized or message in line:
                    lines.pop(i)
                    break
                # Also try matching if any part of the message is in the line
                elif message_parts and any(part.strip() in line for part in message_parts if part.strip()):
                    lines.pop(i)
                    break
    
    return lines


def _apply_add_state(lines: list, details: dict) -> list:
    """Add a state to a state diagram."""
    name = details.get("name")
    parent = details.get("parent")
    
    if not name:
        return lines
    
    if parent:
        # Find parent state block
        in_parent = False
        for i, line in enumerate(lines):
            if f"state {parent}" in line:
                in_parent = True
            elif in_parent and line.strip() == "}":
                lines.insert(i, f"    {name}")
                break
    else:
        # Add at end
        lines.append(name)
    
    return lines


def _apply_remove_state(lines: list, state_name: str) -> list:
    """Remove a state and its transitions."""
    # Remove state definition
    for i in range(len(lines) - 1, -1, -1):
        if state_name in lines[i] and not re.search(r'(->|\[)', lines[i]):
            lines.pop(i)
            break
    
    # Remove transitions involving this state
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if state_name in line and re.search(r'->', line):
            lines.pop(i)
    
    return lines


def _apply_add_transition(lines: list, details: dict) -> list:
    """Add a transition to a state diagram."""
    from_state = details.get("from")
    to_state = details.get("to")
    label = details.get("label", "")
    
    if not from_state or not to_state:
        return lines
    
    if label:
        new_line = f"{from_state} --> {to_state} : {label}"
    else:
        new_line = f"{from_state} --> {to_state}"
    
    # Find insertion point
    insert_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if re.search(r'-->', lines[i]):
            insert_idx = i + 1
            break
    
    lines.insert(insert_idx, new_line)
    return lines


def _apply_remove_transition(lines: list, details: dict) -> list:
    """Remove a transition from a state diagram."""
    from_state = details.get("from")
    to_state = details.get("to")
    
    if not from_state or not to_state:
        return lines
    
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if from_state in line and to_state in line and '-->' in line:
            lines.pop(i)
            break
    
    return lines


def _apply_add_note(lines: list, details: dict) -> list:
    """Add a note to the diagram."""
    target = details.get("target")
    text = details.get("text", "")
    
    if not target or not text:
        return lines
    
    new_line = f'note for {target} "{text}"'
    lines.append(new_line)
    return lines


def _apply_remove_note(lines: list, details: dict) -> list:
    """Remove a note from the diagram."""
    target = details.get("target")
    
    if not target:
        return lines
    
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith('note ') and target in lines[i]:
            lines.pop(i)
            break
    
    return lines


def _apply_modify_note(lines: list, details: dict) -> list:
    """Modify an existing note."""
    target = details.get("target")
    new_text = details.get("new_text", "")
    
    if not target or not new_text:
        return lines
    
    for i, line in enumerate(lines):
        if line.strip().startswith('note ') and target in line:
            lines[i] = f'note for {target} "{new_text}"'
            break
    
    return lines


def edit_diagram_mermaid(user_prompt: str, existing_mermaid_code: str) -> str:
    """
    Calls OpenAI API to generate edit instructions, then applies them to existing Mermaid code.

    Args:
        user_prompt (str): The user's prompt describing what changes to make to the diagram.
        existing_mermaid_code (str): The existing Mermaid diagram code to modify.

    Returns:
        str: The updated Mermaid code for the UML diagram.
    """
    try:
        openai_client = get_openai_client()
        
        system_prompt = MERMAID_EDIT_SYSTEM_PROMPT

        # Create a user message that includes both the existing code and the edit request
        user_message = f"""Existing Mermaid diagram code:
{existing_mermaid_code}

User's edit request: {user_prompt}

Generate edit instructions in JSON format as specified in the system prompt."""

        logger.info(f"Editing Mermaid UML diagram. Edit request: {user_prompt[:100]}...")
        logger.debug(f"Existing code length: {len(existing_mermaid_code)} chars")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=messages,
            temperature=0.3,
            top_p=0.7,
            stream=False,
        )

        # Log the LLM call
        log_llm_call(
            model=OPENAI_MODEL_NAME,
            messages=messages,
            response=response,
            temperature=0.3,
            top_p=0.7,
            function_name="edit_diagram_mermaid"
        )

        raw_answer = response.choices[0].message.content.strip()
        
        # Extract JSON from response (remove markdown code blocks if present)
        json_text = raw_answer
        if '```' in json_text:
            # Try to extract JSON from code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', json_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
        else:
            # Try to find JSON object in the text
            json_match = re.search(r'\{.*\}', json_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
        
        # Parse JSON edit instructions
        try:
            edit_instructions = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON edit instructions: {e}")
            logger.error(f"Raw response: {raw_answer[:500]}")
            raise ValueError(f"Failed to parse edit instructions as JSON: {e}")
        
        logger.info(f"Parsed edit instructions with {len(edit_instructions.get('edits', []))} edits")
        
        # Apply edits using the reliable edit application function
        updated_mermaid_code = apply_mermaid_edit(existing_mermaid_code, edit_instructions)
        
        logger.info(f"Updated Mermaid code (length: {len(updated_mermaid_code)} chars)")
        
        # Log the post-edit mermaid code
        log_mermaid_code(
            mermaid_code=updated_mermaid_code,
            code_type="post_edit",
            function_name="edit_diagram_mermaid",
            context=f"Edit request: {user_prompt[:200]}"
        )
        
        return updated_mermaid_code

    except Exception as e:
        # Log the error
        log_llm_call(
            model=OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": MERMAID_EDIT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message if 'user_message' in locals() else f"Edit request: {user_prompt}"}
            ],
            temperature=0.3,
            top_p=0.7,
            error=str(e),
            function_name="edit_diagram_mermaid"
        )
        logger.error(f"Error while editing Mermaid diagram: {e}", exc_info=True)
        raise

