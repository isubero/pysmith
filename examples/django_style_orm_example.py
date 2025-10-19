"""
Example: Django-style ORM with Pysmith Models

This example demonstrates how to use Pysmith's Model class
with built-in persistence, similar to Django ORM.
"""

from typing import Optional

from sqlalchemy.orm import DeclarativeBase

from pysmith.db import configure
from pysmith.models import Model


# Step 1: Define SQLAlchemy Base (required once per app)
class Base(DeclarativeBase):
    pass


# Step 2: Configure database (once at app startup)
configure("sqlite:///example.db", Base, echo=True)


# Step 3: Define your models
class Author(Model):
    id: int
    name: str
    email: str
    bio: Optional[str]


class Book(Model):
    id: int
    title: str
    author_id: int  # Foreign key (not nested object)
    pages: Optional[int]


def example_basic_crud() -> None:
    """Example: Basic CRUD operations."""
    print("\n=== Example 1: Basic CRUD ===\n")

    # Create and save
    author = Author(id=1, name="Jane Doe", email="jane@example.com", bio=None)
    author.save()
    print(f"✓ Saved author: {author.name}")

    # Read
    found = Author.find_by_id(1)
    if found:
        print(f"✓ Found author: {found.name}, {found.email}")

        # Update
        found.email = "jane.doe@example.com"
        found.save()
        print(f"✓ Updated author email: {found.email}")

    # Delete
    # found.delete()
    # print("✓ Deleted author")


def example_relations() -> None:
    """Example: Working with relations (foreign keys)."""
    print("\n=== Example 2: Relations (Foreign Keys) ===\n")

    # Create author first
    author = Author(
        id=2, name="John Smith", email="john@example.com", bio=None
    )
    author.save()
    print(f"✓ Saved author: {author.name}")

    # Create book with foreign key
    book = Book(id=1, title="Python Mastery", author_id=author.id, pages=350)
    book.save()
    print(f"✓ Saved book: {book.title} by author_id={book.author_id}")

    # Query back
    found_book = Book.find_by_id(1)
    if found_book:
        print(
            f"✓ Found book: {found_book.title}, "
            f"author_id={found_book.author_id}"
        )

        # Manually fetch the author
        found_author = Author.find_by_id(found_book.author_id)
        if found_author:
            print(f"  Author: {found_author.name}")


def example_validation() -> None:
    """Example: Pydantic validation still works."""
    print("\n=== Example 3: Validation ===\n")

    # Valid data
    user = Author(id=3, name="Valid User", email="valid@example.com", bio=None)
    print(f"✓ Valid: {user.name}")

    # Invalid data (missing required field) would raise error
    # Author(id=4, name="Invalid")  # This would raise ValidationError
    print("✓ Validation works via Pydantic")


def example_find_all() -> None:
    """Example: Query all records."""
    print("\n=== Example 4: Find All ===\n")

    # Create multiple authors
    authors_data = [
        {"id": 10, "name": "Alice", "email": "alice@example.com", "bio": None},
        {"id": 11, "name": "Bob", "email": "bob@example.com", "bio": None},
        {
            "id": 12,
            "name": "Charlie",
            "email": "charlie@example.com",
            "bio": None,
        },
    ]

    for data in authors_data:
        Author(**data).save()
        print(f"✓ Saved: {data['name']}")

    # Find all
    all_authors = Author.find_all()
    print(f"\n✓ Found {len(all_authors)} authors total:")
    for author in all_authors:
        print(f"  - {author.name} ({author.email})")


def example_method_chaining() -> None:
    """Example: Method chaining."""
    print("\n=== Example 5: Method Chaining ===\n")

    # Create and save in one line
    author = Author(
        id=20, name="Chained Author", email="chain@example.com", bio=None
    ).save()

    print(f"✓ Created and saved: {author.name}")


if __name__ == "__main__":
    print("=" * 60)
    print("Pysmith Django-style ORM Example")
    print("=" * 60)

    example_basic_crud()
    example_relations()
    example_validation()
    example_find_all()
    example_method_chaining()

    print("\n" + "=" * 60)
    print("✓ All examples completed!")
    print("=" * 60)
