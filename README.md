# Expense Tracker API

A small but complete backend built with **FastAPI**, **SQLAlchemy (SQLite)** and **JWT authentication**.
Each user registers, logs in, and manages their own expenses. Users can never see or change another user's records.

## Project concept

Resource: **Expense** (belongs to the logged-in user)

| Field | Type | Notes |
|---|---|---|
| id | int | primary key |
| title | string | 1-100 chars |
| description | string, optional | up to 1000 chars |
| amount | float | must be > 0 |
| category | enum | food, transport, rent, utilities, shopping, health, entertainment, other |
| expense_date | date | `YYYY-MM-DD` |
| created_at | datetime | set by server |
| owner_id | int | set from the JWT, never from the request body |

## Tech stack

Python 3.10+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2 + SQLite, PyJWT, passlib (bcrypt), OAuth2PasswordBearer.

## Project structure

```
app/
  main.py          # app creation, router registration, table creation
  config.py        # reads settings from .env
  database.py      # engine, session, get_db dependency
  models.py        # SQLAlchemy models (User, Expense)
  schemas.py       # Pydantic request/response models
  auth.py          # password hashing, JWT create/verify, get_current_user
  routers/
    auth.py        # /auth/register, /auth/login, /auth/me
    expenses.py    # /expenses CRUD
tests/test_api.py  # automated tests
```

## Setup

```bash
git clone <your-repo-url>
cd expense-tracker-api

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env             # Windows: copy .env.example .env
# then edit .env and set SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"   # use this output as SECRET_KEY

uvicorn app.main:app --reload
```

Open Swagger UI at http://127.0.0.1:8000/docs.
Click **Authorize**, enter your username and password, and all protected routes will use your token.

## Environment variables

| Variable | Description | Example |
|---|---|---|
| SECRET_KEY | Secret used to sign JWTs (required) | long random string |
| ALGORITHM | JWT algorithm | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token lifetime | 30 |
| DATABASE_URL | SQLAlchemy URL | sqlite:///./expenses.db |

## Endpoints

| Method | Route | Auth | Purpose | Status codes |
|---|---|---|---|---|
| POST | /auth/register | No | Create a user | 201, 409 if email/username exists, 422 |
| POST | /auth/login | No | Get a JWT (form: username + password) | 200, 401 |
| GET | /auth/me | Yes | Current user | 200, 401 |
| POST | /expenses | Yes | Create expense | 201, 422 |
| GET | /expenses?skip=0&limit=10 | Yes | List your expenses | 200 |
| GET | /expenses/{id} | Yes | Get one expense | 200, 404 |
| PUT | /expenses/{id} | Yes | Update expense | 200, 404, 422 |
| DELETE | /expenses/{id} | Yes | Delete expense | 204, 404 |

Notes:
- Passwords are hashed with bcrypt, never stored in plain text.
- Invalid, missing or expired tokens return `401`.
- Another user's expense returns `404`, so its existence is not leaked.

## Run the tests

```bash
pytest -q
```

## Screenshots

Add Swagger `/docs` screenshots in `screenshots/`: register, login, Authorize, and POST / GET / PUT / DELETE for expenses.
