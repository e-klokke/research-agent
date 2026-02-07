"""Finance worker for financial data and metrics"""
import os
import logging
from typing import List
import httpx

from app.workers.base import BaseWorker
from app.agents.state import Source

logger = logging.getLogger(__name__)


class FinanceWorker(BaseWorker):
    """Worker for financial data using Yahoo Finance and web sources"""

    def __init__(self):
        super().__init__(worker_type="finance")

    async def search(self, query: str, max_results: int = 10) -> List[Source]:
        """
        Search for financial information

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            List of Source objects
        """
        try:
            logger.info(f"Searching financial data for: {query}")

            sources = []

            # Extract ticker symbols if present
            tickers = self._extract_tickers(query)

            # Search financial news and data sites
            financial_sources = await self._search_financial_sites(query, max_results // 2)
            sources.extend(financial_sources)

            # If tickers found, get specific data
            if tickers:
                ticker_sources = await self._get_ticker_data(tickers, query, max_results // 2)
                sources.extend(ticker_sources)

            logger.info(f"Found {len(sources)} finance sources")
            return sources[:max_results]

        except Exception as e:
            logger.error(f"Error during finance search: {e}")
            return []

    def _extract_tickers(self, query: str) -> List[str]:
        """Extract potential stock tickers from query"""
        # Simple ticker extraction - look for uppercase words 1-5 chars
        import re
        words = query.upper().split()
        tickers = []

        common_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD']

        for word in words:
            clean_word = re.sub(r'[^A-Z]', '', word)
            if 1 <= len(clean_word) <= 5 and clean_word in common_tickers:
                tickers.append(clean_word)

        return tickers

    async def _search_financial_sites(self, query: str, max_results: int) -> List[Source]:
        """Search major financial information sites"""
        sources = []

        # Financial sites to search
        financial_domains = [
            "seekingalpha.com",
            "finance.yahoo.com",
            "marketwatch.com",
            "bloomberg.com",
            "fool.com",
            "morningstar.com",
            "investing.com"
        ]

        # Use Tavily API for financial web search
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            logger.warning("TAVILY_API_KEY not set, skipping financial site search")
            return sources

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Add financial context to query
                financial_query = f"{query} stocks investing financial analysis"

                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": financial_query,
                        "search_depth": "advanced",
                        "max_results": max_results,
                        "include_domains": financial_domains,
                    }
                )
                response.raise_for_status()
                data = response.json()

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

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during financial site search: {e}")
        except Exception as e:
            logger.error(f"Error during financial site search: {e}")

        return sources

    async def _get_ticker_data(self, tickers: List[str], query: str, max_results: int) -> List[Source]:
        """Get specific ticker data"""
        sources = []

        for ticker in tickers[:3]:  # Limit to 3 tickers
            try:
                # Create a synthetic source with ticker information
                # In production, this would call Yahoo Finance API or similar
                content = f"Ticker: {ticker}\n"
                content += f"Query: {query}\n"
                content += f"Note: Live financial data requires API integration with Yahoo Finance, Alpha Vantage, or similar service.\n"

                source = self._create_source(
                    url=f"https://finance.yahoo.com/quote/{ticker}",
                    title=f"{ticker} Stock Information",
                    content=content,
                    metadata={
                        "domain": "finance.yahoo.com",
                        "ticker": ticker,
                        "data_type": "ticker_info",
                    }
                )
                sources.append(source)

            except Exception as e:
                logger.error(f"Error getting ticker data for {ticker}: {e}")

        return sources

    def _calculate_credibility_score(self, source_metadata: dict) -> float:
        """
        Calculate credibility score for financial sources

        Args:
            source_metadata: Metadata about the source

        Returns:
            Credibility score between 0.0 and 1.0
        """
        score = 0.5  # Base score

        domain = source_metadata.get('domain', '')

        # Highly trusted financial sources
        if any(trusted in domain for trusted in [
            'bloomberg.com', 'reuters.com', 'wsj.com', 'ft.com',
            'finance.yahoo.com', 'morningstar.com', 'sec.gov'
        ]):
            score += 0.3

        # Good financial sources
        elif any(good in domain for good in [
            'seekingalpha.com', 'marketwatch.com', 'investing.com',
            'fool.com', 'benzinga.com'
        ]):
            score += 0.2

        # Recency matters more for financial data
        if source_metadata.get('published_date'):
            score += 0.1

        # Ticker-specific data gets boost
        if source_metadata.get('ticker'):
            score += 0.1

        return min(1.0, score)
