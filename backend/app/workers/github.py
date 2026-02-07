"""GitHub worker for repository and code search"""
import os
import logging
from typing import List
import httpx

from app.workers.base import BaseWorker
from app.agents.state import Source

logger = logging.getLogger(__name__)


class GitHubWorker(BaseWorker):
    """Worker for GitHub repository and code search"""

    def __init__(self):
        super().__init__(worker_type="github")
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.warning("GITHUB_TOKEN not set - GitHub API rate limits will be restricted")
        self.base_url = "https://api.github.com"

    async def search(self, query: str, max_results: int = 10) -> List[Source]:
        """
        Search GitHub for repositories and code

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            List of Source objects
        """
        try:
            logger.info(f"Searching GitHub for: {query}")

            sources = []

            # Search repositories
            repo_sources = await self._search_repositories(query, max_results // 2)
            sources.extend(repo_sources)

            # Search code
            code_sources = await self._search_code(query, max_results // 2)
            sources.extend(code_sources)

            logger.info(f"Found {len(sources)} GitHub sources")
            return sources[:max_results]

        except Exception as e:
            logger.error(f"Error during GitHub search: {e}")
            return []

    async def _search_repositories(self, query: str, max_results: int) -> List[Source]:
        """Search for repositories"""
        try:
            headers = {
                "Accept": "application/vnd.github.v3+json",
            }
            if self.token:
                headers["Authorization"] = f"token {self.token}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/search/repositories",
                    headers=headers,
                    params={
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": max_results,
                    }
                )
                response.raise_for_status()
                data = response.json()

            sources = []
            for repo in data.get("items", []):
                content = f"{repo.get('description', 'No description')}\n\n"
                content += f"Stars: {repo.get('stargazers_count', 0)}\n"
                content += f"Language: {repo.get('language', 'Unknown')}\n"
                content += f"Last updated: {repo.get('updated_at', 'Unknown')}\n"

                if repo.get('topics'):
                    content += f"Topics: {', '.join(repo.get('topics', []))}\n"

                source = self._create_source(
                    url=repo.get("html_url", ""),
                    title=repo.get("full_name", ""),
                    content=content,
                    metadata={
                        "domain": "github.com",
                        "stars": repo.get("stargazers_count", 0),
                        "language": repo.get("language"),
                        "updated_at": repo.get("updated_at"),
                        "topics": repo.get("topics", []),
                    }
                )
                sources.append(source)

            return sources

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during repository search: {e}")
            return []
        except Exception as e:
            logger.error(f"Error during repository search: {e}")
            return []

    async def _search_code(self, query: str, max_results: int) -> List[Source]:
        """Search for code snippets"""
        try:
            headers = {
                "Accept": "application/vnd.github.v3+json",
            }
            if self.token:
                headers["Authorization"] = f"token {self.token}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/search/code",
                    headers=headers,
                    params={
                        "q": query,
                        "per_page": max_results,
                    }
                )
                response.raise_for_status()
                data = response.json()

            sources = []
            for item in data.get("items", []):
                content = f"File: {item.get('name', 'Unknown')}\n"
                content += f"Repository: {item.get('repository', {}).get('full_name', 'Unknown')}\n"
                content += f"Path: {item.get('path', 'Unknown')}\n"

                source = self._create_source(
                    url=item.get("html_url", ""),
                    title=f"{item.get('repository', {}).get('full_name', 'Unknown')} - {item.get('name', 'Unknown')}",
                    content=content,
                    metadata={
                        "domain": "github.com",
                        "repository": item.get("repository", {}).get("full_name"),
                        "path": item.get("path"),
                        "has_code_examples": True,
                    }
                )
                sources.append(source)

            return sources

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during code search: {e}")
            return []
        except Exception as e:
            logger.error(f"Error during code search: {e}")
            return []

    def _calculate_credibility_score(self, source_metadata: dict) -> float:
        """
        Calculate credibility score for GitHub sources

        Args:
            source_metadata: Metadata about the source

        Returns:
            Credibility score between 0.0 and 1.0
        """
        score = 0.7  # GitHub starts with a good base score

        # Star count matters
        stars = source_metadata.get('stars', 0)
        if stars > 10000:
            score += 0.2
        elif stars > 1000:
            score += 0.15
        elif stars > 100:
            score += 0.1

        # Code examples are valuable
        if source_metadata.get('has_code_examples'):
            score += 0.1

        return min(1.0, score)
