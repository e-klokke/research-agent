"""Pydantic schemas for API requests and responses"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class ResearchRequest(BaseModel):
    """Request to start a new research task"""
    query: str = Field(..., description="The research query", min_length=5)
    domain: Literal['tech', 'investing', 'academic'] = Field('tech', description="Research domain")
    depth: Literal['quick', 'standard', 'deep'] = Field('standard', description="Research depth")


class SourceResponse(BaseModel):
    """A research source in the response"""
    url: str
    title: str
    snippet: str
    source_type: str
    credibility_score: float


class ResearchStatus(BaseModel):
    """Status of a research task"""
    research_id: str
    status: Literal['planning', 'executing', 'quality_check', 'synthesizing', 'completed', 'failed']
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    current_stage: str
    sources_collected: int
    iteration: int
    error_message: Optional[str] = None


class ResearchResult(BaseModel):
    """Complete research result"""
    research_id: str
    query: str
    domain: str
    depth: str
    report: str
    sources: List[SourceResponse]
    confidence_score: float
    completed_at: datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
