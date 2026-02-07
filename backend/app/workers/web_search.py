"""Web search worker using Tavily API"""
import os
import logging
from typing import List
import httpx

from app.workers.base import BaseWorker
from app.agents.state import Source

logger = logging.getLogger(__name__)


class WebSearchWorker(BaseWorker):
    """Worker for web search using Tavily API"""

    def __init__(self):
        super().__init__(worker_type="web")
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")
        self.base_url = "https://api.tavily.com"

    async def search(self, query: str, max_results: int = 10) -> List[Source]:
        """
        Search the web using Tavily API

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            List of Source objects
        """
        try:
            logger.info(f"Searching web for: {query}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "search_depth": "advanced",
                        "max_results": max_results,
                        "include_answer": False,
                        "include_raw_content": False,
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

            logger.info(f"Found {len(sources)} web sources")
            return sources

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during web search: {e}")
            return []
        except Exception as e:
            logger.error(f"Error during web search: {e}")
            return []

    def _calculate_credibility_score(self, source_metadata: dict) -> float:
        """
        Calculate credibility score for web sources

        Args:
            source_metadata: Metadata about the source

        Returns:
            Credibility score between 0.0 and 1.0
        """
        # Start with Tavily's own score if available
        score = source_metadata.get('score', 0.5)

        # Adjust based on domain authority
        domain = source_metadata.get('domain', '')

        # Trusted domains get a boost
        if any(trusted in domain for trusted in [
            'github.com', 'stackoverflow.com', 'arxiv.org',
            'wikipedia.org', 'docs.', 'official'
        ]):
            score = min(1.0, score + 0.2)

        # Educational and government domains
        if any(ext in domain for ext in ['.edu', '.gov', '.org']):
            score = min(1.0, score + 0.15)

        # Penalize certain domains
        if any(spam in domain for spam in ['blogspot', 'wordpress.com', 'medium.com']):
            score = max(0.3, score - 0.1)

        return score
