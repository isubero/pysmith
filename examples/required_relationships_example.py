"""
Example: Required vs Optional Relationships

Demonstrates Pysmith's validation for required relationships,
showing clear error messages when required relationships are missing.
"""

from typing import Annotated, Optional

from sqlalchemy.orm import DeclarativeBase

from pysmith.db import configure
from pysmith.models import Model, Relation


class Base(DeclarativeBase):
    pass


configure("sqlite:///:memory:", Base, echo=False)


# Define models
class Author(Model):
    id: int
    name: str
    email: str


class Publisher(Model):
    id: int
    name: str
    city: str


class Category(Model):
    id: int
    name: str


class Book(Model):
    id: int
    title: str
    pages: int
    # Required relationship - every book MUST have an author
    author: Annotated["Author", Relation()] = None  # type: ignore
    # Optional relationships - book may or may not have these
    publisher: Annotated[Optional["Publisher"], Relation()] = None
    category: Annotated[Optional["Category"], Relation()] = None


def example_required_relationship_success() -> None:
    """✅ Providing required relationships works perfectly."""
    print("=" * 60)
    print("1. Required Relationship - Success")
    print("=" * 60)

    author = Author(id=1, name="Jane Doe", email="jane@example.com").save()
    print(f"✓ Created author: {author.name}")

    # Provide required relationship - works!
    book = Book(
        id=1,
        title="Python Mastery",
        pages=500,
        author=author,  # ← Required!
        publisher=None,  # ← Optional, None is OK
        category=None,  # ← Optional, None is OK
    ).save()

    print(f"✓ Created book: {book.title}")
    print("  - Author: " + (book.author.name if book.author else "None"))
    print(
        "  - Publisher: " + (book.publisher.name if book.publisher else "None")
    )
    print("  - Category: " + (book.category.name if book.category else "None"))
    print()


def example_required_relationship_error() -> None:
    """❌ Missing required relationship gives clear error."""
    print("=" * 60)
    print("2. Required Relationship - Clear Error Message")
    print("=" * 60)

    # Try to create book without author
    book = Book(
        id=2,
        title="Mystery Novel",
        pages=300,
        author=None,  # ← This is required!
        publisher=None,
        category=None,
    )

    try:
        book.save()
        print("❌ Should have raised ValueError!")
    except ValueError as e:
        print("✓ Caught validation error:")
        print(f"  Error: {e}")
        print()
        print("  Benefits:")
        print("  - Fails immediately (not at database)")
        print("  - Clear message about what's missing")
        print("  - Type information included")
        print()


def example_optional_relationships() -> None:
    """✅ Optional relationships can be None."""
    print("=" * 60)
    print("3. Optional Relationships - Flexibility")
    print("=" * 60)

    author = Author(id=2, name="John Smith", email="john@example.com").save()
    publisher = Publisher(id=1, name="Tech Press", city="San Francisco").save()
    category = Category(id=1, name="Programming").save()

    # Book with only author (required)
    book1 = Book(
        id=3,
        title="Quick Start Guide",
        pages=100,
        author=author,  # Required
        # Optional - all None
    ).save()

    print(f"✓ Book 1: {book1.title}")
    print(f"  - Has author: Yes ({book1.author.name})")
    print("  - Has publisher: No")
    print("  - Has category: No")
    print()

    # Book with all relationships
    book2 = Book(
        id=4,
        title="Complete Reference",
        pages=800,
        author=author,  # Required
        publisher=publisher,  # Optional, but provided
        category=category,  # Optional, but provided
    ).save()

    print(f"✓ Book 2: {book2.title}")
    print(f"  - Has author: Yes ({book2.author.name})")
    if book2.publisher:
        print(f"  - Has publisher: Yes ({book2.publisher.name})")
    else:
        print("  - Has publisher: No")
    if book2.category:
        print(f"  - Has category: Yes ({book2.category.name})")
    else:
        print("  - Has category: No")
    print()


def example_mixed_scenarios() -> None:
    """Different scenarios with mixed requirements."""
    print("=" * 60)
    print("4. Mixed Scenarios - Real-World Usage")
    print("=" * 60)

    author = Author(
        id=3, name="Alice Cooper", email="alice@example.com"
    ).save()
    publisher = Publisher(id=2, name="Code Books", city="Seattle").save()

    # Scenario 1: Minimal (only required)
    print("Scenario 1: Minimal book (only required fields)")
    book1 = Book(id=5, title="Minimal Guide", pages=50, author=author).save()
    print(f"  ✓ {book1.title} created with just author")
    print()

    # Scenario 2: With publisher
    print("Scenario 2: Book with publisher")
    book2 = Book(
        id=6,
        title="Professional Edition",
        pages=600,
        author=author,
        publisher=publisher,
    ).save()
    print(f"  ✓ {book2.title} created with author + publisher")
    print()

    # Scenario 3: Try to update by removing required relationship
    print("Scenario 3: Can't remove required relationship")
    try:
        book2.author = None  # type: ignore
        book2.author_id = None  # type: ignore
        book2.save()
        print("  ❌ Should have raised ValueError!")
    except ValueError as e:
        print(f"  ✓ Prevented: {e}")
    print()


def print_benefits() -> None:
    """Print summary of benefits."""
    print("=" * 60)
    print("Benefits of Required Relationship Validation")
    print("=" * 60)
    print()
    print("✅ Fail Fast")
    print("   - Errors at Python level, not database")
    print("   - Immediate feedback during development")
    print()
    print("✅ Clear Messages")
    print("   - Tells you exactly what's missing")
    print("   - Includes type information")
    print()
    print("✅ Type Safety")
    print("   - IDE knows author is required")
    print("   - Autocomplete guides you")
    print()
    print("✅ Flexibility")
    print("   - Use Optional[] for truly optional relationships")
    print("   - Mix required and optional as needed")
    print()
    print("✅ Database Consistency")
    print("   - NOT NULL constraints enforced")
    print("   - Data integrity guaranteed")
    print()


if __name__ == "__main__":
    example_required_relationship_success()
    example_required_relationship_error()
    example_optional_relationships()
    example_mixed_scenarios()
    print_benefits()
