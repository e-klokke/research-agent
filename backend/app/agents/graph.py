"""LangGraph workflow for research agent"""
import logging
from typing import Literal
from langgraph.graph import StateGraph, END

from app.agents.state import ResearchState
from app.agents.planner import plan_research
from app.agents.executor import execute_research
from app.agents.quality_checker import check_quality
from app.agents.synthesizer import synthesize_report

logger = logging.getLogger(__name__)


def should_continue_research(state: ResearchState) -> Literal["execute", "synthesize"]:
    """
    Determine if more research is needed or if we should proceed to synthesis

    Args:
        state: Current research state

    Returns:
        Next node to execute
    """
    needs_more = state.get("needs_more_research", False)
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 2)

    # Check if we should continue
    if needs_more and iteration_count < max_iterations:
        logger.info(f"Continuing research (iteration {iteration_count + 1}/{max_iterations})")
        return "execute"
    else:
        logger.info("Moving to synthesis")
        return "synthesize"


def create_research_graph() -> StateGraph:
    """
    Create the research workflow graph

    Graph structure:
        Entry → Plan → Execute → Quality Check
                         ↑            ↓
                         └────[needs_more?]
                                      ↓
                                  Synthesize → End

    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("plan", plan_research)
    workflow.add_node("execute", execute_research)
    workflow.add_node("quality_check", check_quality)
    workflow.add_node("synthesize", synthesize_report)

    # Add edges
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "quality_check")

    # Conditional edge: continue research or synthesize
    workflow.add_conditional_edges(
        "quality_check",
        should_continue_research,
        {
            "execute": "execute",
            "synthesize": "synthesize"
        }
    )

    workflow.add_edge("synthesize", END)

    # Compile graph
    return workflow.compile()


# Global graph instance
_research_graph = None


def get_research_graph():
    """Get or create the global research graph instance"""
    global _research_graph
    if _research_graph is None:
        logger.info("Compiling research graph")
        _research_graph = create_research_graph()
    return _research_graph
