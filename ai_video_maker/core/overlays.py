"""Keep only explicit, purposeful visual emphasis requests."""
from __future__ import annotations

SUPPORTED = {"question_mark", "exclamation_mark", "check_mark", "warning_mark",
             "short_arrow", "small_highlight", "underline_emphasis", "spark"}
ALIASES = {"exclamation": "exclamation_mark", "warning": "warning_mark", "arrow": "short_arrow"}


def normalize_overlays(raw, archetype: str = "example", character_visible: bool = False) -> list[dict]:
    if not isinstance(raw, list):
        return []
    result = []
    for item in raw:
        if isinstance(item, str):
            kind = ALIASES.get(item, item)
            target = "character" if kind in {"question_mark", "exclamation_mark", "warning_mark"} else "focus_object"
        elif isinstance(item, dict):
            kind = ALIASES.get(item.get("type"), item.get("type"))
            target = item.get("target") or "focus_object"
        else:
            continue
        if kind not in SUPPORTED:
            continue
        if kind == "short_arrow" and archetype not in {"cause_effect", "process"}:
            continue
        if kind == "question_mark" and archetype != "question_reveal":
            continue
        if kind == "check_mark" and archetype not in {"takeaway", "example"}:
            continue
        if target == "character" and not character_visible:
            continue
        if target not in {"character", "focus_object"}:
            target = "focus_object"
        if any(existing["type"] == kind and existing["target"] == target for existing in result):
            continue
        result.append({"type": kind, "target": target})
        if len(result) == 2:
            break
    return result
