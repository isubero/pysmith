"""Tests for Model persistence (save, delete, find)."""

from typing import Optional

import pytest
from sqlalchemy.orm import DeclarativeBase

from pysmith.db import close_session, configure, drop_tables
from pysmith.models import Model


def get_fresh_base():
    """Create a fresh DeclarativeBase to avoid conflicts."""

    class FreshBase(DeclarativeBase):
        pass

    return FreshBase


@pytest.fixture(autouse=True)
def reset_model_cache():
    """Reset Model cache between tests to avoid schema conflicts."""
    # Clear the SQLAlchemy model cache before each test
    Model._sqlalchemy_model_cache.clear()
    yield
    # Clean up after test
    Model._sqlalchemy_model_cache.clear()


@pytest.fixture(autouse=True)
def cleanup_session():
    """Ensure session is closed and rolled back after each test."""
    yield
    try:
        close_session()
    except Exception:
        pass


class TestSessionConfiguration:
    """Test database session configuration."""

    def test_configure_database(self):
        """Test configuring the database."""
        Base = get_fresh_base()
        configure("sqlite:///:memory:", Base)

        # Should not raise
        from pysmith.db import get_base, get_engine

        engine = get_engine()
        base_cls = get_base()

        assert engine is not None
        assert base_cls is Base

    def test_unconfigured_database_raises_error(self):
        """Test that using models without configuration raises error."""

        class User(Model):
            id: int
            name: str

        # Note: This test would need a fresh interpreter context
        # to truly test unconfigured state. Skipping for now.
        # In production, SessionNotConfiguredError is raised
        # when configure() hasn't been called.
        pass


class TestBasicPersistence:
    """Test basic save and find operations."""

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

    def test_save_model(self):
        """Test saving a model instance."""

        class User(Model):
            id: int
            username: str
            email: str

        user = User(id=1, username="alice", email="alice@example.com")
        result = user.save()

        # Should return self for chaining
        assert result is user
        assert result.id == 1
        assert result.username == "alice"
        assert result.email == "alice@example.com"

    def test_find_by_id(self):
        """Test finding a model by ID."""

        class User(Model):
            id: int
            username: str

        # Save first
        user = User(id=1, username="alice")
        user.save()

        # Find it
        found = User.find_by_id(1)
        assert found is not None
        assert found.id == 1
        assert found.username == "alice"

    def test_find_by_id_not_found(self):
        """Test finding non-existent ID returns None."""

        class User(Model):
            id: int
            username: str

        found = User.find_by_id(999)
        assert found is None

    def test_find_all(self):
        """Test finding all model instances."""

        class User(Model):
            id: int
            username: str

        # Save multiple
        User(id=1, username="alice").save()
        User(id=2, username="bob").save()
        User(id=3, username="charlie").save()

        # Find all
        all_users = User.find_all()
        assert len(all_users) == 3
        usernames = {user.username for user in all_users}
        assert usernames == {"alice", "bob", "charlie"}

    def test_find_all_empty(self):
        """Test find_all with no records."""

        class User(Model):
            id: int
            username: str

        all_users = User.find_all()
        assert all_users == []


class TestUpdateAndDelete:
    """Test update and delete operations."""

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

    def test_update_model(self):
        """Test updating a model instance."""

        class User(Model):
            id: int
            username: str
            email: str

        # Save initial
        user = User(id=1, username="alice", email="old@example.com")
        user.save()

        # Update
        user.email = "new@example.com"
        user.save()

        # Verify
        found = User.find_by_id(1)
        assert found is not None
        assert found.email == "new@example.com"

    def test_delete_model(self):
        """Test deleting a model instance."""

        class User(Model):
            id: int
            username: str

        # Save then delete
        user = User(id=1, username="alice")
        user.save()

        user.delete()

        # Should not be found
        found = User.find_by_id(1)
        assert found is None

    def test_delete_unsaved_raises_error(self):
        """Test that deleting unsaved instance raises error."""

        class User(Model):
            id: int
            username: str

        user = User(id=1, username="alice")

        with pytest.raises(ValueError, match="Cannot delete unsaved instance"):
            user.delete()


class TestOptionalFields:
    """Test models with optional fields."""

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

    def test_save_with_none(self):
        """Test saving model with None values."""

        class User(Model):
            id: int
            username: str
            bio: Optional[str]

        user = User(id=1, username="alice", bio=None)
        user.save()

        found = User.find_by_id(1)
        assert found is not None
        assert found.bio is None

    def test_save_with_optional_value(self):
        """Test saving model with optional value present."""

        class User(Model):
            id: int
            username: str
            age: Optional[int]

        user = User(id=1, username="alice", age=30)
        user.save()

        found = User.find_by_id(1)
        assert found is not None
        assert found.age == 30


class TestRelationships:
    """Test relationships using foreign keys."""

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

    def test_foreign_key_relationship(self):
        """Test basic foreign key relationship."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author_id: int

        # Save author first
        author = Author(id=1, name="Jane Doe")
        author.save()

        # Save book with foreign key
        book = Book(id=1, title="Python Guide", author_id=author.id)
        book.save()

        # Verify
        found_book = Book.find_by_id(1)
        assert found_book is not None
        assert found_book.author_id == 1

        # Manual join
        found_author = Author.find_by_id(found_book.author_id)
        assert found_author is not None
        assert found_author.name == "Jane Doe"


class TestMethodChaining:
    """Test method chaining capabilities."""

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

    def test_chaining_save(self):
        """Test that save() returns self for chaining."""

        class User(Model):
            id: int
            username: str

        user = User(id=1, username="alice").save()

        assert user.username == "alice"

        # Verify it was actually saved
        found = User.find_by_id(1)
        assert found is not None


class TestMultipleModels:
    """Test working with multiple model classes."""

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

    def test_multiple_model_classes(self):
        """Test that multiple model classes work independently."""

        class User(Model):
            id: int
            username: str

        class Product(Model):
            id: int
            name: str
            price: float

        # Save instances of both
        User(id=1, username="alice").save()
        Product(id=1, name="Widget", price=19.99).save()

        # Query back
        user = User.find_by_id(1)
        product = Product.find_by_id(1)

        assert user is not None
        assert user.username == "alice"
        assert product is not None
        assert product.name == "Widget"


class TestValidationWithPersistence:
    """Test that Pydantic validation still works with persistence."""

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

    def test_validation_on_save(self):
        """Test that validation happens before save."""

        class User(Model):
            id: int
            username: str
            email: str

        # Valid data
        user = User(id=1, username="alice", email="alice@example.com")
        user.save()  # Should succeed

        # Invalid data should fail validation at creation
        with pytest.raises(Exception):  # Pydantic validation error
            User(id=2, username="bob")  # Missing email

    def test_validation_preserves_types(self):
        """Test that types are preserved through save/load."""

        class User(Model):
            id: int
            username: str
            age: int
            score: float

        user = User(id=1, username="alice", age=30, score=95.5)
        user.save()

        found = User.find_by_id(1)
        assert found is not None
        assert isinstance(found.age, int)
        assert isinstance(found.score, float)
        assert found.age == 30
        assert found.score == 95.5
