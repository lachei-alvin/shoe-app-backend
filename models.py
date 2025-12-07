import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    Float,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import Session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Generator

# Define the path for the SQLite database file
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
DB_FILE_NAME = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")

# Create the SQLAlchemy Engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Configure the SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for the declarative ORM models
Base = declarative_base()

# --- Database Models ---


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    cart_items = relationship("Cart", back_populates="user")
    orders = relationship("Order", back_populates="user")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    image_url = Column(
        String, default="https://placehold.co/600x400/1e40af/ffffff?text=Shoe"
    )
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="products")
    cart_items = relationship("Cart", back_populates="product")


class Cart(Base):
    __tablename__ = "cart"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    order_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float)
    status = Column(String, default="Pending")
    user = relationship("User", back_populates="orders")


# --- Database Dependency Generator ---


def get_db() -> Generator[Session, None, None]:
    """Creates a database session, yields it, and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_database(db: Session):
    """Inserts essential data if the database is empty."""

    # NOTE ON HASHING: This is a pre-hashed string for the mock user "password".
    MOCK_ADMIN_HASH = "$2b$12$K.lVfP.tH6.wY/5Jb4x.rOQ1R2Yk5fN7W9X0Z8C0Q5fN7W9X0Z8C0Q"

    # 1. Create a Default Admin User (if not exists)
    if db.query(User).filter(User.username == "MockAdmin").first() is None:
        admin_user = User(
            username="MockAdmin",
            email="admin@shoeapp.com",
            hashed_password=MOCK_ADMIN_HASH,
            is_admin=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print("--- [DB SEED] Created default MockAdmin with static hash. ---")

    # 2. Create Default Categories

    # Define 6 categories
    category_names = ["Running", "Casual", "Dress", "Boots", "Sandals", "Athletic"]
    categories_map = {}

    for name in category_names:
        category = db.query(Category).filter(Category.name == name).first()
        if category is None:
            category = Category(name=name)
            db.add(category)
            db.commit()
            db.refresh(category)
            print(f"--- [DB SEED] Created default '{name}' category. ---")
        categories_map[name] = category

    # 3. Create Default Products (one per category)

    products_to_seed = [
        {
            "name": "Air Sprint Pro",
            "description": "Ultra-lightweight racer built for marathon performance and speed work.",
            "price": 189.99,
            "image_url": "https://placehold.co/400x300/60a5fa/ffffff?text=Runner",
            "category_name": "Running",
        },
        {
            "name": "Urban Cloud Walker",
            "description": "A classic, low-profile leather sneaker featuring a memory foam insole.",
            "price": 85.00,
            "image_url": "https://placehold.co/400x300/4ade80/ffffff?text=Casual",
            "category_name": "Casual",
        },
        {
            "name": "Executive Oxford",
            "description": "Hand-stitched full-grain leather dress shoe with a polished finish.",
            "price": 199.50,
            "image_url": "https://placehold.co/400x300/9333ea/ffffff?text=Dress",
            "category_name": "Dress",
        },
        {
            "name": "Mountain Hiker",
            "description": "Waterproof tactical boots with ankle support and extreme traction grip.",
            "price": 125.75,
            "image_url": "https://placehold.co/400x300/f97316/ffffff?text=Boots",
            "category_name": "Boots",
        },
        {
            "name": "Summer Breeze Flip-Flop",
            "description": "Contoured footbed and non-slip sole, perfect for the beach or pool.",
            "price": 35.00,
            "image_url": "https://placehold.co/400x300/2dd4bf/ffffff?text=Sandal",
            "category_name": "Sandals",
        },
        {
            "name": "Gym Cross Trainer",
            "description": "Versatile shoe offering lateral support and cushioning for all gym activities.",
            "price": 105.99,
            "image_url": "https://placehold.co/400x300/f87171/ffffff?text=Athletic",
            "category_name": "Athletic",
        },
    ]

    for item in products_to_seed:
        if db.query(Product).filter(Product.name == item["name"]).first() is None:
            product = Product(
                name=item["name"],
                description=item["description"],
                price=item["price"],
                image_url=item["image_url"],
                category_id=categories_map[item["category_name"]].id,
            )
            db.add(product)
            print(f"--- [DB SEED] Created new '{item['name']}' product. ---")

    db.commit()


# Helper function to create the tables in the database
def create_tables():
    """Initializes the database, preserving data if the file already exists."""

    if os.path.exists(DB_FILE_NAME):
        # os.remove(DB_FILE_NAME)  # <-- THIS LINE IS NOW COMMENTED OUT TO PRESERVE YOUR DATA!
        print(
            f"--- [DB INIT] Reusing existing database file: {DB_FILE_NAME}. Existing data will be preserved. ---"
        )
    else:
        print(f"--- [DB INIT] Creating new database file: {DB_FILE_NAME}. ---")

    Base.metadata.create_all(bind=engine)

    # Seed data immediately after creation
    # seed_database checks if essential data already exists, so it is safe to run.
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


# Initialize tables on import
create_tables()
