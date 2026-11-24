# AgriMart Backend

FastAPI + PostgreSQL API for AgriMart — an online store for agricultural
products sold by one farmer. The Next.js frontend consumes this API.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edit SECRET_KEY / DATABASE_URL
```

Local dev runs on SQLite by default (`agrimart.db`), so no database
setup is needed to try it. For PostgreSQL, set in `.env`:

```
DATABASE_URL=postgresql+psycopg://agrimart:agrimart@localhost:5432/agrimart
```

## Run

```bash
uvicorn app.main:app --reload
```

- API docs (Swagger): http://127.0.0.1:8000/docs
- Health check: `GET /health`

Or with Docker (PostgreSQL included), from the repo root:

```bash
docker compose up --build
```

## Database migrations

```bash
alembic revision --autogenerate -m "Describe the change"
alembic upgrade head
```

(Tables are also created automatically on app startup for local dev.)

## Tests

```bash
python -m pytest tests/ -v
```

Tests use an in-memory SQLite database — no PostgreSQL needed.

## API overview

| Area | Endpoints |
| --- | --- |
| Auth | `POST /auth/register`, `POST /auth/login` (form) / `POST /auth/login-json`, `GET /auth/me` |
| Categories | `GET /categories`, `GET /categories/{id}`, `POST/PUT/DELETE /categories/{id}` (admin) |
| Products | `GET /products?q&category_id&skip&limit`, `GET /products/{id}`, `POST/PUT/DELETE /products/{id}` (admin) |
| Cart | `GET /cart`, `POST /cart`, `PUT /cart/{item_id}`, `DELETE /cart/{item_id}`, `DELETE /cart` |
| Orders | `POST /orders`, `GET /orders` (own), `GET /orders/all` (admin), `GET /orders/{id}`, `PATCH /orders/{id}/status` (admin) |
| Payments | `GET /payments/info`, `GET /payments`, `GET /payments/{id}`, `PATCH /payments/{id}/verify` (admin) |

Auth is JWT (Bearer token). Roles: `admin` (the farmer) and `customer`.

## First admin account

Registering with `"role": "admin"` is allowed only while no admin
exists yet. After the first admin is created, only an admin can create
more admins. Create the first admin via `POST /auth/register`.

## Payments — COD + manual bKash / Nagad

There is no live payment-gateway integration (that needs merchant API
credentials). The flow is:

1. Customer checks out with `payment_method`: `cod`, `bkash`, or `nagad`.
2. For `bkash` / `nagad`, the customer must send `sender_number` and
   `transaction_id`. For `cod`, no transaction ID is needed.
3. The merchant numbers shown at checkout come from `GET /payments/info`
   (`BKASH_NUMBER=01736439950` in `.env`; `NAGAD_NUMBER` is a placeholder
   until the real number is provided).
4. The farmer checks the bKash/Nagad app and marks the payment
   `verified` or `rejected` via `PATCH /payments/{id}/verify`.
   The order's `payment_status` follows the payment.

## Environment variables

See `.env.example`: `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`,
`ACCESS_TOKEN_EXPIRE_MINUTES`, `BKASH_NUMBER`, `NAGAD_NUMBER`.
