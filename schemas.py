from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime  # FIX: Import datetime for use in Pydantic schemas

# --- User Schemas ---


class UserBase(BaseModel):
    username: str
    email: str
    is_admin: bool = False


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


# --- Category Schemas ---


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# --- Product Schemas ---


class ProductBase(BaseModel):
    name: str
    description: str
    price: float = Field(..., gt=0, description="Price must be greater than zero.")
    image_url: str = "https://placehold.co/400x300/e0e7ff/1f2937?text=SHOE"
    # NOTE: Using Optional[int] for compatibility with Python < 3.10
    category_id: Optional[int] = None


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    # FIX APPLIED: Replaced 'int | None' with 'Optional[int]' for Python 3.8 compatibility.
    category_id: Optional[int]  # Allows category_id to be an integer or None

    class Config:
        from_attributes = True


# --- Cart Schemas ---


class CartAdd(BaseModel):
    product_id: int
    quantity: int = 1


class Cart(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int

    class Config:
        from_attributes = True


# --- Order Schemas ---


class OrderBase(BaseModel):
    total_amount: float
    status: str = "Pending"


class Order(OrderBase):
    id: int
    user_id: int
    order_date: datetime  # <-- This now works because datetime is imported

    class Config:
        from_attributes = True
