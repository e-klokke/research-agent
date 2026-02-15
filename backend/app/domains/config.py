"""Domain-specific configurations for research"""
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class DomainConfig:
    """Configuration for a research domain"""
    name: str
    workers: List[str]  # List of worker types to use
    quality_weights: Dict[str, float]  # Weights for quality scoring
    max_sources: int  # Maximum sources to collect
    synthesis_template: str  # Template for final report


# Tech Domain Configuration
TECH_DOMAIN = DomainConfig(
    name="tech",
    workers=["web_search", "github", "docs", "stackoverflow", "reddit", "youtube"],
    quality_weights={
        "recency": 0.8,
        "authority": 0.9,
        "relevance": 0.95,
    },
    max_sources=30,
    synthesis_template="""# Technical Research Report

## Executive Summary
{summary}

## Key Findings
{findings}

## Technology Comparison
{comparison}

## Implementation Considerations
{implementation}

## Community Insights
{community}

## Security & Risk Analysis
{risks}

## Recommendations
{recommendations}

## Sources
{sources}

## Confidence Score: {confidence}/10
"""
)


# Investing Domain Configuration
INVESTING_DOMAIN = DomainConfig(
    name="investing",
    workers=["web_search", "finance", "news"],
    quality_weights={
        "recency": 0.95,
        "data_quality": 0.9,
        "source_credibility": 0.85,
    },
    max_sources=30,
    synthesis_template="""# Investment Analysis Report

## Executive Summary
{summary}

## Fundamental Analysis
{fundamentals}

## Market Sentiment
{sentiment}

## Financial Metrics
{metrics}

## Risk Assessment
{risks}

## Investment Recommendation
{recommendation}

## Sources
{sources}

## Confidence Score: {confidence}/10
"""
)


# Academic Domain Configuration
ACADEMIC_DOMAIN = DomainConfig(
    name="academic",
    workers=["academic", "web_search", "docs", "reddit", "stackoverflow"],
    quality_weights={
        "authority": 0.95,
        "citation_count": 0.9,
        "peer_review": 0.95,
    },
    max_sources=30,
    synthesis_template="""# Academic Research Report

## Abstract
{abstract}

## Literature Review
{literature_review}

## Key Papers & Findings
{key_papers}

## Methodology Analysis
{methodology}

## Citation Analysis
{citations}

## Community Discussion
{community}

## Research Gaps
{gaps}

## Future Directions
{future_work}

## Bibliography
{bibliography}

## Confidence Score: {confidence}/10
"""
)


# Depth configurations
DEPTH_CONFIG = {
    "quick": {
        "max_sources": 10,
        "max_iterations": 1,
        "time_estimate": "30-60 seconds"
    },
    "standard": {
        "max_sources": 20,
        "max_iterations": 2,
        "time_estimate": "1-2 minutes"
    },
    "deep": {
        "max_sources": 30,
        "max_iterations": 3,
        "time_estimate": "2-4 minutes"
    }
}


def get_domain_config(domain: str) -> DomainConfig:
    """Get configuration for a specific domain"""
    if domain == "tech":
        return TECH_DOMAIN
    elif domain == "investing":
        return INVESTING_DOMAIN
    elif domain == "academic":
        return ACADEMIC_DOMAIN
    else:
        raise ValueError(f"Unknown domain: {domain}")
