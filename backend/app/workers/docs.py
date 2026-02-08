"""Documentation worker for official docs sites"""
import os
import logging
from typing import List
import httpx

from app.workers.base import BaseWorker
from app.agents.state import Source

logger = logging.getLogger(__name__)


class DocsWorker(BaseWorker):
    """Worker for searching official documentation sites"""

    def __init__(self):
        super().__init__(worker_type="docs")

    async def search(self, query: str, max_results: int = 10) -> List[Source]:
        """
        Search documentation sites

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            List of Source objects
        """
        try:
            logger.info(f"Searching documentation for: {query}")

            # Use Tavily with documentation domain filter
            tavily_key = os.getenv("TAVILY_API_KEY")
            if not tavily_key:
                logger.warning("TAVILY_API_KEY not set")
                return []

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": f"{query} documentation",
                        "search_depth": "advanced",
                        "max_results": max_results,
                        "include_domains": self._get_docs_domains(),
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
                        "is_documentation": True,
                    }
                )
                sources.append(source)

            logger.info(f"Found {len(sources)} documentation sources")
            return sources

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during docs search: {e}")
            return []
        except Exception as e:
            logger.error(f"Error during docs search: {e}")
            return []

    def _get_docs_domains(self) -> List[str]:
        """Get list of documentation domains"""
        return [
            # Official docs
            "docs.python.org",
            "docs.oracle.com",
            "docs.microsoft.com",
            "developer.mozilla.org",
            "docs.aws.amazon.com",
            "cloud.google.com/docs",
            "docs.docker.com",
            "kubernetes.io/docs",
            "docs.github.com",
            "docs.gitlab.com",
            # Framework docs
            "react.dev",
            "vuejs.org",
            "angular.io/docs",
            "nodejs.org/docs",
            "flask.palletsprojects.com",
            "docs.djangoproject.com",
            "fastapi.tiangolo.com",
            "spring.io/guides",
            # Database docs
            "dev.mysql.com/doc",
            "postgresql.org/docs",
            "mongodb.com/docs",
            "redis.io/documentation",
            # Tool docs
            "git-scm.com/doc",
            "docs.npmjs.com",
            "pip.pypa.io",
        ]

    def _calculate_credibility_score(self, source_metadata: dict) -> float:
        """
        Calculate credibility score for documentation sources

        Args:
            source_metadata: Metadata about the source

        Returns:
            Credibility score between 0.0 and 1.0
        """
        score = 0.8  # Docs start with high base score

        domain = source_metadata.get('domain', '')

        # Official documentation gets highest score
        if any(official in domain for official in [
            'docs.python.org', 'docs.oracle.com', 'docs.microsoft.com',
            'developer.mozilla.org', 'kubernetes.io', 'docs.docker.com'
        ]):
            score += 0.2

        # Framework official docs
        elif any(framework in domain for framework in [
            'react.dev', 'vuejs.org', 'angular.io',
            'fastapi.tiangolo.com', 'docs.djangoproject.com'
        ]):
            score += 0.15

        return min(1.0, score)
