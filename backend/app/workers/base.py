"""Base worker class for data gathering"""
from abc import ABC, abstractmethod
from typing import List
import logging
from datetime import datetime

from app.agents.state import Source

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """Abstract base class for all workers"""

    def __init__(self, worker_type: str):
        self.worker_type = worker_type

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[Source]:
        """
        Search for information based on the query

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            List of Source objects
        """
        pass

    def _calculate_credibility_score(self, source_metadata: dict) -> float:
        """
        Calculate credibility score for a source based on various factors

        Args:
            source_metadata: Metadata about the source

        Returns:
            Credibility score between 0.0 and 1.0
        """
        score = 0.5  # Base score

        # Domain authority
        domain = source_metadata.get('domain', '')
        if any(trusted in domain for trusted in ['github.com', 'stackoverflow.com', 'arxiv.org']):
            score += 0.3
        elif any(trusted in domain for trusted in ['.edu', '.gov', '.org']):
            score += 0.2

        # Recency (if available)
        if 'published_date' in source_metadata:
            # Boost score for recent content
            score += 0.1

        # Content quality indicators
        if source_metadata.get('has_code_examples'):
            score += 0.1

        return min(1.0, score)

    def _create_source(
        self,
        url: str,
        title: str,
        content: str,
        metadata: dict
    ) -> Source:
        """
        Create a Source object with calculated credibility score

        Args:
            url: Source URL
            title: Source title
            content: Source content
            metadata: Additional metadata

        Returns:
            Source object
        """
        credibility_score = self._calculate_credibility_score(metadata)

        return Source(
            url=url,
            title=title,
            content=content,
            source_type=self.worker_type,
            credibility_score=credibility_score,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata
        )
