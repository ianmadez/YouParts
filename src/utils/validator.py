import re
from typing import Dict, Any


def clean_url(url: str) -> str:
    """Strips tracking query parameters from YouTube URLs."""
    if not url:
        return ""
    return re.sub(r"(\?|&)si=[^&]+", "", url)


def normalize_part_dict(p: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures raw AI component dictionaries match standard manifest schema."""
    return {
        "part_name": str(
            p.get("part_name") or p.get("name") or p.get("item") or "Unknown Component"
        ).strip(),
        "category": str(p.get("category") or p.get("type") or "Hardware").strip(),
        "quantity": str(
            p.get("quantity") or p.get("qty") or p.get("count") or "1"
        ).strip(),
        "specs_and_dimensions": p.get("specs_and_dimensions"),
        "alternative_parts": p.get("alternative_parts", []),
        "logic_gap_warning": p.get("logic_gap_warning"),
    }
