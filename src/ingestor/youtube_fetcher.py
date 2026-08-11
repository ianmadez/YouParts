import yt_dlp
from typing import Dict, Any, List, Optional


class YouTubeDataFetcher:
    """Uses the yt_dlp Python library directly to extract video metadata, descriptions, and playlist entries."""

    @staticmethod
    def fetch_playlist_urls(playlist_url: str) -> List[str]:
        """Expands a YouTube playlist URL into individual video watch URLs."""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "ignoreerrors": True,
            "no_check_certificate": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                if not info or "entries" not in info:
                    return [playlist_url]

                urls = []
                for entry in info["entries"]:
                    if entry and isinstance(entry, dict):
                        vid_id = entry.get("id") or entry.get("url")
                        if vid_id:
                            if vid_id.startswith("http"):
                                urls.append(vid_id)
                            else:
                                urls.append(f"https://www.youtube.com/watch?v={vid_id}")

                return urls
        except Exception as e:
            print(f"[YouParts] Error fetching playlist {playlist_url}: {e}")
            return [playlist_url]

    @staticmethod
    def fetch_video_details(url: str) -> Optional[Dict[str, Any]]:
        """Fetches metadata, title, and description for an individual video URL."""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "ignoreerrors": True,
            "no_check_certificate": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None

                # Handle edge case where yt-dlp returns a playlist container
                if "entries" in info:
                    entries = info.get("entries") or []
                    if not entries:
                        return None
                    info = entries[0]

                description = info.get("description") or ""

                return {
                    "video_id": info.get("id"),
                    "title": info.get("title"),
                    "url": info.get("webpage_url")
                    or f"https://www.youtube.com/watch?v={info.get('id')}",
                    "description": description,
                    "duration": info.get("duration"),
                    "uploader": info.get("uploader"),
                    "transcript_summary": "",
                }
        except Exception as e:
            print(f"[YouParts] Error fetching video details for {url}: {e}")
            return None
