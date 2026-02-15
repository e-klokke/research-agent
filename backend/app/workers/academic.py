"""
Academic Research Worker
Searches academic papers from ArXiv, Google Scholar, PubMed, and Semantic Scholar
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from .base import BaseWorker, Source


class AcademicWorker(BaseWorker):
    """
    Worker for academic paper research

    Data Sources:
    - ArXiv: Physics, CS, Math, Stats preprints (free)
    - Google Scholar: Cross-disciplinary via SerpAPI (paid)
    - PubMed: Medical and life sciences (free)
    - Semantic Scholar: AI-powered paper discovery (free)
    """

    def __init__(self):
        super().__init__("academic")
        self.serpapi_key = os.getenv("SERPAPI_KEY", "")
        self.semantic_scholar_api = "https://api.semanticscholar.org/graph/v1"

    async def search(self, query: str, max_results: int = 10) -> List[Source]:
        """Search across all academic sources"""
        sources = []

        # Run all searches in parallel
        results = await asyncio.gather(
            self._search_arxiv(query, max_results=5),
            self._search_pubmed(query, max_results=5),
            self._search_semantic_scholar(query, max_results=5),
            self._search_google_scholar(query, max_results=5) if self.serpapi_key else asyncio.sleep(0),
            return_exceptions=True
        )

        # Flatten results
        for result in results:
            if isinstance(result, list):
                sources.extend(result)
            elif isinstance(result, Exception):
                print(f"Academic search error: {result}")

        # Sort by credibility and recency
        sources.sort(key=lambda s: (s.credibility, s.date or ""), reverse=True)

        # Deduplicate by DOI or title
        seen = set()
        unique_sources = []
        for source in sources:
            # Extract DOI from metadata if available
            doi = source.metadata.get("doi", "")
            identifier = doi if doi else source.title.lower().strip()

            if identifier not in seen:
                seen.add(identifier)
                unique_sources.append(source)

        return unique_sources[:max_results]

    async def _search_arxiv(self, query: str, max_results: int = 5) -> List[Source]:
        """
        Search ArXiv preprints
        ArXiv has high-quality CS, physics, math papers
        """
        sources = []

        # ArXiv API: http://export.arxiv.org/api/query
        base_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        xml_text = await response.text()
                        sources = self._parse_arxiv_xml(xml_text)
        except Exception as e:
            print(f"ArXiv search error: {e}")

        return sources

    def _parse_arxiv_xml(self, xml_text: str) -> List[Source]:
        """Parse ArXiv API XML response"""
        sources = []

        try:
            root = ET.fromstring(xml_text)
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'arxiv': 'http://arxiv.org/schemas/atom'}

            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                summary_elem = entry.find('atom:summary', ns)
                published_elem = entry.find('atom:published', ns)
                link_elem = entry.find('atom:id', ns)

                # Extract authors
                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())

                # Extract categories
                categories = []
                for category in entry.findall('atom:category', ns):
                    term = category.get('term')
                    if term:
                        categories.append(term)

                # Extract DOI if available
                doi_elem = entry.find('arxiv:doi', ns)
                doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else ""

                if title_elem is not None and link_elem is not None:
                    title = title_elem.text.strip().replace('\n', ' ')
                    summary = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None else ""
                    url = link_elem.text.strip()

                    # Parse date
                    date_str = published_elem.text.strip()[:10] if published_elem is not None else None

                    # ArXiv credibility: 0.8 (high quality preprints)
                    credibility = self.calculate_credibility(
                        domain="arxiv.org",
                        has_author=bool(authors),
                        date_str=date_str
                    )
                    credibility = min(credibility, 0.85)  # Cap at 0.85 (preprints, not peer-reviewed)

                    source = Source(
                        url=url,
                        title=title,
                        snippet=summary[:300] + "..." if len(summary) > 300 else summary,
                        credibility=credibility,
                        worker="academic_arxiv",
                        date=date_str,
                        metadata={
                            "source_type": "preprint",
                            "authors": authors[:5],  # Limit to first 5 authors
                            "categories": categories,
                            "doi": doi,
                            "pdf_url": url.replace("/abs/", "/pdf/") + ".pdf"
                        }
                    )
                    sources.append(source)

        except Exception as e:
            print(f"ArXiv XML parsing error: {e}")

        return sources

    async def _search_pubmed(self, query: str, max_results: int = 5) -> List[Source]:
        """
        Search PubMed for medical/life sciences papers
        PubMed Central (PMC) has full-text articles
        """
        sources = []

        # PubMed E-utilities API
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Search for PMIDs
                search_params = {
                    "db": "pubmed",
                    "term": query,
                    "retmax": max_results,
                    "retmode": "json",
                    "sort": "relevance"
                }

                async with session.get(search_url, params=search_params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        search_data = await response.json()
                        id_list = search_data.get("esearchresult", {}).get("idlist", [])

                        if id_list:
                            # Step 2: Fetch summaries for PMIDs
                            fetch_params = {
                                "db": "pubmed",
                                "id": ",".join(id_list),
                                "retmode": "json"
                            }

                            async with session.get(fetch_url, params=fetch_params, timeout=aiohttp.ClientTimeout(total=10)) as fetch_response:
                                if fetch_response.status == 200:
                                    fetch_data = await fetch_response.json()
                                    sources = self._parse_pubmed_json(fetch_data)

        except Exception as e:
            print(f"PubMed search error: {e}")

        return sources

    def _parse_pubmed_json(self, data: Dict[str, Any]) -> List[Source]:
        """Parse PubMed API JSON response"""
        sources = []

        try:
            result = data.get("result", {})

            for pmid, article in result.items():
                if pmid == "uids":  # Skip metadata entry
                    continue

                title = article.get("title", "")
                authors = article.get("authors", [])
                pub_date = article.get("pubdate", "")
                source_journal = article.get("source", "")
                doi = article.get("elocationid", "")

                # Extract DOI if available (format: "doi: 10.xxxx/xxxxx")
                if doi.startswith("doi: "):
                    doi = doi[5:]

                # Build PubMed URL
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                # Build snippet from available info
                snippet = f"Published in {source_journal}. "
                if authors:
                    author_names = [a.get("name", "") for a in authors[:3]]
                    snippet += f"Authors: {', '.join(author_names)}. "

                # Parse date (PubMed format: "2024 Jan 15")
                date_str = None
                try:
                    if pub_date:
                        date_obj = datetime.strptime(pub_date.split()[0], "%Y")
                        date_str = date_obj.strftime("%Y-%m-%d")
                except:
                    pass

                # PubMed credibility: 0.9 (peer-reviewed medical journals)
                credibility = self.calculate_credibility(
                    domain="pubmed.ncbi.nlm.nih.gov",
                    has_author=bool(authors),
                    date_str=date_str
                )
                credibility = min(credibility, 0.9)  # Cap at 0.9 (high quality peer-reviewed)

                source = Source(
                    url=url,
                    title=title,
                    snippet=snippet.strip(),
                    credibility=credibility,
                    worker="academic_pubmed",
                    date=date_str,
                    metadata={
                        "source_type": "peer_reviewed",
                        "pmid": pmid,
                        "journal": source_journal,
                        "authors": [a.get("name", "") for a in authors[:5]],
                        "doi": doi
                    }
                )
                sources.append(source)

        except Exception as e:
            print(f"PubMed JSON parsing error: {e}")

        return sources

    async def _search_semantic_scholar(self, query: str, max_results: int = 5) -> List[Source]:
        """
        Search Semantic Scholar for AI-powered paper discovery
        Semantic Scholar has citation counts and influential citations
        """
        sources = []

        url = f"{self.semantic_scholar_api}/paper/search"
        params = {
            "query": query,
            "limit": max_results,
            "fields": "paperId,title,abstract,authors,year,citationCount,influentialCitationCount,url,openAccessPdf,externalIds"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        papers = data.get("data", [])

                        for paper in papers:
                            title = paper.get("title", "")
                            abstract = paper.get("abstract", "")
                            paper_id = paper.get("paperId", "")
                            year = paper.get("year")
                            citation_count = paper.get("citationCount", 0)
                            influential_citations = paper.get("influentialCitationCount", 0)
                            paper_url = paper.get("url", "")
                            pdf_url = paper.get("openAccessPdf", {}).get("url", "") if paper.get("openAccessPdf") else ""

                            # Extract authors
                            authors = [a.get("name", "") for a in paper.get("authors", [])]

                            # Extract DOI
                            external_ids = paper.get("externalIds", {})
                            doi = external_ids.get("DOI", "")
                            arxiv_id = external_ids.get("ArXiv", "")

                            # Build snippet
                            snippet = abstract[:300] + "..." if abstract and len(abstract) > 300 else abstract
                            if not snippet:
                                snippet = f"Citations: {citation_count} (Influential: {influential_citations})"

                            # Date
                            date_str = f"{year}-01-01" if year else None

                            # Credibility based on citations (boosted for highly-cited papers)
                            base_credibility = self.calculate_credibility(
                                domain="semanticscholar.org",
                                has_author=bool(authors),
                                date_str=date_str
                            )

                            # Boost credibility for highly-cited papers
                            citation_boost = min(citation_count / 1000, 0.15)  # Up to +0.15 for 1000+ citations
                            influential_boost = min(influential_citations / 100, 0.05)  # Up to +0.05 for 100+ influential
                            credibility = min(base_credibility + citation_boost + influential_boost, 0.95)

                            source = Source(
                                url=paper_url or f"https://www.semanticscholar.org/paper/{paper_id}",
                                title=title,
                                snippet=snippet,
                                credibility=credibility,
                                worker="academic_semantic_scholar",
                                date=date_str,
                                metadata={
                                    "source_type": "academic_paper",
                                    "paper_id": paper_id,
                                    "authors": authors[:5],
                                    "citation_count": citation_count,
                                    "influential_citations": influential_citations,
                                    "doi": doi,
                                    "arxiv_id": arxiv_id,
                                    "pdf_url": pdf_url
                                }
                            )
                            sources.append(source)

        except Exception as e:
            print(f"Semantic Scholar search error: {e}")

        return sources

    async def _search_google_scholar(self, query: str, max_results: int = 5) -> List[Source]:
        """
        Search Google Scholar via SerpAPI
        Requires SERPAPI_KEY environment variable
        """
        if not self.serpapi_key:
            return []

        sources = []

        url = "https://serpapi.com/search"
        params = {
            "engine": "google_scholar",
            "q": query,
            "api_key": self.serpapi_key,
            "num": max_results
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("organic_results", [])

                        for result in results:
                            title = result.get("title", "")
                            snippet = result.get("snippet", "")
                            link = result.get("link", "")
                            publication_info = result.get("publication_info", {})
                            cited_by = result.get("inline_links", {}).get("cited_by", {}).get("total", 0)

                            # Extract authors and year
                            authors_str = publication_info.get("authors", [])
                            authors = [a.get("name", "") for a in authors_str] if isinstance(authors_str, list) else []

                            # Extract year from publication_info summary
                            summary = publication_info.get("summary", "")
                            year = None
                            import re
                            year_match = re.search(r'\b(19|20)\d{2}\b', summary)
                            if year_match:
                                year = year_match.group(0)

                            date_str = f"{year}-01-01" if year else None

                            # Credibility based on citations
                            base_credibility = self.calculate_credibility(
                                domain="scholar.google.com",
                                has_author=bool(authors),
                                date_str=date_str
                            )

                            # Citation boost
                            citation_boost = min(cited_by / 1000, 0.15)
                            credibility = min(base_credibility + citation_boost, 0.95)

                            source = Source(
                                url=link,
                                title=title,
                                snippet=snippet,
                                credibility=credibility,
                                worker="academic_google_scholar",
                                date=date_str,
                                metadata={
                                    "source_type": "academic_paper",
                                    "authors": authors,
                                    "citations": cited_by,
                                    "publication_info": summary
                                }
                            )
                            sources.append(source)

        except Exception as e:
            print(f"Google Scholar search error: {e}")

        return sources
