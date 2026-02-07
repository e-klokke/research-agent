"""Synthesizer agent - creates final research report"""
import logging
from typing import List

from app.agents.state import ResearchState, Source
from app.utils.llm import get_claude_client
from app.domains.config import get_domain_config

logger = logging.getLogger(__name__)


async def synthesize_report(state: ResearchState) -> ResearchState:
    """
    Synthesize final research report from collected sources

    Args:
        state: Current research state

    Returns:
        Updated state with final report
    """
    try:
        logger.info("Synthesizing final report")

        query = state["query"]
        sources = state["sources"]
        domain = state["domain"]

        # Get domain config for template
        domain_config = get_domain_config(domain)

        # Build system prompt based on domain
        system_prompt = _build_system_prompt(domain)

        # Build research context from sources
        research_context = _build_research_context(sources)

        # Create synthesis prompt
        prompt = f"""Query: "{query}"

Research Findings:
{research_context}

Create a comprehensive research report that:
1. Directly answers the query
2. Synthesizes information from all sources
3. Resolves any contradictions
4. Provides clear recommendations
5. Includes proper citations
6. Assesses confidence level

Use the following structure:
{domain_config.synthesis_template}

Important:
- Be specific and actionable
- Cite sources with [1], [2], etc.
- Note any uncertainties or conflicting information
- Provide a confidence score (1-10) based on source quality and consensus
"""

        # Get Claude to synthesize
        claude = get_claude_client()
        report = await claude.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=4096,
            temperature=0.5
        )

        # Extract confidence score from report
        confidence_score = _extract_confidence_score(report)

        # Build source citations
        source_citations = _build_source_citations(sources)
        report += f"\n\n## Source Citations\n\n{source_citations}"

        # Update state
        state["final_report"] = report
        state["confidence_score"] = confidence_score
        state["current_stage"] = "completed"

        logger.info(f"Report synthesized. Confidence: {confidence_score}/10")

        return state

    except Exception as e:
        logger.error(f"Error in synthesizer: {e}")
        state["current_stage"] = "failed"
        state["error_message"] = f"Synthesis failed: {str(e)}"
        return state


def _build_system_prompt(domain: str) -> str:
    """Build system prompt based on domain"""
    if domain == "tech":
        return """You are a senior technology research analyst. Your reports are known for:
- Technical accuracy and depth
- Practical implementation guidance
- Balanced evaluation of trade-offs
- Clear security and risk assessments
- Actionable recommendations

Write in a professional but accessible style. Use technical terminology appropriately but explain complex concepts clearly."""

    elif domain == "investing":
        return """You are a senior investment research analyst. Your reports are known for:
- Rigorous fundamental analysis
- Data-driven insights
- Balanced risk assessment
- Clear investment thesis
- Practical recommendations

Write in a professional, objective style. Support claims with data and cite sources. Be clear about uncertainties and risks."""

    else:
        return "You are a research analyst. Create comprehensive, well-sourced reports."


def _build_research_context(sources: List[Source]) -> str:
    """Build research context from sources for synthesis"""
    context_parts = []

    for i, source in enumerate(sources[:20], 1):  # Top 20 sources
        context_parts.append(
            f"[{i}] {source.title}\n"
            f"Source: {source.source_type} | Credibility: {source.credibility_score:.2f}\n"
            f"URL: {source.url}\n"
            f"Content: {source.content[:500]}...\n"
        )

    return "\n".join(context_parts)


def _build_source_citations(sources: List[Source]) -> str:
    """Build formatted source citations"""
    citations = []

    for i, source in enumerate(sources[:20], 1):
        citations.append(
            f"[{i}] {source.title}\n"
            f"    {source.url}\n"
            f"    Type: {source.source_type} | "
            f"Credibility: {source.credibility_score:.2f}/1.0"
        )

    return "\n\n".join(citations)


def _extract_confidence_score(report: str) -> float:
    """
    Extract confidence score from report

    Args:
        report: The synthesized report

    Returns:
        Confidence score (0.0-1.0)
    """
    try:
        # Look for "Confidence Score: X/10" pattern
        if "Confidence Score:" in report:
            score_text = report.split("Confidence Score:")[1].split("\n")[0]
            # Extract number before /10
            score = float(score_text.split("/")[0].strip())
            return score / 10  # Normalize to 0-1

        # Default to medium confidence
        return 0.7

    except Exception as e:
        logger.warning(f"Could not extract confidence score: {e}")
        return 0.7
