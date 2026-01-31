# 🧾 Expense Tracker MCP Server

A **multi-user, async, MCP-compatible Expense Tracker** built with **FastMCP + SQLite**.
Designed for **AI agents**, **Claude**, and **MCP-based tools** to manage personal finance data such as **expenses, savings, budgets, and saving goals**.

---

## 🚀 Features

### ✅ Expenses

* Add, list, update, delete expenses
* Date-range filtering
* Category-wise summaries
* Automatic category & subcategory normalization

### ✅ Savings

* Track savings entries
* Validate saving sources
* Date-based filtering

### ✅ Saving Goals

* Create & manage saving goals
* Track progress
* Get insights (monthly pace, remaining amount, on-track / behind)

### ✅ Budgets

* Set monthly budgets per category
* Check budget status per month
* Over/under budget insights

### ✅ Multi-User Support

* Each user has an isolated database
* Automatic DB creation per user
* Session-based `current_user` support

### ✅ MCP Native

* Fully compatible with **FastMCP**
* Works with **Claude Desktop**, **local MCP clients**, and **AI agents**
* Supports `tools` + `resources`

---

## 🏗 Project Structure

```
expense-tracker-mcp-server/
│
├── data/
│   ├── default_user/
│   │   └── expenses.db
│   └── <other_users>/
│       └── expenses.db
│
├── prompts/
│   ├── financial_assistant.txt
│   ├── budget_coach.txt
│   └── savings_advisor.txt
│
├── resources/
│   ├── categories.json
│   ├── saving_sources.json
│   └── budget_rules.json
│
├── main.py
├── requirements.txt
├── pyproject.toml
├── README.md
└── uv.lock
```

---

## ⚙️ Tech Stack

* **Python 3.10+**
* **FastMCP**
* **SQLite (aiosqlite)**
* **AsyncIO**
* **JSON-based resources**

---

## 📦 Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/DevDoshi19/expense-tracker-mcp-server.git
cd expense-tracker-mcp-server
```

### 2️⃣ Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / Mac
.venv\Scripts\activate      # Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the MCP Server

### Using FastMCP (recommended)

```bash
uv run fastmcp run main.py
```

Or:

```bash
python main.py
```

---

## 🔌 MCP Configuration Example (Claude Desktop)

```json
{
  "mcpServers": {
    "Expense Tracker": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "path/to/main.py"
      ],
      "transport": "stdio"
    }
  }
}
```

---

## 👤 Multi-User Usage

### Initialize a user

```json
{
  "tool": "initialize_user",
  "arguments": {
    "user_id": "dev_doshi"
  }
}
```

### Set current user

```json
{
  "tool": "set_current_user",
  "arguments": {
    "user_id": "dev_doshi"
  }
}
```

All subsequent actions will run under that user.

---

## 🧠 Data Storage Design

* Each user has **their own SQLite database**
* Stored under:

  ```
  data/<user_id>/expenses.db
  ```
* Ideal for:

  * Local use
  * MCP demos
  * Small-to-medium scale deployments

> ⚠️ For large-scale production, migrate to PostgreSQL or a managed DB.

---

## 📚 MCP Resources

Available MCP resources:

* `expense://categories`
* `expense://saving-sources`
* `expense://budget-rules`
* `prompt://financial-assistant`
* `prompt://budget-coach`
* `prompt://savings-advisor`
* `system://info`

---

## 🔒 Security Notes

* Current version uses session-based `user_id`
* No authentication layer yet
* Intended for **trusted MCP environments**
* Add OAuth / JWT for public deployment

---

## 🛣 Roadmap

* [ ] PostgreSQL support
* [ ] Auth integration
* [ ] User-level quotas
* [ ] Cloud deployment guide
* [ ] Analytics & charts
* [ ] Backup & retention policies

---

## 👨‍💻 Author

**Dev**
MCP • Agentic AI • Systems Engineering

---

## ⭐ Support

If this project helped you:

* ⭐ Star the repo
* 🧠 Share with MCP builders
* 🛠 Fork & extend
