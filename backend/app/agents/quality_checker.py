"""Quality checker agent - validates research quality and identifies gaps"""
import logging
from typing import List

from app.agents.state import ResearchState, Source
from app.utils.llm import get_claude_client

logger = logging.getLogger(__name__)


QUALITY_CHECKER_SYSTEM_PROMPT = """You are a research quality analyst. Your job is to evaluate the quality and completeness of research findings.

Analyze the collected sources and determine:
1. Overall quality score (0.0 to 1.0)
2. Whether the sources adequately answer the query
3. Any critical information gaps
4. Whether more research is needed

Consider:
- Source credibility and diversity
- Recency and relevance of information
- Coverage of different perspectives
- Presence of contradictory information
- Depth of technical/financial details

Respond in this format:
QUALITY_SCORE: 0.0-1.0
NEEDS_MORE: yes/no
GAPS:
- Gap 1 (if any)
- Gap 2 (if any)
REASONING: Brief explanation
"""


async def check_quality(state: ResearchState) -> ResearchState:
    """
    Check quality of collected sources and identify gaps

    Args:
        state: Current research state

    Returns:
        Updated state with quality assessment
    """
    try:
        logger.info("Checking research quality")

        query = state["query"]
        sources = state["sources"]
        iteration_count = state["iteration_count"]
        max_iterations = state["max_iterations"]

        # Check if we have minimum sources
        if len(sources) < 5:
            logger.warning(f"Only {len(sources)} sources collected")
            if iteration_count < max_iterations:
                state["needs_more_research"] = True
                state["identified_gaps"] = ["Insufficient sources collected"]
                state["quality_score"] = 0.3
                state["current_stage"] = "executing"
                return state

        # Calculate basic quality metrics
        avg_credibility = sum(s.credibility_score for s in sources) / len(sources) if sources else 0
        source_types = set(s.source_type for s in sources)
        diversity_score = len(source_types) / 3  # Normalize by expected types

        # Build summary for Claude
        sources_summary = _build_sources_summary(sources[:15])  # Top 15 sources

        prompt = f"""Query: "{query}"

Sources collected: {len(sources)}
Average credibility: {avg_credibility:.2f}
Source types: {', '.join(source_types)}
Iterations so far: {iteration_count}/{max_iterations}

Top Sources:
{sources_summary}

Evaluate if these sources adequately answer the query. Consider:
- Do we have enough high-quality sources?
- Are there major gaps in coverage?
- Is there sufficient diversity of perspectives?
- Should we conduct more research (we have {max_iterations - iteration_count} iterations left)?"""

        # Get Claude's assessment
        claude = get_claude_client()
        response = await claude.generate(
            prompt=prompt,
            system_prompt=QUALITY_CHECKER_SYSTEM_PROMPT,
            max_tokens=1024,
            temperature=0.3
        )

        # Parse response
        quality_score, needs_more, gaps = _parse_quality_response(response)

        # Don't iterate more if we've hit the limit
        if iteration_count >= max_iterations:
            needs_more = False
            logger.info("Max iterations reached, proceeding to synthesis")

        # Update state
        state["quality_score"] = quality_score
        state["needs_more_research"] = needs_more
        state["identified_gaps"] = gaps

        if needs_more:
            logger.info(f"Quality check: More research needed. Gaps: {gaps}")
            state["current_stage"] = "executing"
        else:
            logger.info(f"Quality check: Sufficient quality ({quality_score:.2f})")
            state["current_stage"] = "synthesizing"

        return state

    except Exception as e:
        logger.error(f"Error in quality checker: {e}")
        # On error, proceed to synthesis with what we have
        state["quality_score"] = 0.5
        state["needs_more_research"] = False
        state["identified_gaps"] = []
        state["current_stage"] = "synthesizing"
        return state


def _build_sources_summary(sources: List[Source]) -> str:
    """Build a summary of sources for quality assessment"""
    summary = []
    for i, source in enumerate(sources[:15], 1):
        summary.append(
            f"{i}. [{source.source_type}] {source.title}\n"
            f"   URL: {source.url}\n"
            f"   Credibility: {source.credibility_score:.2f}\n"
            f"   Preview: {source.content[:150]}...\n"
        )
    return "\n".join(summary)


def _parse_quality_response(response: str) -> tuple[float, bool, List[str]]:
    """
    Parse quality checker response

    Args:
        response: Claude's response

    Returns:
        Tuple of (quality_score, needs_more, gaps)
    """
    try:
        quality_score = 0.5
        needs_more = False
        gaps = []

        lines = response.strip().split("\n")
        for line in lines:
            line = line.strip()

            if line.startswith("QUALITY_SCORE:"):
                try:
                    quality_score = float(line.split(":")[1].strip())
                except ValueError:
                    pass

            elif line.startswith("NEEDS_MORE:"):
                needs_more = "yes" in line.lower()

            elif line.startswith("- ") and "GAPS:" in response.split(line)[0]:
                gap = line[2:].strip()
                if gap and not gap.startswith("Gap"):
                    gaps.append(gap)

        return quality_score, needs_more, gaps

    except Exception as e:
        logger.error(f"Error parsing quality response: {e}")
        return 0.5, False, []
