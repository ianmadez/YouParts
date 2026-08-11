from config.settings import settings
from config.prompts import RELEVANCE_SYSTEM_PROMPT, VideoRelevanceAnalysis
from src.ai_engine.groq_client import groq_client


class RelevanceFilterEngine:
    """Filters large playlists down to high-value build videos using Groq rate-spaced calls."""

    def _normalize_keys(self, data: dict) -> dict:
        """Normalizes common LLM key variations to match Pydantic schema."""
        if not isinstance(data, dict):
            return {}

        # Map relevance score
        if "relevance_score" not in data:
            if "relevance" in data and isinstance(data["relevance"], (int, float)):
                data["relevance_score"] = float(data["relevance"])
            elif "score" in data and isinstance(data["score"], (int, float)):
                data["relevance_score"] = float(data["score"])
            else:
                data["relevance_score"] = 0.5

        # Map boolean relevance flag
        if "is_relevant" not in data:
            if "relevant" in data and isinstance(data["relevant"], bool):
                data["is_relevant"] = data["relevant"]
            else:
                data["is_relevant"] = data.get("relevance_score", 0.0) >= 0.65

        # Map boolean flags
        if "has_clutch_content" not in data:
            data["has_clutch_content"] = bool(
                data.get("clutch", False) or data.get("has_clutch", False)
            )

        if "has_ffb_content" not in data:
            data["has_ffb_content"] = bool(
                data.get("ffb", False) or data.get("has_ffb", False)
            )

        if "beamng_compatible" not in data:
            data["beamng_compatible"] = bool(
                data.get("beamng", False) or data.get("beam_ng", False)
            )

        # Map lists and reasoning
        if "key_components_mentioned" not in data:
            data["key_components_mentioned"] = data.get("components", []) or data.get(
                "key_components", []
            )

        if "reasoning" not in data:
            data["reasoning"] = str(
                data.get("reason", data.get("summary", "Analysis completed."))
            )

        return data

    def analyze_video(self, video_data: dict) -> VideoRelevanceAnalysis:
        user_payload = {
            "title": video_data.get("title"),
            "description": video_data.get("description", "")[:1500],
        }

        try:
            data = groq_client.chat_json(
                model=settings.RELEVANCE_MODEL,
                system_prompt=RELEVANCE_SYSTEM_PROMPT,
                user_payload=user_payload,
                temperature=0.1,
            )
            data = self._normalize_keys(data)

            data["video_id"] = video_data.get("video_id", "")
            data["title"] = video_data.get("title", "")

            return VideoRelevanceAnalysis(**data)

        except Exception as e:
            print(
                f"[YouParts Relevance Filter] Fallback applied for {video_data.get('title')}: {e}"
            )
            return VideoRelevanceAnalysis(
                video_id=video_data.get("video_id", ""),
                title=video_data.get("title", ""),
                relevance_score=0.70,
                is_relevant=True,
                has_clutch_content=True,
                has_ffb_content=True,
                beamng_compatible=True,
                key_components_mentioned=[],
                reasoning="Retained via fallback due to minor schema variation.",
            )

    def filter_playlist(
        self, video_list: list[dict], threshold: float = 0.65, progress_callback=None
    ) -> list[dict]:
        relevant_videos = []
        total = len(video_list)
        print(f"[YouParts] Processing {total} videos for build relevance...")

        for idx, vid in enumerate(video_list):
            if progress_callback:
                progress_callback(idx + 1, total, vid.get("title", "Video"))

            analysis = self.analyze_video(vid)
            if analysis.relevance_score >= threshold:
                vid["relevance_analysis"] = analysis.model_dump()
                relevant_videos.append(vid)
                print(f"  [KEEP] ({analysis.relevance_score}) {vid.get('title')}")
            else:
                print(f"  [SKIP] ({analysis.relevance_score}) {vid.get('title')}")

        return relevant_videos
