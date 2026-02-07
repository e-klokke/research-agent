# Instructions for Claude Code

## Project Context
This is a research agent that provides intelligent analysis for technology evaluation and investment research. It uses LangGraph for agent orchestration, FastAPI for the backend API, and Next.js for the frontend.

## Architecture
- **Backend**: Python FastAPI with LangGraph agent workflow
- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Agent Flow**: Planner → Executor → Quality Checker → Synthesizer
- **Domains**: Tech research and Investment research

## Implementation Priority
Follow the plan in `docs/IMPLEMENTATION_PLAN.md` exactly:
1. Week 1: Core infrastructure + basic tech research
2. Week 2: Expand tech sources + polish UI
3. Week 3: Add investing domain
4. Week 4: Production features

## Key Files to Build

### Phase 1 (Week 1, Days 1-7):
1. `backend/app/agents/state.py` - State definitions
2. `backend/app/domains/config.py` - Domain configurations
3. `backend/app/agents/planner.py` - Planner agent
4. `backend/app/workers/base.py` - Base worker class
5. `backend/app/workers/web_search.py` - Tavily integration
6. `backend/app/workers/github.py` - GitHub API integration
7. `backend/app/agents/executor.py` - Executor orchestrator
8. `backend/app/agents/quality_checker.py` - Quality validation
9. `backend/app/agents/synthesizer.py` - Report generation
10. `backend/app/agents/graph.py` - LangGraph workflow
11. `backend/app/utils/llm.py` - Claude API wrapper
12. `backend/app/main.py` - FastAPI application
13. `frontend/src/components/ResearchInput.tsx` - Input form
14. `frontend/src/components/ProgressTracker.tsx` - Progress display
15. `frontend/src/components/ResultsDisplay.tsx` - Results view
16. `frontend/src/lib/api.ts` - API client
17. `frontend/src/app/research/page.tsx` - Main research page

### Testing Requirements:
- After each component: Write unit test
- After Phase 1: End-to-end test with real tech query
- Log all API calls and responses
- Validate LangGraph state transitions

## Code Standards
- **Python**: Type hints, docstrings, async/await
- **TypeScript**: Strict mode, explicit types
- **Error Handling**: Try/catch all API calls
- **Logging**: Use structured logging
- **Comments**: Explain complex logic

## Development Guidelines
1. Build incrementally - one component at a time
2. Test each component before moving to next
3. Use the provided code skeleton as reference
4. Follow the exact file structure shown
5. Don't skip error handling
6. Log progress at each step

## First Test Query
When Phase 1 is complete, test with:
"Compare Kubernetes vs Docker Swarm for enterprise deployment with 500 employees"

Expected:
- Execution time: < 3 minutes
- Sources: 15-25
- Output: Structured technical report with sources

## Questions to Ask
Before implementing each component, ask:
1. What is this component's responsibility?
2. What state does it receive and return?
3. What external APIs does it call?
4. What error cases need handling?
5. How do I test it works correctly?

## Success Criteria
- All components follow architecture diagram
- State flows correctly through LangGraph
- Frontend polls backend and displays results
- Reports include proper citations
- Cost per query < $0.50

Start with Phase 1, Day 1-2: Project Setup and core infrastructure.
