# Development Setup Guide

## Prerequisites Installation

### 1. Python 3.11+
```bash
# macOS
brew install python@3.11

# Ubuntu
sudo apt update
sudo apt install python3.11 python3.11-venv

# Windows
# Download from python.org
```

### 2. Node.js 18+
```bash
# macOS
brew install node@18

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows
# Download from nodejs.org
```

## API Keys Setup

### 1. Anthropic API Key
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Navigate to API Keys
4. Create new key
5. Copy key (starts with `sk-ant-`)

### 2. Tavily API Key
1. Go to https://tavily.com
2. Sign up for account
3. Navigate to Dashboard
4. Copy API key

### 3. GitHub Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `public_repo`, `read:user`
4. Generate and copy token

## Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys

# Create app directory structure
mkdir -p app/agents app/workers app/domains app/models app/utils
touch app/__init__.py
touch app/agents/__init__.py
touch app/workers/__init__.py
touch app/domains/__init__.py
touch app/models/__init__.py
touch app/utils/__init__.py

# Run backend
uvicorn app.main:app --reload
```

Backend should be running at http://localhost:8000

Test with: http://localhost:8000/health

## Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Install additional packages
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Run frontend
npm run dev
```

Frontend should be running at http://localhost:3000

## Verify Setup

### 1. Test Backend API
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### 2. Test Frontend
- Open http://localhost:3000 in browser
- Should see Next.js default page

### 3. Test API Integration
```bash
curl -X POST http://localhost:8000/api/research/start \
  -H "Content-Type: application/json" \
  -d '{"query":"test","domain":"tech","depth":"quick"}'
```

## Common Issues

### Python venv not activating
- Windows: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Then retry activation

### Port already in use
- Backend: Change port with `uvicorn app.main:app --reload --port 8001`
- Frontend: Change port with `npm run dev -- -p 3001`

### Module not found errors
- Ensure venv is activated
- Run `pip install -r requirements.txt` again

### API key errors
- Verify keys are correct in `.env`
- Check for extra spaces or quotes
- Ensure `.env` is in backend directory

## Development Workflow

1. **Start Backend** (Terminal 1)
```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
```

2. **Start Frontend** (Terminal 2)
```bash
   cd frontend
   npm run dev
```

3. **Make Changes**
   - Backend: Edit Python files, auto-reloads
   - Frontend: Edit React components, auto-reloads

4. **Test**
   - Open http://localhost:3000
   - Submit test query
   - Check terminal logs for errors

## Ready to Build

Once setup is complete, you're ready to start building the agent following the implementation plan in `docs/IMPLEMENTATION_PLAN.md`.

Start with implementing the core agent components in `backend/app/agents/`.
