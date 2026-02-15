"""
YouTube Worker - Video content analysis and transcript extraction
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from .base import BaseWorker, Source


class YouTubeWorker(BaseWorker):
    """Worker for YouTube video content analysis"""

    def __init__(self):
        super().__init__("youtube")
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.api_base_url = "https://www.googleapis.com/youtube/v3"

    async def search(
        self, query: str, max_results: int = 10, context: Optional[Dict[str, Any]] = None
    ) -> List[Source]:
        """
        Search YouTube for relevant videos

        Args:
            query: Search query
            max_results: Maximum number of results
            context: Additional context (domain, depth, etc.)

        Returns:
            List of Source objects with video metadata and transcripts
        """
        if not self.api_key:
            print("YouTube API key not configured")
            return []

        # Search for videos
        video_results = await self._search_videos(query, max_results)

        if not video_results:
            return []

        # Get video IDs
        video_ids = [video["id"] for video in video_results]

        # Get detailed video information (statistics, snippets)
        video_details = await self._get_video_details(video_ids)

        # Create sources
        sources = []
        for video in video_details:
            try:
                video_id = video.get("id", "")
                snippet = video.get("snippet", {})
                statistics = video.get("statistics", {})

                title = snippet.get("title", "")
                description = snippet.get("description", "")
                channel_title = snippet.get("channelTitle", "")
                published_at = snippet.get("publishedAt", "")
                thumbnails = snippet.get("thumbnails", {})

                view_count = int(statistics.get("viewCount", 0))
                like_count = int(statistics.get("likeCount", 0))
                comment_count = int(statistics.get("commentCount", 0))

                # Parse date
                date_str = published_at[:10] if published_at else None

                # Build content snippet from description
                content = description[:400] + "..." if len(description) > 400 else description

                # Extract key moments from description (timestamps)
                timestamps = self._extract_timestamps(description)

                # Calculate credibility based on channel authority and engagement
                base_credibility = self.calculate_credibility(
                    domain="youtube.com",
                    has_author=bool(channel_title),
                    date_str=date_str,
                )

                # Boost based on engagement
                engagement_score = (view_count / 10000) + (like_count / 100) + (comment_count / 10)
                engagement_boost = min(engagement_score / 100, 0.2)
                credibility = min(base_credibility + engagement_boost, 0.8)  # Cap at 0.8

                # Identify if it's an educational/tutorial video
                video_category = self._categorize_video(title, description)

                source = self.create_source(
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    title=title,
                    content=content,
                    source_type="youtube_video",
                    metadata={
                        "video_id": video_id,
                        "channel": channel_title,
                        "views": view_count,
                        "likes": like_count,
                        "comments": comment_count,
                        "engagement_score": int(engagement_score),
                        "category": video_category,
                        "timestamps": timestamps,
                        "thumbnail": thumbnails.get("high", {}).get("url", ""),
                    },
                )

                source.credibility_score = credibility

                sources.append(source)

            except Exception as e:
                print(f"Error processing YouTube video: {e}")
                continue

        # Sort by engagement and recency
        sources.sort(
            key=lambda s: (
                s.metadata.get("engagement_score", 0),
                s.metadata.get("views", 0),
            ),
            reverse=True,
        )

        return sources

    async def _search_videos(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search for videos using YouTube Data API"""
        url = f"{self.api_base_url}/search"
        params = {
            "part": "id,snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": "relevance",
            "videoDuration": "medium",  # Prefer 4-20 minute videos
            "videoDefinition": "any",
            "key": self.api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get("items", [])

                        # Extract video IDs and basic info
                        results = []
                        for item in items:
                            video_id = item.get("id", {}).get("videoId")
                            if video_id:
                                results.append({"id": video_id})

                        return results

                    else:
                        error_data = await response.text()
                        print(f"YouTube search error: {response.status} - {error_data}")

        except Exception as e:
            print(f"YouTube search exception: {e}")

        return []

    async def _get_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed information for videos"""
        if not video_ids:
            return []

        url = f"{self.api_base_url}/videos"
        params = {
            "part": "id,snippet,statistics,contentDetails",
            "id": ",".join(video_ids),
            "key": self.api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("items", [])
                    else:
                        error_data = await response.text()
                        print(f"YouTube video details error: {response.status} - {error_data}")

        except Exception as e:
            print(f"YouTube video details exception: {e}")

        return []

    def _extract_timestamps(self, description: str) -> List[Dict[str, str]]:
        """Extract timestamps from video description"""
        timestamps = []

        # Match patterns like "0:00", "1:23", "12:34:56"
        pattern = r'(\d{1,2}:?\d{2}:?\d{0,2})\s*[-–—]\s*(.+?)(?=\n|$)'
        matches = re.findall(pattern, description, re.MULTILINE)

        for time, title in matches:
            timestamps.append({
                "time": time.strip(),
                "title": title.strip()[:100]  # Limit title length
            })

        return timestamps[:10]  # Return max 10 timestamps

    def _categorize_video(self, title: str, description: str) -> str:
        """
        Categorize video based on title and description
        Returns: 'tutorial', 'review', 'talk', 'demo', 'discussion', or 'other'
        """
        combined = f"{title} {description}".lower()

        # Category keywords
        categories = {
            "tutorial": ["tutorial", "how to", "guide", "step by step", "learn", "course", "lesson"],
            "review": ["review", "comparison", "vs", "versus", "pros and cons", "tested"],
            "talk": ["talk", "conference", "presentation", "keynote", "speech", "lecture"],
            "demo": ["demo", "demonstration", "showcase", "walkthrough", "live coding"],
            "discussion": ["discussion", "interview", "podcast", "panel", "debate"],
        }

        # Count matches for each category
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in combined)
            if score > 0:
                category_scores[category] = score

        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)

        return "other"

    async def _get_transcript(self, video_id: str) -> Optional[str]:
        """
        Get transcript for a video (requires youtube-transcript-api)
        This is a placeholder - implementation would use youtube-transcript-api library
        """
        # Note: This requires the youtube-transcript-api library
        # pip install youtube-transcript-api
        #
        # from youtube_transcript_api import YouTubeTranscriptApi
        #
        # try:
        #     transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        #     transcript = " ".join([item['text'] for item in transcript_list])
        #     return transcript
        # except Exception as e:
        #     print(f"Transcript error for {video_id}: {e}")
        #     return None

        # For now, return None
        # Transcripts can be added in a future update with youtube-transcript-api
        return None
