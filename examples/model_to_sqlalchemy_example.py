"""
Example: Converting pysmith.Model to SQLAlchemy models

This example demonstrates how to convert Model classes to
SQLAlchemy models for database operations.
"""

from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from pysmith.db.adapters import (
    create_sqlalchemy_model_from_annotations,
    create_sqlalchemy_model_from_model,
)
from pysmith.models import Model


# Define the SQLAlchemy Base
class Base(DeclarativeBase):
    pass


# ============================================================================
# Example 1: Convert a Model class to SQLAlchemy
# ============================================================================

print("=" * 70)
print("Example 1: Basic Model to SQLAlchemy Conversion")
print("=" * 70)


class User(Model):
    """User model with validation."""

    id: int
    username: str
    email: str
    age: Optional[int]
    is_active: bool


print(f"Original Model: {User.__name__}")
print(f"Fields: {list(User.__annotations__.keys())}")
print()

# Convert to SQLAlchemy
UserSQLAlchemy = create_sqlalchemy_model_from_model(
    User, Base, table_name="users"
)

print(f"SQLAlchemy Model: {UserSQLAlchemy.__name__}")
print(f"Table: {UserSQLAlchemy.__tablename__}")
print(f"Columns: {list(UserSQLAlchemy.__annotations__.keys())}")
print()


# ============================================================================
# Example 2: Custom table name and string lengths
# ============================================================================

print("=" * 70)
print("Example 2: Custom Configuration")
print("=" * 70)


class Article(Model):
    """Article model."""

    id: int
    title: str
    slug: str
    content: Optional[str]
    views: int


ArticleSQLAlchemy = create_sqlalchemy_model_from_model(
    Article,
    Base,
    table_name="blog_articles",  # Custom table name
    primary_key_field="id",
    string_length=500,  # Longer strings for content fields
)

print(f"Table name: {ArticleSQLAlchemy.__tablename__}")
print(f"Columns: {list(ArticleSQLAlchemy.__annotations__.keys())}")
print()


# ============================================================================
# Example 3: Create SQLAlchemy model from raw annotations
# ============================================================================

print("=" * 70)
print("Example 3: From Raw Annotations (no Model class)")
print("=" * 70)

# Define a model structure without creating a Model class
product_annotations = {
    "id": int,
    "name": str,
    "description": Optional[str],
    "price": float,
    "stock_quantity": int,
}

ProductSQLAlchemy = create_sqlalchemy_model_from_annotations(
    "Product",
    product_annotations,
    Base,
    table_name="products",
)

print(f"Created SQLAlchemy model: {ProductSQLAlchemy.__name__}")
print(f"Table: {ProductSQLAlchemy.__tablename__}")
print(f"Columns: {list(ProductSQLAlchemy.__annotations__.keys())}")
print()


# ============================================================================
# Example 4: Using the SQLAlchemy model with a database
# ============================================================================

print("=" * 70)
print("Example 4: Using SQLAlchemy Models with Database")
print("=" * 70)

# Create an in-memory SQLite database for testing
engine = create_engine("sqlite:///:memory:", echo=False)

# Create all tables
Base.metadata.create_all(engine)

# Use the converted model with a session
with Session(engine) as session:
    # Create a new user using the SQLAlchemy model
    new_user = UserSQLAlchemy(
        id=1,
        username="alice",
        email="alice@example.com",
        age=30,
        is_active=True,
    )

    session.add(new_user)
    session.commit()

    # Query the user back
    user = session.query(UserSQLAlchemy).filter_by(username="alice").first()

    print(f"Created user: {user.username}")
    print(f"Email: {user.email}")
    print(f"Age: {user.age}")
    print(f"Active: {user.is_active}")

print()


# ============================================================================
# Example 5: Multiple models for a complete schema
# ============================================================================

print("=" * 70)
print("Example 5: Multiple Models for Complete Schema")
print("=" * 70)


class Category(Model):
    """Category model."""

    id: int
    name: str
    description: Optional[str]


class Tag(Model):
    """Tag model."""

    id: int
    name: str
    color: Optional[str]


# Convert all models
CategorySQLAlchemy = create_sqlalchemy_model_from_model(
    Category, Base, table_name="categories"
)

TagSQLAlchemy = create_sqlalchemy_model_from_model(
    Tag, Base, table_name="tags"
)

print("Created SQLAlchemy models:")
print(
    f"  - {CategorySQLAlchemy.__name__} -> {CategorySQLAlchemy.__tablename__}"
)
print(f"  - {TagSQLAlchemy.__name__} -> {TagSQLAlchemy.__tablename__}")
print()


# ============================================================================
# Example 6: Workflow - Model validation then SQLAlchemy persistence
# ============================================================================

print("=" * 70)
print("Example 6: Complete Workflow (Validation + Persistence)")
print("=" * 70)


class Order(Model):
    """Order model with validation."""

    id: int
    order_number: str
    total_amount: float
    is_paid: bool


# Step 1: Use Model for validation
print("Step 1: Validate data with Model")
order_data = {
    "id": 1,
    "order_number": "ORD-001",
    "total_amount": 99.99,
    "is_paid": False,
}

validated_order = Order(**order_data)
print(
    f"  Validated: {validated_order.order_number} - ${validated_order.total_amount}"
)

# Step 2: Convert Model to SQLAlchemy for persistence
print("\nStep 2: Convert to SQLAlchemy for database storage")
OrderSQLAlchemy = create_sqlalchemy_model_from_model(
    Order, Base, table_name="orders"
)

# Step 3: Create tables and save
Base.metadata.create_all(engine)

with Session(engine) as session:
    # Create SQLAlchemy instance from validated data
    db_order = OrderSQLAlchemy(**order_data)
    session.add(db_order)
    session.commit()

    # Query back
    saved_order = session.query(OrderSQLAlchemy).first()
    print(f"  Saved to DB: {saved_order.order_number} (ID: {saved_order.id})")

print()
print("=" * 70)
print("All examples completed successfully! ✓")
print("=" * 70)
print()
print("Key takeaways:")
print("  1. Model classes provide validation")
print("  2. SQLAlchemy provides database persistence")
print("  3. Convert between them seamlessly")
print("  4. Use Model for API validation, SQLAlchemy for DB")
print("=" * 70)
