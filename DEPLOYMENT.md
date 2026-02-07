# Deployment Guide

## Production Deployment Options

### Option 1: Docker Compose (Recommended for Self-Hosting)

**Prerequisites:**
- Docker and Docker Compose installed
- API keys configured

**Steps:**

1. **Clone and configure:**
```bash
git clone https://github.com/YOUR_USERNAME/research-agent.git
cd research-agent

# Create .env file
cp backend/.env.example .env

# Add your API keys to .env
nano .env
```

2. **Build and run:**
```bash
docker-compose up -d
```

3. **Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health

4. **View logs:**
```bash
docker-compose logs -f
```

5. **Stop:**
```bash
docker-compose down
```

### Option 2: Railway (Backend) + Vercel (Frontend)

#### Backend on Railway:

1. **Connect GitHub:**
   - Go to https://railway.app
   - Create new project from GitHub repo
   - Select `research-agent` repository

2. **Configure:**
   - Root directory: `/backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Add environment variables:**
   ```
   ANTHROPIC_API_KEY=your_key
   TAVILY_API_KEY=your_key
   GITHUB_TOKEN=your_key
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   ```

4. **Deploy:**
   - Railway will auto-deploy
   - Note the generated URL (e.g., https://research-agent-production.up.railway.app)

#### Frontend on Vercel:

1. **Connect GitHub:**
   - Go to https://vercel.com
   - Import your GitHub repository

2. **Configure:**
   - Root directory: `/frontend`
   - Framework preset: Next.js
   - Build command: `npm run build`
   - Output directory: `.next`

3. **Add environment variable:**
   ```
   NEXT_PUBLIC_API_URL=https://your-railway-url.railway.app
   ```

4. **Deploy:**
   - Vercel will auto-deploy
   - Access at: https://your-project.vercel.app

### Option 3: Render (Full Stack)

#### Backend:

1. **Create Web Service:**
   - Go to https://render.com
   - New → Web Service
   - Connect GitHub repository
   - Root directory: `backend`

2. **Configure:**
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3.11

3. **Add environment variables:**
   - Same as Railway above

#### Frontend:

1. **Create Static Site:**
   - New → Static Site
   - Root directory: `frontend`

2. **Configure:**
   - Build command: `npm install && npm run build`
   - Publish directory: `out`
   - Add environment variable: `NEXT_PUBLIC_API_URL`

## Environment Variables

### Required (Backend):
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
TAVILY_API_KEY=tvly-xxxxx
GITHUB_TOKEN=ghp_xxxxx
```

### Optional (Backend):
```env
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Required (Frontend):
```env
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

## Monitoring

### Health Checks:
- **Backend:** `GET /health`
- Expected response: `{"status":"healthy","timestamp":"..."}`

### Logs:
- **Docker:** `docker-compose logs -f backend`
- **Railway/Render:** View in dashboard

### Metrics to Monitor:
- API response times
- Error rates
- Research completion rates
- API costs (Anthropic + Tavily)

## Scaling

### Horizontal Scaling:
- Backend: Run multiple instances behind load balancer
- Frontend: Automatic with Vercel/Render

### Caching:
- Search results cached for 24 hours
- Add Redis for production caching:
  ```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  ```

### Database (Future):
- Replace in-memory storage with PostgreSQL
- Store research history persistently

## Cost Estimation

### Per Query:
- Anthropic API: $0.15-0.40
- Tavily API: $0.02-0.05
- **Total: ~$0.20-0.50 per research query**

### Monthly (100 queries/day):
- API costs: ~$600-1500/month
- Hosting:
  - Railway: ~$5-20/month
  - Vercel: Free tier OK for <1000 users
  - **Total: ~$605-1520/month**

### Optimization:
- Enable Claude prompt caching → 70-90% savings
- Implement query deduplication
- Target: **~$200-500/month** for 100 queries/day

## Security

### Production Checklist:
- [ ] Use HTTPS for all endpoints
- [ ] Add rate limiting
- [ ] Implement authentication (Clerk/Auth0)
- [ ] Rotate API keys regularly
- [ ] Enable CORS only for trusted domains
- [ ] Set up monitoring and alerts
- [ ] Enable automatic backups
- [ ] Use secrets management (not .env in production)

### Rate Limiting (Add to main.py):
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/research/start")
@limiter.limit("10/minute")
async def start_research(request: Request, ...):
    ...
```

## Troubleshooting

### Backend won't start:
1. Check environment variables are set
2. Verify API keys are valid
3. Check logs for specific errors

### Frontend can't connect to backend:
1. Verify `NEXT_PUBLIC_API_URL` is correct
2. Check CORS settings in backend
3. Ensure backend is running and accessible

### Research queries failing:
1. Check API key limits/quotas
2. Verify internet connectivity
3. Check worker logs for specific errors

## Support

For deployment issues:
- Check logs first
- Review TESTING.md for common issues
- Check GitHub Issues: https://github.com/YOUR_USERNAME/research-agent/issues
