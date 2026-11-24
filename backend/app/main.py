"""AgriMart API — FastAPI + PostgreSQL. Single-farmer online store."""
from fastapi import FastAPI

from .database import Base, engine
from .routers import auth, cart, categories, orders, payments, products

# Create tables on startup (Alembic migrations are for production changes).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgriMart API", description="Online store for agricultural products sold by one farmer.", version="0.1.0")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": "AgriMart API"}
