"""Expense Tracker - a small Flask REST API backed by SQLite.

Routes
------
GET    /                         -> the web page (templates/index.html)
GET    /api/expenses             -> list expenses (optional ?category=Food&month=2026-10)
POST   /api/expenses             -> create an expense
PUT    /api/expenses/<id>        -> update an expense
DELETE /api/expenses/<id>        -> delete an expense
GET    /api/summary?month=YYYY-MM -> monthly total and total per category
GET    /api/categories           -> the allowed categories
"""

import os
import sqlite3
from datetime import date, datetime

from flask import Flask, g, jsonify, render_template, request

CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Health", "Entertainment", "Other"]


def create_app(db_path=None):
    """App factory: lets tests create an app with their own temporary database."""
    app = Flask(__name__)
    app.config["DATABASE"] = db_path or os.environ.get("DATABASE_PATH", "expenses.db")

    # ---------- database helpers ----------
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row  # rows behave like dicts
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        db = sqlite3.connect(app.config["DATABASE"])
        db.execute(
            """CREATE TABLE IF NOT EXISTS expenses (
                   id       INTEGER PRIMARY KEY AUTOINCREMENT,
                   amount   REAL    NOT NULL,
                   category TEXT    NOT NULL,
                   date     TEXT    NOT NULL,   -- stored as YYYY-MM-DD
                   note     TEXT    DEFAULT ''
               )"""
        )
        db.commit()
        db.close()

    init_db()

    # ---------- validation ----------
    def validate(data):
        """Return (clean_data, error_message). Exactly one of them is None."""
        if not isinstance(data, dict):
            return None, "Request body must be JSON"

        try:
            amount = float(data.get("amount"))
        except (TypeError, ValueError):
            return None, "Amount must be a number"
        if amount <= 0:
            return None, "Amount must be greater than 0"

        category = data.get("category")
        if category not in CATEGORIES:
            return None, f"Category must be one of {CATEGORIES}"

        date_str = data.get("date") or date.today().isoformat()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except (TypeError, ValueError):
            return None, "Date must be in YYYY-MM-DD format"

        note = str(data.get("note", "")).strip()
        if len(note) > 200:
            return None, "Note must be at most 200 characters"

        return {"amount": round(amount, 2), "category": category, "date": date_str, "note": note}, None

    def row_to_dict(row):
        return {k: row[k] for k in row.keys()}

    # ---------- routes ----------
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/categories")
    def categories():
        return jsonify(CATEGORIES)

    @app.get("/api/expenses")
    def list_expenses():
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []
        category = request.args.get("category")
        month = request.args.get("month")  # YYYY-MM
        if category:
            query += " AND category = ?"
            params.append(category)
        if month:
            query += " AND substr(date, 1, 7) = ?"
            params.append(month)
        query += " ORDER BY date DESC, id DESC"
        rows = get_db().execute(query, params).fetchall()  # parameterised -> no SQL injection
        return jsonify([row_to_dict(r) for r in rows])

    @app.post("/api/expenses")
    def add_expense():
        clean, error = validate(request.get_json(silent=True))
        if error:
            return jsonify({"error": error}), 400
        db = get_db()
        cur = db.execute(
            "INSERT INTO expenses (amount, category, date, note) VALUES (?, ?, ?, ?)",
            (clean["amount"], clean["category"], clean["date"], clean["note"]),
        )
        db.commit()
        return jsonify({"id": cur.lastrowid, **clean}), 201

    @app.put("/api/expenses/<int:expense_id>")
    def update_expense(expense_id):
        clean, error = validate(request.get_json(silent=True))
        if error:
            return jsonify({"error": error}), 400
        db = get_db()
        cur = db.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, note = ? WHERE id = ?",
            (clean["amount"], clean["category"], clean["date"], clean["note"], expense_id),
        )
        db.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Expense not found"}), 404
        return jsonify({"id": expense_id, **clean})

    @app.delete("/api/expenses/<int:expense_id>")
    def delete_expense(expense_id):
        db = get_db()
        cur = db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        db.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Expense not found"}), 404
        return jsonify({"message": "Deleted"})

    @app.get("/api/summary")
    def summary():
        month = request.args.get("month") or date.today().strftime("%Y-%m")
        rows = get_db().execute(
            """SELECT category, ROUND(SUM(amount), 2) AS total
               FROM expenses WHERE substr(date, 1, 7) = ?
               GROUP BY category ORDER BY total DESC""",
            (month,),
        ).fetchall()
        by_category = {r["category"]: r["total"] for r in rows}
        return jsonify({"month": month, "total": round(sum(by_category.values()), 2), "by_category": by_category})

    return app


# `gunicorn app:app` (used on Render) imports this object
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
