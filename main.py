import json
import os
from typing import Optional, Dict, List, Any
from datetime import datetime
import aiosqlite
import asyncio
from fastmcp import FastMCP
from contextlib import asynccontextmanager

# Base directories
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Resource paths
CATEGORIES_PATH = os.path.join(BASE_DIR, "resources/categories.json")
BUDGET_RULES_PATH = os.path.join(BASE_DIR, "resources/budget_rules.json")
SAVING_SOURCES_PATH = os.path.join(BASE_DIR, "resources/saving_sources.json")
FINANCIAL_ASSISTANT_PROMPT = os.path.join(BASE_DIR, "prompts/financial_assistant.txt")
BUDGET_COACH_PROMPT = os.path.join(BASE_DIR, "prompts/budget_coach.txt")
SAVINGS_ADVISOR_PROMPT = os.path.join(BASE_DIR, "prompts/savings_advisor.txt")

# Initialize FastMCP
mcp = FastMCP(name="Expense Tracker")

# Global user context (set by authentication middleware)
CURRENT_USER_ID = "default_user"


def get_user_db_path(user_id: str) -> str:
    """Get the database path for a specific user."""
    user_dir = os.path.join(DATA_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "expenses.db")


@asynccontextmanager
async def get_db_connection(user_id: str):
    """Async context manager for database connections."""
    db_path = get_user_db_path(user_id)
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    try:
        yield conn
        await conn.commit()
    except Exception as e:
        await conn.rollback()
        raise e
    finally:
        await conn.close()

def load_json(path: str) -> Dict:
    """Load JSON file synchronously."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_user_id(user_id: Optional[str]) -> str:
    """Resolve user ID with fallback to current user."""
    if not user_id:
        return CURRENT_USER_ID
    return user_id


# ============================================
# DATABASE INITIALIZATION
# ============================================

async def init_db(user_id: str):
    """Initialize database tables for a user."""
    db_path = get_user_db_path(user_id)
    
    async with aiosqlite.connect(db_path) as conn:
        # Enable WAL mode for better concurrency
        await conn.execute("PRAGMA journal_mode=WAL")
        
        # Create expenses table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        
        # Create savings table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS savings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                source TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        
        # Create saving_goals table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS saving_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                note TEXT DEFAULT ''
            )
        """)
        
        # Create budgets table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL UNIQUE,
                monthly_limit REAL NOT NULL
            )
        """)
        
        await conn.commit()

# ============================================
# VALIDATION FUNCTIONS
# ============================================

async def validate_category(category: str, subcategory: Optional[str] = None) -> tuple[str, str]:
    """Validate category and subcategory.

    Always returns a valid (category, subcategory) pair by normalizing unknown
    inputs to safe defaults. This prevents client-side errors when users pass
    unexpected values.
    """
    categories = load_json(CATEGORIES_PATH)
    normalized_category = (category or "").strip().lower()
    normalized_subcategory = (subcategory or "").strip().lower()

    if normalized_category not in categories:
        normalized_category = "misc"

    available_subcategories = categories[normalized_category]

    if not normalized_subcategory:
        if "other" in available_subcategories:
            normalized_subcategory = "other"
        else:
            normalized_subcategory = available_subcategories[0]
    elif normalized_subcategory not in available_subcategories:
        if "other" in available_subcategories:
            normalized_subcategory = "other"
        else:
            normalized_subcategory = available_subcategories[0]

    return normalized_category, normalized_subcategory


async def validate_saving_source(source: str) -> str:
    """Normalize saving source to safe defaults."""
    sources = load_json(SAVING_SOURCES_PATH)
    normalized_source = (source or "").strip().lower()

    if not normalized_source:
        return "other" if "other" in sources else sources[0]

    if normalized_source not in sources:
        return "other" if "other" in sources else sources[0]

    return normalized_source


def months_between(start_date: str, end_date: str) -> int:
    """Calculate full months between two YYYY-MM-DD dates."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return (end.year - start.year) * 12 + (end.month - start.month)


# ============================================
# SYSTEM INFO RESOURCE
# ============================================

