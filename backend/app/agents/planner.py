"""Planner agent - decomposes queries into sub-tasks"""
import logging
import json
from typing import List

from app.agents.state import ResearchState, SubTask
from app.utils.llm import get_claude_client
from app.domains.config import get_domain_config, DEPTH_CONFIG

logger = logging.getLogger(__name__)


PLANNER_SYSTEM_PROMPT = """You are a research planning expert. Your job is to break down complex research queries into specific, actionable sub-tasks.

For each query, you should:
1. Understand the domain (tech or investing)
2. Identify key aspects that need investigation
3. Determine appropriate sources for each aspect
4. Prioritize sub-tasks by importance

Available worker types:
- web_search: General web search for articles, blogs, documentation
- github: Search GitHub repositories and code examples
- docs: Search official documentation
- finance: Financial data and metrics (investing domain only)
- news: Recent news and market sentiment (investing domain only)

Output your plan as a JSON list of sub-tasks with this format:
[
  {
    "task_id": "1",
    "description": "Specific research task",
    "worker_type": "web_search",
    "priority": 5
  }
]

Priority scale: 1 (low) to 5 (critical)
"""


async def plan_research(state: ResearchState) -> ResearchState:
    """
    Plan research by decomposing query into sub-tasks

    Args:
        state: Current research state

    Returns:
        Updated state with sub-tasks and strategy
    """
    try:
        logger.info(f"Planning research for query: {state['query']}")

        query = state["query"]
        domain = state["domain"]
        depth = state["depth"]

        # Get domain configuration
        domain_config = get_domain_config(domain)
        depth_config = DEPTH_CONFIG[depth]

        # Create planning prompt
        prompt = f"""Query: "{query}"
Domain: {domain}
Research Depth: {depth} ({depth_config['time_estimate']})
Maximum Sources: {depth_config['max_sources']}

Available workers for this domain: {', '.join(domain_config.workers)}

Break this query into specific sub-tasks. Consider:
- What are the key aspects to research?
- What sources would provide the best information?
- How should tasks be prioritized?

Create 3-7 sub-tasks that will thoroughly answer this query."""

        # Get Claude to plan
        claude = get_claude_client()
        response = await claude.generate(
            prompt=prompt,
            system_prompt=PLANNER_SYSTEM_PROMPT,
            max_tokens=2048,
            temperature=0.5
        )

        # Parse sub-tasks from response
        sub_tasks = _parse_subtasks(response)

        # Filter by available workers
        available_workers = set(domain_config.workers)
        sub_tasks = [
            task for task in sub_tasks
            if task.worker_type in available_workers
        ]

        # Limit number of sub-tasks based on depth
        max_tasks = {"quick": 3, "standard": 5, "deep": 7}[depth]
        sub_tasks = sub_tasks[:max_tasks]

        logger.info(f"Created {len(sub_tasks)} sub-tasks")

        # Update state
        state["sub_tasks"] = sub_tasks
        state["research_strategy"] = f"Using {len(sub_tasks)} parallel searches across {len(set(t.worker_type for t in sub_tasks))} worker types"
        state["current_stage"] = "executing"
        state["max_iterations"] = depth_config["max_iterations"]
        state["iteration_count"] = 0

        return state

    except Exception as e:
        logger.error(f"Error in planner: {e}")
        state["current_stage"] = "failed"
        state["error_message"] = f"Planning failed: {str(e)}"
        return state


def _parse_subtasks(response: str) -> List[SubTask]:
    """
    Parse sub-tasks from Claude's response

    Args:
        response: Claude's JSON response

    Returns:
        List of SubTask objects
    """
    try:
        # Extract JSON from response (handle markdown code blocks)
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]

        # Parse JSON
        tasks_data = json.loads(json_str.strip())

        # Create SubTask objects
        sub_tasks = []
        for task_data in tasks_data:
            sub_task = SubTask(
                task_id=str(task_data.get("task_id", len(sub_tasks) + 1)),
                description=task_data.get("description", ""),
                worker_type=task_data.get("worker_type", "web_search"),
                priority=task_data.get("priority", 3),
                status="pending"
            )
            sub_tasks.append(sub_task)

        # Sort by priority (highest first)
        sub_tasks.sort(key=lambda t: t.priority, reverse=True)

        return sub_tasks

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing sub-tasks JSON: {e}")
        logger.error(f"Response was: {response}")

        # Fallback: create a single web search task
        return [
            SubTask(
                task_id="1",
                description="Search web for relevant information",
                worker_type="web_search",
                priority=5,
                status="pending"
            )
        ]
    except Exception as e:
        logger.error(f"Error creating sub-tasks: {e}")
        return []
