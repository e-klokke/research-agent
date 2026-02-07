"""News worker for financial and tech news"""
import os
import logging
from typing import List
import httpx

from app.workers.base import BaseWorker
from app.agents.state import Source

logger = logging.getLogger(__name__)


class NewsWorker(BaseWorker):
    """Worker for news articles from financial and tech news sources"""

    def __init__(self):
        super().__init__(worker_type="news")

    async def search(self, query: str, max_results: int = 10) -> List[Source]:
        """
        Search for news articles

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            List of Source objects
        """
        try:
            logger.info(f"Searching news for: {query}")

            # Use Tavily API with news focus
            tavily_key = os.getenv("TAVILY_API_KEY")
            if not tavily_key:
                logger.warning("TAVILY_API_KEY not set")
                return []

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": f"{query} news",
                        "search_depth": "advanced",
                        "max_results": max_results,
                        "include_domains": self._get_news_domains(),
                        "days": 30,  # Recent news only
                    }
                )
                response.raise_for_status()
                data = response.json()

            sources = []
            for result in data.get("results", []):
                source = self._create_source(
                    url=result.get("url", ""),
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    metadata={
                        "domain": result.get("url", "").split("/")[2] if "/" in result.get("url", "") else "",
                        "score": result.get("score", 0.5),
                        "published_date": result.get("published_date"),
                    }
                )
                sources.append(source)

            logger.info(f"Found {len(sources)} news sources")
            return sources

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during news search: {e}")
            return []
        except Exception as e:
            logger.error(f"Error during news search: {e}")
            return []

    def _get_news_domains(self) -> List[str]:
        """Get list of trusted news domains"""
        return [
            # Financial news
            "reuters.com",
            "bloomberg.com",
            "wsj.com",
            "ft.com",
            "cnbc.com",
            "marketwatch.com",
            "benzinga.com",
            # Tech news
            "techcrunch.com",
            "theverge.com",
            "arstechnica.com",
            "wired.com",
            "zdnet.com",
            "cnet.com",
            # General news
            "nytimes.com",
            "washingtonpost.com",
            "theguardian.com",
        ]

    def _calculate_credibility_score(self, source_metadata: dict) -> float:
        """
        Calculate credibility score for news sources

        Args:
            source_metadata: Metadata about the source

        Returns:
            Credibility score between 0.0 and 1.0
        """
        score = 0.6  # News starts with good base score

        domain = source_metadata.get('domain', '')

        # Tier 1 news sources
        if any(tier1 in domain for tier1 in [
            'reuters.com', 'bloomberg.com', 'wsj.com', 'ft.com',
            'nytimes.com', 'washingtonpost.com'
        ]):
            score += 0.3

        # Tier 2 news sources
        elif any(tier2 in domain for tier2 in [
            'cnbc.com', 'marketwatch.com', 'techcrunch.com',
            'theverge.com', 'arstechnica.com'
        ]):
            score += 0.2

        # Recency is critical for news
        if source_metadata.get('published_date'):
            score += 0.15

        return min(1.0, score)
