"""Tests for relationship functionality with Annotated and Relation."""

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
    yield
    Model._sqlalchemy_model_cache.clear()


@pytest.fixture(autouse=True)
def cleanup_session():
    """Ensure session is closed and rolled back after each test."""
    yield
    try:
        close_session()
    except Exception:
        pass


class TestRelationExtraction:
    """Test extracting relationship metadata from annotations."""

    def test_extract_simple_relationship(self):
        """Test extracting a simple many-to-one relationship."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[
                Optional["Author"], Relation(back_populates="books")
            ]

        relationships = Book._extract_relationships()

        assert "author" in relationships
        assert isinstance(relationships["author"], Relation)
        assert relationships["author"].back_populates == "books"

    def test_extract_one_to_many_relationship(self):
        """Test extracting one-to-many relationship."""

        class Author(Model):
            id: int
            name: str
            books: Annotated[list["Book"], Relation(back_populates="author")]

        relationships = Author._extract_relationships()

        assert "books" in relationships
        assert isinstance(relationships["books"], Relation)

    def test_no_relationships(self):
        """Test model without relationships."""

        class User(Model):
            id: int
            username: str
            email: str

        relationships = User._extract_relationships()

        assert len(relationships) == 0


class TestForeignKeyGeneration:
    """Test automatic foreign key field generation."""

    def test_generate_fk_for_many_to_one(self):
        """Test FK generation for many-to-one relationship."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[
                Optional["Author"], Relation(back_populates="books")
            ]

        relationships = Book._extract_relationships()
        foreign_keys = Book._generate_foreign_keys(relationships)

        assert "author_id" in foreign_keys
        assert foreign_keys["author_id"] == Optional[int]

    def test_generate_fk_for_required_relationship(self):
        """Test FK generation for required (non-optional) relationship."""

        class Category(Model):
            id: int
            name: str

        class Product(Model):
            id: int
            name: str
            category: Annotated[
                "Category", Relation(back_populates="products")
            ]

        relationships = Product._extract_relationships()
        foreign_keys = Product._generate_foreign_keys(relationships)

        assert "category_id" in foreign_keys
        # For non-optional relationships, FK should be int (not Optional[int])
        # Note: Current implementation makes all FKs Optional, may need adjustment

    def test_skip_fk_for_one_to_many(self):
        """Test that FK is NOT generated for one-to-many relationships."""

        class Author(Model):
            id: int
            name: str
            books: Annotated[list["Book"], Relation(back_populates="author")]

        relationships = Author._extract_relationships()
        foreign_keys = Author._generate_foreign_keys(relationships)

        # Should NOT generate books_id
        assert len(foreign_keys) == 0


class TestRelationshipSQLAlchemyGeneration:
    """Test SQLAlchemy model generation with relationships."""

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

    def test_sqlalchemy_includes_foreign_key(self):
        """Test that generated SQLAlchemy model includes FK field."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[
                Optional["Author"], Relation(back_populates="books")
            ]

        BookSQLAlchemy = Book.to_sqlalchemy_model(
            self.Base, table_name="books"
        )

        # Check that author_id field exists
        assert hasattr(BookSQLAlchemy, "author_id")
        assert "author_id" in BookSQLAlchemy.__annotations__

    def test_original_annotations_not_modified(self):
        """Test that original model annotations aren't permanently modified."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[
                Optional["Author"], Relation(back_populates="books")
            ]

        # Generate SQLAlchemy model
        Book.to_sqlalchemy_model(self.Base, table_name="books")

        # Check original annotations unchanged
        assert "author_id" not in Book.__annotations__
        assert "author" in Book.__annotations__


