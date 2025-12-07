from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Token Schemas REMOVED ---

# --- User Schemas ---


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_admin: bool

    class Config:
        from_attributes = True


# --- Product/Category Schemas ---
class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    image_url: str
    category_id: int


class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True


# --- Cart/Order Schemas ---


class CartAdd(BaseModel):
    product_id: int
    quantity: int = 1


class CartBase(BaseModel):
    user_id: int
    product_id: int
    quantity: int


class Cart(CartBase):
    id: int

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    user_id: int
    total_amount: float
    status: str


class Order(OrderBase):
    id: int
    order_date: datetime

    class Config:
        from_attributes = True
