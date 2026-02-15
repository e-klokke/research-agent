"""
Reddit Worker - Community discussions and sentiment analysis
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base import BaseWorker, Source


class RedditWorker(BaseWorker):
    """Worker for Reddit community discussions and sentiment analysis"""

    def __init__(self):
        super().__init__("reddit")
        self.client_id = os.getenv("REDDIT_CLIENT_ID", "")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        self.user_agent = "ResearchAgent/1.0"
        self.access_token = None
        self.token_expiry = None

        # Relevant subreddits by domain
        self.tech_subreddits = [
            "programming", "webdev", "reactjs", "Python", "MachineLearning",
            "devops", "kubernetes", "docker", "AWS", "golang", "rust",
            "javascript", "Frontend", "Backend", "softwareengineering"
        ]

        self.investing_subreddits = [
            "investing", "stocks", "wallstreetbets", "options",
            "ValueInvesting", "dividends", "StockMarket", "SecurityAnalysis",
            "Bogleheads", "ETFs", "CryptoCurrency", "personalfinance"
        ]

        self.academic_subreddits = [
            "science", "AskScience", "scholar", "GradSchool", "AskAcademia",
            "Physics", "biology", "chemistry", "ComputerScience", "math",
            "statistics", "neuroscience", "psychology"
        ]

    async def _get_access_token(self) -> str:
        """Get OAuth2 access token for Reddit API"""
        # Check if we have a valid token
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        if not self.client_id or not self.client_secret:
            # Fall back to public API (limited)
            return ""

        # Request new token
        auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
        data = {"grant_type": "client_credentials"}
        headers = {"User-Agent": self.user_agent}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://www.reddit.com/api/v1/access_token",
                    auth=auth,
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data.get("access_token", "")
                        expires_in = token_data.get("expires_in", 3600)
                        self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
                        return self.access_token
        except Exception as e:
            print(f"Reddit OAuth error: {e}")

        return ""

    async def search(
        self, query: str, max_results: int = 10, context: Optional[Dict[str, Any]] = None
    ) -> List[Source]:
        """
        Search Reddit for discussions

        Args:
            query: Search query
            max_results: Maximum number of results
            context: Additional context (domain, depth, etc.)

        Returns:
            List of Source objects with Reddit posts and comments
        """
        # Get access token
        token = await self._get_access_token()

        # Determine relevant subreddits based on context/query
        domain = context.get("domain", "tech") if context else "tech"
        subreddits = self._get_relevant_subreddits(domain, query)

        # Search across subreddits
        all_sources = []

        # Search in multiple subreddits concurrently
        tasks = [
            self._search_subreddit(query, subreddit, token, max_results // len(subreddits) + 1)
            for subreddit in subreddits[:5]  # Limit to top 5 subreddits
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_sources.extend(result)
            elif isinstance(result, Exception):
                print(f"Reddit search error: {result}")

        # Sort by score and recency
        all_sources.sort(
            key=lambda s: (
                s.metadata.get("score", 0),
                s.metadata.get("num_comments", 0),
            ),
            reverse=True,
        )

        return all_sources[:max_results]

    def _get_relevant_subreddits(self, domain: str, query: str) -> List[str]:
        """Get relevant subreddits based on domain and query"""
        query_lower = query.lower()

        if domain == "tech":
            subreddits = self.tech_subreddits.copy()
        elif domain == "investing":
            subreddits = self.investing_subreddits.copy()
        elif domain == "academic":
            subreddits = self.academic_subreddits.copy()
        else:
            subreddits = self.tech_subreddits.copy()

        # Boost specific subreddits based on query keywords
        keyword_map = {
            "react": ["reactjs", "Frontend"],
            "python": ["Python", "learnpython"],
            "kubernetes": ["kubernetes", "devops"],
            "docker": ["docker", "devops"],
            "machine learning": ["MachineLearning", "datascience"],
            "crypto": ["CryptoCurrency", "Bitcoin"],
            "stock": ["stocks", "StockMarket"],
        }

        # Reorder based on relevance
        for keyword, relevant_subs in keyword_map.items():
            if keyword in query_lower:
                for sub in relevant_subs:
                    if sub in subreddits:
                        subreddits.remove(sub)
                        subreddits.insert(0, sub)

        return subreddits

    async def _search_subreddit(
        self, query: str, subreddit: str, token: str, max_results: int
    ) -> List[Source]:
        """Search a specific subreddit"""
        sources = []

        url = f"https://oauth.reddit.com/r/{subreddit}/search" if token else f"https://www.reddit.com/r/{subreddit}/search.json"

        params = {
            "q": query,
            "limit": max_results,
            "sort": "relevance",
            "restrict_sr": "true",  # Restrict search to this subreddit
            "t": "all",  # Time filter: all time
        }

        headers = {"User-Agent": self.user_agent}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data.get("data", {}).get("children", [])

                        for post in posts:
                            post_data = post.get("data", {})
                            if not post_data:
                                continue

                            title = post_data.get("title", "")
                            selftext = post_data.get("selftext", "")
                            score = post_data.get("score", 0)
                            num_comments = post_data.get("num_comments", 0)
                            created_utc = post_data.get("created_utc", 0)
                            permalink = post_data.get("permalink", "")
                            author = post_data.get("author", "[deleted]")
                            subreddit_name = post_data.get("subreddit", subreddit)

                            # Build snippet
                            snippet = selftext[:300] if selftext else f"{num_comments} comments | Score: {score}"

                            # Convert timestamp to date
                            date_str = datetime.fromtimestamp(created_utc).strftime("%Y-%m-%d") if created_utc else None

                            # Calculate credibility based on score and comments
                            base_credibility = self.calculate_credibility(
                                domain="reddit.com",
                                has_author=author != "[deleted]",
                                date_str=date_str,
                            )

                            # Boost based on engagement
                            engagement_boost = min((score + num_comments) / 1000, 0.15)
                            credibility = min(base_credibility + engagement_boost, 0.75)  # Cap at 0.75 (community content)

                            source = self.create_source(
                                url=f"https://reddit.com{permalink}",
                                title=title,
                                content=snippet,
                                source_type="reddit_discussion",
                                metadata={
                                    "subreddit": subreddit_name,
                                    "author": author,
                                    "score": score,
                                    "num_comments": num_comments,
                                    "engagement": score + num_comments,
                                    "sentiment": self._analyze_sentiment(title, selftext),
                                },
                            )

                            source.credibility_score = credibility

                            sources.append(source)

        except Exception as e:
            print(f"Reddit search error for r/{subreddit}: {e}")

        return sources

    def _analyze_sentiment(self, title: str, text: str) -> str:
        """
        Simple sentiment analysis based on keywords
        Returns: 'positive', 'negative', or 'neutral'
        """
        combined = f"{title} {text}".lower()

        # Positive keywords
        positive_words = [
            "good", "great", "excellent", "amazing", "best", "love", "awesome",
            "perfect", "highly recommend", "works well", "success", "improved"
        ]

        # Negative keywords
        negative_words = [
            "bad", "terrible", "worst", "hate", "awful", "horrible", "broken",
            "doesn't work", "failed", "issue", "problem", "bug", "disappointed"
        ]

        positive_count = sum(1 for word in positive_words if word in combined)
        negative_count = sum(1 for word in negative_words if word in combined)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
