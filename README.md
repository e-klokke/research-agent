# Research Agent - Tech & Investing Intelligence

AI-powered research agent for technology evaluation and investment analysis.

## Features
- **Tech Research**: Technology comparisons, security analysis, implementation guides
- **Investment Research**: Fundamental analysis, market sentiment, risk assessment
- **Multi-source Intelligence**: Web, GitHub, documentation, financial data
- **Quality Validation**: Credibility scoring, gap detection, iterative refinement

## Architecture
- **Backend**: Python + FastAPI + LangGraph
- **Frontend**: Next.js + TypeScript + Tailwind
- **LLM**: Claude 3.5 Sonnet (Anthropic)
- **Search**: Tavily API, GitHub API

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- API Keys: Anthropic, Tavily, GitHub

### Setup
```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/research-agent.git
cd research-agent

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add API keys to .env
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000

## API Keys Required
- `ANTHROPIC_API_KEY`: Get from https://console.anthropic.com
- `TAVILY_API_KEY`: Get from https://tavily.com
- `GITHUB_TOKEN`: Get from https://github.com/settings/tokens

## Development Status
🚧 **In Development** - Week 1: Core tech research agent

## License
MIT
