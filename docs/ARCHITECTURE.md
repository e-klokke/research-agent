# Research Agent Architecture

## System Overview
```
User Query → Planner → Executor (parallel) → Quality Checker → Synthesizer → Output
                ↓           ↓
            Memory ←→ Vector Store
```

## Core Components

### 1. Planner Agent
- Decomposes complex queries into sub-tasks
- Selects appropriate sources based on domain
- Determines research depth and strategy

### 2. Executor Agent
- Orchestrates parallel worker execution
- Workers: WebSearch, GitHub, Docs, Finance, News
- Async execution with asyncio.gather()

### 3. Quality Checker
- Filters sources by credibility score
- Detects information gaps
- Triggers re-search if needed (max 3 iterations)

### 4. Synthesizer Agent
- Combines findings into structured report
- Resolves contradictions
- Generates confidence scores

### 5. Memory System
- Short-term: Redis (session context)
- Long-term: PostgreSQL + Vector DB (past research)

## Domain Configuration

### Tech Domain
- **Sources**: Web, GitHub, Stack Overflow, Documentation
- **Workers**: web_search, github, docs, stackoverflow
- **Quality Weights**: recency=0.8, authority=0.9
- **Output**: Technical evaluation report

### Investing Domain
- **Sources**: Yahoo Finance, SEC Filings, News, Analysis
- **Workers**: web_search, finance, sec_filings, news
- **Quality Weights**: recency=0.95, data_quality=0.9
- **Output**: Investment analysis report

## LangGraph Workflow
```python
Entry → Planner → Executor → Quality Check
                                    ↓
                        [needs_more?] → Yes → Executor (loop)
                                    ↓
                                   No → Synthesizer → End
```

## API Endpoints
- `POST /api/research/start` - Start research
- `GET /api/research/status/{id}` - Poll progress
- `GET /api/research/result/{id}` - Get final report

## Cost Optimization
- Prompt caching with Claude (90% savings)
- Redis caching for search results (24hr TTL)
- Vector DB for similar query matching
- Estimated: $0.20-0.60 per query
