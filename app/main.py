from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.database import Base, engine
from app.routers import auth, expenses


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Expense Tracker API",
    description="A FastAPI backend with JWT authentication and user-owned expense CRUD.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(expenses.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Expense Tracker API is running. See /docs for Swagger UI."}
