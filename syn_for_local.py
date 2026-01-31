import json
from typing import Optional
from fastmcp import FastMCP
import os
import asyncio
import aiosqlite  # Changed: sqlite3 → aiosqlite
import tempfile
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__),"database/expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__),"resources/categories.json")
BUDGET_RULES_PATH = os.path.join(os.path.dirname(__file__), "resources/budget_rules.json")
SAVING_SOURCES_PATH = os.path.join(os.path.dirname(__file__), "resources/saving_sources.json")
FINANCIAL_ASSISTANT_PROMPT = os.path.join(os.path.dirname(__file__), "prompts/financial_assistant.txt")
BUDGET_COACH_PROMPT = os.path.join(os.path.dirname(__file__), "prompts/budget_coach.txt")
SAVINGS_ADVISOR_PROMPT = os.path.join(os.path.dirname(__file__), "prompts/savings_advisor.txt")

mcp = FastMCP(name="Expense Tracker")

async def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

#------------------------------------------- Initialize database and tables ------------------------------

async def init_db():
    with sqlite3.connect(DB_PATH) as c :
        
        # Create expenses table

        c.execute("""CREATE TABLE IF NOT EXISTS expenses(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT NOT NULL,
                  amount REAL NOT NULL,
                  category TEXT NOT NULL,
                  subcategory TEXT DEFAULT '',
                  note TEXT DEFAULT ''
                )
            """)
        
        # Create savings table

        c.execute("""
            CREATE TABLE IF NOT EXISTS savings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                source TEXT DEFAULT '',
                note TEXT DEFAULT ''
                )
        """)

        # Create saving_goals table

        c.execute("""
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

        c.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE,
            monthly_limit REAL NOT NULL
            )
        """)

asyncio.run(init_db())  # database initialization

#-------------------------------------------- validation functions -------------------------------------------

def validate_category(category: str, subcategory: Optional[str] = None):
    categories = load_json(CATEGORIES_PATH)
    category = category.lower()
    subcategory = subcategory.lower() if subcategory else "other"

    if category not in categories:
        raise ValueError(f"Invalid category: {category}")

    if subcategory and subcategory not in categories[category]:
        raise ValueError(
            f"Invalid subcategory '{subcategory}' for category '{category}'"
        )

def validate_saving_source(source: str) -> str:
    sources = load_json(SAVING_SOURCES_PATH)
    normalized_source = (source or "").strip().lower()

    if not normalized_source:
        return "other" if "other" in sources else sources[0]

    if normalized_source not in sources:
        return "other" if "other" in sources else sources[0]

    return normalized_source

def months_between(start_date: str, end_date: str) -> int:
    """
    Calculate full months between two YYYY-MM-DD dates.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return (end.year - start.year) * 12 + (end.month - start.month)

# -------------------------------------------- system info -------------------------------------------

@mcp.resource("system://info", mime_type="application/json")
def system_info():
    return json.dumps({
        "name": "Expense Tracker MCP Server",
        "version": "1.0.0",
        "status": "stable",
        "description": "Personal finance tracking server with expenses, savings, budgets, and goal insights",

        "capabilities": {
            "expenses": ["add", "list", "update", "delete", "summaries"],
            "savings": ["add", "list"],
            "goals": ["add", "progress", "insights"],
            "budgets": ["set", "check"],
            "resources": [
                "categories",
                "saving-sources",
                "budget-rules",
                "prompts"
            ]
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
            "Use insights tools before coaching"
        ],

        "contact": {
            "maintainer": "Dev",
            "project_type": "MCP Remote Server"
        }
    })


#-------------------------------------------- expense tools ------------------------------------------- 

@mcp.tool
def add_expense(date, amount:float, category:str, subcategory:str="", note:str="")-> dict:
    """Add a new expense to the database."""
    if amount <= 0:
        raise ValueError("amount must be positive")

    validate_category(category, subcategory)

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("""
            INSERT INTO expenses(date, amount, category, subcategory, note)
            VALUES(?,?,?,?,?)
        """, (date, amount, category, subcategory, note))
    return {"status":"ok","id": cur.lastrowid}

@mcp.tool
def list_expenses():
    """
    List all expenses in the database. Returns a list of dictionaries representing each expense.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("SELECT id,date,amount,category,subcategory,note FROM expenses ORDER BY date ASC")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    
