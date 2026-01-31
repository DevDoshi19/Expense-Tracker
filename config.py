#!/usr/bin/env python3
"""
Environment configuration for Expense Tracker MCP Server.
Supports local and remote deployment.

Set environment variables:
  - MCP_TRANSPORT: "stdio" (default, Claude Desktop), "sse" (server), "http" (custom)
  - MCP_HOST: "localhost" (default) or remote IP
  - MCP_PORT: 5000 (default for remote)
  - MCP_ENV: "local" (default) or "production"
"""

import os
from typing import Literal

# ============================================
# CONFIGURATION
# ============================================

# Deployment environment
ENVIRONMENT = os.getenv("MCP_ENV", "local")  # "local" or "production"

# MCP Transport Configuration
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")  # "stdio", "sse", or "http"
MCP_HOST = os.getenv("MCP_HOST", "localhost")
MCP_PORT = int(os.getenv("MCP_PORT", "5000"))

# Database Configuration
DB_ENABLE_WAL = os.getenv("DB_ENABLE_WAL", "true").lower() == "true"

# Logging
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Allowed Origins (for remote CORS)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# ============================================
# CONFIGURATION DISPLAY
# ============================================

def print_config():
    """Print current configuration."""
    if ENABLE_LOGGING:
        print("\n" + "=" * 60)
        print("EXPENSE TRACKER MCP SERVER CONFIGURATION")
        print("=" * 60)
        print(f"Environment:       {ENVIRONMENT}")
        print(f"Transport:         {MCP_TRANSPORT}")
        print(f"Host:              {MCP_HOST}")
        print(f"Port:              {MCP_PORT}")
        print(f"Database WAL:      {DB_ENABLE_WAL}")
        print(f"Logging Enabled:   {ENABLE_LOGGING}")
        print(f"Allowed Origins:   {', '.join(ALLOWED_ORIGINS)}")
        print("=" * 60)
        print(f"Deployment Mode:   {'LOCAL (Claude Desktop)' if ENVIRONMENT == 'local' else 'REMOTE (Production)'}")
        print("=" * 60 + "\n")

# ============================================
# TRANSPORT CONFIGURATION GUIDE
# ============================================

def get_deployment_info():
    """Get deployment information based on transport type."""
    info = {
        "stdio": {
            "use_case": "Claude Desktop (local)",
            "command": "Already configured in claude_desktop_config.json",
            "requires_host_port": False
        },
        "sse": {
            "use_case": "Server-Sent Events (cloud)",
            "command": "Deploy to cloud server, access via HTTP",
            "requires_host_port": True,
            "example": "https://your-server.com:port"
        },
        "http": {
            "use_case": "Custom HTTP (enterprise)",
            "command": "Deploy with FastAPI wrapper",
            "requires_host_port": True,
            "example": "http://your-server.com:port"
        }
    }
    return info.get(MCP_TRANSPORT, info["stdio"])

# Print config on startup
if __name__ != "__main__":
    print_config()
