from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth / user schemas ----------
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Expense schemas ----------
class Category(str, Enum):
    food = "food"
    transport = "transport"
    rent = "rent"
    utilities = "utilities"
    shopping = "shopping"
    health = "health"
    entertainment = "entertainment"
    other = "other"


class ExpenseBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    amount: float = Field(gt=0, description="Amount spent, must be greater than 0")
    category: Category = Category.other
    expense_date: date


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(ExpenseBase):
    """Used for PUT: the full record is replaced."""


class ExpenseOut(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
