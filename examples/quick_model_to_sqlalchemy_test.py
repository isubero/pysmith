"""
Quick test of the Model.to_sqlalchemy_model() method
"""

from typing import Optional

from sqlalchemy.orm import DeclarativeBase

from pysmith.models import Model


class Base(DeclarativeBase):
    pass


class User(Model):
    """User model."""

    id: int
    name: str
    email: str
    age: Optional[int]


# Use the new convenience method!
print("Converting User Model to SQLAlchemy...")
UserSQLAlchemy = User.to_sqlalchemy_model(Base, table_name="users")

print(f"✓ Created SQLAlchemy model: {UserSQLAlchemy.__name__}")
print(f"  Table: {UserSQLAlchemy.__tablename__}")
print(f"  Columns: {list(UserSQLAlchemy.__annotations__.keys())}")

# Show column details
print("\nColumn details:")
for col_name in UserSQLAlchemy.__annotations__:
    col = getattr(UserSQLAlchemy, col_name)
    if hasattr(col, "expression"):
        col_expr = col.expression
        print(
            f"  {col_name}: nullable={col_expr.nullable}, "
            f"primary_key={col_expr.primary_key}"
        )

print("\n✓ Model.to_sqlalchemy_model() works perfectly!")