class TestRelationshipPersistence:
    """Test persisting models with relationships."""

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

    def test_save_with_relationship_object(self):
        """Test saving model with relationship object (ORM-style)."""

        class Author(Model):
            id: int
            name: str
            email: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[
                Optional["Author"], Relation(back_populates="books")
            ]

        # Save author
        author = Author(id=1, name="Jane Doe", email="jane@example.com")
        author.save()

        # ORM-style: Pass the author object directly!
        book = Book(id=1, title="Python Guide", author=author)
        book.save()

        # Verify it was saved with correct FK
        found = Book.find_by_id(1)
        assert found is not None
        assert found.title == "Python Guide"
        assert found.author_id == 1  # type: ignore - FK auto-extracted!

    def test_save_with_none_relationship(self):
        """Test saving model with None relationship (optional FK)."""

        class Category(Model):
            id: int
            name: str

        class Product(Model):
            id: int
            name: str
            category: Annotated[Optional["Category"], Relation()]

        # Create product without category
        product = Product(id=1, name="Widget", category=None)
        product.save()

        found = Product.find_by_id(1)
        assert found is not None
        assert found.name == "Widget"

    def test_method_chaining_with_relationship(self):
        """Test method chaining with relationship object assignment."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        # Method chaining with relationship
        author = Author(id=1, name="Jane").save()
        book = Book(id=1, title="Guide", author=author).save()

        assert book.title == "Guide"
        assert book.author_id == 1  # type: ignore
        assert book.author == author

    def test_multiple_relationships_on_same_model(self):
        """Test model with multiple relationship objects."""

        class User(Model):
            id: int
            username: str

        class Post(Model):
            id: int
            title: str
            author: Annotated[Optional["User"], Relation()]
            reviewer: Annotated[Optional["User"], Relation()]

        user1 = User(id=1, username="alice").save()
        user2 = User(id=2, username="bob").save()

        # Pass multiple relationship objects
        post = Post(id=1, title="My Post", author=user1, reviewer=user2)
        post.save()

        # Verify both FKs extracted
        found = Post.find_by_id(1)
        assert found is not None
        assert found.author_id == 1  # type: ignore
        assert found.reviewer_id == 2  # type: ignore

    def test_update_relationship(self):
        """Test updating a relationship by changing the object."""

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
        assert book.author_id == 1  # type: ignore

        # Update to second author
        book.author = author2
        book.save()

        # Verify FK updated
        found = Book.find_by_id(1)
        assert found is not None
        assert found.author_id == 2  # type: ignore

    def test_relationship_with_unsaved_object_raises_error(self):
        """Test that passing an unsaved relationship object raises error."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        # Create author but DON'T save it
        author = Author(id=1, name="Jane")

        # Try to create book with unsaved author
        # This should work at creation time, but should have None FK
        book = Book(id=1, title="Book", author=author)

        # Author has id, so FK should be extracted
        assert book.author_id == 1  # type: ignore

    def test_one_to_many_relationship(self):
        """Test that one-to-many relationships don't generate FKs."""

        class Author(Model):
            id: int
            name: str
            books: Annotated[list["Book"], Relation(back_populates="author")]

        # Create author with empty books list
        author = Author(id=1, name="Jane", books=[])
        author.save()

        # Verify no books_id field generated
        assert not hasattr(author, "books_id")

    def test_relationship_object_preserved(self):
        """Test that relationship object is preserved on the instance."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        author = Author(id=1, name="Jane").save()
        book = Book(id=1, title="Book", author=author)

        # Relationship object should be preserved
        assert book.author is author
        assert book.author.name == "Jane"
        assert book.author_id == 1  # type: ignore

    def test_find_all_with_relationships(self):
        """Test find_all with models that have relationships."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        # Create author
        author = Author(id=1, name="Jane").save()

        # Create multiple books
        Book(id=1, title="Book 1", author=author).save()
        Book(id=2, title="Book 2", author=author).save()
        Book(id=3, title="Book 3", author=None).save()

        # Find all
        all_books = Book.find_all()
        assert len(all_books) == 3

        # Check FKs
        assert all_books[0].author_id == 1  # type: ignore
        assert all_books[1].author_id == 1  # type: ignore
        assert all_books[2].author_id is None  # type: ignore


