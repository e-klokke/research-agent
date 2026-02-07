# Testing Guide

This guide walks through testing the Phase 1 research agent implementation.

## Prerequisites

Before testing, ensure you have:
1. Python 3.11+ installed
2. Node.js 18+ installed
3. API keys for:
   - Anthropic (Claude)
   - Tavily (web search)
   - GitHub (optional, but recommended)

## Setup Steps

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Edit `backend/.env` and add your API keys:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
TAVILY_API_KEY=tvly-your-key-here
GITHUB_TOKEN=ghp_your-token-here

ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

### Terminal 1: Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Test backend health:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","timestamp":"..."}
```

### Terminal 2: Start Frontend

```bash
cd frontend
npm run dev
```

Expected output:
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

## Testing Scenarios

### Test 1: Quick Tech Research

1. Open http://localhost:3000
2. Click "Start Research"
3. Enter query: "Compare Redis vs Memcached for session storage"
4. Domain: Technology
5. Depth: Quick
6. Click "Start Research"

**Expected Results:**
- Progress tracker appears showing stages
- Research completes in 30-60 seconds
- Report includes:
  - Executive summary
  - Technology comparison
  - Implementation considerations
  - Recommendations
  - 10-15 sources cited
  - Confidence score

### Test 2: Standard Tech Research

Query: "Compare Kubernetes vs Docker Swarm for enterprise deployment with 500 employees"

**Expected Results:**
- Completes in 1-2 minutes
- 15-20 sources collected
- Comprehensive analysis covering:
  - Architecture comparison
  - Scalability considerations
  - Security features
  - Operational complexity
  - Cost implications
- Higher confidence score than quick research

### Test 3: Deep Tech Research

Query: "Evaluate zero-trust architecture solutions for hybrid cloud security"

**Expected Results:**
- Completes in 2-4 minutes
- 20-25 sources collected
- Multiple research iterations
- Detailed analysis with:
  - Multiple vendor solutions
  - Implementation patterns
  - Security assessments
  - Real-world case studies

## Validation Checklist

### Backend
- [ ] Server starts without errors
- [ ] Health endpoint returns 200
- [ ] Logs show agent workflow execution
- [ ] Claude API calls succeed
- [ ] Tavily API calls succeed
- [ ] GitHub API calls succeed (if token provided)

### Frontend
- [ ] Page loads without errors
- [ ] Input form validates correctly
- [ ] Progress tracker updates in real-time
- [ ] Results display properly formatted
- [ ] Sources are clickable and open in new tabs
- [ ] Confidence score displays correctly

### Agent Workflow
- [ ] Planner creates appropriate sub-tasks
- [ ] Executor runs tasks in parallel
- [ ] Quality checker validates sources
- [ ] Synthesizer creates coherent report
- [ ] Sources are properly cited
- [ ] No duplicate sources in results

## Common Issues

### Issue: "ANTHROPIC_API_KEY not set"
**Solution:** Check that `.env` file exists in `backend/` directory and contains valid API key

### Issue: "TAVILY_API_KEY not set"
**Solution:** Sign up at https://tavily.com and add API key to `.env`

### Issue: "Connection refused" errors
**Solution:** Ensure backend is running on port 8000 before starting frontend

### Issue: Research times out
**Solution:**
- Check API keys are valid
- Check internet connection
- Review backend logs for errors
- Reduce research depth to "quick" for testing

### Issue: Frontend shows CORS errors
**Solution:** Backend should already have CORS configured for localhost:3000. Check that backend is running.

## Performance Benchmarks

Expected performance metrics:

| Depth    | Time      | Sources | API Calls |
|----------|-----------|---------|-----------|
| Quick    | 30-60s    | 10-15   | 3-5       |
| Standard | 1-2 min   | 15-20   | 5-8       |
| Deep     | 2-4 min   | 20-25   | 8-12      |

## Cost Estimation

Phase 1 implementation costs (per query):

- Claude API: $0.15-0.40
- Tavily API: $0.02-0.05
- Total: **$0.20-0.50 per query**

With prompt caching (future optimization):
- Estimated savings: 70-90%
- Target cost: **$0.05-0.15 per query**

## Next Steps After Testing

Once Phase 1 testing is successful:

1. **Week 2 (Days 8-14):**
   - Add DocsWorker and StackOverflowWorker
   - Implement source credibility scoring refinements
   - Build enhanced UI components
   - Test with 10+ real queries

2. **Week 3 (Days 15-21):**
   - Add investing domain workers (Finance, SEC, News)
   - Implement investment-specific synthesis
   - Cross-domain testing

3. **Week 4 (Days 22-28):**
   - Add research history and export
   - Set up production deployment
   - Launch preparation

## Support

If you encounter issues:
1. Check logs in `backend/logs/research_agent.log`
2. Review this testing guide
3. Check API key validity
4. Verify all dependencies are installed

## Success Criteria

Phase 1 is successful if:
- [x] All core components implemented
- [ ] Backend starts without errors
- [ ] Frontend connects to backend
- [ ] Research workflow completes end-to-end
- [ ] Reports are coherent and well-structured
- [ ] Sources are relevant and properly cited
- [ ] Performance meets benchmarks
- [ ] Cost per query < $0.60
