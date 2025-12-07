import sys
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta

# FIX: Ensure compatibility for Annotated on Python < 3.9
if sys.version_info < (3, 9):
    try:
        from typing_extensions import Annotated, List
    except ImportError:
        # If running Python < 3.9 and typing_extensions is not installed
        from typing import List

        Annotated = object  # Placeholder to avoid immediate syntax error
    else:
        from typing import List
else:
    from typing import Annotated, List

# Importing models and utility
from models import get_db, Category, Product, Cart, Order, User
from schemas import (
    Category as CategorySchema,
    CategoryCreate,
    Product as ProductSchema,
    ProductBase,
    Cart as CartSchema,
    CartAdd,
    Order as OrderSchema,
    UserCreate,
    User as UserSchema,
)
from sqlalchemy.exc import IntegrityError
from utils import get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES

# ====================================================================
# --- DEPENDENCY ALIAS DEFINITIONS (Ensuring definition before use) ---
# ====================================================================

# 1. Database Session Dependency
SessionDep = Annotated[Session, Depends(get_db)]


# 2. Mock User Dependency Function
def get_mock_user(db: SessionDep) -> User:
    """
    MOCK FUNCTION: Returns the first user in the database, or creates a mock admin.
    This is used to bypass real authentication for development.
    """
    user = db.query(User).first()

    if user:
        return user
    else:
        # Fallback to create a MOCK ADMIN user if none exists
        mock_password = "mock_admin_password"
        # Local import here is safe as utils is defined outside app.py
        from utils import get_password_hash

        mock_admin = User(
            username="MockAdmin",
            email="admin@test.com",
            hashed_password=get_password_hash(mock_password),
            is_admin=True,
        )
        try:
            db.add(mock_admin)
            db.commit()
            db.refresh(mock_admin)
            return mock_admin
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to create mock admin: {e}"
            )


# 3. Current User Dependency Alias
UserDep = Annotated[User, Depends(get_mock_user)]


# 4. Admin Permission Checker
def check_admin_permission(current_user: User):
    """Helper to check if the user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )


# ====================================================================
# --- FastAPI Setup ---
# ====================================================================

app = FastAPI(title="Shoe App Backend (UNSECURED)")

# --- CORS Configuration ---
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====================================================================
# --- Public & Authentication Routes ---
# ====================================================================


@app.post("/users/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: SessionDep):
    """Creates a new user and hashes the password."""
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_admin=False,
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="User could not be created due to database constraint.",
        )


@app.post("/token")
async def login_for_access_token():
    """MOCK LOGIN: Always returns a success token payload."""
    return {"access_token": "mock_unsecured_token", "token_type": "bearer"}


@app.get("/users/me", response_model=UserSchema)
def read_users_me(current_user: UserDep):
    """Retrieves information about the current mock user."""
    return current_user


@app.get("/products", response_model=List[ProductSchema])
def list_products(db: SessionDep):
    """Retrieves all products."""
    return db.query(Product).all()


@app.get("/categories", response_model=List[CategorySchema])
def list_categories(db: SessionDep):
    """Retrieves all categories."""
    return db.query(Category).all()


# ====================================================================
# --- Customer Routes ---
# ====================================================================


@app.get("/cart/{user_id}", response_model=List[CartSchema])
def get_user_cart(user_id: int, current_user: UserDep, db: SessionDep):
    """
    Retrieves the contents of the current user's shopping cart.
    """
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other users' carts.",
        )

    cart_items = db.query(Cart).filter(Cart.user_id == user_id).all()
    return cart_items


@app.post("/cart/add", response_model=CartSchema)
def add_to_cart(cart_item_data: CartAdd, current_user: UserDep, db: SessionDep):
    """Adds a product to the current mock user's cart or increments quantity."""
    product_id = cart_item_data.product_id
    quantity = cart_item_data.quantity
    user_id = current_user.id

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    cart_item = (
        db.query(Cart)
        .filter(Cart.user_id == user_id, Cart.product_id == product_id)
        .first()
    )

    if cart_item:
        cart_item.quantity += quantity
        if cart_item.quantity <= 0:
            db.delete(cart_item)
            db.commit()
            raise HTTPException(status_code=200, detail="Item removed from cart.")

        db.commit()
        db.refresh(cart_item)
    else:
        if quantity <= 0:
            raise HTTPException(
                status_code=400, detail="Cannot add zero or negative quantity."
            )

        new_cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.add(new_cart_item)
        db.commit()
        db.refresh(new_cart_item)
        cart_item = new_cart_item

    return cart_item


