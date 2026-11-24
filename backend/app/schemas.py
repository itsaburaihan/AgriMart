"""Pydantic request / response schemas."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from .models import OrderStatus, PaymentMethod, PaymentStatus, UserRole


# ---------- Users / auth ----------
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    phone: str | None = Field(default=None, max_length=20)
    role: UserRole = UserRole.CUSTOMER  # admin only allowed while no admin exists


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Categories ----------
class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Products ----------
class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    price: Decimal = Field(gt=0)
    unit: str = Field(default="kg", max_length=20)
    stock: int = Field(default=0, ge=0)
    image_url: str | None = None
    category_id: int
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    unit: str | None = None
    stock: int | None = Field(default=None, ge=0)
    image_url: str | None = None
    category_id: int | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: Decimal
    unit: str
    stock: int
    image_url: str | None
    is_active: bool
    category_id: int
    category_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Cart ----------
class CartAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    price: Decimal
    quantity: int
    subtotal: Decimal

    model_config = {"from_attributes": True}


# ---------- Orders ----------
class OrderCreate(BaseModel):
    delivery_address: str = Field(min_length=5)
    phone: str = Field(min_length=8, max_length=20)
    payment_method: PaymentMethod
    # Required for bkash / nagad, forbidden for cod (validated in the router).
    sender_number: str | None = None
    transaction_id: str | None = None


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: Decimal

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    total_amount: Decimal
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    delivery_address: str
    phone: str
    created_at: datetime
    items: list[OrderItemOut] = []

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


# ---------- Payments ----------
class PaymentOut(BaseModel):
    id: int
    order_id: int
    method: PaymentMethod
    sender_number: str | None
    transaction_id: str | None
    amount: Decimal
    status: PaymentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentVerify(BaseModel):
    status: PaymentStatus  # verified or rejected (pending is not a valid decision)


class PaymentInfoOut(BaseModel):
    """Merchant numbers the frontend shows at checkout."""
    bkash_number: str
    nagad_number: str
