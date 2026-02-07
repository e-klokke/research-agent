"""FastAPI application for research agent"""
import os
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.models.schemas import (
    ResearchRequest,
    ResearchStatus,
    ResearchResult,
    SourceResponse,
    HealthResponse
)
from app.agents.state import ResearchState
from app.agents.graph import get_research_graph
from app.utils.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# In-memory storage for research tasks (for MVP, replace with Redis/DB later)
research_tasks: Dict[str, ResearchState] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    logger.info("Starting Research Agent API")
    # Warm up the graph
    get_research_graph()
    yield
    logger.info("Shutting down Research Agent API")


# Create FastAPI app
app = FastAPI(
    title="Research Agent API",
    description="AI-powered research agent for tech and investing intelligence",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.post("/api/research/start")
async def start_research(request: ResearchRequest) -> dict:
    """
    Start a new research task

    Args:
        request: Research request parameters

    Returns:
        Research ID for tracking
    """
    try:
        # Generate research ID
        research_id = str(uuid.uuid4())

        logger.info(f"Starting research {research_id}: {request.query}")

        # Initialize state
        initial_state: ResearchState = {
            "query": request.query,
            "domain": request.domain,
            "depth": request.depth,
            "sub_tasks": [],
            "research_strategy": "",
            "sources": [],
            "iteration_count": 0,
            "max_iterations": 2,
            "needs_more_research": False,
            "quality_score": 0.0,
            "identified_gaps": [],
            "final_report": None,
            "confidence_score": 0.0,
            "current_stage": "planning",
            "error_message": None,
        }

        # Store initial state
        research_tasks[research_id] = initial_state

        # Run research in background
        asyncio.create_task(run_research(research_id, initial_state))

        return {
            "research_id": research_id,
            "message": "Research started",
            "status": "planning"
        }

    except Exception as e:
        logger.error(f"Error starting research: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_research(research_id: str, initial_state: ResearchState):
    """
    Run research workflow in background

    Args:
        research_id: Research task ID
        initial_state: Initial research state
    """
    try:
        logger.info(f"Running research workflow for {research_id}")

        # Get graph
        graph = get_research_graph()

        # Run workflow
        final_state = await graph.ainvoke(initial_state)

        # Update stored state
        research_tasks[research_id] = final_state

        logger.info(f"Research {research_id} completed with status: {final_state['current_stage']}")

    except Exception as e:
        logger.error(f"Error running research {research_id}: {e}")
        # Update state with error
        research_tasks[research_id]["current_stage"] = "failed"
        research_tasks[research_id]["error_message"] = str(e)


@app.get("/api/research/status/{research_id}", response_model=ResearchStatus)
async def get_research_status(research_id: str):
    """
    Get status of a research task

    Args:
        research_id: Research task ID

    Returns:
        Current status
    """
    if research_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")

    state = research_tasks[research_id]

    # Calculate progress
    stage_progress = {
        "planning": 10,
        "executing": 40,
        "quality_check": 70,
        "synthesizing": 90,
        "completed": 100,
        "failed": 0
    }
    progress = stage_progress.get(state["current_stage"], 0)

    return ResearchStatus(
        research_id=research_id,
        status=state["current_stage"],
        progress=progress,
        current_stage=state["current_stage"],
        sources_collected=len(state.get("sources", [])),
        iteration=state.get("iteration_count", 0),
        error_message=state.get("error_message")
    )


@app.get("/api/research/result/{research_id}", response_model=ResearchResult)
async def get_research_result(research_id: str):
    """
    Get final research result

    Args:
        research_id: Research task ID

    Returns:
        Complete research result
    """
    if research_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")

    state = research_tasks[research_id]

    if state["current_stage"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Research not completed yet. Current stage: {state['current_stage']}"
        )

    if not state.get("final_report"):
        raise HTTPException(status_code=500, detail="Report not available")

    # Convert sources to response format
    sources_response = [
        SourceResponse(
            url=source.url,
            title=source.title,
            snippet=source.content[:200],
            source_type=source.source_type,
            credibility_score=source.credibility_score
        )
        for source in state["sources"][:20]
    ]

    return ResearchResult(
        research_id=research_id,
        query=state["query"],
        domain=state["domain"],
        depth=state["depth"],
        report=state["final_report"],
        sources=sources_response,
        confidence_score=state["confidence_score"],
        completed_at=datetime.utcnow()
    )


@app.get("/api/research/history")
async def get_research_history(limit: int = 10):
    """
    Get research history

    Args:
        limit: Maximum number of results to return

    Returns:
        List of completed research tasks
    """
    try:
        # Get completed research tasks
        completed = [
            {
                "research_id": rid,
                "query": state["query"],
                "domain": state["domain"],
                "depth": state["depth"],
                "completed": state["current_stage"] == "completed",
                "confidence_score": state.get("confidence_score", 0),
            }
            for rid, state in research_tasks.items()
            if state["current_stage"] in ["completed", "failed"]
        ]

        # Sort by most recent (research_id is UUID which is time-sortable)
        completed.sort(key=lambda x: x["research_id"], reverse=True)

        return {"history": completed[:limit], "total": len(completed)}

    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/research/export/{research_id}")
async def export_research(research_id: str, format: str = "json"):
    """
    Export research result in various formats

    Args:
        research_id: Research task ID
        format: Export format (json, markdown)

    Returns:
        Exported research data
    """
    if research_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")

    state = research_tasks[research_id]

    if state["current_stage"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Research not completed yet. Current stage: {state['current_stage']}"
        )

    try:
        if format == "json":
            # Export as JSON
            return {
                "research_id": research_id,
                "query": state["query"],
                "domain": state["domain"],
                "depth": state["depth"],
                "report": state["final_report"],
                "sources": [
                    {
                        "url": source.url,
                        "title": source.title,
                        "content": source.content[:500],
                        "type": source.source_type,
                        "credibility": source.credibility_score,
                    }
                    for source in state["sources"]
                ],
                "confidence_score": state["confidence_score"],
                "metadata": {
                    "iterations": state["iteration_count"],
                    "total_sources": len(state["sources"]),
                    "quality_score": state.get("quality_score", 0),
                }
            }

        elif format == "markdown":
            # Export as Markdown
            md = f"# Research Report\n\n"
            md += f"**Query:** {state['query']}\n\n"
            md += f"**Domain:** {state['domain']}\n\n"
            md += f"**Confidence:** {state['confidence_score']:.2f}/1.0\n\n"
            md += f"---\n\n"
            md += state["final_report"]
            return {"content": md, "format": "markdown"}

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except Exception as e:
        logger.error(f"Error exporting research: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/research/{research_id}")
async def delete_research(research_id: str):
    """
    Delete a research task from history

    Args:
        research_id: Research task ID

    Returns:
        Success message
    """
    if research_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")

    del research_tasks[research_id]
    return {"message": "Research deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
