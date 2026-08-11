import re
from typing import List, Dict, Any
from src.ingestor.youtube_fetcher import YouTubeDataFetcher


class PlaylistParser:
    """Expands raw user inputs (mix of playlist URLs and individual video links) into deduplicated video metadata lists."""

    @classmethod
    def expand_and_fetch_all(cls, raw_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Takes raw URLs, identifies playlists vs individual vids, fetches metadata,
        and deduplicates by YouTube video ID.
        """
        try:
            all_target_urls: List[str] = []

            # 1. Expand playlists and collect raw video links
            for url in raw_urls:
                cleaned_url = url.strip()
                if not cleaned_url:
                    continue

                if "list=" in cleaned_url or "playlist" in cleaned_url:
                    print(f"[YouParts Parser] Expanding playlist: {cleaned_url}")
                    playlist_vids = YouTubeDataFetcher.fetch_playlist_urls(cleaned_url)
                    if playlist_vids:
                        all_target_urls.extend(playlist_vids)
                    else:
                        all_target_urls.append(cleaned_url)
                else:
                    all_target_urls.append(cleaned_url)

            # 2. Deduplicate URLs preserving order (outside the ingestion loop)
            unique_urls = list(dict.fromkeys(all_target_urls))
            print(
                f"[YouParts Parser] Found {len(unique_urls)} unique videos to process."
            )

            # 3. Fetch detailed metadata for each video
            metadata_list: List[Dict[str, Any]] = []
            seen_ids = set()

            for vid_url in unique_urls:
                details = YouTubeDataFetcher.fetch_video_details(vid_url)
                if details and details.get("video_id") not in seen_ids:
                    seen_ids.add(details["video_id"])
                    metadata_list.append(details)

            # 4. Return full metadata list after processing ALL videos
            return metadata_list

        except Exception as e:
            print(f"[YouParts Parser Error]: {e}")
            return []
