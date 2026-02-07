"""Executor agent - orchestrates parallel worker execution"""
import asyncio
import logging
from typing import List, Dict

from app.agents.state import ResearchState, Source, SubTask
from app.workers.web_search import WebSearchWorker
from app.workers.github import GitHubWorker
from app.workers.finance import FinanceWorker
from app.workers.news import NewsWorker
from app.domains.config import get_domain_config

logger = logging.getLogger(__name__)


class Executor:
    """Orchestrates parallel execution of research tasks"""

    def __init__(self):
        self.workers: Dict[str, any] = {
            "web_search": WebSearchWorker(),
            "github": GitHubWorker(),
            "finance": FinanceWorker(),
            "news": NewsWorker(),
        }

    async def execute_task(self, task: SubTask, query: str) -> List[Source]:
        """
        Execute a single research task

        Args:
            task: The sub-task to execute
            query: The original research query

        Returns:
            List of sources found
        """
        try:
            worker = self.workers.get(task.worker_type)
            if not worker:
                logger.warning(f"No worker found for type: {task.worker_type}")
                return []

            # Create search query from task description and original query
            search_query = f"{query} {task.description}"

            logger.info(f"Executing task {task.task_id}: {task.description}")
            sources = await worker.search(search_query, max_results=10)

            return sources

        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
            return []

    async def execute_all_tasks(
        self,
        tasks: List[SubTask],
        query: str
    ) -> List[Source]:
        """
        Execute all tasks in parallel

        Args:
            tasks: List of sub-tasks to execute
            query: The original research query

        Returns:
            Combined list of all sources
        """
        try:
            logger.info(f"Executing {len(tasks)} tasks in parallel")

            # Execute all tasks concurrently
            results = await asyncio.gather(
                *[self.execute_task(task, query) for task in tasks],
                return_exceptions=True
            )

            # Combine all sources
            all_sources = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Task {tasks[i].task_id} failed: {result}")
                else:
                    all_sources.extend(result)
                    tasks[i].status = "completed"

            logger.info(f"Collected {len(all_sources)} total sources")

            # Remove duplicates based on URL
            seen_urls = set()
            unique_sources = []
            for source in all_sources:
                if source.url not in seen_urls:
                    seen_urls.add(source.url)
                    unique_sources.append(source)

            logger.info(f"After deduplication: {len(unique_sources)} unique sources")

            return unique_sources

        except Exception as e:
            logger.error(f"Error executing tasks: {e}")
            return []


async def execute_research(state: ResearchState) -> ResearchState:
    """
    Execute research by running all sub-tasks in parallel

    Args:
        state: Current research state

    Returns:
        Updated state with collected sources
    """
    try:
        logger.info("Executing research tasks")

        query = state["query"]
        sub_tasks = state["sub_tasks"]
        domain = state["domain"]

        # Get domain config for max sources
        domain_config = get_domain_config(domain)

        # Create executor
        executor = Executor()

        # Execute all tasks
        new_sources = await executor.execute_all_tasks(sub_tasks, query)

        # Add to existing sources
        existing_sources = state.get("sources", [])
        all_sources = existing_sources + new_sources

        # Sort by credibility score
        all_sources.sort(key=lambda s: s.credibility_score, reverse=True)

        # Limit to max sources
        all_sources = all_sources[:domain_config.max_sources]

        # Update state
        state["sources"] = all_sources
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        state["current_stage"] = "quality_check"

        logger.info(f"Execution complete. Total sources: {len(all_sources)}")

        return state

    except Exception as e:
        logger.error(f"Error in executor: {e}")
        state["current_stage"] = "failed"
        state["error_message"] = f"Execution failed: {str(e)}"
        return state
