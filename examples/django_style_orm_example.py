"""
Example: Django-style ORM with Pysmith Models

This example demonstrates how to use Pysmith's Model class
with built-in persistence and ORM-style relationships.
"""

from typing import Annotated, Optional

from sqlalchemy.orm import DeclarativeBase

from pysmith.db import configure
from pysmith.models import Model, Relation


# Step 1: Define SQLAlchemy Base (required once per app)
class Base(DeclarativeBase):
    pass


# Step 2: Configure database (once at app startup)
configure("sqlite:///:memory:", Base, echo=False)


# Step 3: Define your models with relationships
class Author(Model):
    id: int
    name: str
    email: str
    bio: Optional[str]
    books: Annotated[list["Book"], Relation(back_populates="author")] = []


class Book(Model):
    id: int
    title: str
    pages: Optional[int]
    # Foreign key 'author_id' auto-generated!
    author: Annotated[Optional["Author"], Relation(back_populates="books")] = (
        None
    )


def example_basic_crud() -> None:
    """Example: Basic CRUD operations."""
    print("\n=== Example 1: Basic CRUD ===\n")

    # Create and save
    author = Author(
        id=1, name="Jane Doe", email="jane@example.com", bio=None, books=[]
    )
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
    """Example: ORM-style relationships."""
    print("\n=== Example 2: ORM-Style Relationships ===\n")

    # Create author
    author = Author(
        id=2, name="John Smith", email="john@example.com", bio=None, books=[]
    )
    author.save()
    print(f"✓ Saved author: {author.name}")

    # ORM-style: Pass author object directly!
    book = Book(id=1, title="Python Mastery", pages=350, author=author)
    book.save()
    print(f"✓ Saved book: {book.title}")
    print(f"  author_id auto-extracted: {book.author_id}")  # type: ignore

    # Query back
    found_book = Book.find_by_id(1)
    if found_book:
        print(f"✓ Found book: {found_book.title}")
        print(f"  author_id: {found_book.author_id}")  # type: ignore

        # Manually fetch the author (lazy loading coming soon!)
        found_author = Author.find_by_id(found_book.author_id)  # type: ignore
        if found_author:
            print(f"  Author: {found_author.name}")


def example_validation() -> None:
    """Example: Pydantic validation still works."""
    print("\n=== Example 3: Validation ===\n")

    # Valid data
    user = Author(
        id=3, name="Valid User", email="valid@example.com", bio=None, books=[]
    )
    print(f"✓ Valid: {user.name}")

    # Invalid data (missing required field) would raise error
    # Author(id=4, name="Invalid")  # This would raise ValidationError
    print("✓ Validation works via Pydantic")


def example_find_all() -> None:
    """Example: Query all records."""
    print("\n=== Example 4: Find All ===\n")

    # Create multiple authors
    authors_data = [
        {
            "id": 10,
            "name": "Alice",
            "email": "alice@example.com",
            "bio": None,
            "books": [],
        },
        {
            "id": 11,
            "name": "Bob",
            "email": "bob@example.com",
            "bio": None,
            "books": [],
        },
        {
            "id": 12,
            "name": "Charlie",
            "email": "charlie@example.com",
            "bio": None,
            "books": [],
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
    """Example: Method chaining with relationships."""
    print("\n=== Example 5: Method Chaining ===\n")

    # Create and save in one line
    author = Author(
        id=20,
        name="Chained Author",
        email="chain@example.com",
        bio=None,
        books=[],
    ).save()

    # Chain with relationships!
    book = Book(id=20, title="Chained Book", pages=200, author=author).save()

    print(f"✓ Created and saved author: {author.name}")
    print(f"✓ Created and saved book: {book.title}")
    print(f"  author_id auto-extracted: {book.author_id}")  # type: ignore


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
