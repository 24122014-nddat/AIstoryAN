from __future__ import annotations

import json
import re
from typing import Any

def parse_story_output(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    data = _try_parse_json(text)
    if not isinstance(data, dict):
        data = {}

    story = _clean_text(data.get("story")) or _fallback_story(text)
    foundation = _clean_text(data.get("foundation"))
    choices = _normalize_choices(data.get("choices"))
    state_updates = _normalize_state_updates(data.get("state_updates"))

    return {
        "foundation": foundation,
        "story": story,
        "choices": choices,
        "state_updates": state_updates,
    }

def _normalize_state_updates(value: Any) -> dict[str, Any]:
    """
    Normalizes state_updates to ensure it has the required structure.
    
    Args:
        value: The raw state_updates value from JSON
    
    Returns:
        A normalized dictionary with:
        - gold_change: int (default 0)
        - items_acquired: list[str] (default [])
    """
    if not isinstance(value, dict):
        return {"gold_change": 0, "items_acquired": []}
    
    # Ensure gold_change is an integer
    gold_change = value.get("gold_change", 0)
    if not isinstance(gold_change, int):
        try:
            gold_change = int(gold_change)
        except (ValueError, TypeError):
            gold_change = 0
    
    # Ensure items_acquired is a list of strings
    items_acquired = value.get("items_acquired", [])
    if not isinstance(items_acquired, list):
        items_acquired = []
    else:
        # Filter to only include strings
        items_acquired = [str(item) for item in items_acquired if isinstance(item, (str, int, float))]
    
    return {
        "gold_change": gold_change,
        "items_acquired": items_acquired,
    }

def _try_parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S | re.I)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except Exception:
            pass

    obj = re.search(r"\{.*\}", text, flags=re.S)
    if obj:
        try:
            return json.loads(obj.group(0))
        except Exception:
            pass

    return None

def _clean_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""

def _normalize_choices(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    choices: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        text = re.sub(r"^\s*[-*\d.)]+\s*", "", item).strip()
        if 3 <= len(text) <= 220:
            choices.append(text)
    return list(dict.fromkeys(choices))[:4]

def _fallback_story(text: str) -> str:
    text = re.sub(r"```(?:json)?", "", text, flags=re.I).replace("```", "").strip()
    return text or "Không có phản hồi từ AI."
