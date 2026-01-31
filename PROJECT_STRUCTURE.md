# FastMCP Cloud - Project Structure

## Required Files (Keep These)

### Core Application
- `main.py` - MCP server with all 12 tools
- `config.py` - Environment-based configuration
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project metadata
- `README.md` - Documentation

### Configuration
- `.env.example` - Environment template for cloud deployment
- `.gitignore` - Git configuration

### AI Prompts (Assistants)
- `prompts/financial_assistant.txt` - Financial advice chatbot
- `prompts/budget_coach.txt` - Budget optimization assistant  
- `prompts/savings_advisor.txt` - Savings strategy advisor

### Resource Files (Validation Data)
- `resources/categories.json` - Expense categories (21 main + 140+ subcategories)
- `resources/saving_sources.json` - Saving sources (14 types)
- `resources/budget_rules.json` - Budget calculation rules

### Runtime
- `data/` - SQLite database directory (created at runtime)
- `__pycache__/` - Python cache (auto-generated, can ignore)
- `.git/` - Git repository

---

## Files to Remove (Not Needed for FastMCP Cloud)

### Documentation Files
- `DEPLOYMENT_CHECKLIST.md`
- `DEPLOYMENT_COMPLETE.md`
- `FINAL_STATUS_REPORT.md`
- `GITHUB_DEPLOYMENT_GUIDE.md`
- `GITHUB_PUSH_SUMMARY.txt`
- `QUICK_GITHUB_PUSH.md`
- `READY_TO_DEPLOY.txt`
- `REMOTE_DEPLOYMENT_READY.txt`
- `FASTMCP_CLOUD_READY.txt`

### Test & Local Files
- `test_deployment.py`
- `syn_for_local.py`

### Infrastructure Files (Other Platforms)
- `deploy.sh`
- `docker-compose.yml`
- `Dockerfile`

### Development Files
- `uv.lock`
- `.python-version`

---

## FastMCP Cloud Deployment

**Upload to FastMCP Cloud:**
1. Only files under "Required Files" section
2. Keep prompts/ and resources/ folders
3. Set environment variables in FastMCP dashboard:
   - `MCP_TRANSPORT=sse`
   - `MCP_ENV=production`
   - `ENABLE_LOGGING=true`

**Expected Upload Size:** ~200 KB

**Post-Deployment:**
- Database will be created automatically in `data/` at first run
- All 12 tools immediately available to Claude
- AI assistants ready to use via tool calls
