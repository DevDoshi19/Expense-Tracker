# Expense Tracker MCP Server - GitHub & Cloud Deployment Guide

## 📋 Step 1: Prepare GitHub Repository

### Create a new GitHub repository
1. Go to github.com/new
2. Repository name: `expense-tracker-mcp-server`
3. Description: "Personal finance tracking MCP server with expenses, savings, budgets, and goals"
4. Choose Public or Private
5. Click "Create Repository"

### Copy the commands they provide

---

## 📤 Step 2: Push to GitHub

```bash
# Navigate to your project
cd c:\Users\devdo\OneDrive\Desktop\expense-tracker-mcp-server

# Initialize git (if not already done)
git init

# Add your GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/expense-tracker-mcp-server.git

# Add all files
git add -A

# Create initial commit
git commit -m "Initial commit: Expense Tracker MCP Server - Production Ready"

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## 📁 Step 3: Which Files to Upload

### ✅ UPLOAD THESE:
```
expense-tracker-mcp-server/
├── main.py                          (Core server - 950 lines)
├── config.py                        (Configuration - NEW)
├── syn_for_local.py                 (Local helper)
├── requirements.txt                 (Python dependencies)
├── pyproject.toml                   (Project metadata)
├── README.md                        (Project overview)
├── prompts/
│   ├── financial_assistant.txt
│   ├── budget_coach.txt
│   └── savings_advisor.txt
├── resources/
│   ├── categories.json
│   ├── saving_sources.json
│   └── budget_rules.json
├── DEPLOYMENT_CHECKLIST.md          (Pre-deployment guide)
├── FINAL_STATUS_REPORT.md           (Project status)
├── DEPLOYMENT_COMPLETE.md           (Completion report)
├── READY_TO_DEPLOY.txt              (Summary)
├── test_deployment.py               (Verification script)
└── .gitignore                       (Already set up)
```

### ❌ DO NOT UPLOAD THESE:
```
data/                                (User databases - add to .gitignore)
__pycache__/                         (Already in .gitignore)
.venv/                               (Virtual env - already in .gitignore)
.git/                                (Git metadata)
```

### ✅ Make sure .gitignore includes:
```
data/
__pycache__/
.venv/
.env
*.db
*.sqlite
uv.lock
```

---

## 🚀 Step 4: Deployment Options

### **Option A: Local (Claude Desktop) - NO CHANGES NEEDED**
```
Current setup works as-is. Just restart Claude Desktop.

Transport: stdio (default)
Command: mcp.run()
```

### **Option B: Cloud Deployment (Render, Railway, Heroku)**

#### For Render.com:
```bash
# Set environment variables in Render dashboard:
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0  # Listen on all interfaces
MCP_PORT=5000     # Render will assign a port

# Start command: python main.py
```

#### For Railway.app:
```bash
# Set environment variables:
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8000

# Connect via: https://your-railway-url.up.railway.app:8000
```

#### For Heroku:
```bash
# Install Heroku CLI
# Create Procfile with:
web: python main.py

# Set environment variables:
heroku config:set MCP_TRANSPORT=sse
heroku config:set MCP_HOST=0.0.0.0
heroku config:set MCP_PORT=8000

# Deploy via git push heroku main
```

### **Option C: Docker Deployment**

#### Create Dockerfile:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy project files
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Set environment for remote deployment
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

# Create data directory
RUN mkdir -p data

# Run server
CMD ["python", "main.py"]

EXPOSE 8000
```

#### Create docker-compose.yml:
```yaml
version: '3.8'

services:
  expense-tracker:
    build: .
    ports:
      - "8000:8000"
    environment:
      MCP_TRANSPORT: sse
      MCP_HOST: 0.0.0.0
      MCP_PORT: 8000
      MCP_ENV: production
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

#### Deploy with Docker:
```bash
# Build and run locally
docker-compose up --build

# Or on server
docker build -t expense-tracker .
docker run -p 8000:8000 -e MCP_TRANSPORT=sse -e MCP_HOST=0.0.0.0 -e MCP_PORT=8000 expense-tracker
```

---

## 🔧 Step 5: Configuration for Remote Servers

### Environment Variables to Set:

```bash
# Deployment environment
MCP_ENV=production              # or "local"

