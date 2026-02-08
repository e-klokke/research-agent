"""StackOverflow worker for technical Q&A"""
import os
import logging
from typing import List
import httpx

from app.workers.base import BaseWorker
from app.agents.state import Source

logger = logging.getLogger(__name__)


class StackOverflowWorker(BaseWorker):
    """Worker for searching StackOverflow and Stack Exchange sites"""

    def __init__(self):
        super().__init__(worker_type="stackoverflow")

    async def search(self, query: str, max_results: int = 10) -> List[Source]:
        """
        Search StackOverflow for technical Q&A

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            List of Source objects
        """
        try:
            logger.info(f"Searching StackOverflow for: {query}")

            # Use Tavily with StackOverflow domain filter
            tavily_key = os.getenv("TAVILY_API_KEY")
            if not tavily_key:
                logger.warning("TAVILY_API_KEY not set")
                return []

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": query,
                        "search_depth": "advanced",
                        "max_results": max_results,
                        "include_domains": self._get_stackoverflow_domains(),
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
                        "has_code_examples": "```" in result.get("content", "") or "code" in result.get("content", "").lower(),
                    }
                )
                sources.append(source)

            logger.info(f"Found {len(sources)} StackOverflow sources")
            return sources

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during StackOverflow search: {e}")
            return []
        except Exception as e:
            logger.error(f"Error during StackOverflow search: {e}")
            return []

    def _get_stackoverflow_domains(self) -> List[str]:
        """Get list of Stack Exchange network domains"""
        return [
            "stackoverflow.com",
            "serverfault.com",
            "superuser.com",
            "askubuntu.com",
            "dba.stackexchange.com",
            "devops.stackexchange.com",
            "unix.stackexchange.com",
        ]

    def _calculate_credibility_score(self, source_metadata: dict) -> float:
        """
        Calculate credibility score for StackOverflow sources

        Args:
            source_metadata: Metadata about the source

        Returns:
            Credibility score between 0.0 and 1.0
        """
        score = 0.7  # StackOverflow starts with good base score

        # StackOverflow is highly trusted for technical questions
        domain = source_metadata.get('domain', '')
        if 'stackoverflow.com' in domain:
            score += 0.2

        # Code examples are valuable
        if source_metadata.get('has_code_examples'):
            score += 0.1

        return min(1.0, score)