@mcp.tool
def list_expenses_by_date(start_date:str, end_date:str):
    """
    List expenses within a specific date range.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("""
            SELECT id,date,amount,category,subcategory,note 
            FROM expenses 
            WHERE date BETWEEN ? AND ? 
            ORDER BY date ASC
        """, (start_date, end_date))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


@mcp.tool
def expense_summary_by_category(start_date, end_date,category:Optional[str]=None)-> list:
    """
    Get a summary of expenses grouped by category.
    """
    if start_date > end_date:
        raise ValueError("start_date must be before end_date")
    query = """
        SELECT category, SUM(amount) as total_amount
        FROM expenses
        WHERE date BETWEEN ? AND ?
    """
    parameters = [start_date, end_date]
    if category:
        query += " AND category = ?"
        parameters.append(category)
    
    query += " GROUP BY category ORDER BY total_amount ASC"

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(query, parameters)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

@mcp.tool
def update_expense(
    expense_id: int,
    date: Optional[str] = None,
    amount: Optional[float] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    note: Optional[str] = None
) -> dict:
    """
    Update an existing expense entry.
    """
    updates = []
    values = []

    if date is not None:
        updates.append("date = ?")
        values.append(date)
    if amount is not None:
        updates.append("amount = ?")
        values.append(amount)
    if category is not None:
        updates.append("category = ?")
        values.append(category)
    if subcategory is not None:
        updates.append("subcategory = ?")
        values.append(subcategory)
    if note is not None:
        updates.append("note = ?")
        values.append(note)

    if not updates:
        return {"status": "no fields to update", "id": expense_id}

    values.append(expense_id)

    with sqlite3.connect(DB_PATH) as c:
        c.execute(
            f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?",
            values
        )

    return {"status": "ok", "id": expense_id}

@mcp.tool
def delete_expense(expense_id: int) -> dict:
    """
    Delete an expense by ID.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )
        return {
            "status": "ok",
            "deleted_rows": cur.rowcount
        }

#-------------------------------------------- saving tools ------------------------------------------- 

@mcp.tool
def add_saving(date: str, amount: float, source: str = "", note: str = "") -> dict :
    """Add a new saving entry to the database."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    
    source = validate_saving_source(source)

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("""
            INSERT INTO savings(date, amount, source, note)
            VALUES(?,?,?,?)
        """, (date, amount, source, note))

    return {"status": "ok", "id": cur.lastrowid}

@mcp.tool
def list_savings(start_date: Optional[str] = None, end_date: Optional[str] = None) -> list:
    """
    List savings entries, optionally filtered by date range.
    """
    query = "SELECT id, date, amount, source, note FROM savings WHERE 1=1"
    params = []

    if start_date and end_date:
        query += " AND date BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    query += " ORDER BY date ASC"

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    
@mcp.tool
def delete_saving(saving_id: int) -> dict:
    """
    Delete a saving entry by ID.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "DELETE FROM savings WHERE id = ?",
            (saving_id,)
        )
        return {
            "status": "ok" if cur.rowcount else "not_found",
            "deleted_rows": cur.rowcount
        }


#-------------------------------------------- saving goal tools -------------------------------------------

@mcp.tool
def add_saving_goal(name: str, target_amount: float, start_date: str, end_date: Optional[str] = None) -> dict:
    """Add a new saving goal to the database."""
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("""
            INSERT INTO saving_goals(name, target_amount, start_date, end_date)
            VALUES(?,?,?,?)
        """, (name, target_amount, start_date, end_date))
    return {"status": "ok", "id": cur.lastrowid}

