"""Server-Sent Events utilities for real-time streaming"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SSEStream:
    """Server-Sent Events stream manager"""

    @staticmethod
    def format_sse(data: Dict[str, Any], event: str = "message") -> str:
        """
        Format data as Server-Sent Event

        Args:
            data: Data to send
            event: Event type

        Returns:
            Formatted SSE string
        """
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    @staticmethod
    async def stream_progress(
        research_id: str,
        get_state_func
    ) -> AsyncGenerator[str, None]:
        """
        Stream research progress updates

        Args:
            research_id: Research task ID
            get_state_func: Function to get current state

        Yields:
            SSE formatted progress updates
        """
        last_stage = None
        last_sources_count = 0

        while True:
            try:
                state = get_state_func(research_id)

                if not state:
                    yield SSEStream.format_sse(
                        {"error": "Research not found"},
                        event="error"
                    )
                    break

                current_stage = state.get("current_stage", "unknown")
                sources_count = len(state.get("sources", []))

                # Send update if state changed
                if current_stage != last_stage or sources_count != last_sources_count:
                    progress_data = {
                        "research_id": research_id,
                        "stage": current_stage,
                        "sources_collected": sources_count,
                        "iteration": state.get("iteration_count", 0),
                        "timestamp": datetime.utcnow().isoformat()
                    }

                    yield SSEStream.format_sse(progress_data, event="progress")

                    last_stage = current_stage
                    last_sources_count = sources_count

                # Check if completed or failed
                if current_stage in ["completed", "failed"]:
                    final_data = {
                        "research_id": research_id,
                        "stage": current_stage,
                        "message": "Research completed" if current_stage == "completed" else "Research failed",
                        "error": state.get("error_message") if current_stage == "failed" else None
                    }
                    yield SSEStream.format_sse(final_data, event="complete")
                    break

                # Wait before next check
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error streaming progress: {e}")
                yield SSEStream.format_sse(
                    {"error": str(e)},
                    event="error"
                )
                break
