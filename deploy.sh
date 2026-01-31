#!/bin/bash
# Quick deployment commands for Expense Tracker MCP Server

# ============================================
# STEP 1: Push to GitHub
# ============================================
echo "Step 1: Pushing to GitHub..."
git add -A
git commit -m "Production-ready: Expense Tracker MCP Server with remote deployment support"
git branch -M main
git push -u origin main

echo "✅ Pushed to GitHub!"

# ============================================
# STEP 2: Deploy Locally (Claude Desktop)
# ============================================
echo ""
echo "Step 2: To run locally on Claude Desktop:"
echo "  python main.py"

# ============================================
# STEP 3: Deploy to Render.com
# ============================================
echo ""
echo "Step 3: To deploy to Render:"
echo "  1. Sign up at render.com"
echo "  2. Create new Web Service"
echo "  3. Connect your GitHub repository"
echo "  4. Set environment variables:"
echo "     MCP_TRANSPORT=sse"
echo "     MCP_HOST=0.0.0.0"
echo "     MCP_PORT=8000"
echo "  5. Deploy!"

# ============================================
# STEP 4: Deploy to Railway
# ============================================
echo ""
echo "Step 4: To deploy to Railway:"
echo "  1. Sign up at railway.app"
echo "  2. Create new project"
echo "  3. Deploy from GitHub"
echo "  4. Set environment variables:"
echo "     MCP_TRANSPORT=sse"
echo "     MCP_HOST=0.0.0.0"
echo "     MCP_PORT=8000"

# ============================================
# STEP 5: Deploy with Docker
# ============================================
echo ""
echo "Step 5: To deploy with Docker:"
echo "  docker build -t expense-tracker ."
echo "  docker run -p 8000:8000 \\"
echo "    -e MCP_TRANSPORT=sse \\"
echo "    -e MCP_HOST=0.0.0.0 \\"
echo "    -e MCP_PORT=8000 \\"
echo "    expense-tracker"