@mcp.tool
def get_saving_goal_progress(goal_id: int) -> dict:
    """Get the progress of a saving goal."""
    with sqlite3.connect(DB_PATH) as c:
        goal_cur = c.execute("""
            SELECT id, name, target_amount, start_date, end_date
            FROM saving_goals
            WHERE id = ?
        """, (goal_id,))
        
        goal = goal_cur.fetchone()
        if not goal:
            return {"status": "Goal not found"}

        total_saved_cur = c.execute("""
            SELECT SUM(amount) FROM savings
            WHERE date >= ? AND (date <= ? OR ? IS NULL)
        """, (goal[3], goal[4], goal[4]))
        total_saved = total_saved_cur.fetchone()[0] or 0.0

    return {
        "goal_id": goal[0],
        "name": goal[1],
        "target_amount": goal[2],
        "total_saved": total_saved,
        "progress_percentage": (total_saved / goal[2]) * 100 if goal[2] > 0 else 0
    }

@mcp.tool
def get_saving_goal_insights(goal_id: int) -> dict:
    """
    Get detailed insights for a saving goal:
    - time remaining
    - required monthly saving
    - pace status (ahead / on_track / behind)
    """
    today = datetime.today().strftime("%Y-%m-%d")

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("""
            SELECT name, target_amount, start_date, end_date
            FROM saving_goals
            WHERE id = ?
        """, (goal_id,))
        goal = cur.fetchone()

        if not goal:
            return {"status": "Goal not found"}

        name, target_amount, start_date, end_date = goal

        if not end_date:
            return {"status": "Goal has no end date"}

        cur = c.execute("""
            SELECT SUM(amount) FROM savings
            WHERE date >= ? AND date <= ?
        """, (start_date, today))
        total_saved = cur.fetchone()[0] or 0.0

    months_total = max(months_between(start_date, end_date), 1)
    months_elapsed = max(months_between(start_date, today), 0)
    months_remaining = max(months_total - months_elapsed, 0)

    remaining_amount = max(target_amount - total_saved, 0)

    required_monthly = (
        remaining_amount / months_remaining
        if months_remaining > 0
        else 0
    )

    current_monthly_avg = (
        total_saved / months_elapsed
        if months_elapsed > 0
        else total_saved
    )

    if months_remaining == 0 and remaining_amount > 0:
        status = "missed_goal"
    elif current_monthly_avg >= required_monthly:
        status = "on_track"
    else:
        status = "behind"

    return {
        "goal": name,
        "target_amount": target_amount,
        "total_saved": total_saved,
        "months_total": months_total,
        "months_elapsed": months_elapsed,
        "months_remaining": months_remaining,
        "required_monthly_saving": round(required_monthly, 2),
        "current_monthly_average": round(current_monthly_avg, 2),
        "status": status
    }

@mcp.tool
def list_saving_goals() -> list:
    """
    List all saving goals.
    Used by the LLM to resolve goal IDs.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("""
            SELECT id, name, target_amount, start_date, end_date, note
            FROM saving_goals
            ORDER BY start_date ASC
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

@mcp.tool
def update_saving_goal(
    goal_id: int,
    name: Optional[str] = None,
    target_amount: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    note: Optional[str] = None
) -> dict:
    """
    Update an existing saving goal.
    """
    updates = []
    values = []

    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if target_amount is not None:
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
        return {"status": "no fields to update", "id": goal_id}

    values.append(goal_id)

    with sqlite3.connect(DB_PATH) as c:
        c.execute(
            f"UPDATE saving_goals SET {', '.join(updates)} WHERE id = ?",
            values
        )

    return {"status": "ok", "id": goal_id}