@app.post(
    "/orders/create", response_model=OrderSchema, status_code=status.HTTP_201_CREATED
)
def place_order(current_user: UserDep, db: SessionDep):
    """
    Creates a new order from the user's cart items and clears the cart.
    [Image of a transaction flow showing: 1. Fetch Cart Items + Product Prices -> 2. Calculate Total Cost -> 3. Create a new record in the Orders table with total amount -> 4. Delete all associated records from the Cart table -> 5. Commit Transaction.]
    """
    user_id = current_user.id

    # 1. Fetch cart items and join with products to get prices
    cart_data = (
        db.query(Cart, Product).join(Product).filter(Cart.user_id == user_id).all()
    )

    if not cart_data:
        raise HTTPException(
            status_code=400, detail="Cart is empty, cannot place order."
        )

    # 2. Calculate Total Amount
    total_amount = sum(
        cart_item.quantity * product.price for cart_item, product in cart_data
    )

    # 3. Create the Order
    new_order = Order(user_id=user_id, total_amount=total_amount, status="Processing")
    db.add(new_order)

    # 4. Clear the Cart
    db.query(Cart).filter(Cart.user_id == user_id).delete()

    # 5. Commit the Transaction
    db.commit()
    db.refresh(new_order)

    return new_order


@app.get("/orders/user/{user_id}", response_model=List[OrderSchema])
def list_orders_by_user(user_id: int, current_user: UserDep, db: SessionDep):
    """Retrieves orders for a specific user."""
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other users' orders.",
        )

    return db.query(Order).filter(Order.user_id == user_id).all()


# ====================================================================
# --- Admin Routes ---
# ====================================================================

# --- Admin Product CRUD ---


@app.post(
    "/products/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED
)
def create_product(product_data: ProductBase, current_user: UserDep, db: SessionDep):
    """Admin: Creates a new product."""
    check_admin_permission(current_user)

    db_product = Product(**product_data.model_dump())

    try:
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError as e:
        db.rollback()
        if "FOREIGN KEY constraint failed" in str(e):
            raise HTTPException(
                status_code=400, detail="Invalid category_id specified."
            )
        raise HTTPException(status_code=400, detail="Product could not be created.")


@app.put("/products/{product_id}", response_model=ProductSchema)
def update_product(
    product_id: int, product_data: ProductBase, current_user: UserDep, db: SessionDep
):
    """Admin: Updates an existing product."""
    check_admin_permission(current_user)

    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in product_data.model_dump().items():
        setattr(db_product, key, value)

    try:
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Update failed, check if category_id is valid."
        )


@app.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, current_user: UserDep, db: SessionDep):
    """Admin: Deletes a product."""
    check_admin_permission(current_user)

    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(db_product)
    db.commit()
    return {"message": f"Product ID {product_id} deleted successfully."}


# --- Admin Category CRUD ---


@app.post(
    "/categories/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED
)
def create_category(category: CategoryCreate, current_user: UserDep, db: SessionDep):
    """Admin: Creates a new category."""
    check_admin_permission(current_user)

    db_category = Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.put("/categories/{category_id}", response_model=CategorySchema)
def update_category(
    category_id: int,
    category_data: CategoryCreate,
    current_user: UserDep,
    db: SessionDep,
):
    """Admin: Updates an existing category's name."""
    check_admin_permission(current_user)

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.name = category_data.name
    db.commit()
    db.refresh(category)
    return category


@app.delete("/categories/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(category_id: int, current_user: UserDep, db: SessionDep):
    """Admin: Deletes a category."""
    check_admin_permission(current_user)

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()
    return {"message": f"Category ID {category_id} deleted successfully."}


# --- Admin Orders ---


@app.get("/orders", response_model=List[OrderSchema])
def list_all_orders(current_user: UserDep, db: SessionDep):
    """Admin: Retrieves all orders."""
    check_admin_permission(current_user)
    return db.query(Order).all()


# --- Admin Users ---
@app.get("/users/all", response_model=List[UserSchema])
def read_all_users(current_user: UserDep, db: SessionDep):
    """Admin: Retrieves all users."""
    check_admin_permission(current_user)
    return db.query(User).all()


@app.post("/admin/promote/{username}", response_model=UserSchema)
def promote_user_to_admin(username: str, current_user: UserDep, db: SessionDep):
    """Admin: Promotes a user to admin."""
    check_admin_permission(current_user)

    user_to_promote = db.query(User).filter(User.username == username).first()
    if not user_to_promote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user_to_promote.is_admin:
        return user_to_promote

    user_to_promote.is_admin = True
    db.commit()
    db.refresh(user_to_promote)

    return user_to_promote


@app.get("/")
def read_root():
    return {"message": "Shoe App Backend Running"}
