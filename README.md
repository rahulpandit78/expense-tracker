# Expense Tracker

![CI](../../actions/workflows/ci.yml/badge.svg)

A simple web app to track daily expenses. Add, edit, delete and filter expenses by category, and see a monthly total with a per-category breakdown.

**Tech stack:** Python, Flask, SQLite, HTML/CSS/JavaScript, pytest, GitHub Actions, Render

## Features

- Add, edit and delete expenses (amount, category, date, note)
- Filter the list by category and month
- Monthly summary: total spend and total per category
- Server-side input validation (positive amount, known category, valid date)
- Automated tests run on every push via GitHub Actions

## How it works

```
Browser (HTML/CSS/JS)  --fetch()-->  Flask REST API (app.py)  --SQL-->  SQLite (expenses.db)
```

The front end is one HTML page. JavaScript calls the API with `fetch()` and redraws the table and summary from the JSON it gets back.

### API

| Method | Route | What it does |
|--------|-------|--------------|
| GET | `/api/expenses?category=Food&month=2026-10` | List expenses (filters optional) |
| POST | `/api/expenses` | Create an expense |
| PUT | `/api/expenses/<id>` | Update an expense |
| DELETE | `/api/expenses/<id>` | Delete an expense |
| GET | `/api/summary?month=2026-10` | Monthly total and per-category totals |
| GET | `/api/categories` | Allowed categories |

Example request body for POST/PUT:

```json
{ "amount": 250, "category": "Food", "date": "2026-10-17", "note": "Lunch" }
```

Invalid input returns `400` with an error message; a missing id returns `404`.

## Run locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                   # open http://127.0.0.1:5000
```

## Run tests

```bash
pytest -v
```

Each test uses its own temporary database, so tests never touch your real data.

## Deploy on Render

1. Push this repo to GitHub.
2. On [render.com](https://render.com), choose **New → Blueprint** and select this repo (it reads `render.yaml`).
   Or choose **New → Web Service** with build command `pip install -r requirements.txt` and start command `gunicorn app:app`.
3. Render gives you a public URL.

Note: on Render's free plan the disk is temporary, so the SQLite data resets when the service restarts. That is fine for a demo; a real deployment would use a hosted database such as PostgreSQL.

## Project structure

```
app.py                  Flask app: routes, validation, database
templates/index.html    The single web page
static/script.js        Front-end logic (fetch calls, table, form)
static/style.css        Styling
tests/test_app.py       pytest unit tests
.github/workflows/ci.yml  GitHub Actions: runs tests on every push
render.yaml             Render deployment config
```