@mcp.resource("system://info")
async def system_info() -> str:
    """System information and capabilities."""
    info = {
        "name": "Expense Tracker MCP Server",
        "version": "2.0.0",
        "status": "production",
        "description": "Personal finance tracking server with expenses, savings, budgets, and goal insights",
        "capabilities": {
            "expenses": ["add", "list", "update", "delete", "summaries"],
            "savings": ["add", "list", "delete"],
            "goals": ["add", "progress", "insights", "list", "update", "delete"],
            "budgets": ["set", "check", "list", "update", "delete"],
            "resources": ["categories", "saving-sources", "budget-rules", "prompts"]
        },
        "constraints": {
            "date_format": "YYYY-MM-DD",
            "currency": "user-defined",
            "timezone": "local server time",
            "negative_amounts": "not allowed"
        },
        "best_practices": [
            "Always resolve IDs via list tools",
            "Never assume missing data",
            "Use insights tools before coaching",
            "Validate categories before adding expenses"
        ],
        "contact": {
            "maintainer": "Dev",
            "project_type": "MCP Remote Server"
        }
    }
    return json.dumps(info, indent=2)


# ============================================
# EXPENSE TOOLS
# ============================================

@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = "",
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new expense to the database."""
    user_id = resolve_user_id(user_id)
    
    if amount <= 0:
        raise ValueError("amount must be positive")
    
    category, subcategory = await validate_category(category, subcategory)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("""
            INSERT INTO expenses(date, amount, category, subcategory, note)
            VALUES(?, ?, ?, ?, ?)
        """, (date, amount, category, subcategory, note))
        
        expense_id = cursor.lastrowid
    
    return {
        "status": "ok",
        "id": expense_id,
        "category": category,
        "subcategory": subcategory,
        "message": "Expense added successfully"
    }

@mcp.tool()
async def list_expenses(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all expenses in the database."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute(
            "SELECT id, date, amount, category, subcategory, note FROM expenses ORDER BY date DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@mcp.tool()
async def list_expenses_by_date(
    start_date: str,
    end_date: str,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List expenses within a specific date range."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("""
            SELECT id, date, amount, category, subcategory, note 
            FROM expenses 
            WHERE date BETWEEN ? AND ? 
            ORDER BY date DESC
        """, (start_date, end_date))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@mcp.tool()
async def expense_summary_by_category(
    start_date: str,
    end_date: str,
    category: Optional[str] = None,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get a summary of expenses grouped by category."""
    user_id = resolve_user_id(user_id)
    
    if start_date > end_date:
        raise ValueError("start_date must be before end_date")
    
    await init_db(user_id)
    
    query = """
        SELECT category, SUM(amount) as total_amount, COUNT(*) as count
        FROM expenses
        WHERE date BETWEEN ? AND ?
    """
    parameters = [start_date, end_date]
    
    if category:
        query += " AND category = ?"
        parameters.append(category.lower())
    
    query += " GROUP BY category ORDER BY total_amount DESC"
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute(query, parameters)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@mcp.tool()
async def update_expense(
    expense_id: int,
    date: Optional[str] = None,
    amount: Optional[float] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    note: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing expense entry."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    updates = []
    values = []
    
    if date is not None:
        updates.append("date = ?")
        values.append(date)
    if amount is not None:
        if amount <= 0:
            raise ValueError("amount must be positive")
        updates.append("amount = ?")
        values.append(amount)
    if category is not None:
        category, normalized_subcategory = await validate_category(category, subcategory)
        updates.append("category = ?")
        values.append(category)
        if subcategory is None:
            updates.append("subcategory = ?")
            values.append(normalized_subcategory)
        else:
            updates.append("subcategory = ?")
            values.append(normalized_subcategory)
    elif subcategory is not None:
        async with get_db_connection(user_id) as conn:
            cursor = await conn.execute("SELECT category FROM expenses WHERE id = ?", (expense_id,))
            row = await cursor.fetchone()
            if not row:
                return {"status": "not_found", "id": expense_id, "message": "Expense not found"}
            current_category = row["category"]

        current_category, normalized_subcategory = await validate_category(current_category, subcategory)
        updates.append("subcategory = ?")
        values.append(normalized_subcategory)
    if note is not None:
        updates.append("note = ?")
        values.append(note)
    
    if not updates:
        return {"status": "no_changes", "id": expense_id, "message": "No fields to update"}
    
    values.append(expense_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute(
            f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?",
            values
        )
        
        if cursor.rowcount == 0:
            return {"status": "not_found", "id": expense_id, "message": "Expense not found"}
    
    return {"status": "ok", "id": expense_id, "message": "Expense updated successfully"}


@mcp.tool()
async def delete_expense(expense_id: int, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Delete an expense by ID."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        
        if cursor.rowcount == 0:
            return {"status": "not_found", "message": "Expense not found"}
    
    return {"status": "ok", "deleted_rows": cursor.rowcount, "message": "Expense deleted successfully"}


# ============================================
# SAVING TOOLS
# ============================================

@mcp.tool()
async def add_saving(
    date: str,
    amount: float,
    source: str = "",
    note: str = "",
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new saving entry to the database."""
    user_id = resolve_user_id(user_id)
    
    if amount <= 0:
        raise ValueError("amount must be positive")
    
    source = await validate_saving_source(source)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("""
            INSERT INTO savings(date, amount, source, note)
            VALUES(?, ?, ?, ?)
        """, (date, amount, source, note))
        
        saving_id = cursor.lastrowid
    
    return {"status": "ok", "id": saving_id, "message": "Saving added successfully"}


@mcp.tool()
async def list_savings(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List savings entries, optionally filtered by date range."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    query = "SELECT id, date, amount, source, note FROM savings WHERE 1=1"
    params = []
    
    if start_date and end_date:
        query += " AND date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    
    query += " ORDER BY date DESC"
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@mcp.tool()
async def delete_saving(saving_id: int, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Delete a saving entry by ID."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("DELETE FROM savings WHERE id = ?", (saving_id,))
        
        if cursor.rowcount == 0:
            return {"status": "not_found", "message": "Saving not found"}
    
    return {"status": "ok", "deleted_rows": cursor.rowcount, "message": "Saving deleted successfully"}


# ============================================
# SAVING GOAL TOOLS
# ============================================

@mcp.tool()
async def add_saving_goal(
    name: str,
    target_amount: float,
    start_date: str,
    end_date: Optional[str] = None,
    note: str = "",
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new saving goal to the database."""
    user_id = resolve_user_id(user_id)
    
    if target_amount <= 0:
        raise ValueError("target_amount must be positive")
    
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("""
            INSERT INTO saving_goals(name, target_amount, start_date, end_date, note)
            VALUES(?, ?, ?, ?, ?)
        """, (name, target_amount, start_date, end_date, note))
        
        goal_id = cursor.lastrowid
    
    return {"status": "ok", "id": goal_id, "message": "Saving goal added successfully"}


@mcp.tool()
async def list_saving_goals(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all saving goals."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("""
            SELECT id, name, target_amount, start_date, end_date, note
            FROM saving_goals
            ORDER BY start_date DESC
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@mcp.tool()
async def get_saving_goal_progress(
    goal_id: int,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get the progress of a saving goal."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("""
            SELECT id, name, target_amount, start_date, end_date
            FROM saving_goals
            WHERE id = ?
        """, (goal_id,))
        
        goal = await cursor.fetchone()
        if not goal:
            return {"status": "not_found", "message": "Goal not found"}
        
        goal_dict = dict(goal)
        
        cursor = await conn.execute("""
            SELECT SUM(amount) FROM savings
            WHERE date >= ? AND (date <= ? OR ? IS NULL)
        """, (goal_dict['start_date'], goal_dict['end_date'], goal_dict['end_date']))
        
        result = await cursor.fetchone()
        total_saved = result[0] if result[0] is not None else 0.0
    
    progress_pct = (total_saved / goal_dict['target_amount']) * 100 if goal_dict['target_amount'] > 0 else 0
    
    return {
        "status": "ok",
        "goal_id": goal_dict['id'],
        "name": goal_dict['name'],
        "target_amount": goal_dict['target_amount'],
        "total_saved": total_saved,
        "remaining": max(goal_dict['target_amount'] - total_saved, 0),
        "progress_percentage": round(progress_pct, 2)
    }


@mcp.tool()
async def get_saving_goal_insights(
    goal_id: int,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get detailed insights for a saving goal."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    today = datetime.today().strftime("%Y-%m-%d")
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("""
            SELECT name, target_amount, start_date, end_date
            FROM saving_goals
            WHERE id = ?
        """, (goal_id,))
        
        goal = await cursor.fetchone()
        if not goal:
            return {"status": "not_found", "message": "Goal not found"}
        
        goal_dict = dict(goal)
        
        if not goal_dict['end_date']:
            return {"status": "no_deadline", "message": "Goal has no end date"}
        
        cursor = await conn.execute("""
            SELECT SUM(amount) FROM savings
            WHERE date >= ? AND date <= ?
        """, (goal_dict['start_date'], today))
        
        result = await cursor.fetchone()
        total_saved = result[0] if result[0] is not None else 0.0
    
    months_total = max(months_between(goal_dict['start_date'], goal_dict['end_date']), 1)
    months_elapsed = max(months_between(goal_dict['start_date'], today), 0)
    months_remaining = max(months_total - months_elapsed, 0)
    
    remaining_amount = max(goal_dict['target_amount'] - total_saved, 0)
    
    required_monthly = remaining_amount / months_remaining if months_remaining > 0 else 0
    current_monthly_avg = total_saved / months_elapsed if months_elapsed > 0 else total_saved
    
    if months_remaining == 0 and remaining_amount > 0:
        status = "missed_goal"
    elif current_monthly_avg >= required_monthly:
        status = "on_track"
    else:
        status = "behind"
    
    return {
        "status": "ok",
        "goal": goal_dict['name'],
        "target_amount": goal_dict['target_amount'],
        "total_saved": total_saved,
        "months_total": months_total,
        "months_elapsed": months_elapsed,
        "months_remaining": months_remaining,
        "required_monthly_saving": round(required_monthly, 2),
        "current_monthly_average": round(current_monthly_avg, 2),
        "pace_status": status
    }


@mcp.tool()
async def update_saving_goal(
    goal_id: int,
    name: Optional[str] = None,
    target_amount: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    note: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing saving goal."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    updates = []
    values = []
    
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if target_amount is not None:
        if target_amount <= 0:
            raise ValueError("target_amount must be positive")
        updates.append("target_amount = ?")
        values.append(target_amount)
    if start_date is not None:
        updates.append("start_date = ?")
        values.append(start_date)
    if end_date is not None:
        updates.append("end_date = ?")
        values.append(end_date)
    if note is not None:
        updates.append("note = ?")
        values.append(note)
    
    if not updates:
        return {"status": "no_changes", "id": goal_id, "message": "No fields to update"}
    
    values.append(goal_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute(
            f"UPDATE saving_goals SET {', '.join(updates)} WHERE id = ?",
            values
        )
        
        if cursor.rowcount == 0:
            return {"status": "not_found", "id": goal_id, "message": "Goal not found"}
    
    return {"status": "ok", "id": goal_id, "message": "Goal updated successfully"}


@mcp.tool()
async def delete_saving_goal(goal_id: int, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Delete a saving goal by ID."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("DELETE FROM saving_goals WHERE id = ?", (goal_id,))
        
        if cursor.rowcount == 0:
            return {"status": "not_found", "message": "Goal not found"}
    
    return {"status": "ok", "deleted_goal_id": goal_id, "message": "Goal deleted successfully"}


# ============================================
# BUDGET TOOLS
# ============================================

@mcp.tool()
async def set_budget(
    category: str,
    monthly_limit: float,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Set a budget for a specific category."""
    user_id = resolve_user_id(user_id)
    
    if monthly_limit <= 0:
        raise ValueError("monthly_limit must be positive")
    
    category, _ = await validate_category(category)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        await conn.execute("""
            INSERT INTO budgets(category, monthly_limit)
            VALUES(?, ?)
            ON CONFLICT(category) DO UPDATE SET monthly_limit=excluded.monthly_limit
        """, (category, monthly_limit))
    
    return {
        "status": "ok",
        "category": category,
        "monthly_limit": monthly_limit,
        "message": "Budget set successfully"
    }


@mcp.tool()
async def list_budgets(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all budgets."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("""
            SELECT category, monthly_limit
            FROM budgets
            ORDER BY category ASC
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@mcp.tool()
async def check_budget_status(
    category: str,
    year: int,
    month: int,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Check the budget status for a specific category and month."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute(
            "SELECT monthly_limit FROM budgets WHERE category = ?",
            (category.lower(),)
        )
        budget = await cursor.fetchone()
        
        if not budget:
            return {"status": "no_budget", "message": "No budget set for this category"}
        
        budget_dict = dict(budget)
        
        cursor = await conn.execute("""
            SELECT SUM(amount) FROM expenses
            WHERE category = ? AND date >= ? AND date < ?
        """, (category.lower(), start_date, end_date))
        
        result = await cursor.fetchone()
        total_expenses = result[0] if result[0] is not None else 0.0
    
    remaining = budget_dict['monthly_limit'] - total_expenses
    status = "over_budget" if total_expenses > budget_dict['monthly_limit'] else "under_budget"
    
    return {
        "status": "ok",
        "category": category.lower(),
        "year": year,
        "month": month,
        "monthly_limit": budget_dict['monthly_limit'],
        "total_expenses": total_expenses,
        "remaining_budget": remaining,
        "budget_status": status,
        "usage_percentage": round((total_expenses / budget_dict['monthly_limit']) * 100, 2)
    }


@mcp.tool()
async def update_budget(
    category: str,
    monthly_limit: float,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Update the budget for a specific category."""
    user_id = resolve_user_id(user_id)
    
    if monthly_limit <= 0:
        raise ValueError("monthly_limit must be positive")
    
    category, _ = await validate_category(category)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("""
            UPDATE budgets
            SET monthly_limit = ?
            WHERE category = ?
        """, (monthly_limit, category))
        
        if cursor.rowcount == 0:
            return {"status": "not_found", "message": "Budget not found for this category"}
    
    return {
        "status": "ok",
        "category": category,
        "monthly_limit": monthly_limit,
        "message": "Budget updated successfully"
    }


@mcp.tool()
async def delete_budget(category: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Delete a budget for a category."""
    user_id = resolve_user_id(user_id)
    await init_db(user_id)
    
    async with get_db_connection(user_id) as conn:
        cursor = await conn.execute("DELETE FROM budgets WHERE category = ?", (category.lower(),))
        
        if cursor.rowcount == 0:
            return {"status": "not_found", "message": "Budget not found"}
    
    return {
        "status": "ok",
        "deleted_rows": cursor.rowcount,
        "message": "Budget deleted successfully"
    }


# ============================================
# RESOURCES
# ============================================

@mcp.resource("expense://categories")
async def categories() -> str:
    """Valid categories and subcategories for expenses."""
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()


@mcp.resource("expense://saving-sources")
async def saving_sources() -> str:
    """Valid sources for savings entries."""
    with open(SAVING_SOURCES_PATH, "r", encoding="utf-8") as f:
        return f.read()


@mcp.resource("expense://budget-rules")
async def budget_rules() -> str:
    """Rules and assumptions used for budgets."""
    with open(BUDGET_RULES_PATH, "r", encoding="utf-8") as f:
        return f.read()


@mcp.resource("prompt://financial-assistant")
async def financial_assistant_prompt() -> str:
    """Financial assistant prompt for LLM guidance."""
    with open(FINANCIAL_ASSISTANT_PROMPT, "r", encoding="utf-8") as f:
        return f.read()


@mcp.resource("prompt://budget-coach")
async def budget_coach_prompt() -> str:
    """Budget coach prompt for LLM guidance."""
    with open(BUDGET_COACH_PROMPT, "r", encoding="utf-8") as f:
        return f.read()


@mcp.resource("prompt://savings-advisor")
async def savings_advisor_prompt() -> str:
    """Savings advisor prompt for LLM guidance."""
    with open(SAVINGS_ADVISOR_PROMPT, "r", encoding="utf-8") as f:
        return f.read()


# ============================================
# AUTHENTICATION & USER MANAGEMENT
# ============================================

# Initialize database for a new user

@mcp.tool()
async def initialize_user(user_id: str) -> Dict[str, Any]:
    """Initialize database for a new user. Call this when a new user signs up."""
    await init_db(user_id)
    return {
        "status": "ok",
        "user_id": user_id,
        "message": f"Database initialized for user {user_id}",
        "db_path": get_user_db_path(user_id)
    }


@mcp.tool()
async def set_current_user(user_id: str) -> Dict[str, Any]:
    """Set the current active user for this session."""
    global CURRENT_USER_ID
    CURRENT_USER_ID = user_id
    await init_db(user_id)
    return {
        "status": "ok",
        "current_user": CURRENT_USER_ID,
        "message": f"Current user set to {user_id}"
    }


@mcp.tool()
async def get_current_user() -> Dict[str, Any]:
    """Get the current active user ID."""
    return {
        "status": "ok",
        "current_user": CURRENT_USER_ID
    }


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    mcp.run()