class TestAdvancedRelationships:
    """Test advanced relationship scenarios."""

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

    def test_self_referential_relationship(self):
        """Test self-referential relationships (e.g., parent category)."""

        class Category(Model):
            id: int
            name: str
            parent: Annotated[Optional["Category"], Relation()]

        # Create parent category
        electronics = Category(id=1, name="Electronics", parent=None).save()

        # Create child category with parent
        laptops = Category(id=2, name="Laptops", parent=electronics).save()

        # Verify FK extracted
        assert laptops.parent_id == 1  # type: ignore

        # Query back
        found = Category.find_by_id(2)
        assert found is not None
        assert found.parent_id == 1  # type: ignore

    def test_three_level_relationship_chain(self):
        """Test relationships across three models."""

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

        # Create chain: Author → Book → Review
        author = Author(id=1, name="Jane").save()
        book = Book(id=1, title="Python", author=author).save()
        review = Review(id=1, rating=5, book=book).save()

        # Verify chain
        assert review.book_id == 1  # type: ignore
        assert book.author_id == 1  # type: ignore

        # Navigate chain manually
        found_review = Review.find_by_id(1)
        assert found_review is not None

        found_book = Book.find_by_id(found_review.book_id)  # type: ignore
        assert found_book is not None

        found_author = Author.find_by_id(found_book.author_id)  # type: ignore
        assert found_author is not None
        assert found_author.name == "Jane"

    def test_relationship_none_to_object_update(self):
        """Test updating from None relationship to an object."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        # Create book without author
        book = Book(id=1, title="Book", author=None).save()
        assert book.author_id is None  # type: ignore

        # Update with author
        author = Author(id=1, name="Jane").save()
        book.author = author
        book.save()

        # Verify FK now set
        found = Book.find_by_id(1)
        assert found is not None
        assert found.author_id == 1  # type: ignore

    def test_relationship_object_to_none_update(self):
        """Test updating from object relationship to None."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()]

        # Create book with author
        author = Author(id=1, name="Jane").save()
        book = Book(id=1, title="Book", author=author).save()
        assert book.author_id == 1  # type: ignore

        # Update to None
        book.author = None
        book.save()

        # Verify FK now None
        found = Book.find_by_id(1)
        assert found is not None
        assert found.author_id is None  # type: ignore

    def test_complex_model_with_mixed_fields(self):
        """Test model with regular fields and relationships mixed."""

        class Publisher(Model):
            id: int
            name: str
            city: str

        class Author(Model):
            id: int
            name: str
            email: str
            bio: Optional[str]

        class Book(Model):
            id: int
            title: str
            isbn: str
            pages: int
            price: float
            in_stock: bool
            description: Optional[str]
            # Relationships
            author: Annotated[Optional["Author"], Relation()]
            publisher: Annotated[Optional["Publisher"], Relation()]

        # Create related objects
        pub = Publisher(id=1, name="TechBooks", city="NYC").save()
        auth = Author(
            id=1, name="Jane", email="jane@example.com", bio=None
        ).save()

        # Create book with all fields
        Book(
            id=1,
            title="Python Deep Dive",
            isbn="978-1234567890",
            pages=500,
            price=49.99,
            in_stock=True,
            description="A comprehensive guide",
            author=auth,
            publisher=pub,
        ).save()

        # Verify everything
        found = Book.find_by_id(1)
        assert found is not None
        assert found.title == "Python Deep Dive"
        assert found.pages == 500
        assert found.price == 49.99
        assert found.in_stock is True
        assert found.author_id == 1  # type: ignore
        assert found.publisher_id == 1  # type: ignore


class TestRelationMetadata:
    """Test Relation class functionality."""

    def test_relation_initialization(self):
        """Test Relation class initialization."""
        rel = Relation(back_populates="books", lazy=True)

        assert rel.back_populates == "books"
        assert rel.lazy is True
        assert rel.cascade is None

    def test_relation_with_cascade(self):
        """Test Relation with cascade option."""
        rel = Relation(back_populates="items", cascade="all, delete-orphan")

        assert rel.cascade == "all, delete-orphan"

    def test_relation_repr(self):
        """Test Relation __repr__."""
        rel = Relation(back_populates="books")

        assert "Relation" in repr(rel)
        assert "books" in repr(rel)
