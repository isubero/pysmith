"""
Example: Lazy Loading Relationships

Demonstrates Pysmith's lazy loading feature where accessing a relationship
automatically queries the related object - no manual joins needed!
"""

from typing import Annotated, Optional

from sqlalchemy.orm import DeclarativeBase

from pysmith.db import configure
from pysmith.models import Model, Relation


# Setup
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


class Book(Model):
    id: int
    title: str
    pages: int
    # Relationships with lazy loading!
    author: Annotated[Optional["Author"], Relation()] = None
    publisher: Annotated[Optional["Publisher"], Relation()] = None


class Review(Model):
    id: int
    rating: int
    comment: str
    book: Annotated[Optional["Book"], Relation()] = None


def example_basic_lazy_load():
    """Demonstrate basic lazy loading."""
    print("=" * 60)
    print("Example 1: Basic Lazy Loading")
    print("=" * 60)

    # Create author and book
    author = Author(id=1, name="Jane Doe", email="jane@example.com").save()
    Book(id=1, title="Python Mastery", pages=500, author=author).save()

    # Query the book
    found_book = Book.find_by_id(1)
    assert found_book is not None

    print(f"✓ Found book: {found_book.title}")

    # Lazy load: Just access .author - no manual query needed!
    print("\n  Accessing book.author...")
    loaded_author = found_book.author  # ← Lazy loads automatically!

    print(f"  ✨ Author lazy-loaded: {loaded_author.name}")
    print(f"     Email: {loaded_author.email}")
    print("     No manual Author.find_by_id() needed!")

    print()


def example_lazy_load_chain():
    """Demonstrate lazy loading across a chain of relationships."""
    print("=" * 60)
    print("Example 2: Lazy Loading Chains")
    print("=" * 60)

    # Create chain: Author → Book → Review
    author = Author(id=2, name="John Smith", email="john@example.com").save()
    book = Book(id=2, title="Django Guide", pages=400, author=author).save()
    Review(id=1, rating=5, comment="Excellent!", book=book).save()

    # Query the review
    found_review = Review.find_by_id(1)
    assert found_review is not None

    print(f"✓ Found review: {found_review.comment} ({found_review.rating}★)")

    # Lazy load the entire chain!
    print("\n  Lazy loading chain: Review → Book → Author")
    print(f"  Book: {found_review.book.title}")  # ← Lazy load book
    print(f"  Author: {found_review.book.author.name}")  # ← Lazy load author
    print("  ✨ All done without manual queries!")

    print()


def example_multiple_relationships():
    """Demonstrate lazy loading multiple relationships."""
    print("=" * 60)
    print("Example 3: Multiple Relationships")
    print("=" * 60)

    # Create related objects
    author = Author(id=3, name="Alice", email="alice@example.com").save()
    publisher = Publisher(id=1, name="TechBooks", city="NYC").save()

    # Create book with multiple relationships
    Book(
        id=3,
        title="Advanced Python",
        pages=600,
        author=author,
        publisher=publisher,
    ).save()

    # Query back
    found = Book.find_by_id(3)
    assert found is not None

    print(f"✓ Found book: {found.title}")

    # Lazy load both relationships
    print("\n  Lazy loading relationships...")
    print(f"  Author: {found.author.name} ({found.author.email})")
    print(f"  Publisher: {found.publisher.name}, {found.publisher.city}")
    print("  ✨ Both loaded automatically!")

    print()


def example_caching():
    """Demonstrate that lazy loading caches results."""
    print("=" * 60)
    print("Example 4: Caching (Avoid Repeated Queries)")
    print("=" * 60)

    # Create data
    author = Author(id=4, name="Bob", email="bob@example.com").save()
    Book(id=4, title="Caching Demo", pages=300, author=author).save()

    # Query book
    found = Book.find_by_id(4)
    assert found is not None

    print(f"✓ Found book: {found.title}")

    # First access - queries database
    print("\n  First access to book.author:")
    first = found.author
    print(f"    → Queried database, loaded: {first.name}")

    # Second access - returns cached result (no query!)
    print("\n  Second access to book.author:")
    second = found.author
    print(f"    → Returned from cache: {second.name}")

    # Verify it's the same object (cached)
    assert first is second
    print("    ✨ Same object reference - no duplicate query!")

    print()


def example_none_relationship():
    """Demonstrate lazy loading with None relationships."""
    print("=" * 60)
    print("Example 5: Optional Relationships (None)")
    print("=" * 60)

    # Create book without author
    Book(id=5, title="No Author Yet", pages=250, author=None).save()

    # Query back
    found = Book.find_by_id(5)
    assert found is not None

    print(f"✓ Found book: {found.title}")

    # Access author - should be None (no query)
    print("\n  Accessing book.author...")
    author = found.author
    print(f"    → Result: {author}")
    print("    ✨ Returns None without querying!")

    print()


def example_loop_no_n_plus_one():
    """Demonstrate lazy loading in loops (note: N+1 still possible)."""
    print("=" * 60)
    print("Example 6: Lazy Loading in Loops")
    print("=" * 60)

    # Create authors and books
    author1 = Author(id=5, name="Author A", email="a@example.com").save()
    author2 = Author(id=6, name="Author B", email="b@example.com").save()

    Book(id=10, title="Book 1", pages=100, author=author1).save()
    Book(id=11, title="Book 2", pages=200, author=author2).save()
    Book(id=12, title="Book 3", pages=150, author=author1).save()

    # Find all books
    all_books = Book.find_all()

    print(f"✓ Found {len(all_books)} books")
    print("\n  Lazy loading authors in loop:")

    # Lazy load authors
    for book in all_books:
        # Each access lazy-loads if not cached
        author_name = book.author.name if book.author else "Unknown"
        print(f"    - {book.title} by {author_name}")

    print("\n  ✨ Note: Each unique author queried once")
    print("     (Cache prevents duplicate queries for same author)")
    print("     For optimal performance, use eager loading (coming soon!)")

    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Pysmith Lazy Loading Examples")
    print("=" * 60)
    print()

    example_basic_lazy_load()
    example_lazy_load_chain()
    example_multiple_relationships()
    example_caching()
    example_none_relationship()
    example_loop_no_n_plus_one()

    print("=" * 60)
    print("✓ All examples completed!")
    print()
    print("Key Takeaway:")
    print("  Just access book.author - Pysmith handles the rest!")
    print("  No manual joins, no explicit queries needed.")
    print("=" * 60)
