"""
Patent Worker - USPTO and EPO patent search
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from .base import BaseWorker, Source


class PatentWorker(BaseWorker):
    """Worker for patent search across USPTO and EPO databases"""

    def __init__(self):
        super().__init__("patent")
        self.uspto_base_url = "https://developer.uspto.gov/ibd-api/v1"
        self.uspto_api_key = os.getenv("USPTO_API_KEY", "")  # Optional, free tier available
        self.epo_base_url = "https://ops.epo.org/3.2/rest-services"

    async def search(
        self, query: str, max_results: int = 10, context: Optional[Dict[str, Any]] = None
    ) -> List[Source]:
        """
        Search patent databases

        Args:
            query: Search query
            max_results: Maximum number of results
            context: Additional context (domain, depth, etc.)

        Returns:
            List of Source objects with patent metadata
        """
        # Search both USPTO and EPO in parallel
        tasks = [
            self._search_uspto(query, max_results // 2),
            self._search_epo(query, max_results // 2),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_sources = []
        for result in results:
            if isinstance(result, list):
                all_sources.extend(result)
            elif isinstance(result, Exception):
                print(f"Patent search error: {result}")

        # Sort by date and relevance
        all_sources.sort(
            key=lambda s: (
                s.metadata.get("citations", 0),
                s.metadata.get("year", 0),
            ),
            reverse=True,
        )

        # Deduplicate by patent number
        seen = set()
        unique_sources = []
        for source in all_sources:
            patent_number = source.metadata.get("patent_number", "")
            if patent_number and patent_number not in seen:
                seen.add(patent_number)
                unique_sources.append(source)

        return unique_sources[:max_results]

    async def _search_uspto(self, query: str, max_results: int) -> List[Source]:
        """
        Search US Patent and Trademark Office

        Uses the USPTO Patent Examination Data System (PEDS) API
        """
        sources = []

        # USPTO Patent Full-Text Database search
        # Note: USPTO's API is somewhat limited. For production, consider using
        # Google Patents API or PatentsView API which have better search capabilities

        # For now, we'll use a simple approach with the public patent search
        # In production, integrate with PatentsView API (https://api.patentsview.org/doc.html)

        try:
            # Using PatentsView API (free, no key required for basic use)
            url = "https://api.patentsview.org/patents/query"

            # Build query parameters
            payload = {
                "q": {"_text_any": {"patent_title": query}},
                "f": [
                    "patent_number",
                    "patent_title",
                    "patent_abstract",
                    "patent_date",
                    "assignee_organization",
                    "inventor_last_name",
                    "inventor_first_name",
                    "cited_patent_number"
                ],
                "o": {"per_page": max_results}
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        patents = data.get("patents", [])

                        for patent in patents:
                            patent_number = patent.get("patent_number", "")
                            title = patent.get("patent_title", "")
                            abstract = patent.get("patent_abstract", "")
                            patent_date = patent.get("patent_date", "")

                            # Get assignee (company/organization)
                            assignees = patent.get("assignees", [])
                            assignee = assignees[0].get("assignee_organization", "") if assignees else ""

                            # Get inventors
                            inventors = patent.get("inventors", [])
                            inventor_names = []
                            for inv in inventors[:3]:  # Limit to first 3
                                first = inv.get("inventor_first_name", "")
                                last = inv.get("inventor_last_name", "")
                                if last:
                                    inventor_names.append(f"{first} {last}".strip())

                            # Get citation count (cited patents)
                            citations = len(patent.get("cited_patents", []))

                            # Parse date
                            year = None
                            if patent_date:
                                try:
                                    year = int(patent_date[:4])
                                except:
                                    pass

                            # Build content
                            content = abstract[:400] + "..." if abstract and len(abstract) > 400 else abstract

                            source = self.create_source(
                                url=f"https://patents.google.com/patent/US{patent_number}",
                                title=title,
                                content=content or f"Patent {patent_number} by {assignee}",
                                source_type="patent",
                                metadata={
                                    "patent_number": f"US{patent_number}",
                                    "assignee": assignee,
                                    "inventors": inventor_names,
                                    "patent_date": patent_date,
                                    "year": year,
                                    "citations": citations,
                                    "office": "USPTO",
                                },
                            )

                            # Patent credibility based on citations and assignee reputation
                            base_credibility = 0.8  # Patents are generally credible
                            citation_boost = min(citations / 50, 0.15)
                            source.credibility_score = min(base_credibility + citation_boost, 0.95)

                            sources.append(source)

        except Exception as e:
            print(f"USPTO search error: {e}")

        return sources

    async def _search_epo(self, query: str, max_results: int) -> List[Source]:
        """
        Search European Patent Office

        Uses EPO Open Patent Services (OPS) API
        Note: Requires registration for API key, but free tier available
        """
        sources = []

        # EPO OPS requires OAuth2 authentication
        # For simplicity, we'll use the public Espacenet interface
        # In production, integrate with EPO OPS API for better results

        # Using Google Patents as a proxy for EPO patents
        try:
            # Google Patents Custom Search API alternative
            # This is a simplified version - in production use proper EPO OPS API

            url = "https://serpapi.com/search"
            params = {
                "engine": "google_patents",
                "q": query,
                "num": max_results,
            }

            # Only use if SerpAPI key is available (same as Google Scholar)
            serpapi_key = os.getenv("SERPAPI_KEY", "")
            if serpapi_key:
                params["api_key"] = serpapi_key

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = data.get("organic_results", [])

                            for result in results:
                                patent_id = result.get("patent_id", "")
                                title = result.get("title", "")
                                snippet = result.get("snippet", "")
                                pdf_link = result.get("pdf", "")

                                # Extract filing info
                                publication_info = result.get("publication_info", {})
                                filing_date = publication_info.get("filing_date", "")
                                publication_date = publication_info.get("publication_date", "")

                                # Extract assignee
                                assignee = result.get("assignee", "")

                                # Extract inventors
                                inventors = result.get("inventors", [])
                                inventor_names = [inv.get("name", "") for inv in inventors[:3]]

                                # Parse year
                                year = None
                                if publication_date:
                                    try:
                                        year = int(publication_date[:4])
                                    except:
                                        pass

                                # Determine patent office from patent_id
                                office = "EPO" if patent_id.startswith("EP") else "Other"

                                source = self.create_source(
                                    url=f"https://patents.google.com/patent/{patent_id}",
                                    title=title,
                                    content=snippet,
                                    source_type="patent",
                                    metadata={
                                        "patent_number": patent_id,
                                        "assignee": assignee,
                                        "inventors": inventor_names,
                                        "filing_date": filing_date,
                                        "publication_date": publication_date,
                                        "year": year,
                                        "pdf_url": pdf_link,
                                        "office": office,
                                    },
                                )

                                source.credibility_score = 0.85  # EPO patents are credible

                                sources.append(source)

        except Exception as e:
            print(f"EPO search error: {e}")

        return sources

    def _extract_patent_classification(self, patent_data: Dict[str, Any]) -> List[str]:
        """
        Extract International Patent Classification (IPC) codes
        """
        classifications = []

        # This would extract from patent data
        # Example: ["H04L 29/06", "G06F 21/62"]

        return classifications

    def _analyze_citation_network(self, patent_number: str, cited_patents: List[str]) -> Dict[str, Any]:
        """
        Analyze patent citation network
        Returns metrics about the patent's influence
        """
        return {
            "citations_count": len(cited_patents),
            "influence_score": min(len(cited_patents) / 10, 1.0),
        }
