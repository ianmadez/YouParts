import time
import json
from groq import Groq
from config.settings import settings
from config.prompts import EXTRACTION_SYSTEM_PROMPT, VideoBOMExtraction


class BOMExtractorEngine:
    """Uses Groq (llama-3.3-70b-versatile) to extract hallucination-free BOMs with logic gap detection."""

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def extract_bom_from_video(self, video_data: dict) -> VideoBOMExtraction:
        """Extracts structured parts list and resources from a single video dictionary."""
        time.sleep(settings.REQUEST_DELAY_SECONDS)

        payload = {
            "video_id": video_data.get("video_id"),
            "video_title": video_data.get("title"),
            "video_url": video_data.get("url"),
            "description": video_data.get("description", ""),
            "transcript_summary": video_data.get("transcript_summary", "")[:2000],
        }

        retries = 0
        while retries < settings.MAX_RETRIES:
            try:
                response = self.client.chat.completions.create(
                    model=settings.EXTRACTION_MODEL,
                    messages=[
                        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps(payload)},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,  # Zero temperature for maximum deterministic adherence
                )

                raw_json = response.choices[0].message.content
                parsed_data = json.loads(raw_json)

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
                retries += 1
                print(
                    f"[YouParts Extractor] Retry {retries}/{settings.MAX_RETRIES} due to error: {e}"
                )
                time.sleep(settings.REQUEST_DELAY_SECONDS * 2)

        # Fallback empty extraction if max retries reached
        return VideoBOMExtraction(
            video_id=video_data.get("video_id", ""),
            video_title=video_data.get("title", ""),
            video_url=video_data.get("url", ""),
            overall_logic_gaps=["Failed to extract BOM after maximum retries."],
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
                    all_logic_gaps.append(f"[{ext.video_title}]: {gap}")

        # Deduplicate and consolidate duplicate parts across videos
        consolidated_parts = []
        seen_names = {}

        for part in raw_parts:
            norm_name = part["part_name"].strip().lower()
            if norm_name in seen_names:
                existing = seen_names[norm_name]
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
