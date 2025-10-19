"""
Example: Type Safety with Pysmith Models

Demonstrates how the save() method returns the correct type,
providing full type hints and autocomplete support.
"""

from typing import Optional

from sqlalchemy.orm import DeclarativeBase

from pysmith.db import configure
from pysmith.models import Model


# Setup
class Base(DeclarativeBase):
    pass


configure("sqlite:///:memory:", Base, echo=False)


# Define models
class User(Model):
    id: int
    username: str
    email: str
    age: Optional[int]


class Product(Model):
    id: int
    name: str
    price: float
    stock: int


def demonstrate_type_safety() -> None:
    """Demonstrate type safety after save()."""
    print("=== Type Safety Example ===\n")

    # Create and save a User
    user = User(id=1, username="alice", email="alice@example.com", age=30)

    # save() returns User, not Model!
    # This means you get full autocomplete and type checking
    saved_user = user.save()

    # Type checker knows this is a User
    print(f"User ID: {saved_user.id}")
    print(f"Username: {saved_user.username}")  # ✅ Type-safe!
    print(f"Email: {saved_user.email}")  # ✅ Type-safe!
    print(f"Age: {saved_user.age}")  # ✅ Type-safe!

    # Method chaining also preserves type
    another_user = User(
        id=2, username="bob", email="bob@example.com", age=25
    ).save()

    # Type checker knows this is a User
    print(f"\nAnother user: {another_user.username}")  # ✅ Type-safe!

    # Works with different model types too
    product = Product(id=1, name="Widget", price=19.99, stock=100).save()

    # Type checker knows this is a Product
    print(f"\nProduct: {product.name}")  # ✅ Type-safe!
    print(f"Price: ${product.price}")  # ✅ Type-safe!
    print(f"Stock: {product.stock}")  # ✅ Type-safe!

    # Try to access User attributes on Product - type checker will warn!
    # product.username  # ❌ Type error: Product has no attribute 'username'

    print("\n✓ Type safety working perfectly!")


def demonstrate_find_type_safety() -> None:
    """Demonstrate type safety with find methods."""
    print("\n=== Type Safety with Find Methods ===\n")

    # find_by_id returns Optional[User]
    found_user = User.find_by_id(1)

    if found_user:
        # Type checker knows this is a User
        print(f"Found user: {found_user.username}")  # ✅ Type-safe!
        print(f"Email: {found_user.email}")  # ✅ Type-safe!

    # find_all returns list[User]
    all_users = User.find_all()

    for user in all_users:
        # Type checker knows each item is a User
        print(f"- {user.username}: {user.email}")  # ✅ Type-safe!

    print("\n✓ Find methods are type-safe too!")


if __name__ == "__main__":
    demonstrate_type_safety()
    demonstrate_find_type_safety()

    print("\n" + "=" * 50)
    print("Type safety helps catch errors at development time!")
    print("Your IDE will provide autocomplete for all fields!")
    print("=" * 50)
