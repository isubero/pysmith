"""Tests for lazy loading relationships."""

from typing import Annotated, Optional

import pytest
from sqlalchemy.orm import DeclarativeBase

from pysmith.db import close_session, configure, drop_tables
from pysmith.models import Model, Relation


def get_fresh_base():
    """Create a fresh DeclarativeBase to avoid conflicts."""

    class FreshBase(DeclarativeBase):
        pass

    return FreshBase


@pytest.fixture(autouse=True)
def reset_model_cache():
    """Reset Model cache between tests to avoid schema conflicts."""
    Model._sqlalchemy_model_cache.clear()
    Model._lazy_loaders_setup.clear()
    yield
    Model._sqlalchemy_model_cache.clear()
    Model._lazy_loaders_setup.clear()


@pytest.fixture(autouse=True)
def cleanup_session():
    """Ensure session is closed and rolled back after each test."""
    yield
    try:
        close_session()
    except Exception:
        pass


class TestLazyLoading:
    """Test lazy loading of relationships."""

    def setup_method(self):
        """Setup fresh database for each test."""
        self.Base = get_fresh_base()
        configure("sqlite:///:memory:", self.Base)

    def teardown_method(self):
        """Clean up after each test."""
        try:
            drop_tables()
            close_session()
        except Exception:
            pass

    def test_lazy_load_relationship(self):
        """Test basic lazy loading of a relationship."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        # Create author and book
        author = Author(id=1, name="Jane Doe").save()
        Book(id=1, title="Python Guide", author=author).save()

        # Query book (without author loaded)
        found_book = Book.find_by_id(1)
        assert found_book is not None

        # Lazy load author by accessing it
        loaded_author = found_book.author  # ← Lazy load!

        # Verify it loaded correctly
        assert loaded_author is not None
        assert loaded_author.id == 1
        assert loaded_author.name == "Jane Doe"

    def test_lazy_load_caches_result(self):
        """Test that lazy loading caches the result."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        # Create data
        author = Author(id=1, name="Jane").save()
        book = Book(id=1, title="Book", author=author).save()

        # Query book
        found_book = Book.find_by_id(1)
        assert found_book is not None

        # First access - loads from DB
        first_access = found_book.author
        assert first_access is not None

        # Second access - should return same cached object
        second_access = found_book.author
        assert second_access is first_access  # Same object reference

    def test_lazy_load_none_relationship(self):
        """Test lazy loading when relationship is None."""

        class Category(Model):
            id: int
            name: str

        class Product(Model):
            id: int
            name: str
            category: Annotated[Optional["Category"], Relation()]

        # Create product without category
        product = Product(id=1, name="Widget", category=None).save()

        # Query back
        found = Product.find_by_id(1)
        assert found is not None

        # Access category - should be None
        loaded_category = found.category
        assert loaded_category is None

    def test_lazy_load_after_update(self):
        """Test lazy loading after updating a relationship."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        # Create two authors
        author1 = Author(id=1, name="Alice").save()
        author2 = Author(id=2, name="Bob").save()

        # Create book with first author
        book = Book(id=1, title="Book", author=author1).save()

        # Query and verify first author loads
        found = Book.find_by_id(1)
        assert found is not None
        assert found.author is not None
        assert found.author.name == "Alice"

        # Update to second author
        found.author = author2
        found.save()

        # Query again and verify second author loads
        updated = Book.find_by_id(1)
        assert updated is not None
        assert updated.author is not None
        assert updated.author.name == "Bob"

    def test_lazy_load_multiple_relationships(self):
        """Test lazy loading with multiple relationships on same model."""

        class User(Model):
            id: int
            username: str

        class Post(Model):
            id: int
            title: str
            author: Annotated[Optional["User"], Relation()]
            reviewer: Annotated[Optional["User"], Relation()]

        # Create users and post
        user1 = User(id=1, username="alice").save()
        user2 = User(id=2, username="bob").save()
        post = Post(id=1, title="Post", author=user1, reviewer=user2).save()

        # Query back
        found = Post.find_by_id(1)
        assert found is not None

        # Lazy load both relationships
        loaded_author = found.author
        loaded_reviewer = found.reviewer

        assert loaded_author is not None
        assert loaded_author.username == "alice"
        assert loaded_reviewer is not None
        assert loaded_reviewer.username == "bob"

    def test_lazy_load_chain(self):
        """Test lazy loading across a chain of relationships."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        class Review(Model):
            id: int
            rating: int
            book: Annotated[Optional["Book"], Relation()]

        # Create chain
        author = Author(id=1, name="Jane").save()
        book = Book(id=1, title="Python", author=author).save()
        review = Review(id=1, rating=5, book=book).save()

        # Query review and navigate chain
        found_review = Review.find_by_id(1)
        assert found_review is not None

        # Lazy load book
        loaded_book = found_review.book
        assert loaded_book is not None
        assert loaded_book.title == "Python"

        # Lazy load author from book
        loaded_author = loaded_book.author
        assert loaded_author is not None
        assert loaded_author.name == "Jane"

    def test_lazy_load_with_find_all(self):
        """Test lazy loading works with find_all."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        # Create author and books
        author = Author(id=1, name="Jane").save()
        Book(id=1, title="Book 1", author=author).save()
        Book(id=2, title="Book 2", author=author).save()

        # Find all books
        all_books = Book.find_all()
        assert len(all_books) == 2

        # Lazy load author from each book
        for book in all_books:
            loaded_author = book.author
            assert loaded_author is not None
            assert loaded_author.name == "Jane"

    def test_assignment_updates_cache(self):
        """Test that assigning a relationship updates the cache."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        # Create book
        author = Author(id=1, name="Jane").save()
        book = Book(id=1, title="Book", author=None).save()

        # Assign author (should update cache and FK)
        book.author = author

        # Access should return the assigned author (from cache)
        accessed = book.author
        assert accessed is author
        assert book.author_id == 1  # type: ignore

    def test_lazy_load_self_referential(self):
        """Test lazy loading with self-referential relationships."""

        class Category(Model):
            id: int
            name: str
            parent: Annotated[Optional["Category"], Relation()]

        # Create parent and child
        electronics = Category(id=1, name="Electronics", parent=None).save()
        laptops = Category(id=2, name="Laptops", parent=electronics).save()

        # Query child and lazy load parent
        found = Category.find_by_id(2)
        assert found is not None

        loaded_parent = found.parent
        assert loaded_parent is not None
        assert loaded_parent.name == "Electronics"
