from config.settings import settings
from config.prompts import EXTRACTION_SYSTEM_PROMPT, VideoBOMExtraction, LogicGap
from src.ai_engine.groq_client import groq_client

# Fresh LLM regeneration attempts when the model returns a structurally invalid
# schema. Transport/API retries are handled inside groq_client.chat_json; this
# loop re-calls the model so a "successful API call with garbage schema" is
# retried rather than falling straight through to the fallback extraction.
LOCAL_REGENERATION_ATTEMPTS = 2


class BOMExtractorEngine:
    """Uses Groq (llama-3.3-70b-versatile) to extract hallucination-free BOMs with logic gap detection."""

    def extract_bom_from_video(self, video_data: dict) -> VideoBOMExtraction:
        """Extracts structured parts list and resources from a single video dictionary."""
        payload = {
            "video_id": video_data.get("video_id"),
            "video_title": video_data.get("title"),
            "video_url": video_data.get("url"),
            "description": video_data.get("description", ""),
            "transcript_summary": video_data.get("transcript_summary", "")[:2000],
        }

        last_error = None
        for attempt in range(LOCAL_REGENERATION_ATTEMPTS):
            try:
                parsed_data = groq_client.chat_json(
                    model=settings.EXTRACTION_MODEL,
                    system_prompt=EXTRACTION_SYSTEM_PROMPT,
                    user_payload=payload,
                    temperature=0.0,  # Zero temperature for maximum deterministic adherence
                )

                # Normalize keys and raw string variations in external_resources
                raw_resources = parsed_data.get("external_resources", [])
                clean_resources = []
                if isinstance(raw_resources, list):
                    for item in raw_resources:
                        if isinstance(item, str):
                            clean_resources.append(
                                {
                                    "resource_type": "External Link",
                                    "title": "Resource Link",
                                    "url": item,
                                }
                            )
                        elif isinstance(item, dict):
                            res_type = (
                                item.get("resource_type")
                                or item.get("type")
                                or "External Link"
                            )
                            title = (
                                item.get("title")
                                or item.get("name")
                                or item.get("description")
                                or "Resource Link"
                            )
                            url = item.get("url") or item.get("link") or ""
                            if url:
                                clean_resources.append(
                                    {
                                        "resource_type": str(res_type),
                                        "title": str(title),
                                        "url": str(url),
                                    }
                                )
                parsed_data["external_resources"] = clean_resources

                # Alias check for parts lists if key was named differently by LLM
                if not parsed_data.get("required_parts"):
                    for alias in [
                        "parts",
                        "components",
                        "bom",
                        "items",
                        "materials",
                        "required_components",
                    ]:
                        if parsed_data.get(alias) and isinstance(
                            parsed_data[alias], list
                        ):
                            parsed_data["required_parts"] = parsed_data[alias]
                            break

                # Normalize parts list required keys
                for part_key in ["required_parts", "optional_parts"]:
                    raw_parts = parsed_data.get(part_key, [])
                    clean_parts = []
                    if isinstance(raw_parts, list):
                        for p in raw_parts:
                            if isinstance(p, str):
                                clean_parts.append(
                                    {
                                        "part_name": p,
                                        "category": "Hardware",
                                        "quantity": "1",
                                        "specs_and_dimensions": None,
                                        "alternative_parts": [],
                                        "logic_gap_warning": None,
                                    }
                                )
                            elif isinstance(p, dict):
                                p["part_name"] = str(
                                    p.get("part_name")
                                    or p.get("name")
                                    or p.get("item")
                                    or p.get("title")
                                    or "Unknown Component"
                                )
                                p["category"] = str(
                                    p.get("category") or p.get("type") or "Hardware"
                                )
                                p["quantity"] = str(
                                    p.get("quantity")
                                    or p.get("qty")
                                    or p.get("count")
                                    or "1"
                                )
                                clean_parts.append(p)
                    parsed_data[part_key] = clean_parts

                # Enforce source video metadata context
                parsed_data["video_id"] = video_data.get("video_id", "")
                parsed_data["video_title"] = video_data.get("title", "")
                parsed_data["video_url"] = video_data.get("url", "")

                return VideoBOMExtraction(**parsed_data)

            except Exception as e:
                last_error = e
                print(
                    f"[YouParts Extractor] Regeneration attempt {attempt + 1}/"
                    f"{LOCAL_REGENERATION_ATTEMPTS} due to error: {e}"
                )

        # Fallback: explicitly flag the failure as a logic gap (never a silent
        # empty BOM that looks successful). Video metadata is populated so the
        # gap is attributable to a source video in the workspace.
        return VideoBOMExtraction(
            video_id=video_data.get("video_id", ""),
            video_title=video_data.get("title", ""),
            video_url=video_data.get("url", ""),
            overall_logic_gaps=[
                LogicGap(description=f"Failed to extract BOM: {last_error}")
            ],
        )

    def aggregate_master_bom(self, extractions: list[VideoBOMExtraction]) -> dict:
        """Combines multiple video extractions into a deduplicated master project manifest."""
        raw_parts = []
        master_resources = []
        all_logic_gaps = []

        for ext in extractions:
            for item in ext.required_parts:
                item_dict = item.model_dump()

                # Flag unspecified quantities for hardware/fasteners
                if (
                    item_dict.get("logic_gap_warning")
                    and item_dict.get("quantity") == "1"
                ):
                    item_dict["quantity"] = "Unspecified"

                item_dict["source_video_title"] = ext.video_title
                item_dict["source_video_url"] = ext.video_url
                raw_parts.append(item_dict)

            for res in ext.external_resources:
                res_dict = res.model_dump()
                res_dict["source_video_title"] = ext.video_title
                master_resources.append(res_dict)

            if ext.overall_logic_gaps:
                for gap in ext.overall_logic_gaps:
                    gap_dict = gap.model_dump()
                    gap_dict["source_video_title"] = ext.video_title
                    gap_dict["source_video_url"] = ext.video_url
                    all_logic_gaps.append(gap_dict)

        # Deduplicate and consolidate duplicate parts across videos
        consolidated_parts = []
        seen_names = {}

        for part in raw_parts:
            norm_name = part["part_name"].strip().lower()
            if norm_name in seen_names:
                existing = seen_names[norm_name]
                # Audit trail: record the duplicate's original name(s)
                existing.setdefault("merged_from", [])
                if part["part_name"] not in existing["merged_from"]:
                    existing["merged_from"].append(part["part_name"])
                for src_name in part.get("merged_from") or []:
                    if src_name not in existing["merged_from"]:
                        existing["merged_from"].append(src_name)
                # Preserve purchase state across merges
                existing["bought"] = existing.get("bought", False) or part.get(
                    "bought", False
                )
                # Combine specs if the existing one is empty
                if not existing.get("specs_and_dimensions") and part.get(
                    "specs_and_dimensions"
                ):
                    existing["specs_and_dimensions"] = part["specs_and_dimensions"]
            else:
                seen_names[norm_name] = part
                consolidated_parts.append(part)

        return {
            "parts_manifest": consolidated_parts,
            "external_resources": master_resources,
            "logic_gaps": all_logic_gaps,
        }
