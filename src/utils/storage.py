import os
import json
import pandas as pd
from typing import Dict, Any, List

SAVED_DIR = "saved_manifests"


def save_manifest(
    build_focus: str, master_data: Dict[str, Any], analyzed_videos: List[Dict[str, Any]]
) -> str:
    """Saves the current workspace manifest to disk."""
    os.makedirs(SAVED_DIR, exist_ok=True)
    clean_name = "".join(
        c if c.isalnum() or c in (" ", "_") else "" for c in build_focus
    )
    filename = f"{clean_name.replace(' ', '_').lower()[:30]}_manifest.json"
    filepath = os.path.join(SAVED_DIR, filename)

    payload = {
        "build_focus": build_focus,
        "master_bom": master_data,
        "analyzed_videos": analyzed_videos,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return filepath


def list_saved_manifests() -> List[str]:
    """Returns a list of all locally saved manifest filenames."""
    if not os.path.exists(SAVED_DIR):
        return []
    return [f for f in os.listdir(SAVED_DIR) if f.endswith(".json")]


def load_manifest(filename: str) -> Dict[str, Any]:
    """Loads a manifest file from disk."""
    filepath = os.path.join(SAVED_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
