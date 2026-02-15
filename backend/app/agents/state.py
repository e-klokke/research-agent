"""State definitions for LangGraph workflow"""
from typing import TypedDict, List, Optional, Literal
from dataclasses import dataclass


@dataclass
class Source:
    """A research source with metadata"""
    url: str
    title: str
    content: str
    source_type: str  # 'web', 'github', 'docs', 'finance', 'news'
    credibility_score: float  # 0.0 to 1.0
    timestamp: str
    metadata: dict


@dataclass
class SubTask:
    """A decomposed research sub-task"""
    task_id: str
    description: str
    worker_type: str  # 'web_search', 'github', 'docs', etc.
    priority: int  # 1-5, higher is more important
    status: Literal['pending', 'in_progress', 'completed', 'failed']


class ResearchState(TypedDict):
    """Main state for the research workflow"""
    # Input
    query: str
    domain: Literal['tech', 'investing', 'academic']
    depth: Literal['quick', 'standard', 'deep']

    # Planning phase
    sub_tasks: List[SubTask]
    research_strategy: str

    # Execution phase
    sources: List[Source]
    iteration_count: int
    max_iterations: int

    # Quality checking phase
    needs_more_research: bool
    quality_score: float
    identified_gaps: List[str]

    # Synthesis phase
    final_report: Optional[str]
    confidence_score: float

    # Status tracking
    current_stage: Literal['planning', 'executing', 'quality_check', 'synthesizing', 'completed', 'failed']
    error_message: Optional[str]