# Transport configuration
MCP_TRANSPORT=sse              # or "http", "stdio"
MCP_HOST=0.0.0.0              # 0.0.0.0 for cloud, localhost for local
MCP_PORT=8000                 # Port number (cloud assigns automatically)

# Database
DB_ENABLE_WAL=true            # Enable WAL mode for concurrency

# Logging
ENABLE_LOGGING=true           # Set to false in production for performance
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Security
ALLOWED_ORIGINS=*             # Restrict in production
```

### Example .env file for production:
```
MCP_ENV=production
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8000
DB_ENABLE_WAL=true
ENABLE_LOGGING=false
LOG_LEVEL=WARNING
ALLOWED_ORIGINS=https://your-domain.com
```

---

## 🔐 Step 6: Security Checklist for Production

- [ ] Use HTTPS/TLS in production
- [ ] Set `MCP_HOST=0.0.0.0` to listen on all interfaces
- [ ] Use environment variables (not hardcoded values)
- [ ] Restrict `ALLOWED_ORIGINS` to your domain
- [ ] Enable database backups
- [ ] Set `ENABLE_LOGGING=false` for performance
- [ ] Use strong authentication for cloud platforms
- [ ] Regular security updates for Python packages
- [ ] Monitor error logs and performance

---

## 📊 Step 7: GitHub Repository Best Practices

### Add a .gitignore file:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
data/
*.db
*.sqlite
*.sqlite3
uv.lock
.env
.env.local

# OS
.DS_Store
Thumbs.db
```

### Add a README.md in root:
Already exists! It's good to go.

### Add a LICENSE:
Choose a license (MIT recommended for open source):
- MIT License (permissive, popular)
- Apache 2.0 (with patent clause)
- GPL 3.0 (copyleft)

```bash
# Create LICENSE file in root
git add LICENSE
git commit -m "Add MIT License"
git push
```

---

## 🌍 Step 8: Access from Claude Desktop (Remote)

### If deploying to cloud:

1. Update `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "python",
      "args": [
        "c:/path/to/main.py"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

2. For remote access, use the MCP client library:
```bash
pip install mcp
```

3. Create a client script:
```python
import asyncio
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def connect_remote():
    # Connect to remote MCP server
    url = "https://your-server.com:8000"
    async with sse_client(url) as transport:
        async with ClientSession(transport) as session:
            # Use the tools here
            pass

asyncio.run(connect_remote())
```

---

## 📋 Step 9: Deployment Checklist

### Before pushing to GitHub:
- [ ] All files committed locally
- [ ] No sensitive data in code
- [ ] .gitignore is set up correctly
- [ ] README is comprehensive
- [ ] LICENSE file added
- [ ] config.py created and tested
- [ ] test_deployment.py passes

### After pushing to GitHub:
- [ ] Repository is visible on GitHub
- [ ] All files are uploaded correctly
- [ ] Clone to test: `git clone https://github.com/YOUR_USERNAME/expense-tracker-mcp-server.git`
- [ ] Test locally: `python main.py`

### For cloud deployment:
- [ ] Create Dockerfile (if using containers)
- [ ] Set environment variables on platform
- [ ] Configure domain/SSL
- [ ] Test remote connection
- [ ] Monitor logs for errors
- [ ] Set up automated backups

---

## 🔄 Step 10: Continuous Deployment

### GitHub Actions (Auto-deploy on push):

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Render
        run: |
          curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
```

---

## 📞 Summary

**Quick Start:**
```bash
# Step 1: Commit and push to GitHub
git add -A
git commit -m "Initial commit"
git push -u origin main

# Step 2: For local (Claude Desktop) - done!
# Step 3: For cloud deployment - set environment variables:
export MCP_TRANSPORT=sse
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
python main.py
```

**Your project is now:**
✅ Version controlled on GitHub
✅ Ready for local deployment (Claude Desktop)
✅ Configured for remote deployment (cloud)
✅ Docker-ready (containerization)
✅ Scalable and maintainable

**Next:** Choose your deployment platform and set environment variables accordingly!