@mcp.tool
def delete_saving_goal(goal_id: int) -> dict:
    """
    Delete a saving goal by ID.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "DELETE FROM saving_goals WHERE id = ?",
            (goal_id,)
        )

        if cur.rowcount == 0:
            return {"status": "Goal not found"}

        return {
            "status": "ok",
            "deleted_goal_id": goal_id
        }

#-------------------------------------------- budget tools -------------------------------------------

@mcp.tool
def set_budget(category: str, monthly_limit: float) -> dict:
    """Set a budget for a specific category."""
    if monthly_limit <= 0:
        raise ValueError("monthly_limit must be positive")

    validate_category(category)

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("""
            INSERT INTO budgets(category, monthly_limit)
            VALUES(?, ?)
            ON CONFLICT(category) DO UPDATE SET monthly_limit=excluded.monthly_limit
        """, (category, monthly_limit))
    return {"status": "ok", "category": category, "monthly_limit": monthly_limit}

@mcp.tool
def check_budget_status(category: str, year: int, month: int) -> dict:
    """
    Check the budget status for a specific category and month.
    Dates must be in YYYY-MM-DD format.
    """
    start_date = f"{year}-{month:02d}-01"
    end_date = (
        f"{year + 1}-01-01"
        if month == 12
        else f"{year}-{month + 1:02d}-01"
    )

    with sqlite3.connect(DB_PATH) as c:
        budget_cur = c.execute(
            "SELECT monthly_limit FROM budgets WHERE category = ?",
            (category,)
        )
        budget = budget_cur.fetchone()
        if not budget:
            return {"status": "No budget set for this category"}

        expenses_cur = c.execute(
            """
            SELECT SUM(amount) FROM expenses
            WHERE category = ? AND date >= ? AND date < ?
            """,
            (category, start_date, end_date)
        )
        total_expenses = expenses_cur.fetchone()[0] or 0.0

    return {
        "category": category,
        "monthly_limit": budget[0],
        "total_expenses": total_expenses,
        "remaining_budget": budget[0] - total_expenses,
        "status": "over_budget" if total_expenses > budget[0] else "under_budget"
    }

@mcp.tool
def list_budgets() -> list:
    """
    List all budgets.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("""
            SELECT category, monthly_limit
            FROM budgets
            ORDER BY category ASC
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    
@mcp.tool
def update_budget(category: str, monthly_limit: float) -> dict:
    """
    Update the budget for a specific category.
    """
    if monthly_limit <= 0:
        raise ValueError("monthly_limit must be positive")

    validate_category(category)

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("""
            UPDATE budgets
            SET monthly_limit = ?
            WHERE category = ?
        """, (monthly_limit, category))
        if cur.rowcount == 0:
            return {"status": "Budget not found for this category"}

    return {"status": "ok", "category": category, "monthly_limit": monthly_limit}

@mcp.tool
def delete_budget(category: str) -> dict:
    """
    Delete a budget for a category.
    """
    category = category.lower()

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "DELETE FROM budgets WHERE category = ?",
            (category,)
        )
        return {
            "status": "ok" if cur.rowcount else "not_found",
            "deleted_rows": cur.rowcount
        }

#-------------------------------------------- resources -------------------------------------------

@mcp.resource("expense://categories",mime_type="application/json")
def categories():
    # read fresh each time so you can edit the file without restarting 
    with open(CATEGORIES_PATH,"r",encoding="utf-8") as f:
        return f.read()   

@mcp.resource("expense://saving-sources", mime_type="application/json")
def saving_sources():
    """
    Valid sources for savings entries.
    """
    with open(SAVING_SOURCES_PATH, "r", encoding="utf-8") as f:
        return f.read()

@mcp.resource("expense://budget-rules", mime_type="application/json")
def budget_rules():
    """
    Rules and assumptions used for budgets.
    """
    with open(BUDGET_RULES_PATH, "r", encoding="utf-8") as f:
        return f.read()

#-------------------------------------------- prompts -------------------------------------------

@mcp.resource("prompt://financial-assistant", mime_type="text/plain")
def financial_assistant_prompt():
    return open(FINANCIAL_ASSISTANT_PROMPT, "r", encoding="utf-8").read()

@mcp.resource("prompt://budget-coach", mime_type="text/plain")
def budget_coach_prompt():
    return open(BUDGET_COACH_PROMPT, "r", encoding="utf-8").read()

@mcp.resource("prompt://savings-advisor", mime_type="text/plain")
def savings_advisor_prompt():
    return open(SAVINGS_ADVISOR_PROMPT, "r", encoding="utf-8").read()

#-------------------------------------------- run remote server -------------------------------------------

if __name__ == "__main__":
    mcp.run()